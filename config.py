import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TWELVEDATA_API_KEY")
BASE_URL = "https://api.twelvedata.com/time_series"

if not API_KEY:
    raise ValueError("请设置 TWELVEDATA_API_KEY 环境变量")