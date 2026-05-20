"""
诊断硅基流动 API 问题
"""
import requests

API_KEY = "sk-vunezqxntdjfcuqmnklkpbiwbzmyqaxqmqdaguoetrwkymlt"
BASE_URL = "https://api.siliconflow.cn/v1"

print("=" * 60)
print("硅基流动 API 诊断")
print("=" * 60)

# 1. 检查账户余额
print("\n[1] 检查账户余额...")
try:
    r = requests.get(
        f"{BASE_URL}/user/info",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    if r.status_code == 200:
        info = r.json()
        print(f"  状态码: {r.status_code}")
        print(f"  返回数据: {info}")
    else:
        print(f"  状态码: {r.status_code}")
        print(f"  错误: {r.text}")
except Exception as e:
    print(f"  异常: {e}")

# 2. 检查模型列表
print("\n[2] 检查可用模型...")
try:
    r = requests.get(
        f"{BASE_URL}/models",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    if r.status_code == 200:
        models = r.json().get("data", [])
        image_models = [m for m in models if "flux" in m["id"].lower()]
        print(f"  找到 {len(image_models)} 个 Flux 模型:")
        for m in image_models[:5]:
            print(f"    - {m['id']}")
    else:
        print(f"  状态码: {r.status_code}")
        print(f"  错误: {r.text}")
except Exception as e:
    print(f"  异常: {e}")

# 3. 测试图片生成 API
print("\n[3] 测试图片生成 API...")
try:
    r = requests.post(
        f"{BASE_URL}/images/generations",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": "a beautiful sunset",
            "image_size": "512x512",
            "batch_size": 1
        },
        timeout=30
    )
    print(f"  状态码: {r.status_code}")
    print(f"  响应头: {dict(r.headers)}")
    print(f"  响应内容: {r.text[:500]}")
except Exception as e:
    print(f"  异常: {e}")

print("\n" + "=" * 60)
