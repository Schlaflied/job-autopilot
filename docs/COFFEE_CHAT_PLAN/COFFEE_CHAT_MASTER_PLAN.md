# Coffee Chat 完整实施计划 (Master Plan)

**最后更新**: 2026-01-26  
**目标**: 从现有connections和新job listings中识别hidden job opportunities，发送AI个性化消息获得内推

---

## 📋 目录

1. [核心需求](#核心需求)
2. [系统架构](#系统架构)
3. [技术实现](#技术实现)
4. [实施阶段](#实施阶段)
5. [完整工作流](#完整工作流)
6. [优先级](#优先级)

---

## ✅ 已实现功能

### 1. 核心基础设施 (Phase 1-3: ✅ 已完成)

#### 🚀 自动连接引擎
- [`scripts/linkedin_auto_connect.py`](file:///c:/Users/Schlaflied/Desktop/Job%20Autopilot/scripts/linkedin_auto_connect.py) - **稳定运行**
  - 多模态交互（JavaScript + Snapshot + Enter键fallback）
  - Modal处理优化（Send without a note）
  - 每日限额控制（20条/天）
  - 周末检测（自动跳过）
  - 登录验证检查

#### 💾 Memory系统
- [`modules/coffee_chat_memory.py`](file:///c:/Users/Schlaflied/Desktop/Job%20Autopilot/modules/coffee_chat_memory.py) - **稳定运行**
  - 去重功能（防止重复联系）
  - 持久化存储（SQLite database）
  - 状态追踪（pending/accepted/declined）

#### 📥 导入现有Connections
- [`scripts/import_connections.py`](file:///c:/Users/Schlaflied/Desktop/Job%20Autopilot/scripts/import_connections.py) - **可用**
  - 从LinkedIn导入现有connections
  - 自动parse profile URLs
  - 存入Memory避免重复发送

#### 📊 每日状态追踪
- [`scripts/daily_check.py`](file:///c:/Users/Schlaflied/Desktop/Job%20Autopilot/scripts/daily_check.py) - **已验证**
  - 检查pending invitations
  - 生成每日报告（sent/pending/accepted/declined）
  - 完整的Send → Track反馈循环

### 2. AI Agents (Phase 4: 🟡 部分完成)

#### 🤖 已实现的Agents
| Agent | 文件 | 状态 | 功能 |
|-------|------|------|------|
| **ContactRankerAgent** | [`coffee_chat_agents.py`](file:///c:/Users/Schlaflied/Desktop/Job%20Autopilot/modules/coffee_chat_agents.py#L21-L127) | ✅ | 根据校友/职位匹配度排序 |
| **PersonalizationAgent** | [`coffee_chat_agents.py`](file:///c:/Users/Schlaflied/Desktop/Job%20Autopilot/modules/coffee_chat_agents.py#L130-L291) | ✅ | AI生成个性化消息（GPT-4） |
| **ScamDetectionAgent** | [`coffee_chat_agents.py`](file:///c:/Users/Schlaflied/Desktop/Job%20Autopilot/modules/coffee_chat_agents.py#L294-L428) | ✅ | 检测fake/scam账号 |
| **HiddenJobDetector** | [`hidden_job_detector.py`](file:///c:/Users/Schlaflied/Desktop/Job%20Autopilot/modules/hidden_job_detector.py) | ✅ | 从公司帖子检测招聘信号 |

#### 🔗 Job Scraper整合
- [`modules/job_contact_integrator.py`](file:///c:/Users/Schlaflied/Desktop/Job%20Autopilot/modules/job_contact_integrator.py) - **已完成**
  - 从high-score jobs（≥7分）提取公司
  - 按domain分组jobs
  - 为LinkedIn alumni搜索提供目标公司列表

### 3. 待实现功能 (Phase 5-10: ⚪ Todo)

#### ❌ 缺失的关键功能
1. **ActivityFilterAgent** - LinkedIn活跃度检测（30天内发帖）
2. **BackgroundMatcherAgent** - AI判断校友/未来上司关系
3. **个人帖子检测** - 扩展HiddenJobDetector检测connection的个人帖子
4. **LinkedIn消息发送** - 实现send direct message功能
5. **AI Disclosure强制模板** - 在PersonalizationAgent中添加GitHub链接
6. **统一Pipeline** - 整合Track 1 (existing) + Track 2 (new jobs)

---

## 🔍 关键问题讨论

### Q1: Quota问题 - "找不到那么多有job posting的公司"

**现状问题**:
- 目前 [`linkedin_auto_connect.py`](file:///c:/Users/Schlaflied/Desktop/Job%20Autopilot/scripts/linkedin_auto_connect.py#L1099-L1100) 需要手动输入`--company`参数
- 每天20个quota，但有时找不到足够多有job posting的公司
- 用户建议：能否让Chrome DevTools自动点"People recommend for you"？

**解决方案**:
我们采用**三源策略**（而非仅靠job scraper）：

```
┌────────────────────────────────────────────────┐
│         每日20个Quota分配策略                  │
├────────────────────────────────────────────────┤
│ Source 1: Job Scraper公司 (优先)     → 10个   │
│   - 从高分jobs (≥7) 提取公司                  │
│   - 搜索这些公司的校友                         │
│                                                │
│ Source 2: 现有Connections (Hidden Job)→ 5个   │
│   - 检测connection公司的招聘信号               │
│   - 向这些人发coffee chat消息                 │
│                                                │
│ Source 3: LinkedIn推荐 (补充)      → 5个      │
│   - "People you may know"                     │
│   - 自动点击Connect按钮                        │
│   - 作为兜底方案（当前两个source不足时）       │
└────────────────────────────────────────────────┘
```

**实现建议**:
1. **优先级排序**: Job Scraper > Hidden Job Detection > LinkedIn推荐
2. **自动fallback**: 如果Job Scraper公司<5个，自动切换到LinkedIn推荐页面
3. **新增功能**: 在`linkedin_auto_connect.py`添加`--mode recommend`选项

### Q2: 如何运行 `import_connections.py`？

**运行命令**:
```bash
# 在项目根目录运行（c:\Users\Schlaflied\Desktop\Job Autopilot）
python scripts/import_connections.py --pages 5

# 参数说明:
# --pages 5    # 翻5页connections（约500个contacts）
```

**它做什么**:
1. 打开LinkedIn Connections页面
2. 自动滚动翻页
3. 提取所有connection的profile URLs
4. 存入Memory（`data/coffee_chat.db`）
5. **目的**: 避免向已连接的人重复发送connection request

**为什么需要它**:
- 你有几百个existing connections
- 如果不导入，auto-connect可能会重复发送给这些人
- Memory会标记这些人为`status='connected'`

**验证是否成功**:
```bash
# 查看数据库中有多少contacts
python -c "from modules.coffee_chat_memory import CoffeeChatMemory; m = CoffeeChatMemory(); print(f'Total contacts: {len(m.get_all_contacts())}')"
```

### Q3: 双轨逻辑核心策略

你说得对！Focus是：

**双轨并行 (Two-Track Strategy)**:

| Track | 数据源 | 目标人群 | 行动 |
|-------|--------|----------|------|
| **Track 1** | Job Scraper | 高分job公司的校友 | Send connection request |
| **Track 2** | 现有Connections | 公司有hiring signals的人 | Send coffee chat message |

**关键区别**:
- **Track 1**: 新人，需要先发connection request → 等待accept → 发消息
- **Track 2**: 已连接，直接发coffee chat消息（无需等待）

**为什么两个都要**:
1. **Track 1**: 找"新"机会，扩大network
2. **Track 2**: 利用"现有"资源，挖掘hidden market
3. **互补性**: Track 2回复率更高（已连接），Track 1覆盖面更广

---

## 🎯 核心需求

### 用户场景
- **已有资源**: 几百个LinkedIn connections
- **核心挑战**: 识别哪些公司正在招人（hidden job market）
- **行动目标**: 向这些人发coffee chat邀请，获得内推

### 关键需求

#### 1. 多源招聘信号检测
| 信号源 | 检测方式 | 权重 | 实现状态 |
|--------|----------|------|---------|
| **公司页面帖子** | 关键词匹配 (hiring, join our team) | 40% | ✅ 已实现 |
| **个人connection发帖** | 检测connection是否发招聘信息 | 30% | ⚪ 待实现 |
| **Job Scraper listings** | 从Indeed/LinkedIn获取新职位 | 50% | ✅ 已实现 |

#### 2. 目标人群筛选
- ✅ **校友** - 同学校毕业（优先级最高）- ContactRankerAgent已支持
- ⚪ **未来上司** - AI判断职位层级（Manager/Director/VP）- 待实现BackgroundMatcherAgent
- ⚪ **相关领域** - L&D、AI、HR等（用户配置）- 待实现

#### 3. 活跃度检测
- ⚪ 发消息前检查对方**最近是否在LinkedIn发帖** - 待实现ActivityFilterAgent
- 避免给"死号"浪费quota

#### 4. AI Disclosure（强制）
- ⚪ 所有消息末尾必须包含透明声明 - 待添加到PersonalizationAgent
- 包含GitHub项目链接：`github.com/Schlaflied/job-autopilot`

---

## 🏗️ 系统架构

### 数据流图

```
┌──────────────────────────────────────────────────────┐
│                  INPUT SOURCES                       │
├──────────────────────────────────────────────────────┤
│  Track 1: Existing Connections (几百个)              │
│  │                                                    │
│  ├─ Profile Scraping                                 │
│  ├─ Company Info + Posts                             │
│  └─ Recent Activity                                  │
│                                                       │
│  Track 2: Job Scraper (Indeed, LinkedIn Jobs)       │
│  │                                                    │
│  ├─ New Job Postings (score ≥ 7)                    │
│  ├─ Extract Companies                                │
│  └─ Search Alumni at Companies                       │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│            SIGNAL DETECTION LAYER                    │
├──────────────────────────────────────────────────────┤
│  🔍 HiddenJobDetector                                │
│     ├─ Company Page Posts (强信号 40%)               │
│     ├─ Personal Posts by Connections (中等 30%)      │
│     ├─ Job Listings (强信号 50%)                     │
│     └─ Aggregate Score (综合判断)                    │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│             TARGET FILTERING LAYER                   │
├──────────────────────────────────────────────────────┤
│  ✅ ActivityFilterAgent                              │
│     └─ Recent Post Detection (30天内活跃)            │
│                                                       │
│  🎯 BackgroundMatcherAgent                           │
│     ├─ Alumni Detection (校友 +40分)                 │
│     ├─ Role Similarity (未来上司 +35分)              │
│     └─ Field Relevance (领域匹配 +25分)              │
│                                                       │
│  Decision: should_contact = match_score ≥ 40         │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│              ACTION DECISION LAYER                   │
├──────────────────────────────────────────────────────┤
│  For Existing Connections:                           │
│    → Send Message Directly (已连接)                  │
│                                                       │
│  For New Targets (from job scraper):                 │
│    → Send Connection Request                         │
│    → Wait for Accept                                 │
│    → Send Message                                    │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│               MESSAGING LAYER                        │
├──────────────────────────────────────────────────────┤
│  💬 PersonalizationAgent                             │
│     └─ Generate Coffee Chat Message                  │
│         + Hiring Signal Context                      │
│         + Background Similarity                      │
│         + AI Disclosure (强制)                       │
│         + GitHub Link                                │
└──────────────────────────────────────────────────────┘
```

---

## 🛠️ 技术实现

### Phase 6: 招聘信号增强检测

#### 扩展 `HiddenJobDetector`

```python
# modules/hidden_job_detector.py

class HiddenJobDetector:
    
    def check_personal_hiring_posts(self, contact_posts: List[str]) -> Dict:
        """检测个人LinkedIn帖子中的招聘信号"""
        signals = []
        
        for post in contact_posts:
            post_lower = post.lower()
            
            # 强信号：直接招聘
            if any(kw in post_lower for kw in ['we are hiring', "we're hiring", 'join our team']):
                signals.append({'type': 'direct_hiring', 'strength': 'strong'})
            
            # 中等信号：团队扩张
            elif any(kw in post_lower for kw in ['growing team', 'new role']):
                signals.append({'type': 'team_growth', 'strength': 'medium'})
        
        is_hiring = len([s for s in signals if s['strength'] == 'strong']) > 0
        confidence = min(1.0, len(signals) * 0.3)
        
        return {'is_hiring': is_hiring, 'confidence': confidence, 'signals': signals}
    
    def aggregate_signals(
        self, 
        company_signals: Dict, 
        personal_signals: Dict, 
        job_listings: List
    ) -> Dict:
        """聚合所有来源的招聘信号"""
        total_confidence = 0.0
        
        # 公司信号 (权重 0.4)
        if company_signals.get('is_likely_hiring'):
            total_confidence += company_signals['confidence'] * 0.4
        
        # 个人信号 (权重 0.3)
        if personal_signals.get('is_hiring'):
            total_confidence += personal_signals['confidence'] * 0.3
        
        # Job listings (权重 0.5 - 最强证据)
        if job_listings:
            total_confidence += 0.5
        
        return {
            'is_likely_hiring': total_confidence >= 0.3,
            'confidence': min(1.0, total_confidence),
            'sources': {
                'company_posts': company_signals.get('is_likely_hiring', False),
                'personal_posts': personal_signals.get('is_hiring', False),
                'job_listings': len(job_listings) > 0
            }
        }
```

---

### Phase 7: LinkedIn活跃度检测

#### 新建 `ActivityFilterAgent`

```python
# modules/coffee_chat_agents.py

class ActivityFilterAgent:
    """检测LinkedIn用户活跃度"""
    
    async def check_activity(self, profile_snapshot: str) -> Dict:
        """从profile snapshot检测活跃度"""
        activity_section = self._extract_activity_section(profile_snapshot)
        
        if not activity_section:
            return {'is_active': False, 'reason': 'No activity section found'}
        
        recent_posts = self._parse_recent_posts(activity_section)
        
        if recent_posts:
            latest_post_time = recent_posts[0].get('time_ago', '1y')
            is_active = self._is_recent(latest_post_time)  # 30天内
            
            return {
                'is_active': is_active,
                'last_activity': latest_post_time,
                'activity_score': min(100, len(recent_posts) * 10),
                'recent_posts': recent_posts[:3]
            }
        
        return {'is_active': False, 'last_activity': 'No posts'}
    
    def _is_recent(self, time_ago: str) -> bool:
        """判断时间是否在30天内 (e.g., '2d', '3w', '1mo')"""
        time_ago_lower = time_ago.lower()
        
        if 'd' in time_ago_lower or 'h' in time_ago_lower:
            return True
        elif 'w' in time_ago_lower:
            weeks = int(re.search(r'\d+', time_ago_lower).group())
            return weeks <= 4
        elif 'mo' in time_ago_lower:
            months = int(re.search(r'\d+', time_ago_lower).group())
            return months <= 1
        return False
```

---

### Phase 8: 背景相似度判断

#### 新建 `BackgroundMatcherAgent`

```python
# modules/coffee_chat_agents.py

class BackgroundMatcherAgent:
    """判断contact与用户的背景相似度"""
    
    async def analyze_background_match(
        self, 
        contact: Dict, 
        user_profile: Dict
    ) -> Dict:
        """分析背景相似度"""
        is_alumni = self._check_alumni(contact, user_profile)
        role_analysis = await self._analyze_role_relationship(contact, user_profile)
        
        # 计算match score
        match_score = 0
        reasons = []
        
        if is_alumni:
            match_score += 40
            reasons.append(f"Alumni: {contact.get('school_name')}")
        
        if role_analysis.get('is_potential_supervisor'):
            match_score += 35
            reasons.append(f"Potential supervisor: {role_analysis['reasoning']}")
        
        if role_analysis.get('field_match'):
            match_score += 25
            reasons.append(f"Field match: {role_analysis['field']}")
        
        return {
            'match_score': match_score,
            'is_alumni': is_alumni,
            'is_potential_supervisor': role_analysis.get('is_potential_supervisor'),
            'should_contact': match_score >= 40  # 至少满足一项
        }
    
    async def _analyze_role_relationship(self, contact: Dict, user_profile: Dict) -> Dict:
        """使用AI判断是否为潜在上司"""
        prompt = f"""Analyze if this contact could be a potential supervisor.

Contact: {contact.get('title')} at {contact.get('company')}
User: {user_profile.get('background')} targeting {user_profile.get('target_fields')}

Is contact in managerial role (Manager/Director/VP)?
Is their field relevant?

Return JSON:
{{
    "is_potential_supervisor": true/false,
    "field_match": true/false,
    "reasoning": "brief explanation"
}}
"""
        # AI call logic...
```

---

### Phase 9: Job Scraper 整合

#### `JobContactIntegrator` 增强

```python
# modules/job_contact_integrator.py

class JobContactIntegrator:
    """整合Job Scraper和Coffee Chat"""
    
    async def find_contacts_from_job_listings(
        self,
        job_score_threshold: int = 7,
        max_jobs: int = 10
    ) -> List[Dict]:
        """从高分job listings中找校友contacts"""
        
        # Step 1: 获取高分jobs
        jobs = get_cached_jobs(score_threshold=job_score_threshold, limit=max_jobs)
        
        # Step 2: 提取公司
        companies = {}
        for job in jobs:
            domain = job.get('company_domain')
            if domain:
                companies[domain] = {
                    'name': job.get('company'),
                    'jobs': companies.get(domain, {}).get('jobs', []) + [job]
                }
        
        # Step 3: 搜索校友
        user_profile = self.memory.get_user_profile()
        schools = [s['name'] for s in user_profile.get('schools', [])]
        
        all_contacts = []
        for domain, info in companies.items():
            contacts = await search_alumni(company_domain=domain, schools=schools)
            
            for contact in contacts:
                contact['source'] = 'job_listing'
                contact['related_jobs'] = info['jobs']
                contact['has_active_posting'] = True
            
            all_contacts.extend(contacts)
        
        return all_contacts
```

---

### Phase 10: AI Disclosure（强制）

#### 修改 `PersonalizationAgent`

```python
# modules/coffee_chat_agents.py

AI_DISCLOSURE_TEMPLATE = """

---
📌 Transparency: This message was AI-generated using my open-source automation project (github.com/Schlaflied/job-autopilot) to save time, but I'm a real person genuinely interested in connecting. Check out the project on GitHub if you're curious!"""

def generate_coffee_chat_message(self, contact: Dict, user_profile: Dict) -> str:
    """生成消息 WITH MANDATORY AI DISCLOSURE"""
    
    # AI生成主体消息
    message = self._generate_message_with_ai(contact, user_profile)
    
    # 🚨 强制添加AI Disclosure
    final_message = message + AI_DISCLOSURE_TEMPLATE
    
    return final_message
```

---

## 📋 实施阶段

### Week 1: 核心功能

#### Day 1-2: 活跃度检测
- [ ] 实现 `ActivityFilterAgent`
- [ ] 测试活跃度判断逻辑（30天阈值）

#### Day 3-4: 背景匹配
- [ ] 实现 `BackgroundMatcherAgent`
- [ ] 校友检测（rule-based）
- [ ] 上司判断（AI-based）

#### Day 5: 招聘信号增强
- [ ] 扩展 `HiddenJobDetector`
- [ ] 个人帖子检测
- [ ] 信号聚合逻辑

### Week 2: 整合与测试

#### Day 6-7: Job Scraper整合
- [ ] 增强 `JobContactIntegrator`
- [ ] 自动从job listings找校友

#### Day 8-9: 统一Pipeline
- [ ] 创建 `scripts/coffee_chat_pipeline.py`
- [ ] 整合Track 1 (existing) + Track 2 (new jobs)

#### Day 10: 消息发送
- [ ] 实现 `scripts/send_coffee_chat_messages.py`
- [ ] LinkedIn消息发送逻辑
- [ ] 强制AI disclosure

---

## 🎯 完整工作流

### 自动化Pipeline

```bash
# Step 1: 导入existing connections (如果还没做)
python scripts/import_connections.py --pages 10

# Step 2: 运行完整pipeline
python scripts/coffee_chat_pipeline.py --mode both

# Pipeline内部流程:
# ┌─────────────────────────────────────────┐
# │ Track 1: Existing Connections           │
# ├─────────────────────────────────────────┤
# │ 1. 获取已连接contacts                    │
# │ 2. 活跃度检测 (ActivityFilterAgent)      │
# │ 3. 招聘信号检测 (HiddenJobDetector)      │
# │ 4. 背景匹配 (BackgroundMatcherAgent)     │
# │ 5. 计算综合得分                          │
# └─────────────────────────────────────────┘
#              +
# ┌─────────────────────────────────────────┐
# │ Track 2: Job Listings                   │
# ├─────────────────────────────────────────┤
# │ 1. 获取高分jobs (score ≥ 7)             │
# │ 2. 提取公司 → 搜索校友                   │
# │ 3. 活跃度检测                            │
# │ 4. 背景匹配                              │
# │ 5. 计算综合得分                          │
# └─────────────────────────────────────────┘
#              ↓
# ┌─────────────────────────────────────────┐
# │ 去重 + 排序 (by final_score)            │
# └─────────────────────────────────────────┘
#              ↓
# ┌─────────────────────────────────────────┐
# │ Top 10 Candidates                       │
# └─────────────────────────────────────────┘
#              ↓
# ┌─────────────────────────────────────────┐
# │ 发送消息 (带AI Disclosure)              │
# │ - Existing: 直接发消息                   │
# │ - New: 发连接请求 → 等待 → 发消息        │
# └─────────────────────────────────────────┘
```

---

## 📊 优先级排序

### 🔴 P0 (立即开始)
1. **ActivityFilterAgent** - 避免给死号浪费quota
2. **AI Disclosure强制模板** - 透明度要求
3. **BackgroundMatcherAgent** - 校友/上司判断

### 🟡 P1 (Week 2)
4. **HiddenJobDetector扩展** - 个人帖子检测
5. **JobContactIntegrator增强** - job listing整合
6. **统一Pipeline脚本** - `coffee_chat_pipeline.py`

### 🟢 P2 (优化阶段)
7. **消息回复检测** - 追踪谁回复了
8. **Follow-up机制** - 3天无回复发follow-up
9. **A/B测试** - 优化消息模板

---

## 🚨 风险控制

| 风险 | 缓解措施 |
|------|----------|
| **LinkedIn检测spam** | • 每日限制5条消息<br>• 20-35秒随机延迟<br>• 个性化每条消息 |
| **AI disclosure被嫌弃** | • A/B测试监控回复率<br>• 如果<10%调整disclosure方式 |
| **误判hiring signals** | • 人工review top 15公司<br>• 多源信号聚合降低误判 |
| **背景匹配不准** | • AI判断 + rule-based双保险<br>• 设置得分阈值40分 |

---

## 📈 成功指标

| Metric | Target | 测量方式 |
|--------|--------|----------|
| **Response Rate** | ≥ 30% | 回复数 / 发送数 |
| **Coffee Chat Success** | ≥ 15% | 约到chat / 发送数 |
| **Referral Rate** | ≥ 5% | 获得内推 / coffee chat数 |
| **活跃度准确率** | ≥ 80% | 人工验证前100个 |

---

## 📄 文件清单

### 需要修改
- ✏️ `modules/hidden_job_detector.py` - 增强招聘信号检测
- ✏️ `modules/coffee_chat_agents.py` - 添加3个新Agent + AI disclosure
- ✏️ `modules/job_contact_integrator.py` - Job scraper整合
- ✏️ `scripts/import_connections.py` - 抓取公司帖子

### 需要新建
- ✨ `scripts/coffee_chat_pipeline.py` - 统一主脚本
- ✨ `scripts/send_coffee_chat_messages.py` - 消息发送

### 数据库扩展
```python
# modules/coffee_chat_models.py
class CoffeeChatContact(Base):
    # 新增字段
    company_recent_posts = Column(JSON)
    personal_recent_posts = Column(JSON)
    activity_score = Column(Float)
    background_match_score = Column(Float)
    final_score = Column(Float)
```

---

**下一步**: 请选择是否开始实施Week 1的功能！
