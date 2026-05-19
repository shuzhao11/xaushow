import requests
import pandas as pd
from config import API_KEY, BASE_URL

def fetch_1min_data(symbol: str, start_dt_str: str, end_dt_str: str) -> pd.DataFrame:
    """
    获取1分钟K线数据。
    start_dt_str, end_dt_str: 原始字符串格式 "YYYY-MM-DD HH:MM:SS"，直接传给API
    返回 DataFrame，列: datetime_str (原始字符串), open, high, low, close
    """
    all_data = []
    next_page_token = None
    while True:
        params = {
            "symbol": symbol,
            "interval": "1min",
            "start_date": start_dt_str,
            "end_date": end_dt_str,
            "apikey": API_KEY,
            "outputsize": 5000,
            "timezone": "Asia/Shanghai"   # 强制使用北京时间
        }
        if next_page_token:
            params["next_page_token"] = next_page_token

        resp = requests.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        if "values" not in data:
            raise Exception(f"API 错误: {data}")

        for item in data["values"]:
            # 保留原始时间字符串，不做任何转换
            raw_dt_str = item["datetime"]
            all_data.append({
                "datetime_str": raw_dt_str,
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
            })

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break

    df = pd.DataFrame(all_data)
    if df.empty:
        raise ValueError("未获取到任何数据，请检查日期范围或 symbol")

    # 按原始时间字符串排序（字符串格式 "YYYY-MM-DD HH:MM:SS" 支持字典序排序）
    df = df.sort_values("datetime_str").reset_index(drop=True)
    return df