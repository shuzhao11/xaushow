import requests

# Twelve Data API 配置（请替换成你自己的API密钥）
API_KEY = "306ebfb24c9545a3baeef6a7a86c0cb6"
BASE_URL = "https://api.twelvedata.com/time_series"

def get_current_price(symbol="XAU/USD"):
    """获取实时/最新价格（使用北京时间时区）"""
    params = {
        "symbol": symbol,
        "interval": "1min",
        "apikey": API_KEY,
        "outputsize": 1,
        "timezone": "Asia/Shanghai"   # 强制使用北京时间
    }
    try:
        resp = requests.get(BASE_URL, params=params)
        data = resp.json()
        if "values" in data and data["values"]:
            latest = data["values"][0]
            return {
                "datetime": latest["datetime"],
                "close": latest["close"]
            }
    except Exception as e:
        print(f"❌ 实时价格请求失败: {e}")
    return None

def get_historical_price(target_datetime_str, symbol="XAU/USD"):
    """获取指定时间的历史数据（使用北京时间时区）"""
    params = {
        "symbol": symbol,
        "interval": "1min",
        "apikey": API_KEY,
        "outputsize": 5000,
        "timezone": "Asia/Shanghai"   # 强制使用北京时间
    }
    try:
        resp = requests.get(BASE_URL, params=params)
        data = resp.json()
        if "values" in data:
            for item in data["values"]:
                # 由于返回的时间字符串格式为 "2026-05-14 12:30:00"
                if item["datetime"].startswith(target_datetime_str):
                    return {
                        "datetime": item["datetime"],
                        "close": item["close"]
                    }
    except Exception as e:
        print(f"❌ 历史价格请求失败: {e}")
    return None

if __name__ == "__main__":
    # 获取最新价格
    current = get_current_price()
    if current:
        print(f"📊 API 当前最新价格: {current['close']} (北京时间: {current['datetime']})")
    else:
        print("⚠️ 未能获取到当前数据，请检查API密钥和网络连接")

    # 获取指定时间价格
    target = get_historical_price("2026-05-14 12:35")
    if target:
        print(f"📊 API 历史价格: {target['close']} (北京时间: {target['datetime']})")
    else:
        print("⚠️ 未找到该时间点的数据")