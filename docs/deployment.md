# Railway 单体上线

这份说明对应你现在选的最简方案：

- 一个 Railway 服务
- 一个持久化 Volume
- SQLite 保存订阅和文章元数据
- 本地文件目录保存文章 HTML、JSON、播客文稿和音频

这个方案最适合第一版快速上线。

## 为什么现在不用 Supabase

因为你当前最关键的是：

- 应用先稳定跑起来
- 每天 8:00 自动生成
- 邮件能发
- 文章和音频能保存

这些需求，Railway 单体部署就够了。等以后订阅用户变多、要做后台管理、多环境部署，再迁移到 Postgres 或对象存储也不晚。

## 你要准备什么

1. 一个 GitHub 仓库
2. 一个 Railway 账号
3. 一个 OpenAI API Key
4. 一个 Gmail App Password

## 第一步：把代码推到 GitHub

在本地项目目录执行：

```bash
git init
git add .
git commit -m "Initial daily news briefing app"
```

然后新建 GitHub 仓库并推送。

## 第二步：在 Railway 创建项目

1. 登录 [Railway](https://railway.com/)
2. 点击 `New Project`
3. 选择 `Deploy from GitHub repo`
4. 选择你的这个仓库

Railway 会自动识别本项目，并使用仓库里的 [railway.json](/Users/xuyihuan/Library/CloudStorage/OneDrive-Personal/Xu Eric/Personal Document/AI/news/railway.json) 和 [nixpacks.toml](/Users/xuyihuan/Library/CloudStorage/OneDrive-Personal/Xu Eric/Personal Document/AI/news/nixpacks.toml) 启动。

## 第三步：添加持久化 Volume

在 Railway 项目里：

1. 打开你的服务
2. 找到 `Volumes`
3. 新建一个 Volume
4. 挂载路径设为：

```text
/data
```

这样应用生成的数据库和归档文件都会持久保存，不会因为重新部署丢失。

## 第四步：配置环境变量

在 Railway 服务的 Variables 中添加：

```text
OPENAI_API_KEY=你的 OpenAI Key
APP_BASE_URL=https://你的-railway-域名
APP_TIMEZONE=America/New_York
APP_LOCALE=zh_CN
SECRET_KEY=换成一串随机字符串

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=xuyihuanjpjp@gmail.com
SMTP_PASSWORD=你的 Google App Password
SMTP_FROM_EMAIL=xuyihuanjpjp@gmail.com
SMTP_FROM_NAME=Daily News Briefing
SMTP_USE_TLS=true

DATA_DIR=/data
DATABASE_PATH=/data/app.db
ALLOW_DEMO_FALLBACK=false
```

注意：

- `APP_BASE_URL` 必须填 Railway 分配给你的公开域名
- `SMTP_PASSWORD` 必须是 Google App Password，不是邮箱登录密码
- `ALLOW_DEMO_FALLBACK=false` 表示生产环境不允许用演示数据冒充真实新闻

## 第五步：生成公开域名

在 Railway 服务里开启 Public Networking，拿到类似这样的域名：

```text
https://your-app-name.up.railway.app
```

然后把这个值填回 `APP_BASE_URL`。

## 第六步：验证上线

部署成功后，检查：

1. 首页能打开
2. `/healthz` 返回 `{"ok": true}`
3. 点击“实时生成当前版本”能生成文章
4. 提交订阅邮箱后能写入数据库
5. `data` Volume 里能看到：
   - `app.db`
   - `articles/YYYY-MM-DD/...`
   - `audio/YYYY-MM-DD/...`

## 定时任务怎么工作

应用启动后，内部 APScheduler 会自动注册任务：

- 每天美东时间 `08:00`
- 自动生成一篇新闻摘要
- 自动给全部订阅邮箱发送邮件

所以你不需要额外再配置一个外部 cron。

## 这个方案的边界

第一版这样完全够用，但有几个边界要知道：

- 只适合单实例运行
- SQLite 不适合高并发写入
- 文件都在一个 Volume 上，后面迁移时要搬数据

如果以后你要做这些，就该升级架构：

- 订阅用户明显变多
- 需要后台管理
- 需要多个运行实例
- 需要更稳定的文件存储和数据库

那时再迁移到 Postgres 和对象存储就好。
