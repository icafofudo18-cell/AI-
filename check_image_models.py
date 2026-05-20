"""
检查所有可用的图片生成模型
"""
import requests

API_KEY = "sk-vunezqxntdjfcuqmnklkpbiwbzmyqaxqmqdaguoetrwkymlt"

r = requests.get(
    "https://api.siliconflow.cn/v1/models",
    headers={"Authorization": f"Bearer {API_KEY}"}
)

models = r.json().get("data", [])
print(f"总共 {len(models)} 个模型\n")

# 筛选可能用于图片生成的模型
keywords = ["flux", "sd", "stable", "diffusion", "image", "paint"]
image_models = []

for m in models:
    model_id = m["id"].lower()
    if any(kw in model_id for kw in keywords):
        image_models.append(m)

print(f"找到 {len(image_models)} 个可能的图片生成模型:\n")
for m in image_models[:20]:
    print(f"  - {m['id']}")
    if m.get('enabled'):
        print(f"    状态: 可用")
    else:
        print(f"    状态: 禁用")
