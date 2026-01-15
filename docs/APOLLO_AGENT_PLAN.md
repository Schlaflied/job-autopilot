# Apollo Automation Plan: "Job Autopilot Helper" System

## 1. 核心目标
**Objective**: Build a robust, cost-effective (zero-token cost), and open-source friendly system to automate email scraping from Apollo.io.

**Constraints**:
1.  **Must use local browser session**: Leverage user's logged-in state and free view credits.
2.  **Must work with Docker backend**: Bridge the gap between containerized Python/DB and host OS browser.
3.  **Minimize AI Cost**: Use rule-based JS logic instead of vision-based AI agents.

---

## 2. 关键决策点 (Addressing User Concerns)

### **A. 邮件生成策略 (Precision Cold Email)**
**警示**: 抓到邮箱只是第一步，发送高质量的邮件才是关键。AI 绝不能"信口开河"。
**要求**:
1.  **Strict Context**: 必须使用 **针对该职位优化过的简历 (Tailored Resume)** 作为输入。
2.  **ATS Acknowledgement**: 针对大公司，邮件必须明确提到 **"I have already applied via your portal (ID: xxx)"**，将 Cold Email 定位为 "Follow-up" 而非 "Bypass"。
3.  **No Hallucination**: 严禁 AI 编造不存在的经历。

### **B. 解决 "找错 HR" (Department Targeting)**
**痛点**: 大公司可能有几十个 HR，负责不同部门。
**策略**:
1.  **AI 推理部门**: 在搜索前，先用 AI 分析 JD，提取部门关键词 (e.g., "Engineering", "Sales", "Marketing")。
2.  **精准搜索**: Apollo 搜索时，Job Title 不只搜 "HR"，而是搜 `"{Department} Recruiter"` (例如 "Technical Recruiter", "Sales Recruiter")。
3.  **Hiring Manager 优先**: 对于中小公司 (<500人)，优先搜 "Head of {Department}" 或 "VP of {Department}"，直接联系业务老板比联系 HR 有效。

### **C. 放弃 "LinkedIn Overlay" 模式，改用 "Direct Apollo Website" 模式**

你提到的痛点是真实的：在 LinkedIn 上用 Apollo 插件非常麻烦（需下滑、点进 Profile、点插件浮窗、再点 Reveal）。路径太长，极易失败。

**新策略**：我们的插件**不操作 LinkedIn，直接操作 Apollo 官网 (app.apollo.io)**。
*   **流程**：插件直接打开 `https://app.apollo.io/#/people`。
*   **优势**：Apollo 官网的搜索功能极其强大。我们可以直接把公司名填入 "Organization" 筛选器，把 "HR" 填入 "Job Title" 筛选器。
*   **结果**：直接得到一个清洗好的 HR 列表，根本不需要去 LinkedIn 上一个个翻人。这是一个**降维打击**的方案。

### **B. 解决 "公司重名" (Entity Disambiguation)**

重名是抓取的经典难题（比如搜 "Delta"，出来 "Delta Airlines", "Delta Faucet", "Delta Dental"...）。

**解决方案：Domain (域名) 匹配法**
*   **Step 1**: Job Scraper 爬取职位时，通常能拿到职位对应的 **Apply URL** 或者公司官网 **Domain** (例如 `openai.com`)。
*   **Step 2**: 在 Apollo 搜索时，**不搜公司名，只搜 Domain**。
    *   Apollo 支持 `q_organization_domains[]=openai.com` 参数。
*   **优势**: 域名是全球唯一的，绝对不会重名！
*   **Fallback**: 如果实在没有域名，才搜公司名，并让插件提取搜索结果的第一条 Company Industry/Location 进行简单的模糊比对（这里可以用极其轻量的规则或 GPT-4o-mini 辅助判断，成本可控）。

---

## 3. 架构设计 (Client-Server Model)

