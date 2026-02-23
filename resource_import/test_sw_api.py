# -*- coding: utf-8 -*-
import requests
import time

# 计算时间戳（毫秒）
end_time = int(time.time() * 1000)
start_time = end_time - 5 * 60 * 1000  # 最近5分钟

# 使用字符串格式的时间戳
query = f"""
{{
    services: getAllServices(duration: {{start: "{start_time}", end: "{end_time}", step: MINUTE}}) {{
        id
        name
        normal
    }}
}}
"""

response = requests.post(
    "http://localhost:12800/graphql",
    json={"query": query},
    headers={"Content-Type": "application/json"},
    timeout=30
)

print("Status:", response.status_code)
print("Response:", response.text)
