# Vercel + Supabase 部署

当前仓库已经收成这条架构：

- Vercel 负责前端页面与展示入口
- Railway 负责长耗时的生成接口与定时任务
- Supabase Postgres 保存文章与订阅数据
- Supabase Storage 保存文章归档与音频文件
- Gemini 负责新闻搜索、结构化生成与语音

## 需要的环境变量

在 Vercel 中至少配置：

```text
GEMINI_API_KEY=
GEMINI_NEWS_MODEL=gemini-3-flash-preview
GEMINI_TTS_MODEL=gemini-2.5-flash-preview-tts
GEMINI_TTS_VOICE=Aoede

APP_BASE_URL=https://你的-vercel-域名
GENERATOR_API_BASE_URL=https://你的-railway-域名
APP_TIMEZONE=America/New_York
APP_LOCALE=zh_CN
CORS_ALLOWED_ORIGINS=https://你的-vercel-域名
SECRET_KEY=一串随机字符串

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=xuyihuanjpjp@gmail.com
SMTP_PASSWORD=你的 Google App Password
SMTP_FROM_EMAIL=xuyihuanjpjp@gmail.com
SMTP_FROM_NAME=Daily News Briefing
SMTP_USE_TLS=true

DATABASE_URL=你的 Supabase Postgres 连接串
SUPABASE_URL=你的 Supabase 项目 URL
SUPABASE_SERVICE_ROLE_KEY=你的 service role key
SUPABASE_STORAGE_BUCKET=daily-news-assets
SUPABASE_STORAGE_PUBLIC_BASE_URL=

ALLOW_DEMO_FALLBACK=false
```

## Supabase 初始化

1. 在 Supabase SQL Editor 中运行 [supabase/schema.sql](/Users/xuyihuan/Library/CloudStorage/OneDrive-Personal/Xu Eric/Personal Document/AI/news/supabase/schema.sql)
2. 在 Storage 中创建 bucket：

```text
daily-news-assets
```

3. 如果你希望音频和文章链接可直接访问，把 bucket 设置为 public

## 双部署建议

Vercel:

- `APP_BASE_URL=https://你的-vercel-域名`
- `GENERATOR_API_BASE_URL=https://你的-railway-域名`
- 可以只保留页面访问、归档阅读、订阅入口

Railway:

- `APP_BASE_URL=https://你的-vercel-域名`
- `CORS_ALLOWED_ORIGINS=https://你的-vercel-域名`
- 不配置 `GENERATOR_API_BASE_URL`
- 保留 Gemini / SMTP / Supabase 的完整配置

## Vercel 部署

- [vercel.json](/Users/xuyihuan/Library/CloudStorage/OneDrive-Personal/Xu Eric/Personal Document/AI/news/vercel.json)
- [api/index.py](/Users/xuyihuan/Library/CloudStorage/OneDrive-Personal/Xu Eric/Personal Document/AI/news/api/index.py)

所以直接通过 Vercel CLI 或 GitHub 集成部署即可。

## 关于定时任务

当前推荐：

- Vercel 负责页面展示
- Railway 负责即时生成和定时生成
- 订阅写入可以继续保留在 Vercel，也可以统一收口到 Railway

如果要稳定跑“每天美东 8:00 自动生成”，直接在 Railway 保留 scheduler 即可。
