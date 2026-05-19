# =============================================
# 今日头条自动发布系统 - 配置文件模板
# 使用方法：复制本文件为 config.py，填入你的真实配置
# =============================================

# 热点来源平台（可用平台：微博、知乎、百度、36kr、抖音、哔哩哔哩、少数派等）
HOT_SOURCES = ["微博", "知乎", "百度", "36kr"]

# 每次运行发布的文章数量
PUBLISH_COUNT = 3

# ---- OpenAI 兼容接口配置 ----
# 替换为你的 API 地址（DeepSeek: https://api.deepseek.com/v1, 硅基流动: https://api.siliconflow.cn/v1）
AI_API_BASE = "https://api.deepseek.com/v1"
AI_API_KEY  = "sk-xxxxxxxxxxxxxxxxxxxxxxxx"   # 替换为你的 API Key
AI_MODEL    = "deepseek-chat"   # 或 gpt-4o-mini / Qwen/Qwen2.5-72B-Instruct 等

# ---- 今日头条账号配置 ----
TOUTIAO_PHONE = "1xxxxxxxxxx"   # 你的手机号（首次登录时提示用）

# 文章默认分类（今日头条的频道名）
TOUTIAO_CATEGORY = "社会"

# ---- 定时发布配置 ----
# 每天在哪几个小时执行（24小时制）
SCHEDULE_HOURS = [9, 14, 20]

# ---- 浏览器配置 ----
# True = 无头模式后台运行，False = 显示浏览器窗口（首次登录建议 False）
HEADLESS = False

# 浏览器操作超时时间（毫秒）
TIMEOUT = 30000

# 每篇文章发布间隔（秒），避免频率过高
PUBLISH_INTERVAL = 60

# ---- 文件路径配置 ----
COOKIES_FILE = "toutiao_cookies.json"
PUBLISHED_FILE = "published.json"
LOG_FILE = "toutiao_auto.log"
SCREENSHOTS_DIR = "screenshots"
