# 麦当劳中国 MCP Server 工具清单

来源：麦当劳中国 MCP Server 官方文档 <https://github.com/M-China/mcd-mcp-server>（版本日志截至 `1.0.9`，2026-09-10）。

- 接入地址：`https://mcp.mcd.cn`
- 传输协议：Streamable HTTP
- 鉴权：请求头 `Authorization: Bearer <MCP_TOKEN>`
- 限流：每 Token 每分钟 600 次，超出返回 `429`
- 错误码：`401` Token 无效/过期/未提供；`429` 触发限流

下表 **读** = 只查询，不改变账户或订单状态；**写** = 会产生实际影响，调用前必须获得用户显式授权。

| # | Tool | 名称 | 读/写 |
|---:|---|---|---|
| 1 | `list-nutrition-foods` | 餐品营养信息列表 | 读 |
| 2 | `delivery-query-addresses` | 获取用户可配送地址列表 | 读 |
| 3 | `delivery-create-address` | 新增配送地址 | 写 |
| 4 | `delivery-query-stores` | 查询可配送的门店列表 | 读 |
| 5 | `query-meal-assistance` | 查询助餐服务（仅企业团餐） | 读 |
| 6 | `query-nearby-stores` | 查询附近可用门店 | 读 |
| 7 | `query-store-coupons` | 当前门店下可用优惠券列表 | 读 |
| 8 | `query-meals` | 当前可售卖的餐品列表 | 读 |
| 9 | `query-meal-detail` | 餐品详情（套餐组成与可替换项） | 读 |
| 10 | `calculate-price` | 商品价格计算 | 读 |
| 11 | `create-order` | 创建订单 | 写 |
| 12 | `cancel-order` | 取消订单 | 写 |
| 13 | `query-order` | 查询订单详情 | 读 |
| 14 | `order-list` | 查询历史订单 | 读 |
| 15 | `campaign-calendar` | 活动日历查询 | 读 |
| 16 | `available-coupons` | 麦麦省券列表查询 | 读 |
| 17 | `auto-bind-coupons` | 麦麦省一键领券 | 写 |
| 18 | `query-my-coupons` | 我的优惠券查询 | 读 |
| 19 | `query-my-account` | 我的积分查询 | 读 |
| 20 | `mall-points-products` | 麦麦商城商品列表 | 读 |
| 21 | `mall-product-detail` | 麦麦商城商品详情 | 读 |
| 22 | `mall-create-order` | 积分兑换商品下单 | 写 |
| 23 | `now-time-info` | 获取当前时间信息 | 读 |
| 24 | `query-lottery-info` | 查看积分抽奖活动信息 | 读 |
| 25 | `draw-lottery` | 积分抽奖 | 写 |
| 26 | `query-my-prizes` | 查看我的奖品 | 读 |
| 27 | `mall-order-list` | 麦麦商城订单查询 | 读 |
| 28 | `mall-order-detail` | 麦麦商城订单详情查询 | 读 |
| 29 | `query-party-city` | 主题活动城市列表查询 | 读 |
| 30 | `query-party-store` | 主题活动门店列表查询 | 读 |
| 31 | `query-partystore-date` | 主题活动可预约日期查询 | 读 |
| 32 | `query-partystore-session` | 主题活动可预约场次查询 | 读 |
| 33 | `party-order-create` | 主题活动订单创建 | 写 |

## 本技能实际使用的工具

| Tool | 在本技能中的作用 |
|---|---|
| `now-time-info` | 校准时间，判断时段与活动有效期 |
| `query-nearby-stores` | 按地址定位可下单门店 |
| `query-meals` | 拉取菜单（餐品编码、分类、标签） |
| `list-nutrition-foods` | 拉取营养数据用于组合的营养汇总 |
| `query-meal-detail` | **DIY 的核心**：读取套餐组成与可替换选项 |
| `query-my-coupons` | 账户券 |
| `query-store-coupons` | 门店券 |
| `query-my-account` | 积分余额（用于积分维度建议） |
| `campaign-calendar` | 判断是否值得等下一场活动 |
| `calculate-price` | **价格唯一权威来源** |
| `create-order` | 下单（仅限用户显式确认后） |

## 版本演进

| 日期 | 版本 | 变化 |
|---|---|---|
| 2025-12-09 | 1.0.0 | 麦麦日历与麦麦省领券 |
| 2026-01-23 | 1.0.1 | 新增餐品营养信息列表 |
| 2026-02-13 | 1.0.2 | 新增麦乐送点餐与积分兑换券 |
| 2026-04-02 | 1.0.3 | 新增到店取餐与团餐场景 |
| 2026-05-21 | 1.0.4 | 新增积分兑换实物、商城订单查询、得来速、预约 |
| 2026-06-16 | 1.0.5 | **支持更换套餐内商品组合、部分餐品特制** |
| 2026-07-16 | 1.0.6 | 新增历史订单查询、餐品优惠价、随单购买麦金卡/早餐卡 |
| 2026-07-29 | 1.0.7 | 新增派对、品鉴会等主题活动查询与下单 |
| 2026-08-27 | 1.0.8 | 新增积分抽奖 |
| 2026-09-10 | 1.0.9 | 新增取消订单、餐具选择、订单备注、取餐柜二维码 |

> `1.0.5` 的「更换套餐内商品组合」正是本技能 DIY 能力的官方基础。
