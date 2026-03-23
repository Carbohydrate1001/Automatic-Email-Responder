# 自动客服邮件回复系统 — 使用说明

## 目录

1. [系统概述](#1-系统概述)
2. [环境要求](#2-环境要求)
3. [Azure AD 应用注册](#3-azure-ad-应用注册)
4. [后端配置与启动](#4-后端配置与启动)
5. [前端配置与启动](#5-前端配置与启动)
6. [功能使用说明](#6-功能使用说明)
7. [API 接口文档](#7-api-接口文档)
8. [数据库说明](#8-数据库说明)
9. [常见问题排查](#9-常见问题排查)

---

## 1. 系统概述

本系统面向物流/贸易行业，通过 Microsoft Graph API 读取 Outlook 邮箱中的客户邮件，利用 OpenAI GPT-4o-mini 自动完成以下工作：

- **意图分类**：两阶段判定（业务相关性 Gate + 具体类别分类），共 7 个类别
- **自动回复**：业务邮件生成回复草稿；满足自动发送条件时直接发送
- **人工审核**：未达自动发送条件或发送失败的邮件进入人工处理队列
- **可视化管理**：Web 界面展示邮件列表、详情、审核操作及数据统计
- **公司信息库（JSON）**：维护产品名称、单价、最小订购量、交付时长，供后续回复模板引用

**邮件分类体系（当前实现）**

| 类别标识 | 中文说明 |
|----------|----------|
| `pricing_inquiry` | 询价 / 报价 |
| `order_cancellation` | 取消订单 / 退款 |
| `order_tracking` | 订单追踪 / 物流状态 |
| `shipping_time` | 运输时间 / 预计到达 |
| `shipping_exception` | 运输异常 / 延误 / 损坏 |
| `billing_invoice` | 账单 / 发票 / 付款 |
| `non_business` | 非业务邮件（固定说明模板，不自动发送） |

**技术架构**

```
浏览器 (Vue 3 · 端口 5173)
        ↕  HTTP / Vite Proxy
Flask API 服务 (端口 5005)
    ├── Microsoft Graph API  ←  读取/发送 Outlook 邮件
    ├── OpenAI API (gpt-4o-mini)  ←  分类 + 生成回复
    └── SQLite (email_system.db)  ←  本地持久化
```

---

## 2. 环境要求

| 依赖 | 版本要求 |
|------|----------|
| Python | 3.10 或以上 |
| Node.js | 18 或以上 |
| npm | 9 或以上 |
| Microsoft 365 账号 | 含有效 Outlook 邮箱（用于 OAuth 登录） |
| OpenAI API Key | 支持自定义 Base URL（`https://api.n1n.ai/v1`） |

---

## 3. Azure AD 应用注册

> 系统使用 Microsoft Identity Platform 进行 OAuth2 认证，需要先在 Azure 门户完成应用注册。

### 3.1 创建应用注册

1. 访问 [Azure 门户](https://portal.azure.com) → 搜索 **"应用注册"** → **新注册**
2. 填写名称（如 `EmailResponder`），账户类型选择 **"任何组织目录中的帐户和个人 Microsoft 帐户"**
3. 重定向 URI 选择 **Web**，填入：
   ```
   http://localhost:5005/auth/callback
   ```
4. 点击 **注册**，记录页面上的：
   - **应用程序（客户端）ID** → 对应 `AZURE_CLIENT_ID`
   - **目录（租户）ID** → 对应 `AZURE_TENANT_ID`（多租户场景可保持 `common`）

### 3.2 创建客户端密码

1. 左侧菜单 → **证书和密码** → **新建客户端密码**
2. 描述随意填写，有效期选 **24 个月**，点击 **添加**
3. 立即复制 **值**（离开页面后不可再查看）→ 对应 `AZURE_CLIENT_SECRET`

### 3.3 配置 API 权限

1. 左侧菜单 → **API 权限** → **添加权限** → **Microsoft Graph** → **委托权限**
2. 依次勾选以下权限：
   - `User.Read`
   - `Mail.Read`
   - `Mail.ReadWrite`
   - `Mail.Send`
3. 点击 **授予管理员同意**（如有权限），或通知管理员操作

---

## 4. 后端配置与启动

### 4.1 安装 Python 依赖

```bash
cd Automatic-Email-Responder/backend

# 建议使用虚拟环境
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

`requirements.txt` 包含：

```
Flask==3.1.0
flask-cors==5.0.1
flask-session==0.8.0
msal==1.31.1
requests==2.32.3
openai==1.68.0
python-dotenv==1.0.1
```

### 4.2 创建环境变量文件

```bash
cp .env.example .env
```

用文本编辑器打开 `.env`，填写所有必填项：

```env
# Flask
FLASK_SECRET_KEY=请替换为随机字符串（如 openssl rand -hex 32 的输出）
FLASK_DEBUG=True
FLASK_PORT=5005

# Microsoft Azure AD
AZURE_CLIENT_ID=从 3.1 步骤获取
AZURE_CLIENT_SECRET=从 3.2 步骤获取
AZURE_TENANT_ID=common
AZURE_REDIRECT_URI=http://localhost:5005/auth/callback

# OpenAI
OPENAI_API_KEY=你的 OpenAI API Key
OPENAI_BASE_URL=https://api.n1n.ai/v1
OPENAI_MODEL=gpt-4o-mini

# 分类置信度阈值（0.0~1.0）
# 注意：当前代码中自动发送还要求置信度 >= 0.8（与本阈值共同生效）
CONFIDENCE_THRESHOLD=0.75

# 自动发送失败重试策略
SEND_RETRY_MAX_ATTEMPTS=3
SEND_RETRY_DELAY_SECONDS=1.0
```

> **注意**：`.env` 已被 `.gitignore` 忽略，请勿将真实密钥提交到代码仓库。

### 4.3 启动后端

```bash
python app.py
```

启动成功后将看到：

```
============================================================
  Automated Customer Service Email Reply System
  Server running at: http://127.0.0.1:5005
============================================================
```

验证后端正常：打开浏览器访问 `http://localhost:5005`，应返回：
```json
{"message": "Automated Email Reply System API", "status": "running"}
```

---

## 5. 前端配置与启动

### 5.1 安装 Node.js 依赖

```bash
cd Automatic-Email-Responder/frontend
npm install
```

### 5.2 启动开发服务器

```bash
npm run dev
```

启动成功后访问：**http://localhost:5173**

> 前端通过 Vite 内置代理将 `/api/*` 和 `/auth/*` 请求自动转发到 `http://localhost:5005`，无需额外配置跨域。

### 5.3 构建生产版本（可选）

```bash
npm run build
# 产物输出至 frontend/dist/
```

---

## 6. 功能使用说明

### 6.1 登录

1. 访问 `http://localhost:5173`，自动跳转至登录页
2. 点击 **"使用 Microsoft 账号登录"** 按钮
3. 在弹出的微软登录页面完成账号密码和二步验证
4. 首次登录时需授权应用读取邮件权限，点击 **"接受"**
5. 认证成功后自动跳转至邮件列表页

### 6.2 拉取新邮件

邮件列表页顶部有 **"拉取新邮件"** 按钮，点击后系统将：

1. 通过 Microsoft Graph API 读取最新 50 封未处理邮件
2. 按 `message_id` 去重，已处理过的邮件跳过
3. 对每封邮件执行两阶段分类：
   - 规则兜底（关键词）快速识别明显非业务内容
   - LLM 先做业务相关性 Gate，再做具体类别分类
4. 若分类为 `non_business`（或判定非业务）：生成固定说明模板草稿，状态设为 `ignored_no_reply`（不自动发送）
5. 对业务邮件生成 AI 回复草稿
6. 若满足自动发送条件（`confidence >= CONFIDENCE_THRESHOLD` 且 `confidence >= 0.8`）：自动发送并标记 `auto_sent`
7. 若不满足自动发送条件：进入 `pending_review`
8. 自动发送失败：记录重试次数和错误信息，状态标记 `send_failed`，可人工重试

**当前实现流程图**

```text
拉取邮件
  -> 按 message_id 去重
  -> 两阶段分类（规则兜底 + 业务Gate + 类别分类）
     -> non_business / 非业务 -> 生成固定说明模板 -> ignored_no_reply（不自动发送，结束）
     -> 业务邮件 -> 生成回复草稿
        -> 满足自动发送条件（阈值 + >=0.8）
           -> 发送成功 -> auto_sent（并标记已读）
           -> 发送失败 -> send_failed（记录 retry_count/last_error）
        -> 不满足自动发送条件 -> pending_review
           -> 人工批准发送 -> approved
           -> 人工拒绝 -> rejected
```

### 6.3 邮件列表

- **状态筛选**：全部 / 待审核 / 已自动发送 / 已审核通过 / 已拒绝 / 发送失败 / 已忽略（无需回复）
- **类别筛选**：按 7 个意图类别过滤（含 `non_business`）
- **关键词搜索**：按主题或发件人搜索
- **置信度进度条**：直观展示 AI 分类置信度
- **点击行**：进入邮件详情页

### 6.4 邮件详情与审核

详情页展示：
- 原始邮件（发件人、主题、收件时间、正文）
- AI 分类结果（类别、置信度环形图、分类理由）
- AI 生成的回复草稿（可直接编辑修改）

**对待审核邮件的操作**：

| 按钮 | 说明 |
|------|------|
| 批准并发送 | 将当前回复草稿（含手动修改）通过 Graph API 实际发送，状态改为"已审核通过" |
| 拒绝 | 标记为已拒绝，不发送任何回复 |

### 6.5 数据统计看板

访问导航栏的 **"统计"** 页面，可查看：

- 总邮件数、待审核数、自动处理率、今日新增
- 各处理状态分布（饼图）
- 各意图类别分布
- 近 7 天邮件处理趋势（折线图）

---

## 7. API 接口文档

所有接口需在已登录状态（Session 中含有效 `access_token`）下访问。

### 认证接口（`/auth`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/auth/login` | 跳转 Microsoft 登录页 |
| GET | `/auth/callback` | OAuth2 回调，写入 Session |
| GET | `/auth/logout` | 清除 Session，跳转 MS 登出 |
| GET | `/auth/me` | 返回当前用户信息 |
| GET | `/auth/status` | 检查是否已登录（不跳转） |

### 邮件接口（`/api`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/fetch` | 拉取并处理 Outlook 新邮件 |
| GET | `/api/emails` | 获取邮件列表（支持分页和筛选） |
| GET | `/api/emails/<id>` | 获取单封邮件详情及回复草稿 |
| POST | `/api/emails/<id>/approve` | 审核通过并发送回复 |
| POST | `/api/emails/<id>/reject` | 拒绝该邮件 |
| GET | `/api/stats` | 获取统计数据 |
| GET | `/api/company/products` | 获取公司产品信息库（JSON） |
| PUT | `/api/company/products` | 全量覆盖公司产品信息库 |
| POST | `/api/company/products` | 新增一个产品 |
| PATCH | `/api/company/products/<product_name>` | 按产品名更新（不存在则新增） |
| DELETE | `/api/company/products/<product_name>` | 删除一个产品 |

#### `GET /api/emails` 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `status` | string | 筛选状态：`pending_review` / `auto_sent` / `approved` / `rejected` / `send_failed` / `ignored_no_reply` |
| `category` | string | 筛选类别（见分类体系表） |
| `search` | string | 主题或发件人关键词 |
| `page` | int | 页码，默认 1 |
| `per_page` | int | 每页数量，默认 20，最大 100 |

#### `POST /api/emails/<id>/approve` 请求体（可选）

```json
{
  "reply_text": "自定义回复内容（不传则使用 AI 草稿）"
}
```

#### 公司产品信息库（JSON）字段

每个产品对象字段如下：

| 字段 | 类型 | 说明 |
|------|------|------|
| `product_name` | string | 产品名称（唯一） |
| `unit_price` | number | 单价 |
| `currency` | string | 币种，默认 `USD` |
| `min_order_quantity` | int | 最小订购数量（MOQ） |
| `delivery_lead_time_days` | int | 交付所需时间（天） |

`PUT /api/company/products` 请求示例：

```json
{
  "products": [
    {
      "product_name": "Sea Freight (Standard)",
      "unit_price": 120.0,
      "currency": "USD",
      "min_order_quantity": 1,
      "delivery_lead_time_days": 30
    }
  ]
}
```

---

## 8. 数据库说明

系统当前包含两类数据存储：

1. `backend/email_system.db`（SQLite）：邮件处理主数据，首次运行时自动创建
2. `backend/data/company_products.json`（JSON）：公司产品信息库（产品名、单价、MOQ、交付时长）

### 表结构（SQLite）

**`emails`** — 邮件主表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增主键 |
| `message_id` | TEXT UNIQUE | Graph API 返回的邮件唯一 ID |
| `subject` | TEXT | 邮件主题 |
| `sender` | TEXT | 发件人邮箱 |
| `received_at` | TEXT | 收件时间（ISO 8601） |
| `body` | TEXT | 邮件正文（纯文本） |
| `category` | TEXT | AI 分类结果 |
| `confidence` | REAL | 分类置信度（0.0~1.0） |
| `reasoning` | TEXT | AI 分类理由 |
| `status` | TEXT | `pending_review` / `auto_sent` / `approved` / `rejected` / `send_failed` / `ignored_no_reply` |
| `retry_count` | INTEGER | 发送重试次数（自动发送失败时更新） |
| `last_error` | TEXT | 最后一次发送错误信息 |
| `created_at` | TEXT | 记录创建时间 |

**`replies`** — 回复记录

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增主键 |
| `email_id` | INTEGER FK | 关联邮件 ID |
| `reply_text` | TEXT | 回复内容 |
| `sent_at` | TEXT | 实际发送时间（NULL 表示未发送） |
| `created_at` | TEXT | 回复记录创建时间 |

**`audit_log`** — 审计日志

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增主键 |
| `email_id` | INTEGER FK | 关联邮件 ID |
| `action` | TEXT | 操作类型（如 `auto_sent` / `approved` / `rejected` / `send_failed` / `ignored_no_reply`） |
| `operator` | TEXT | 操作人邮箱（自动处理为 `system`） |
| `created_at` | TEXT | 操作时间 |

---

## 9. 常见问题排查

### Q1：登录后跳回 `/login` 而不是 `/emails`

- 检查 Azure 应用注册中的**重定向 URI** 是否精确为 `http://localhost:5005/auth/callback`
- 检查 `.env` 中 `AZURE_REDIRECT_URI` 与注册值是否一致

### Q2：`MSAL` 报错 `AADSTS700016`

- 应用 `Client ID` 填写错误，或应用注册已被删除
- 重新核对 Azure 门户中的**应用程序（客户端）ID**

### Q3：拉取邮件时报 `401 Unauthorized`

- Session 已过期，重新登录
- 检查 Azure 应用是否已授予 `Mail.Read` / `Mail.ReadWrite` / `Mail.Send` 权限

### Q4：AI 分类或回复生成失败

- 检查 `.env` 中 `OPENAI_API_KEY` 是否有效
- 验证 `OPENAI_BASE_URL=https://api.n1n.ai/v1` 可访问
- 检查账户余额或请求频率限制

### Q5：前端页面空白或 API 请求 404

- 确认后端已在端口 5005 正常运行
- 确认前端 `npm run dev` 正在端口 5173 运行
- 刷新页面或清除浏览器缓存

### Q6：置信度阈值调整

修改 `.env` 中的 `CONFIDENCE_THRESHOLD`（范围 0.0~1.0）后重启后端即可生效：
- 调高（如 0.9）→ 更多邮件转人工审核，更谨慎
- 调低（如 0.5）→ 更多邮件自动发送，效率更高

> 当前代码中自动发送还存在固定门槛 `confidence >= 0.8`，因此仅降低 `CONFIDENCE_THRESHOLD` 不一定会让低于 0.8 的邮件自动发送。
