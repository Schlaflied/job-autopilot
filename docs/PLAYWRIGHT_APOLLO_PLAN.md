# Apollo Agent - Playwright 自动化与 Outreach 策略 V2.0

## 1. 核心技术方案：Playwright 自动化

使用 Playwright 控制真实 Chrome 浏览器，自动从 Apollo.io 获取 HR/Recruiter 联系信息。

### ✅ 关键特性
| 需求 | 实现方式 |
|------|----------|
| **全自动化** | Python 独立脚本 (无 Chrome Extension)，使用 Playwright 控制浏览器 |
| **登录保持** | 首次运行需手动登录 Apollo，Session 会持久化保存 |
| **公司匹配** | 优先 Domain 搜索 (100% 准确)；无 Domain 时校验公司名 |
| **数据写入** | 直接通过 Python 调用数据库模型，不经过 API |

### 🛠️ Title 提取改进 (针对 "Recruiter" 泛称问题)
为确保获取 "Technical Recruiter" 而非泛泛的 "Recruiter"：
1. **DOM 优先策略**：不再只依赖 Regex，而是深入遍历 `role="row"` 下的所有文本块。
2. **最长匹配原则**：优先选择包含关键词且**长度最长**的文本 (例如优先选 "Senior Technical Recruiter" 而非 "Recruiter")。
3. **回退机制**：仅在 DOM 提取失败时，才回退到 Regex 匹配。

---

## 2. 多层级 Outreach 策略 (Multi-Layer Strategy)

为了解决 Apollo 覆盖率不足的问题，采用由高到低的"漏斗式"策略：

| 层级 | 目标 | 方法 | 成功率预估 |
|------|------|------|------------|
| **Layer 1 (Gold)** | **HR / Recruiter 个人邮箱** | Apollo Playwright 自动化 | ~40-60% |
| **Layer 2 (Silver)** | **公司通用招聘邮箱** | 抓取 careers@, jobs@, hello@ (Apollo 或官网) | ~20% |
| **Layer 3 (Bronze)** | **手动搜索辅助** | Google Search Link ("Company Technical Recruiter email") | 需人工 |
| **Layer 4 (Iron)** | **直接网申 (Fallback)** | 如果都失败，仅进行传统的 Apply URL 投递 | N/A |

### 实施细节
- **Layer 1**: 当前正在做的 Playwright 脚本。
- **Layer 2**: 如果 Layer 1 失败，脚本尝试在 Apollo 公司页抓取 Generic Email。
- **Layer 3**: 在 Email Center UI 提供一键跳转 Google 搜索的链接。

---

## 3. Streamlit 集成计划

让自动化脚本融入日常工作流，而不是在黑底白字的终端里敲命令。

### UI 设计
在 **Email Center** 页面顶部添加控制面板：

```text
[ 🚀 Run Apollo Automation ]  Running Status: ✅ Idle

Log Output:
> [22:30:15] Logging into Apollo...
> [22:30:18] Searching for "HubSpot" (hubspot.com)...
> [22:30:25] ✅ Found: Sarah Chen <sarah@hubspot.com> - Senior Technical Recruiter
> [22:30:30] Searching for "SmallStartup"... 
> [22:30:35] ⚠️ No HR found. Trying generic email...
```

### 功能点
1. **一键运行**: 点击按钮触发后台 Python 线程运行 `ApolloAutomation`。
2. **实时日志**: 使用 `st.empty()` 或 `st.code()` 实时显示抓取进度。
3. **手动修正**: 在生成的 Email 预览界面，允许用户手动修改 Title 和 Email。

---

## 4. 文件结构更新

```
modules/
├── apollo_automation.py   # [Core] Playwright 逻辑
│   ├── ApolloAutomation class
│   ├── search_hr_contacts() (Layer 1)
│   ├── search_generic_email() (Layer 2 - Future)
│   └── extract_and_save()

scripts/
└── run_apollo_scraper.py  # [CLI] 命令行入口

streamlit_app.py           # [UI] 集成运行按钮和日志显示
```

---

## 5. 执行前配置清单

- [x] Chrome Profile 路径确认
- [x] Apollo 登录 (Session 已保存)
- [ ] Python 依赖: `playwright` (已安装)
- [ ] 数据库字段: `title` (已支持)

---

## 下一步行动 (Action Items)

1. **Title 验证**: 再次测试抓取，确认 `Senior Technical Recruiter` 等长 Title 能被正确保存。
2. **Streamlit 集成**: 修改 `streamlit_app.py`，加入运行按钮和日志显示。
