# Apollo Automation Plan v2.0

## 0. 术语澄清 (Terminology)

> **这不是"AI Agent"，而是"规则自动化 + 定向 AI 辅助"。**

| 组件 | 类型 | 说明 |
|------|------|------|
| Chrome Extension | **纯自动化** | JS 脚本操控 DOM，无 AI 参与 |
| 职位数据流转 | **规则逻辑** | 从 Loaded Jobs 读取公司信息，自动构建 Apollo 搜索 URL |
| Email 生成 | **AI 辅助** | GPT-4o-mini 根据 JD + Resume 生成邮件内容 |
| 公司消歧 (Fallback) | **AI 辅助** | 仅在重名时启用，分析 JD 选择正确公司 |

**结论**: Token 消耗仅发生在 Email 生成和消歧环节，其余全免费。

---

## 1. 完整数据流 (End-to-End Workflow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: Job Discovery (用户操作)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  User clicks "🔎 Search Jobs" or "📂 Load Cached Jobs"                       │
│       ↓                                                                      │
│  Jobs loaded into st.session_state & saved to PostgreSQL (Job table)        │
│       ↓                                                                      │
│  Each Job contains: title, company, domain (from apply_url), JD, salary...  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: HR Contact Discovery (自动化)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Backend scans Jobs table → finds jobs missing HR contact                    │
│       ↓                                                                      │
│  Creates Task: {job_id: 123, domain: "openai.com", dept: "Engineering"}     │
│       ↓                                                                      │
│  Chrome Extension polls /api/task/next → gets task                           │
│       ↓                                                                      │
│  Extension opens Apollo: https://app.apollo.io/#/people?...                  │
│       ↓                                                                      │
│  Clicks "Access Email" → scrapes email → POSTs to /api/task/complete         │
│       ↓                                                                      │
│  Backend saves to HRContact table (linked to Job via company/domain)         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: Cold Email Generation (AI 辅助)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  User opens Email Center → selects a Job from dropdown                       │
│       ↓                                                                      │
│  System auto-fills HR Email from HRContact table                             │
│       ↓                                                                      │
│  User clicks "✉️ Generate Email"                                             │
│       ↓                                                                      │
│  AI (GPT-4o-mini) generates email:                                           │
│    - INPUT: JD (pain points) + Tailored Resume (user's strengths)            │
│    - OUTPUT: Subject + Body (with custom P.S. from Settings)                 │
│       ↓                                                                      │
│  User reviews → clicks "Create Gmail Draft" → Done!                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 关键逻辑：从 Loaded Jobs 触发 Apollo 搜索

**用户担忧**: Apollo Agent 应该基于已加载的职位去找 HR，而不是随机搜索。

**解决方案**:
1. **Job 表增加字段**: `hr_contact_status` (enum: `pending`, `found`, `not_found`)
2. **后台任务生成逻辑**:
   ```python
   # 只为 hr_contact_status='pending' 的职位创建任务
   jobs_needing_hr = db.query(Job).filter(
       Job.hr_contact_status == 'pending',
       Job.applied == False  # 已申请的不需要再找
   ).limit(10).all()
   
   for job in jobs_needing_hr:
       create_apollo_task(job.id, job.company_domain, job.department)
   ```
3. **Chrome Extension 只处理后台分配的任务**，绝不自行搜索。

---

## 2.5 JD 驱动的精准 HR 搜索 (JD-Driven Search) 🔴 关键

**用户担忧**: 招 Software Engineer 的职位，不能把邮箱发给 Marketing HR。

**解决方案**:
1. **从 Apify Job 数据提取**: `company_domain` (from apply_url) + `job_title`
2. **AI 分析 JD 推断部门** (GPT-4o-mini, ~$0.0001/次):
   - Prompt: "What department is this role in? Reply ONE word."
   - Output: Engineering / Marketing / Sales / HR / Design / Finance
3. **构建精准 Apollo 搜索**:
   - `organizationDomain=openai.com` (公司唯一标识)
   - `personTitles=Technical Recruiter` (部门对应)

**部门 → Recruiter 映射**:
| JD 部门 | 搜索 Title |
|---------|------------|
| Engineering | Technical Recruiter |
| Marketing | Marketing Recruiter |
| Sales | Sales Recruiter |
| Design | Design Recruiter |
| General/Unknown | Recruiter, Talent Acquisition |

**Fallback 逻辑 (小公司无专职 Recruiter)**:
1. 先搜 `Technical Recruiter` → 无结果
2. 再搜 `Recruiter` 或 `HR Manager` → 抓取通用 HR

**Email Subject 要求**:
> [!IMPORTANT]
> 无论发给大公司还是小公司，Subject 必须包含具体职位名称。
> 例如: `Regarding Senior Software Engineer - [Your Name]`

---

## 3. 修正后的开发计划

### Phase 1: 数据模型强化 (1 Day)
- [ ] `Job` 表增加 `company_domain` 和 `hr_contact_status` 字段
- [ ] `HRContact` 表增加 `job_id` 外键 (关联具体职位)
- [ ] `JobScraper` 修改: 从 `apply_url` 提取 domain

### Phase 2: Backend API (1.5 Days)
- [ ] `GET /api/task/next` - 返回待处理的 Apollo 任务
- [ ] `POST /api/task/complete` - 接收抓取结果并更新数据库
- [ ] 任务生成逻辑 (扫描 Job 表)

### Phase 3: Chrome Extension (2 Days)
- [ ] `manifest.json` v3
- [ ] `background.js` - 轮询 + 任务调度
- [ ] `content_script.js` - Apollo DOM 操作

### Phase 4: Email Center 集成 (1 Day)
- [ ] 选择 Job 后自动查询 HRContact
- [ ] 无联系人时显示 "⏳ Waiting for Apollo scrape..."
- [ ] 手动触发按钮: "🔍 Find HR Contact Now"

---

## 4. 用户确认点 (Checklist)

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 从 Loaded Jobs 触发搜索 | ✅ 已确认 | 后台扫描 Job 表生成任务 |
| AI vs 自动化边界 | ✅ 已澄清 | 仅 Email 生成和消歧用 AI |
| HRContact 和 Job 关联 | ✅ 已确认 | **一对多**: 可能抓到多个 HR/HM |
| HR vs HM 优先级 | ✅ 已确认 | **HR 优先**。发 HM 由用户决定 (Settings 开关) |
| 手动触发 Apollo 搜索 | ✅ 已确认 | "🔍 Find HR Now" 支持两种模式 |
| Chrome Extension 安装指南 | ⏳ 延后 | 待功能完善后补充到 README |

---

## 5. 用户体验选项 (UX Choices)

### A. HM Follow-up 控制
用户可以在 **Settings** 页面选择：
- [ ] 5 天无回复后自动发送 HM (Auto)
- [x] 5 天无回复后提醒我，手动决定 (Manual) ← 默认

### B. Extension 执行模式
用户可以在 **Settings** 或 Extension Popup 中选择：
- **Visible Mode**: 打开新 Tab，用户可以看到 Apollo 操作过程
- **Background Mode**: 静默执行，不打扰用户 (高级用户)

### C. 搜索失败处理
| 场景 | UI 显示 |
|------|---------|
| 正在搜索 | ⏳ Searching... |
| 找到 HR | ✅ hr@company.com |
| 搜索完成但无结果 | ❌ Email not found (请手动输入) |

---

## 6. 关键问题：JS 脚本如何把 Email 填入 Email Center？

**核心原理：Extension 不直接操作 Streamlit UI，而是通过数据库中转。**

```
┌──────────────────┐      HTTP POST       ┌──────────────────┐
│ Chrome Extension │  ───────────────────▶ │ Flask API        │
│ (content_script) │  {email, name, ...}  │ /api/task/done   │
└──────────────────┘                       └────────┬─────────┘
                                                    │
                                                    ▼ INSERT
                                           ┌──────────────────┐
                                           │ PostgreSQL       │
                                           │ (HRContact 表)   │
                                           └────────┬─────────┘
                                                    │
                                                    ▼ SELECT
┌──────────────────┐                       ┌──────────────────┐
│ Email Center UI  │ ◀───────────────────── │ Streamlit App    │
│ (自动填充邮箱)    │   读取 HRContact      │ (streamlit_app)  │
└──────────────────┘                       └──────────────────┘
```

**流程说明：**
1. Extension 抓到邮箱后，发送 HTTP 请求到 Docker 里的 Flask API。
2. Flask 把数据存入 PostgreSQL 的 `HRContact` 表。
3. 用户在 Email Center 选择一个 Job 时，Streamlit 查询 `HRContact` 表。
4. 如果找到对应公司的 HR 邮箱，自动填入输入框；否则显示 "⏳ Waiting..."。

**结论：Extension 和 Streamlit 完全解耦，通过数据库通信。**

---

## 6. 合规性再强调 (Compliance)

> [!CAUTION]
> 用户担心"玩火"和"被封号"。

**风险控制措施：**

| 措施 | 说明 |
|------|------|
| **User-Hosted** | 代码运行在用户本地浏览器，非中心化爬取 |
| **Rate Limiting** | 每分钟最多 1 次搜索，模拟真人操作 |
| **No Credential Sharing** | 用户自己登录 Apollo，项目不存储任何账号密码 |
| **Explicit Consent** | Extension 有开关让用户明确启用/禁用 |
| **Open Source** | AGPL-3.0 协议，代码透明，用户自愿使用 |

**法律定位**：这是一个**浏览器辅助工具**，类似于 Password Manager 或 Ad Blocker。用户对自己的账号行为负责。

