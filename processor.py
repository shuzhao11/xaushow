import pandas as pd
from typing import List

def apply_benchmark(df: pd.DataFrame, bench_price: float) -> pd.DataFrame:
    """计算偏移值 = close - bench_price"""
    df["offset"] = df["close"] - bench_price
    return df

def mark_highlight(df: pd.DataFrame, light_rules: List[str]) -> pd.Series:
    """
    根据时间规则标记高亮分钟。
    light_rules: 包含 '1h', '30min', '15min' 的列表
    """
    def is_highlight(dt):
        minute = dt.minute
        for rule in light_rules:
            if rule == "1h" and minute == 0:
                return True
            if rule == "30min" and minute in (0, 30):
                return True
            if rule == "15min" and minute % 15 == 0:
                return True
        return False

    return df["datetime"].apply(is_highlight)