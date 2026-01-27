# Connection Sync 使用指南

## 🎯 目标

1. **导入全部800+个connections** 到AI Memory
2. **自动检测new connections** 每日/每周运行

---

## 📝 使用方法

### 方法1: 导入全部connections（一次性）

```bash
# 在项目根目录运行
cd c:\Users\Schlaflied\Desktop\Job Autopilot

# 导入全部connections（翻30页，约600-1500个）
python scripts/auto_sync_connections.py --pages 30
```

**参数说明**:
- `--pages 30` - 翻30页（每页约20-50个connections）
- 如果800+个connections，建议用`--pages 40`保险点

**输出示例**:
```
📊 Current connections in Memory: 150
📄 Page 1/30...
   Found 48 connections, 3 new
...
✅ Sync Complete!
   Total imported: 650
   New connections: 500
```

---

### 方法2: 定期自动检测new connections

每周运行一次，只导入新增的connections：

```bash
# 周一早上运行
python scripts/auto_sync_connections.py --pages 10
```

**为什么只需要10页**?
- 新connections通常排在前面
- 翻10页足够检测到所有新人

---

## 🤖 完全自动化（推荐）

### Option A: 集成到 `daily_check.py`

每天运行`daily_check.py`时自动同步connections：

**修改建议**:
在 [`scripts/daily_check.py`](file:///c:/Users/Schlaflied/Desktop/Job%20Autopilot/scripts/daily_check.py) 的开头添加：

```python
# 在 run_daily_check() 开头添加
async def run_daily_check(self):
    print("📊 Daily Status Check")
    print("=" * 60)
    
    # ✨ NEW: Sync connections first
    print("\n🔄 Step 1: Sync new connections...")
    syncer = ConnectionSyncer()
    await syncer.sync_all_connections(max_pages=10, detect_new=True)
    
    # 原有逻辑...
```

### Option B: Windows任务计划程序

创建每周自动任务：

1. 打开"任务计划程序"
2. 创建基本任务
   - 名称: "LinkedIn Connection Sync"
   - 触发器: 每周一早上9点
   - 操作: 启动程序
     - 程序: `python`
     - 参数: `c:\Users\Schlaflied\Desktop\Job Autopilot\scripts\auto_sync_connections.py --pages 10`
     - 起始位置: `c:\Users\Schlaflied\Desktop\Job Autopilot`

---

## 📊 验证成功

### 查看Memory中有多少contacts

```bash
python -c "from modules.coffee_chat_memory import CoffeeChatMemory; m = CoffeeChatMemory(); print(f'Total: {len(m.get_all_contacts())}')"
```

### 查看同步报告

报告自动保存到：`data/connection_sync_stats.txt`

```bash
type data\connection_sync_stats.txt
```

---

## 🔍 对比：import_connections.py vs auto_sync_connections.py

| Feature | import_connections.py | auto_sync_connections.py |
|---------|----------------------|--------------------------|
| 翻页能力 | ✅ 支持 | ✅ 支持 |
| 检测新connections | ❌ 无 | ✅ **有** |
| 统计报告 | ❌ 无 | ✅ **有** |
| 去重 | ⚠️ 简单 | ✅ 智能 |
| 推荐使用 | ❌ 旧版本 | ✅ **新版本** |

**建议**: 以后使用 `auto_sync_connections.py`

---

## 💡 常见问题

### Q1: 为什么看到重复的URL在保存？

A: Memory内部有去重机制，重复保存不会创建duplicate records。日志显示多次是因为每页可能看到同一个人（LinkedIn分页重叠）。

### Q2: 多久运行一次？

A: 
- **首次**: 立即运行，导入全部（`--pages 30`）
- **日常**: 每周一次（`--pages 10`）检测新connections

### Q3: 会重复向同一个人发connection request吗？

A: 不会！`linkedin_auto_connect.py`运行时会检查Memory，跳过已存在的contacts。

---

## ✅ 下一步

1. **运行一次性导入**:
   ```bash
   python scripts/auto_sync_connections.py --pages 40
   ```

2. **设置自动化**（选一个）:
   - Option A: 修改`daily_check.py`
   - Option B: Windows任务计划程序

3. **验证成功**:
   ```bash
   python -c "from modules.coffee_chat_memory import CoffeeChatMemory; m = CoffeeChatMemory(); print(f'Total: {len(m.get_all_contacts())}')"
   ```
