# 今日头条自动发布系统

自动从多个平台获取热点 → AI 改写文章 → 发布到今日头条创作者中心。

## 快速开始

### 1. 安装依赖

```powershell
pip install -r requirements.txt
playwright install chromium
```

### 2. 配置 `config.py`

修改以下必填项：
- `AI_API_KEY`: 你的 OpenAI 兼容 API Key
- `AI_API_BASE`: API 地址（默认 OpenAI，可换 DeepSeek 等）
- `AI_MODEL`: 使用的模型名称

### 3. 首次登录（保存 Cookie）

```powershell
python main.py --login
```

浏览器弹出后，手动完成今日头条账号登录，然后按回车保存 Cookie。

### 4. 运行

**手动单次运行：**
```powershell
python main.py
```

**测试（只看改写结果，不发布）：**
```powershell
python main.py --dry-run
```

**测试热点获取：**
```powershell
python main.py --fetch
```

**启动定时调度（长期运行）：**
```powershell
python scheduler.py
```

## 项目结构

| 文件 | 说明 |
|------|------|
| `config.py` | 所有配置项 |
| `hot_fetcher.py` | 热点获取模块 |
| `ai_rewriter.py` | AI 改写模块 |
| `publisher.py` | Playwright 自动发布 |
| `main.py` | 手动运行入口 |
| `scheduler.py` | 定时调度器 |
| `published.json` | 已发布记录 |
| `toutiao_cookies.json` | 登录 Cookie（自动生成） |
| `screenshots/` | 发布截图记录（自动创建） |
| `toutiao_auto.log` | 运行日志（自动生成） |

## 支持的热点平台

通过修改 `config.py` 中的 `HOT_SOURCES`，可选平台包括：
微博、知乎、百度、36kr、抖音、哔哩哔哩、少数派、澎湃、IT之家 等

## 注意事项

1. 首次运行必须先执行 `python main.py --login` 完成登录
2. Cookie 有效期约 30 天，过期需重新登录
3. 建议 `HEADLESS = False` 以便观察发布过程
4. 每篇文章发布间隔建议不低于 60 秒
