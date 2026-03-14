# Vercel + Supabase 部署

当前仓库已经收成这条架构：

- Vercel 负责前端页面与轻量 API 入口
- Supabase Postgres 保存文章与订阅数据
- Supabase Storage 保存文章归档与音频文件
- OpenAI 负责新闻搜索、结构化生成与语音

## 需要的环境变量

在 Vercel 中至少配置：

```text
OPENAI_API_KEY=
OPENAI_NEWS_MODEL=gpt-4.1
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=alloy

APP_BASE_URL=https://你的-vercel-域名
APP_TIMEZONE=America/New_York
APP_LOCALE=zh_CN
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

## Vercel 部署

当前仓库已经包含：

- [vercel.json](/Users/xuyihuan/Library/CloudStorage/OneDrive-Personal/Xu Eric/Personal Document/AI/news/vercel.json)
- [api/index.py](/Users/xuyihuan/Library/CloudStorage/OneDrive-Personal/Xu Eric/Personal Document/AI/news/api/index.py)

所以直接通过 Vercel CLI 或 GitHub 集成部署即可。

## 关于定时任务

当前 Vercel 版本更适合：

- 页面展示
- 即时生成
- 订阅写入

如果你要长期稳定地跑“每天美东 8:00 自动生成”，推荐后续再补：

- Vercel Cron 调用生成接口
或
- 独立后台 job 服务
