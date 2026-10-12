"""离线演示用样例数据。

⚠️ 重要说明
本文件中的数据是**为演示算法链路而虚构的样例**，不是麦当劳的真实菜单、价格或
优惠券。真实数据一律通过麦当劳中国官方 MCP Server（https://mcp.mcd.cn）实时获取。
运行 `python scripts/diy_mc.py demo` 时会使用本文件，目的是让没有 MCP Token 的
访客也能完整看到组合、试算、比价的全部逻辑。

数据结构刻意对齐 MCP 各工具的返回形态，方便在 live 模式下直接替换数据源。
"""

from __future__ import annotations

from typing import Any

SAMPLE_STORE: dict[str, Any] = {
    "storeCode": "SAMPLE-0001",
    "storeName": "示例门店（样例数据）",
    "distance": "1.2km",
}

# 对应 query-meals：当前门店可售卖餐品
SAMPLE_MEALS: list[dict[str, Any]] = [
    # ---- 主食 burgers ----
    {"code": "burger-bigmac", "name": "巨无霸", "category": "主食", "price": 23.0,
     "tags": ["牛肉", "经典", "招牌"], "mealPeriods": ["午餐", "晚餐"]},
    {"code": "burger-mcchicken", "name": "麦香鸡", "category": "主食", "price": 15.0,
     "tags": ["鸡肉", "不辣"], "mealPeriods": ["午餐", "晚餐"]},
    {"code": "burger-spicychicken", "name": "麦辣鸡腿堡", "category": "主食", "price": 19.0,
     "tags": ["鸡肉", "辣", "招牌"], "mealPeriods": ["午餐", "晚餐"]},
    {"code": "burger-doublecheese", "name": "双层吉士汉堡", "category": "主食", "price": 19.5,
     "tags": ["牛肉", "芝士"], "mealPeriods": ["午餐", "晚餐"]},
    {"code": "burger-fish", "name": "麦香鱼", "category": "主食", "price": 15.5,
     "tags": ["鱼", "不辣"], "mealPeriods": ["午餐", "晚餐"]},
    {"code": "burger-grilled", "name": "板烧鸡腿堡", "category": "主食", "price": 21.0,
     "tags": ["鸡肉", "不辣", "煎烤"], "mealPeriods": ["午餐", "晚餐"]},
    # ---- 配餐 sides ----
    {"code": "side-fries-m", "name": "薯条(中)", "category": "配餐", "price": 11.0,
     "tags": ["炸", "土豆"], "mealPeriods": ["早餐", "午餐", "晚餐", "夜宵"]},
    {"code": "side-fries-l", "name": "薯条(大)", "category": "配餐", "price": 13.5,
     "tags": ["炸", "土豆"], "mealPeriods": ["午餐", "晚餐", "夜宵"]},
    {"code": "side-nuggets-5", "name": "麦乐鸡(5块)", "category": "配餐", "price": 12.0,
     "tags": ["鸡肉", "炸"], "mealPeriods": ["午餐", "晚餐", "夜宵"]},
    {"code": "side-wings-2", "name": "麦辣鸡翅(2块)", "category": "配餐", "price": 13.0,
     "tags": ["鸡肉", "炸", "辣"], "mealPeriods": ["午餐", "晚餐", "夜宵"]},
    {"code": "side-corn", "name": "玉米杯", "category": "配餐", "price": 9.0,
     "tags": ["不辣", "轻食"], "mealPeriods": ["早餐", "午餐", "晚餐"]},
    {"code": "side-salad", "name": "蔬菜沙拉", "category": "配餐", "price": 12.5,
     "tags": ["轻食", "不辣", "低卡"], "mealPeriods": ["午餐", "晚餐"]},
    # ---- 饮品 drinks ----
    {"code": "drink-coke-m", "name": "可口可乐(中)", "category": "饮品", "price": 9.0,
     "tags": ["碳酸", "甜"], "mealPeriods": ["午餐", "晚餐", "夜宵"]},
    {"code": "drink-cokezero-m", "name": "零度可乐(中)", "category": "饮品", "price": 9.0,
     "tags": ["碳酸", "零糖", "低卡"], "mealPeriods": ["午餐", "晚餐", "夜宵"]},
    {"code": "drink-sprite-m", "name": "雪碧(中)", "category": "饮品", "price": 9.0,
     "tags": ["碳酸", "甜"], "mealPeriods": ["午餐", "晚餐", "夜宵"]},
    {"code": "drink-orange-m", "name": "橙汁(中)", "category": "饮品", "price": 11.0,
     "tags": ["果汁", "甜"], "mealPeriods": ["早餐", "午餐", "晚餐"]},
    {"code": "drink-americano", "name": "美式咖啡", "category": "饮品", "price": 12.0,
     "tags": ["咖啡", "零糖", "低卡"], "mealPeriods": ["早餐", "午餐"]},
    {"code": "drink-latte", "name": "拿铁", "category": "饮品", "price": 16.0,
     "tags": ["咖啡", "奶"], "mealPeriods": ["早餐", "午餐"]},
    # ---- 甜品 desserts ----
    {"code": "dessert-cone", "name": "圆筒冰淇淋", "category": "甜品", "price": 4.0,
     "tags": ["甜", "冰", "低卡"], "mealPeriods": ["午餐", "晚餐", "夜宵"]},
    {"code": "dessert-pie", "name": "香芋派", "category": "甜品", "price": 8.0,
     "tags": ["甜", "炸"], "mealPeriods": ["午餐", "晚餐", "夜宵"]},
    # ---- 早餐 breakfast ----
    {"code": "bk-mcmuffin-egg", "name": "吉士蛋麦满分", "category": "早餐", "price": 13.0,
     "tags": ["早餐", "蛋"], "mealPeriods": ["早餐"]},
    {"code": "bk-hotcakes", "name": "热香饼", "category": "早餐", "price": 14.0,
     "tags": ["早餐", "甜"], "mealPeriods": ["早餐"]},
]

