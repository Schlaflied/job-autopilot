# Coffee Chat Plan

## 📋 核心文档

| 文件 | 说明 |
|------|------|
| [COFFEE_CHAT_MASTER_PLAN.md](./COFFEE_CHAT_MASTER_PLAN.md) | **🎯 主计划** - 完整的Coffee Chat系统设计和实施路线图 |
| [CONNECTION_SYNC_GUIDE.md](./CONNECTION_SYNC_GUIDE.md) | **📖 使用指南** - 如何导入和自动同步LinkedIn connections |
| [PROJECT_STATUS_v1.md](./PROJECT_STATUS_v1.md) | **📊 项目状态** - 当前实现进度和已完成功能 |
| [MCP_ARCHITECTURE.md](./MCP_ARCHITECTURE.md) | **🔧 技术架构** - Chrome DevTools MCP架构说明 |

---

## 🚀 快速开始

### 1. 导入你的LinkedIn Connections

```bash
# 导入全部800+个connections
python scripts/auto_sync_connections.py --pages 40
```

详见：[CONNECTION_SYNC_GUIDE.md](./CONNECTION_SYNC_GUIDE.md)

### 2. 查看完整计划

查看 [COFFEE_CHAT_MASTER_PLAN.md](./COFFEE_CHAT_MASTER_PLAN.md) 了解：
- 已实现功能
- 待实现功能
- 双轨策略（Job Scraper + Hidden Job Detection）
- Quota分配策略

---

## 🎯 Phase概览

| Phase | 内容 | 状态 |
|-------|------|------|
| 0-3 | 基础设施（Auto-Connect, Memory, Agents） | ✅ 完成 |
| 4 | Hidden Job信号检测 | ✅ 完成 |
| 5 | 每日状态检查 | ✅ 完成 |
| 6 | 招聘信号增强检测 | ⚪ 待实现 |
| 7 | LinkedIn活跃度检测 | ⚪ 待实现 |
| 8 | 背景相似度判断 | ⚪ 待实现 |
| 9 | Job Scraper整合 | ⚪ 待实现 |
| 10 | 统一Pipeline | ⚪ 待实现 |

---

## ✅ 已确认决定

- 周末不发送
- Email通知验证码
- AI决定是否发note（每天5个限额）
- Chrome自动导入connections
- 每天检查一次状态
- **AI披露必须加在消息末尾**（包含GitHub链接）

---

## 🔧 LLM配置

| 用途 | 推荐 |
|------|------|
| 简历优化 | GPT-4o |
| 消息/润色 | Gemini 2.5 Flash |
| 分析/打分 | GPT-4o-mini |

---

## 📁 相关文件结构

```
scripts/
  ├─ linkedin_auto_connect.py    # 主自动化脚本
  ├─ auto_sync_connections.py    # Connection同步（推荐）
  ├─ import_connections.py       # Connection导入（旧版本）
  └─ daily_check.py              # 每日状态检查

modules/
  ├─ coffee_chat_agents.py       # AI Agents
  ├─ coffee_chat_memory.py       # Memory Layer
  ├─ hidden_job_detector.py      # 招聘信号检测
  └─ job_contact_integrator.py   # Job Scraper整合
```

---

## 💡 下一步

1. **导入connections**: 运行 `auto_sync_connections.py`
2. **查看master plan**: 了解完整架构
3. **选择实施优先级**: Phase 7-10中选择先做哪个