### **Backend (Server): Job Autopilot Container**
- **Role**: Command Center (Brain)
- **Responsibilities**:
  - Identify companies/jobs lacking HR contact info.
  - Maintain a `Task Queue` (e.g., "Find HR for openai.com").
  - Expose REST API endpoints for the extension.
  - Store retrieved data into PostgreSQL.

### **Frontend (Client): Chrome Extension**
- **Role**: Field Agent (Hands)
- **Responsibilities**:
  - Run in user's local Chrome browser (User-Hosted).
  - Poll backend for tasks.
  - **Action**: Open `app.apollo.io` -> Filter by Domain -> Reveal Email.
  - Report success/failure back to backend.
  - **Compliance**: Respects user's session and rate limits to simulate human behavior.

---

## 4. 详细工作流 (Revised Workflow)

1.  **Task Generation**:
    - Backend detects a job: "Software Engineer at OpenAI" (Domain: `openai.com` extracted from apply link).
    - Adds task to Queue: `{type: "domain_search", domain: "openai.com", role: "HR"}`.

2.  **Execution (Direct Apollo Search)**:
    - Extension opens background tab: `https://app.apollo.io/#/people?personTitles[]=HR&organizationDomain[]=openai.com`
    - **No Scrolling Needed**: The result list directly shows HR people at that explicit domain.
    - **Action**:
        - Click 1st person's "Access Email".
        - Scrape Email.
        - Send back to Docker.

3.  **Handling "No Domain"**:
    - If scraping failed to get domain, we search by Company Name.
    - Extension scrapes the top 3 company results from Apollo.
    - Returns them to Backend: "I found Delta (Airline), Delta (Faucet)... which one?"
    - Backend (AI Agent) decides based on Job Description context ("This job is about faucets...") and re-queues a precise Domain Search task.

---

## 5. 可行性分析 (Feasibility Check)

| 挑战 | 解决方案 | 风险等级 |
|------|----------|----------|
| **Apollo Quota (免费额度)** | **关键发现**: 免费版不仅有 Export Credits (导出额度，极少)，更有 **View/Email Credits** (查看邮箱额度)。<br>- **Gmail 用户**: 约 **100 credits/月**。<br>- **企业邮箱用户**: 也是有限制的 (Fair Usage Policy)。<br>**对策**: 插件只 "View" 不 "Export" (CSV导出)，且在 UI 显示剩余额度警告。 | Medium |
| **公司重名 (Collision)** | **策略升级**: <br>1. **Domain 优先**: 从职位链接提取 `openai.com` 直接搜。<br>2. **清洗域名**: 自动去除 `careers.`, `jobs.` 等子域名。<br>3. **Fallback**: 若无域名，搜公司名 + 模糊匹配 Industry/Location。 | Low |
| **Apollo 反爬 (Cloudflare)** | 使用用户真实浏览器 + Chrome Extension，拥有最高信任度。 | Low |
| **DOM 结构变动** | 页面改版会导致脚本失效。对策: 开源项目维护选择器配置。 | Medium |
| **法律/合规性** | **User-Hosted**: 代码运行在用户本地，用户对自己账号负责。<br>**Rate Limiting**: 严格限制请求频率，模拟真人，避免滥用。 | Medium |
| **成本** | **$0**. 消耗的是 Apollo Free View Credits。 | Zero |

---

## 6. 开发计划 (Revised Implementation Steps)

### Phase 1: Backend API Setup (2 Days)
- [ ] Create `HRTaskQueue` in database.
- [ ] Implement `app.py` (Flask) endpoints.
- [ ] **Critical**: Enhance `JobScraper` to extract Company Domain (e.g., from email domain or apply link) to solve the duplicate name issue upstream.

### Phase 2: Extension Core (3 Days)
- [ ] Create `manifest.json` v3.
- [ ] Implement `content_script.js` for `app.apollo.io`.
- [ ] Logic to handle credit limits (stop when limit reached).

### Phase 3: Integration & Testing (2 Days)
- [ ] End-to-end test with Domain-based search.
- [ ] Fallback test with Name-based search.
