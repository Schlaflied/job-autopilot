# Email Center 完善计划

## 改进项

### 1. Job 信息展示增强

| 字段 | 改动 |
|------|------|
| Job Description | 添加可展开 JD |
| 薪资 | 显示 `$XX/hr` 或 `/year` |
| 工作地点 | 显示 Remote/Hybrid 标签 |
| 发布时间 | 显示 Posted date |
| Applied Jobs | 侧边管理区 (支持撤销标记) |

### 2. Load Cache 按钮 🔴 重要

- **数据源**: 从云端 PostgreSQL (Neon) 加载
- **过滤规则**: `exclude_applied=True` 排除已标记 Applied 的职位
- **复用**: `JobScraper.get_all_jobs(limit=100, exclude_applied=True)`

### 3. HR 邮箱自动填充

- 选择 Job 后从 `HRContact` 表自动查询
- 无邮箱时显示: "No HR contact found, please enter manually"

### 4. 邮箱验证

```bash
pip install email-validator
```

### 5. 批量发送限制

- **每日限制**: 20 封/天
- 防止被标记为 spam

### 6. 时效性处理

- >30天邮箱显示警告
- bounce 检测后标记无效

---

## 修改文件

| 文件 | 改动 |
|------|------|
| `streamlit_app.py` | Email Center UI (lines 1243-1300) |
| `database.py` | 查询 HRContact |
| `requirements.txt` | 添加 email-validator |

---

## 预计工时: 2.5h
