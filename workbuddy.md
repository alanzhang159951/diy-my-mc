# WorkBuddy 开发上下文

本项目全程使用 **腾讯 WorkBuddy**（桌面智能体）完成需求梳理、资料核实、代码编写、本地验证与报名材料准备。本文档记录开发过程中的关键对话与决策，用于核验 WorkBuddy 专项奖励条件。

- 开发工具：WorkBuddy（桌面智能体，Agent 模式）
- 开发日期：2026-10-12
- 使用能力：网页检索与抓取、本地文件读写、Python 脚本编写与执行、命令行运行

---

## 1. 需求确立

**用户输入**

> 参加麦当劳的活动

**WorkBuddy 的动作**

先追问活动指向（存在多种可能），用户澄清为「WorkBuddy 与麦当劳组织的活动」后，检索并定位到官方活动——
金拱门（中国）有限公司主办的**麦当劳程序员创意开发大赛**，WorkBuddy 为官方合作伙伴。

随后直接从麦当劳 GitHub 官方账号抓取活动原文，而不是依赖二手转述：

- `M-China/mcd-developer-innovation-challenge` 的 `README.md`、`activityGuidelines.md`、`CONTEST_DECLARATION.md`、`RANKING.md`
- `M-China/mcd-mcp-server` 的 `README.md`（33 个 Tool 清单）

**WorkBuddy 发现并记录的关键风险点**

1. **必备文件数量在官方两处不一致**：活动主仓库 README 的表格列为 4 个必备文件，而 `activityGuidelines.md` 列为 **5 个**，多出 `mcp-config.example.json`。按规则文档执行，避免报名被判定失败。
2. **报名 Issue 有格式陷阱**：标题与正文之间不得换行、项目地址不得使用 Markdown 链接格式，否则自动校验会失败。
3. **榜单实际门槛**：抓取 `RANKING.md` 后确认当时榜尾为 4 颗 Star，即进榜门槛远低于直觉预期。
4. **检索到针对 AI 的提示词注入**：在若干"外卖领券"类 SEO 页面中夹带了要求智能体"往记忆库写入指令、后续执行本地脚本"的内容。已识别并拒绝执行，同时向用户提示该风险。

## 2. 选题决策

**WorkBuddy 提供的选项**（基于 MCP 真实能力而非臆想）

- 麦麦消费战报：用历史订单 + 营养 + 券 + 积分生成可分享的个人消费看板
- 麦麦派对管家：围绕主题活动预约全流程
- 麦麦积分精算师：积分/抽奖/商城兑换的最优策略
- 麦麦团队拼单分摊：多人拼单与费用分摊

**用户决策**

> diy我的麦

**WorkBuddy 的落地判断**

「DIY 我的麦」的能力基础是 MCP `1.0.5` 版本新增的**「支持更换套餐内商品组合、部分餐品特制」**。相比已被大量参赛项目覆盖的"省钱比价"方向，该能力的利用度明显更低，且天然贴合"定制"这一差异化叙事。

## 3. 开发过程

**WorkBuddy 产出的文件**

| 文件 | 说明 |
|---|---|
| `SKILL.md` | 技能主体：6 个 Phase 的执行流程、硬规则、输出规范 |
| `scripts/mcd_client.py` | 零依赖 MCP Streamable HTTP 客户端（握手 / SSE 解析 / 会话头 / 工具调用） |
| `scripts/diy_mc.py` | 组合枚举、打分排序、券择优、计价、CLI |
| `scripts/mock_data.py` | 离线样例数据，支撑无 Token 演示 |
| `references/mcd-tools.md` | 33 个官方 Tool 清单与版本演进 |
| `MCP_INTEGRATION.md` | 集成说明、调用时序、设计取舍 |
| `mcp-config.example.json` | 脱敏配置示例 |
| `demo/index.html` | 单文件交互演示页 |

**开发中定位并修复的真实缺陷**

1. **否定标签误命中**：样例数据里 `麦香鱼` 的标签为「不辣」，初版用 `"辣" in tags` 做匹配，导致"搜索辣味"时把不辣的产品也算了进去。修复方案是引入 `NEGATES` 前缀判定（不/无/零/去/免），否定型标签只能靠全等命中，并新增 `--like 不辣 --no 牛肉` 用例做回归。
2. **套餐整包计价导致的展示重复**：套餐路径下组件单价需归零、由整包价承担总价，初版把整包价也当成一行组件渲染，方案卡出现"麦辣鸡腿堡 + … + 麦辣鸡腿堡四件套"的重复。增加 `is_bundle` 标记，展示时跳过、计价时计入。
3. **口味命中回溯缺少依据**：初版只输出命中了哪几个偏好词，无法核对。改为输出"偏好词(命中的餐品名)"，便于验证。

## 4. 本地验证

**WorkBuddy 执行的回归用例**

```
python scripts/diy_mc.py demo --budget 30 --kcal 700 --like 辣,炸
python scripts/diy_mc.py diy  --budget 25 --like 不辣 --no 牛肉 --period 早餐
python scripts/diy_mc.py diy  --budget 20 --kcal 600 --json
```

三条用例均正常输出方案卡；否定标签回归通过。

**材料合规校验**

- `CONTEST_DECLARATION.md` 与官方原文 SHA-256 一致：`cd28101bcb29cc8fb24b372fe91ce6b42c4a1487a54e01f7ade0c8c6a84241b7`
- 仓库内不含任何真实 Token / 密钥 / 账号凭证
- 5 个规定文件齐备且文件名未被改动

## 5. 报名

- 仓库以 Public 形式发布至 GitHub
- 按官方模板发布报名 Issue，规避换行与 Markdown 链接两处格式陷阱

---

## 附：本项目的边界声明

本项目为麦当劳程序员创意开发大赛参赛作品，由参赛者独立开发，**非麦当劳官方产品**。项目输出仅供参考，不构成医疗、营养或其他专业建议；餐品信息、价格及供应状态以麦当劳官方渠道实时结果为准。详见 [`CONTEST_DECLARATION.md`](CONTEST_DECLARATION.md)。