# 对应 list-nutrition-foods：餐品营养（每份）
SAMPLE_NUTRITION: list[dict[str, Any]] = [
    {"code": "burger-bigmac", "kcal": 550, "protein": 26.0, "fat": 29.0, "carb": 45.0, "sodium": 1100},
    {"code": "burger-mcchicken", "kcal": 400, "protein": 21.0, "fat": 16.0, "carb": 43.0, "sodium": 900},
    {"code": "burger-spicychicken", "kcal": 520, "protein": 24.0, "fat": 25.0, "carb": 51.0, "sodium": 1180},
    {"code": "burger-doublecheese", "kcal": 440, "protein": 25.0, "fat": 23.0, "carb": 34.0, "sodium": 1050},
    {"code": "burger-fish", "kcal": 340, "protein": 15.0, "fat": 14.0, "carb": 38.0, "sodium": 720},
    {"code": "burger-grilled", "kcal": 470, "protein": 28.0, "fat": 19.0, "carb": 44.0, "sodium": 1010},
    {"code": "side-fries-m", "kcal": 340, "protein": 4.0, "fat": 17.0, "carb": 42.0, "sodium": 260},
    {"code": "side-fries-l", "kcal": 450, "protein": 6.0, "fat": 22.0, "carb": 56.0, "sodium": 350},
    {"code": "side-nuggets-5", "kcal": 220, "protein": 13.0, "fat": 12.0, "carb": 14.0, "sodium": 470},
    {"code": "side-wings-2", "kcal": 240, "protein": 15.0, "fat": 15.0, "carb": 11.0, "sodium": 520},
    {"code": "side-corn", "kcal": 90, "protein": 3.0, "fat": 2.0, "carb": 18.0, "sodium": 150},
    {"code": "side-salad", "kcal": 45, "protein": 2.0, "fat": 1.5, "carb": 7.0, "sodium": 120},
    {"code": "drink-coke-m", "kcal": 150, "protein": 0.0, "fat": 0.0, "carb": 38.0, "sodium": 25},
    {"code": "drink-cokezero-m", "kcal": 0, "protein": 0.0, "fat": 0.0, "carb": 0.0, "sodium": 20},
    {"code": "drink-sprite-m", "kcal": 145, "protein": 0.0, "fat": 0.0, "carb": 37.0, "sodium": 45},
    {"code": "drink-orange-m", "kcal": 120, "protein": 1.0, "fat": 0.0, "carb": 29.0, "sodium": 15},
    {"code": "drink-americano", "kcal": 5, "protein": 0.3, "fat": 0.0, "carb": 0.8, "sodium": 10},
    {"code": "drink-latte", "kcal": 130, "protein": 7.0, "fat": 6.0, "carb": 12.0, "sodium": 90},
    {"code": "dessert-cone", "kcal": 150, "protein": 3.0, "fat": 4.5, "carb": 24.0, "sodium": 70},
    {"code": "dessert-pie", "kcal": 240, "protein": 3.0, "fat": 11.0, "carb": 32.0, "sodium": 180},
    {"code": "bk-mcmuffin-egg", "kcal": 300, "protein": 15.0, "fat": 13.0, "carb": 28.0, "sodium": 700},
    {"code": "bk-hotcakes", "kcal": 350, "protein": 8.0, "fat": 9.0, "carb": 58.0, "sodium": 620},
]

