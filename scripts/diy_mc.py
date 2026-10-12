"""DIY 我的麦 —— 组合、试算与比价引擎。

用法：
    python scripts/diy_mc.py demo                 # 离线演示（无需 Token）
    python scripts/diy_mc.py diy --budget 30 --kcal 700 --like 辣 --no 牛肉
    python scripts/diy_mc.py diy --period 早餐 --channel 到店 --json
    python scripts/diy_mc.py probe                # 联调真实 MCP（需 MCD_MCP_TOKEN）
    python scripts/diy_mc.py tools                # 列出 MCP 真实工具清单

设计原则：
  1. 价格以后端 calculate-price 为准（live 模式）；离线演示用本地规则模拟同一套逻辑。
  2. 组合优先走「套餐 + 套餐内替换」，这条路径通常比单品自由组合更便宜。
  3. 引擎只做筛选、组合、排序和呈现，不做任何医疗或营养建议。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from itertools import product
from typing import Any, Iterable

# ---------------------------------------------------------------- 可调权重

W_TASTE = 2.0          # 每命中一个口味偏好
W_IN_TARGET = 3.0      # 热量落在目标区间
W_VALUE = 2.0          # 预算余量（越省越高）
W_COUPON = 2.0         # 券利用率
KCAL_PENALTY_PER_100 = 1.0   # 热量偏离目标区间时的惩罚系数
MAX_RESULTS = 3
MAX_SET_COMBOS = 200   # 单个套餐的替换组合枚举上限，防止组合爆炸


# ---------------------------------------------------------------- 数据结构

@dataclass
class Constraints:
    likes: list[str] = field(default_factory=list)
    dislikes: list[str] = field(default_factory=list)
    budget: float = 30.0
    kcal_min: int | None = None
    kcal_max: int | None = None
    period: str | None = None
    channel: str = "外送"
    want_dessert: bool = False

    def describe(self) -> str:
        parts = []
        if self.likes:
            parts.append("口味=" + "+".join(self.likes))
        parts.append(f"预算≤¥{self.budget:.0f}")
        if self.kcal_min or self.kcal_max:
            lo = self.kcal_min if self.kcal_min is not None else "不限"
            hi = self.kcal_max if self.kcal_max is not None else "不限"
            parts.append(f"热量 {lo}–{hi} kcal")
        parts.append(self.channel + "(" + (self.period or "任意时段") + ")")
        if self.dislikes:
            parts.append("排除：" + "、".join(self.dislikes))
        return " · ".join(parts)


@dataclass
class LineItem:
    code: str
    name: str
    qty: int = 1
    price: float = 0.0
    kcal: float = 0.0
    protein: float = 0.0
    fat: float = 0.0
    carb: float = 0.0
    sodium: float = 0.0
    tags: list[str] = field(default_factory=list)
    is_bundle: bool = False   # 整包计价的套餐行，不计入组合展示


@dataclass
class Scheme:
    label: str
    set_name: str | None
    items: list[LineItem]
    swaps: list[str]
    original: float
    coupons: list[dict[str, Any]]
    final: float
    kcal: float
    protein: float
    fat: float
    carb: float
    sodium: float
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)

    @property
    def discount(self) -> float:
        return max(0.0, self.original - self.final)


# ---------------------------------------------------------------- 数据装载

class MockSource:
    """离线样例数据源（对应各 MCP 工具返回）。"""

    name = "离线样例数据（非麦当劳真实菜单）"

    def __init__(self) -> None:
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
        import mock_data  # type: ignore

        self._data = mock_data.as_mcp_like()

    def store(self) -> dict[str, Any]:
        return self._data["store"]

    def meals(self) -> list[dict[str, Any]]:
        return self._data["meals"]

    def nutrition(self) -> list[dict[str, Any]]:
        return self._data["nutrition"]

    def details(self) -> dict[str, dict[str, Any]]:
        return self._data["details"]

    def coupons(self) -> list[dict[str, Any]]:
        return self._data["coupons"]

    def price(self, items: list[LineItem], coupons: list[dict[str, Any]]) -> dict[str, Any]:
        """本地模拟 calculate-price：凑单满减，账号券与门店券各限一张。"""
        total = sum(i.price * i.qty for i in items)
        chosen, discount = choose_coupons(total, coupons)
        return {
            "original": round(total, 2),
            "discount": round(discount, 2),
            "final": round(max(0.0, total - discount), 2),
            "coupons": chosen,
            "engine": "local-mock",
        }


class LiveSource:
    """真实数据源：通过麦当劳中国官方 MCP Server 取数。"""

    name = "麦当劳中国官方 MCP Server"

    def __init__(self, store_code: str | None = None, address: str | None = None) -> None:
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
        from mcd_client import McdMcpClient  # type: ignore

        self.client = McdMcpClient()
        self.client.initialize()
        self._meals: list[dict[str, Any]] | None = None
        self._nutrition: list[dict[str, Any]] | None = None
        self._details: dict[str, dict[str, Any]] = {}
        self.store_code = store_code
        self.address = address

    def _call(self, tool: str, args: dict[str, Any] | None = None) -> Any:
        return self.client.call_tool(tool, args or {})

    @staticmethod
    def _pick(payload: Any, *keys: str) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in keys:
                value = payload.get(key)
                if isinstance(value, list):
                    return value
            for value in payload.values():
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    return value
        return []

    def store(self) -> dict[str, Any]:
        stores = self._pick(self._call("query-nearby-stores", {"address": self.address}), "stores", "data")
        return stores[0] if stores else {}

    def meals(self) -> list[dict[str, Any]]:
        if self._meals is None:
            self._meals = self._pick(
                self._call("query-meals", {"storeCode": self.store_code}), "meals", "products", "data"
            )
        return self._meals or []

    def nutrition(self) -> list[dict[str, Any]]:
        if self._nutrition is None:
            self._nutrition = self._pick(
                self._call("list-nutrition-foods"), "foods", "nutrition", "data"
            )
        return self._nutrition or []

    def details(self) -> dict[str, dict[str, Any]]:
        return self._details

    def detail(self, code: str) -> dict[str, Any]:
        if code not in self._details:
            self._details[code] = self._call("query-meal-detail", {"mealCode": code}) or {}
        return self._details[code]

    def coupons(self) -> list[dict[str, Any]]:
        mine = self._pick(self._call("query-my-coupons"), "coupons", "data")
        store = self._pick(
            self._call("query-store-coupons", {"storeCode": self.store_code}), "coupons", "data"
        )
        return [dict(c, source="账号") for c in mine] + [dict(c, source="门店") for c in store]

    def price(self, items: list[LineItem], coupons: list[dict[str, Any]]) -> dict[str, Any]:
        """真实计价：把候选券一并交给后端，以后端结果为准。"""
        products = [{"productCode": i.code, "quantity": i.qty} for i in items]
        payload = {
            "storeCode": self.store_code,
            "products": products,
            "orderType": "外送",
        }
        if coupons:
            payload["coupons"] = [c.get("couponId") for c in coupons if c.get("couponId")]
        result = self._call("calculate-price", payload)
        if not isinstance(result, dict):
            raise RuntimeError("calculate-price 返回结构无法识别")
        original = float(result.get("originalPrice") or result.get("totalPrice") or 0)
        final = float(result.get("payPrice") or result.get("finalPrice") or original)
        return {
            "original": round(original, 2),
            "discount": round(max(0.0, original - final), 2),
            "final": round(final, 2),
            "coupons": coupons,
            "engine": "mcd-mcp/calculate-price",
        }


# ---------------------------------------------------------------- 券的择优

def choose_coupons(total: float, coupons: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], float]:
    """在"每个来源最多用一张"的约束下，暴力枚举出优惠最大的一组券。"""
    pool = [c for c in coupons if float(c.get("threshold") or 0) <= total]
    if not pool:
        return [], 0.0

    by_source: dict[str, list[dict[str, Any]]] = {}
    for coupon in pool:
        by_source.setdefault(str(coupon.get("source") or "其他"), []).append(coupon)

    sources = list(by_source)
    best: tuple[list[dict[str, Any]], float] = ([], 0.0)
    for combo in product(*([[None] + by_source[s] for s in sources])):
        picked = [c for c in combo if c]
        discount = sum(float(c.get("discount") or 0) for c in picked)
        if discount > best[1]:
            best = (picked, discount)
    return best[0], best[1]


# ---------------------------------------------------------------- 组合构造

def nutrition_index(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        code = row.get("code") or row.get("productCode") or row.get("mealCode")
        if code:
            index[str(code)] = row
    return index


def to_item(code: str, name: str, price: float, qty: int, meals: dict[str, dict[str, Any]],
            nutrition: dict[str, dict[str, Any]]) -> LineItem:
    meal = meals.get(code, {})
    nut = nutrition.get(code, {})
    return LineItem(
        code=code,
        name=name or meal.get("name", code),
        qty=qty,
        price=float(price or 0.0),
        kcal=float(nut.get("kcal") or 0.0),
        protein=float(nut.get("protein") or 0.0),
        fat=float(nut.get("fat") or 0.0),
        carb=float(nut.get("carb") or 0.0),
        sodium=float(nut.get("sodium") or 0.0),
        tags=list(meal.get("tags") or []),
    )


NEGATION_PREFIXES = ("不", "无", "零", "去", "免")


def matches(item: LineItem, word: str) -> bool:
    """判断某个词是否命中一份餐品。

    关键点：否定型标签（如「不辣」「零糖」）不能被当成正向命中。
    否则搜「辣」时会把「不辣」的麦香鱼也算进去。
    """
    if not word:
        return False
    if word in item.name:
        return True
    for tag in item.tags:
        if tag == word:
            return True
        if tag.startswith(NEGATION_PREFIXES):
            continue
        if word in tag:
            return True
    return False


def blocked(items: list[LineItem], dislikes: list[str]) -> bool:
    """忌口一票否决：命中任一排除词就淘汰。"""
    for item in items:
        if any(matches(item, word) for word in dislikes):
            return True
    return False


def same_period(items: list[LineItem], meals: dict[str, dict[str, Any]], period: str | None) -> bool:
    if not period:
        return True
    for item in items:
        periods = meals.get(item.code, {}).get("mealPeriods")
        if periods and period not in periods:
            return False
    return True


def build_from_sets(details: dict[str, dict[str, Any]], meals: dict[str, dict[str, Any]],
                    nutrition: dict[str, dict[str, Any]], period: str | None) -> list[tuple[list[LineItem], str, list[str]]]:
    """路径 A：套餐 + 套餐内替换。"""
    out: list[tuple[list[LineItem], str, list[str]]] = []
    for set_code, detail in details.items():
        components = detail.get("components") or []
        if not components:
            continue
        choices: list[list[dict[str, Any]]] = []
        for comp in components:
            options = [{"code": comp["code"], "name": comp.get("name", comp["code"]),
                        "priceDelta": 0.0, "qty": comp.get("qty", 1)}]
            for opt in comp.get("replaceOptions") or []:
                options.append({"code": opt["code"], "name": opt.get("name", opt["code"]),
                                "priceDelta": float(opt.get("priceDelta") or 0.0),
                                "qty": comp.get("qty", 1)})
            choices.append(options)

        base_price = float(detail.get("price") or 0.0)
        count = 0
        for combo in product(*choices):
            count += 1
            if count > MAX_SET_COMBOS:
                break
            items: list[LineItem] = []
            swaps: list[str] = []
            delta = 0.0
            for original, picked in zip(components, combo):
                delta += picked.get("priceDelta", 0.0) * picked.get("qty", 1)
                items.append(to_item(picked["code"], picked["name"],
                                     _unit_price(picked["code"], meals) + picked.get("priceDelta", 0.0),
                                     picked.get("qty", 1), meals, nutrition))
                if picked["code"] != original["code"]:
                    swaps.append(f"{original.get('name', original['code'])} → {picked['name']}")
            # 套餐价按整包计价：用套餐价覆盖单品价之和
            for item in items:
                item.price = 0.0
            items.append(LineItem(code=set_code, name=detail.get("name", set_code), qty=1,
                                  price=base_price + delta, is_bundle=True))
            if not same_period([i for i in items if not i.is_bundle], meals, period):
                continue
            out.append((items, detail.get("name", set_code), swaps))
    return out


def _unit_price(code: str, meals: dict[str, dict[str, Any]]) -> float:
    return float(meals.get(code, {}).get("price") or 0.0)


def build_from_items(meals_data: list[dict[str, Any]], meals: dict[str, dict[str, Any]],
                     nutrition: dict[str, dict[str, Any]], period: str | None,
                     want_dessert: bool) -> list[tuple[list[LineItem], str, list[str]]]:
    """路径 B：单品自由组合（主食 + 配餐 + 饮品 [+ 甜品]）。"""
    def pool(category: str) -> list[dict[str, Any]]:
        return [m for m in meals_data if m.get("category") == category
                and (not period or period in (m.get("mealPeriods") or []))]

    mains = pool("主食") or pool("早餐")
    sides = pool("配餐")
    drinks = pool("饮品")
    desserts = pool("甜品") if want_dessert else [None]

    out = []
    for main in mains:
        for side in sides:
            for drink in drinks:
                for dessert in desserts:
                    parts = [main, side, drink] + ([dessert] if dessert else [])
                    items = [to_item(p["code"], p["name"], p.get("price", 0), 1, meals, nutrition)
                             for p in parts]
                    out.append((items, "单品自由组合", []))
    return out


# ---------------------------------------------------------------- 打分

def score_scheme(scheme: Scheme, constraints: Constraints) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    real_items = [i for i in scheme.items if not i.is_bundle]
    hit_pairs = [(like, [i.name for i in real_items if matches(i, like)])
                 for like in constraints.likes]
    hits = [like for like, names in hit_pairs if names]
    if hits:
        score += W_TASTE * len(hits)
        detail = "、".join(
            f"{like}({'/'.join(names)})" for like, names in hit_pairs if names
        )
        reasons.append("命中口味：" + detail)

    if constraints.kcal_min is not None or constraints.kcal_max is not None:
        lo = constraints.kcal_min if constraints.kcal_min is not None else 0
        hi = constraints.kcal_max if constraints.kcal_max is not None else 10**6
        if lo <= scheme.kcal <= hi:
            score += W_IN_TARGET
            mid = (lo + hi) / 2 if hi < 10**6 else scheme.kcal
            reasons.append(f"热量 {scheme.kcal:.0f} kcal，落在目标区间")
            score += max(0.0, 1.0 - abs(scheme.kcal - mid) / max(1.0, (hi - lo) / 2 or 1.0))
        else:
            over = (scheme.kcal - hi) if scheme.kcal > hi else (lo - scheme.kcal)
            score -= KCAL_PENALTY_PER_100 * (over / 100.0)
            reasons.append(f"热量 {scheme.kcal:.0f} kcal，偏离目标区间")

    if constraints.budget > 0:
        ratio = 1.0 - (scheme.final / constraints.budget)
        score += W_VALUE * max(0.0, ratio)
        reasons.append(f"到手 ¥{scheme.final:.2f}，占预算 {scheme.final / constraints.budget * 100:.0f}%")

    if scheme.original > 0:
        rate = scheme.discount / scheme.original
        score += W_COUPON * rate
        if scheme.coupons:
            reasons.append(f"用券 {len(scheme.coupons)} 张，省 ¥{scheme.discount:.2f}（利用率 {rate * 100:.0f}%）")

    if scheme.set_name and scheme.set_name != "单品自由组合":
        score += 0.5
        reasons.append("走套餐路径，整包计价更划算")

    return score, reasons


# ---------------------------------------------------------------- 主流程

def generate(constraints: Constraints, source: Any) -> list[Scheme]:
    meals_data = source.meals()
    nutrition_rows = source.nutrition()
    meals = {str(m.get("code")): m for m in meals_data if m.get("code")}
    nutrition = nutrition_index(nutrition_rows)

    raw: list[tuple[list[LineItem], str, list[str]]] = []
    raw += build_from_sets(source.details(), meals, nutrition, constraints.period)
    raw += build_from_items(meals_data, meals, nutrition, constraints.period, constraints.want_dessert)

    schemes: list[Scheme] = []
    for items, set_name, swaps in raw:
        if blocked(items, constraints.dislikes):
            continue
        priced = source.price(items, source.coupons())
        if priced["final"] > constraints.budget + 1e-6:
            continue
        scheme = Scheme(
            label="",
            set_name=set_name,
            items=items,
            swaps=swaps,
            original=priced["original"],
            coupons=priced["coupons"],
            final=priced["final"],
            kcal=sum(i.kcal * i.qty for i in items),
            protein=sum(i.protein * i.qty for i in items),
            fat=sum(i.fat * i.qty for i in items),
            carb=sum(i.carb * i.qty for i in items),
            sodium=sum(i.sodium * i.qty for i in items),
        )
        scheme.score, scheme.reasons = score_scheme(scheme, constraints)
        schemes.append(scheme)

    schemes.sort(key=lambda s: s.score, reverse=True)
    deduped: list[Scheme] = []
    seen: set[tuple] = set()
    for scheme in schemes:
        key = tuple(sorted(i.code for i in scheme.items))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(scheme)
        if len(deduped) >= MAX_RESULTS:
            break

    medals = ["🥇", "🥈", "🥉"]
    for index, scheme in enumerate(deduped):
        scheme.label = f"{medals[index] if index < len(medals) else '·'} 方案 {index + 1}"
    return deduped


# ---------------------------------------------------------------- 输出

def render(schemes: list[Scheme], constraints: Constraints, source_name: str) -> str:
    lines = [f"【约束】{constraints.describe()}", f"【数据源】{source_name}", ""]
    if not schemes:
        lines.append("没有找到满足全部约束的方案。建议放宽预算、热量区间，或减少排除项。")
        return "\n".join(lines)

    for scheme in schemes:
        lines.append(f"{scheme.label} · 到手 ¥{scheme.final:.2f}（原价 ¥{scheme.original:.2f}，省 ¥{scheme.discount:.2f}）")
        combo = " + ".join(f"{i.name}×{i.qty}" if i.qty > 1 else i.name
                           for i in scheme.items if not i.is_bundle)
        lines.append(f"   组合：{combo}")
        if scheme.set_name and scheme.set_name != "单品自由组合":
            lines.append(f"   套餐：{scheme.set_name}")
        if scheme.swaps:
            lines.append("   DIY 替换：" + "；".join(scheme.swaps))
        lines.append(
            f"   营养：能量 {scheme.kcal:.0f} kcal · 蛋白 {scheme.protein:.0f} g · "
            f"脂肪 {scheme.fat:.0f} g · 碳水 {scheme.carb:.0f} g · 钠 {scheme.sodium:.0f} mg"
        )
        if scheme.coupons:
            used = "、".join(f"{c.get('name')}" for c in scheme.coupons)
            lines.append(f"   用券：{used}")
        else:
            lines.append("   用券：未命中可用券")
        if scheme.reasons:
            lines.append("   为什么是它：" + "；".join(scheme.reasons))
        lines.append("")

    lines.append("【状态】已完成：约束确认 → 数据拉取 → 组合试算 → 方案生成")
    lines.append("        下一步需要你：选一个方案（或说\"换个预算/口味\"）")
    lines.append("        未执行：下单")
    return "\n".join(lines)


def to_json(schemes: list[Scheme], constraints: Constraints, source_name: str) -> str:
    return json.dumps(
        {
            "constraints": constraints.__dict__,
            "source": source_name,
            "schemes": [
                {
                    "label": s.label,
                    "setName": s.set_name,
                    "swaps": s.swaps,
                    "original": s.original,
                    "final": s.final,
                    "discount": s.discount,
                    "coupons": [c.get("name") for c in s.coupons],
                    "nutrition": {
                        "kcal": s.kcal, "protein": s.protein, "fat": s.fat,
                        "carb": s.carb, "sodium": s.sodium,
                    },
                    "score": round(s.score, 3),
                    "items": [
                        {"code": i.code, "name": i.name, "qty": i.qty, "price": i.price}
                        for i in s.items
                    ],
                }
                for s in schemes
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


# ---------------------------------------------------------------- 命令行

def parse_likes(value: str | None) -> list[str]:
    """把 "辣,炸" / "辣，炸" / "辣 炸" 都拆成列表。"""
    if not value:
        return []
    normalized = value.replace("，", ",").replace("、", ",").replace(" ", ",")
    return [part.strip() for part in normalized.split(",") if part.strip()]


def build_constraints(args: argparse.Namespace) -> Constraints:
    likes = parse_likes(args.like)
    dislikes = parse_likes(args.no)
    kcal_min = args.kcal_min if args.kcal_min is not None else (
        max(0, args.kcal - 150) if args.kcal else None
    )
    kcal_max = args.kcal_max if args.kcal_max is not None else (
        args.kcal + 150 if args.kcal else None
    )
    return Constraints(
        likes=likes, dislikes=dislikes, budget=args.budget,
        kcal_min=kcal_min, kcal_max=kcal_max,
        period=args.period or None, channel=args.channel,
        want_dessert=args.dessert,
    )


def make_source(args: argparse.Namespace) -> Any:
    """默认走离线样例；显式加 --live 且已配置 Token 时走真实 MCP。"""
    if not getattr(args, "live", False):
        return MockSource()
    return LiveSource(address=getattr(args, "address", None))


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    parser = argparse.ArgumentParser(prog="diy_mc", description="DIY 我的麦 —— 组合、试算与比价")
    sub = parser.add_subparsers(dest="command")

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--budget", type=float, default=30.0, help="到手价上限，默认 30")
        p.add_argument("--kcal", type=int, default=None, help="目标热量，默认上下浮动 150")
        p.add_argument("--kcal-min", type=int, default=None, help="热量下界")
        p.add_argument("--kcal-max", type=int, default=None, help="热量上界")
        p.add_argument("--like", type=str, default="", help="口味偏好，逗号分隔，如 辣,炸")
        p.add_argument("--no", dest="no", type=str, default="", help="忌口，逗号分隔，如 牛肉")
        p.add_argument("--period", type=str, default="", help="时段：早餐/午餐/晚餐/夜宵")
        p.add_argument("--channel", type=str, default="外送", help="外送/到店/得来速")
        p.add_argument("--dessert", action="store_true", help="允许出现甜品")
        p.add_argument("--live", action="store_true", help="使用真实麦当劳 MCP（需 MCD_MCP_TOKEN）")
        p.add_argument("--address", type=str, default=None, help="配送或定位地址（live 模式）")
        p.add_argument("--json", action="store_true", help="输出 JSON")

    add_common(sub.add_parser("diy", help="生成 DIY 方案"))
    add_common(sub.add_parser("demo", help="离线演示（内置样例数据）"))

    sub.add_parser("probe", help="联调真实 MCP，打印握手与工具清单")
    sub.add_parser("tools", help="打印 MCP 真实工具清单")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "probe":
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
        from mcd_client import probe  # type: ignore

        probe()
        return 0

    if args.command == "tools":
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
        from mcd_client import McdMcpClient  # type: ignore

        client = McdMcpClient()
        client.initialize()
        for tool in client.list_tools():
            print(f"- {tool.get('name')}: {(tool.get('description') or '')[:80]}")
        return 0

    constraints = build_constraints(args)
    source = make_source(args)
    schemes = generate(constraints, source)
    print(to_json(schemes, constraints, source.name) if args.json
          else render(schemes, constraints, source.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
