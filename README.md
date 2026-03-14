# Daily News Briefing

一个完整的中文每日新闻摘要应用，满足这些需求：

- 使用 OpenAI 搜集过去 24 小时美国、中国、国际热点
- 聚焦热点、财经、科技三大板块，共 30 条新闻
- 每条新闻提供中文总结、影响分析、发布时间和原文来源链接
- 文章首页展示黄金、原油、标普 500、沪指最近一次收盘指标
- 支持网页端和手机端阅读
- 支持邮箱订阅，每天美东时间早上 8:00 自动发送
- 支持手动“实时生成”一篇当前版本文章
- 同步生成播客式中文文稿和女生语音音频
- 文章、JSON、播客文稿、音频按日期归档保存

## 技术方案

- 前端与访问层：Vercel
- 应用层：FastAPI
- 模型：OpenAI（网页搜索 + 结构化生成 + TTS）
- 后端数据层：Supabase Postgres + Supabase Storage
- 邮件：SMTP
- 前端渲染：Jinja2 模板 + 原生 JS + 响应式 CSS

## 目录结构

```text
app/
  config.py
  db.py
  main.py
  schemas.py
  fixtures/
  services/
  static/
  templates/
data/
requirements.txt
.env.example
```

## 本地启动

1. 创建虚拟环境并安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. 配置环境变量：

```bash
cp .env.example .env
```

至少需要填写：

- `OPENAI_API_KEY`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_FROM_EMAIL`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`

3. 启动应用：

```bash
uvicorn app.main:app --reload
```

4. 打开：

- 首页：[http://127.0.0.1:8000](http://127.0.0.1:8000)

## 关键环境变量

- `OPENAI_NEWS_MODEL`
  默认 `gpt-4.1`
- `OPENAI_TTS_MODEL`
  默认 `gpt-4o-mini-tts`
- `OPENAI_TTS_VOICE`
  默认 `alloy`
- `ALLOW_DEMO_FALLBACK`
  未配置 OpenAI API Key 时，是否允许使用示例数据跑通页面
- `APP_TIMEZONE`
  默认 `America/New_York`
- `APP_BASE_URL`
  邮件中的文章链接地址

## 归档说明

生成后会在 `data/` 下保存：

- `data/app.db`
- `data/articles/YYYY-MM-DD/*.html`
- `data/articles/YYYY-MM-DD/*.json`
- `data/articles/YYYY-MM-DD/*-podcast.txt`
- `data/audio/YYYY-MM-DD/*.mp3`

## 定时任务

应用启动后会自动注册一个每日任务：

- 每天美东时间 `08:00`
- 自动生成当日新闻摘要
- 自动给所有订阅用户发邮件

## 部署建议

当前推荐架构：

- 前端与轻量 API：Vercel
- 数据库：Supabase Postgres
- 归档文件：Supabase Storage

详细说明见 [docs/deployment.md](/Users/xuyihuan/Library/CloudStorage/OneDrive-Personal/Xu Eric/Personal Document/AI/news/docs/deployment.md)。

生产环境建议至少配置：

- `OPENAI_API_KEY`
- `SMTP_HOST=smtp.gmail.com`
- `SMTP_PORT=587`
- `SMTP_USERNAME=xuyihuanjpjp@gmail.com`
- `SMTP_PASSWORD=你的 Google App Password`
- `SMTP_FROM_EMAIL=xuyihuanjpjp@gmail.com`
- `APP_BASE_URL=你的 Vercel 域名`
- `DATABASE_URL=Supabase Postgres 连接串`
- `SUPABASE_URL=你的 Supabase 项目 URL`
- `SUPABASE_SERVICE_ROLE_KEY=仅服务端使用`
- `SUPABASE_STORAGE_BUCKET=daily-news-assets`

## 注意

- 这台当前工作环境未安装 `node`/`npm`，但本项目不依赖前端构建工具。
- 这台当前工作环境没有现成安装项目依赖，所以我没有在这里实际启动服务器。
- Gmail 发信请使用 Google App Password，不要使用邮箱登录密码。
- Vercel 这边更适合承载页面和轻量 API，定时任务如果要长期稳定跑，后续建议拆到独立 job 或 cron 触发器。
