from zoneinfo import ZoneInfo

# ========== 数据源校准配置 ==========
# 如果API返回的价格与实际市场价有固定偏差，在此调整
# 例如：实际价格 = API价格 + price_offset
price_offset = 16.0   # 根据您的观察（4708 - 4692 = 16），请自行测试校准

# API 返回的时间字段所在的时区（根据实际数据源调整）
# 常见选项：ZoneInfo("UTC"), ZoneInfo("Asia/Shanghai"), ZoneInfo("US/Eastern")
api_timezone = ZoneInfo("UTC")   # Twelve Data 默认返回 UTC 时间

# 显示时区（前端展示用）
display_timezone = ZoneInfo("Asia/Shanghai")

# 是否自动处理夏令时（保留 True 即可）
adjust_dst = True

# 缓存时长（秒），避免频繁请求
cache_ttl = 60