# 对应 query-meal-detail：套餐组成与可替换项（DIY 的核心依据）
SAMPLE_MEAL_DETAILS: dict[str, dict[str, Any]] = {
    "set-spicy-meal": {
        "code": "set-spicy-meal",
        "name": "麦辣鸡腿堡四件套",
        "price": 34.0,
        "components": [
            {"code": "burger-spicychicken", "name": "麦辣鸡腿堡", "qty": 1},
            {"code": "side-fries-m", "name": "薯条(中)", "qty": 1,
             "replaceOptions": [
                 {"code": "side-fries-l", "name": "薯条(大)", "priceDelta": 3.0},
                 {"code": "side-corn", "name": "玉米杯", "priceDelta": 0.0},
                 {"code": "side-salad", "name": "蔬菜沙拉", "priceDelta": 1.5},
             ]},
            {"code": "drink-coke-m", "name": "可口可乐(中)", "qty": 1,
             "replaceOptions": [
                 {"code": "drink-cokezero-m", "name": "零度可乐(中)", "priceDelta": 0.0},
                 {"code": "drink-sprite-m", "name": "雪碧(中)", "priceDelta": 0.0},
                 {"code": "drink-orange-m", "name": "橙汁(中)", "priceDelta": 2.0},
                 {"code": "drink-americano", "name": "美式咖啡", "priceDelta": 3.0},
             ]},
            {"code": "side-wings-2", "name": "麦辣鸡翅(2块)", "qty": 1,
             "replaceOptions": [
                 {"code": "side-nuggets-5", "name": "麦乐鸡(5块)", "priceDelta": 0.0},
             ]},
        ],
    },
    "set-bigmac": {
        "code": "set-bigmac",
        "name": "巨无霸四件套",
        "price": 42.0,
        "components": [
            {"code": "burger-bigmac", "name": "巨无霸", "qty": 1},
            {"code": "side-fries-m", "name": "薯条(中)", "qty": 1,
             "replaceOptions": [
                 {"code": "side-fries-l", "name": "薯条(大)", "priceDelta": 3.0},
                 {"code": "side-corn", "name": "玉米杯", "priceDelta": 0.0},
                 {"code": "side-salad", "name": "蔬菜沙拉", "priceDelta": 1.5},
             ]},
            {"code": "drink-coke-m", "name": "可口可乐(中)", "qty": 1,
             "replaceOptions": [
                 {"code": "drink-cokezero-m", "name": "零度可乐(中)", "priceDelta": 0.0},
                 {"code": "drink-americano", "name": "美式咖啡", "priceDelta": 3.0},
             ]},
            {"code": "dessert-pie", "name": "香芋派", "qty": 1},
        ],
    },
    "set-grilled": {
        "code": "set-grilled",
        "name": "板烧鸡腿堡四件套",
        "price": 40.0,
        "components": [
            {"code": "burger-grilled", "name": "板烧鸡腿堡", "qty": 1},
            {"code": "side-fries-m", "name": "薯条(中)", "qty": 1,
             "replaceOptions": [
                 {"code": "side-salad", "name": "蔬菜沙拉", "priceDelta": 1.5},
                 {"code": "side-corn", "name": "玉米杯", "priceDelta": 0.0},
             ]},
            {"code": "drink-coke-m", "name": "可口可乐(中)", "qty": 1,
             "replaceOptions": [
                 {"code": "drink-cokezero-m", "name": "零度可乐(中)", "priceDelta": 0.0},
             ]},
            {"code": "side-nuggets-5", "name": "麦乐鸡(5块)", "qty": 1},
        ],
    },
    "set-breakfast": {
        "code": "set-breakfast",
        "name": "早餐双拼",
        "price": 22.0,
        "components": [
            {"code": "bk-mcmuffin-egg", "name": "吉士蛋麦满分", "qty": 1},
            {"code": "drink-americano", "name": "美式咖啡", "qty": 1,
             "replaceOptions": [
                 {"code": "drink-orange-m", "name": "橙汁(中)", "priceDelta": -1.0},
                 {"code": "drink-latte", "name": "拿铁", "priceDelta": 4.0},
             ]},
        ],
    },
}

# 对应 query-my-coupons / query-store-coupons
SAMPLE_COUPONS: list[dict[str, Any]] = [
    {"couponId": "c-30-12", "name": "账号券 满30减12", "type": "满减",
     "threshold": 30.0, "discount": 12.0, "source": "账号", "expireDate": "样例-3天后"},
    {"couponId": "c-20-5", "name": "门店券 满20减5", "type": "满减",
     "threshold": 20.0, "discount": 5.0, "source": "门店", "expireDate": "样例-1天后"},
    {"couponId": "c-50-20", "name": "账号券 满50减20", "type": "满减",
     "threshold": 50.0, "discount": 20.0, "source": "账号", "expireDate": "样例-7天后"},
]

# 对应 query-my-account
SAMPLE_ACCOUNT: dict[str, Any] = {
    "availablePoints": 1280,
    "totalPoints": 3450,
    "expiringPoints": 120,
    "expiringDate": "样例-30天后",
}


def as_mcp_like() -> dict[str, Any]:
    """打包成便于直接喂给引擎的形态。"""
    return {
        "store": SAMPLE_STORE,
        "meals": SAMPLE_MEALS,
        "nutrition": SAMPLE_NUTRITION,
        "details": SAMPLE_MEAL_DETAILS,
        "coupons": SAMPLE_COUPONS,
        "account": SAMPLE_ACCOUNT,
    }
