import mysql.connector
import os
from pathlib import Path
import sys

# 自動載入 secrets
INFRA_PATH = Path("/Users/ilawusong/Documents/WaW/Infra")
sys.path.insert(0, str(INFRA_PATH / "config"))

try:
    from secrets import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
except ImportError:
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD = "127.0.0.1", 3306, "iot_user", "password"

def get_db_connection(database="iotv9"):
    """獲取資料庫連線池或單一連線"""
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=database
    )

if __name__ == "__main__":
    # 測試連線
    try:
        conn = get_db_connection()
        print("✅ Infra DB 連線測試成功")
        conn.close()
    except Exception as e:
        print(f"❌ 連線失敗: {e}")
