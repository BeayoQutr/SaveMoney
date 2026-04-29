# SaveMoney

一个用于攒钱计划生成、消费记录、消费分析和 AI 辅助记账的 Web 全栈项目。

当前版本是 **Web 全栈版**，前端使用 Next.js + React + TypeScript + Tailwind CSS，后端使用 FastAPI + SQLite + SQLAlchemy + Pydantic。项目适合在电脑和手机浏览器中使用，也适合作为完整 Web 全栈学习项目。

## 已完成功能

- 快速记录消费：金额、备注、日期、分类、支付方式、必要性标记
- 消费记录列表展示、编辑、删除
- 消费列表分页、日期筛选、分类筛选、关键词搜索
- 消费记录筛选面板自适应布局，窄屏和侧栏视图下日期输入不会被挤压
- 每日消费汇总
- 按日期范围统计消费分类
- 本月总览：总消费、消费笔数、日均消费、分类明细
- CSV 导出消费记录
- 攒钱计划生成：根据收入、固定支出、目标和截止日期计算每日需存
- 攒钱计划持久化：自动保存到数据库，首页展示当前计划和进度
- 动态调整攒钱计划
- 常用收入和支出信息保存到浏览器 localStorage
- 数据库备份/恢复：一键下载数据库、从备份文件恢复、导入 CSV
- AI 月度消费分析（优雅降级：未配置 Key 时返回友好提示）
- AI 消费分类建议，失败时回退本地规则
- AI 消费备注优化（未配置 Key 时返回原始备注）
- 可选 API 访问令牌认证
- 后端接口回归测试
- GitHub Actions 基础 CI

## 技术栈

- **前端**：Next.js / React / TypeScript / Tailwind CSS
- **后端**：FastAPI / Python / SQLAlchemy / Pydantic
- **数据库**：SQLite
- **AI**：DeepSeek API
- **测试与质量**：pytest / unittest 兼容测试、ESLint、Next build、GitHub Actions

## 项目结构

```text
SaveMoney/
├─ backend/
│  ├─ app/
│  │  ├─ routers/          # FastAPI 路由（expenses, plans, ai, backup）
│  │  ├─ services/         # 业务逻辑（expense_service, plan_service, ai_service）
│  │  ├─ utils/            # 日期、金额、CSV、备份等工具
│  │  ├─ main.py           # 创建 app、注册 CORS 和 routers
│  │  ├─ models.py         # SQLAlchemy 模型（Expense, SavingPlan）
│  │  ├─ schemas.py        # Pydantic 入参/出参
│  │  ├─ auth.py           # 可选 Bearer Token 认证
│  │  └─ budget_engine.py  # 攒钱计划计算
│  ├─ scripts/             # 数据库迁移脚本
│  ├─ tests/               # 后端测试
│  └─ requirements.txt
├─ frontend/
│  ├─ app/
│  │  ├─ components/       # 页面组件（ExpenseForm, ExpenseList, PlanForm, BackupPanel 等）
│  │  ├─ hooks/            # 前端 hooks
│  │  ├─ lib/              # API 客户端
│  │  ├─ page.tsx          # 页面组合入口
│  │  └─ types.ts          # TypeScript 类型
│  └─ package.json
├─ docs/images/            # 项目截图
└─ .github/workflows/ci.yml
```

## 本地运行

前提：装好 Python 3.10+ 和 Node.js 18+。

### 1. 安装依赖

```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

### 2. 配置环境变量

在 `backend/` 目录下创建 `.env` 文件，内容参考 `backend/.env.example`：

```text
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 可选：设置访问令牌以保护后端 API（不设置则不启用认证）
SAVEMONEY_ACCESS_TOKEN=
```

没有配置 API Key 也可以正常使用攒钱计划、消费记录、统计、CSV 导出、备份恢复等基础功能。AI 功能在配置 Key 后启用。

### 3. 启动后端

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

后端地址：

```text
http://127.0.0.1:8000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

### 4. 启动前端

```bash
cd frontend
npm run dev
```

前端地址：

```text
http://localhost:3000
```

## 运行检查

```bash
# 后端测试
cd backend
pytest

# 前端检查
cd frontend
npm run lint
npm run build
```

## 环境变量说明

| 变量 | 说明 | 位置 |
|---|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek API Key，用于 AI 功能 | `backend/.env` |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `backend/.env` |
| `DEEPSEEK_MODEL` | 使用的模型名称 | `backend/.env` |
| `SAVEMONEY_ACCESS_TOKEN` | 可选访问令牌，保护后端 API | `backend/.env` |
| `SAVEMONEY_DATABASE_URL` | 后端数据库连接地址，默认使用 `backend/savemoney.db` | 后端环境变量（可选，主要用于测试） |
| `NEXT_PUBLIC_API_BASE_URL` | 前端连接的后端地址，默认 `http://127.0.0.1:8000` | `frontend/.env.local`（可选） |
| `NEXT_PUBLIC_SAVEMONEY_ACCESS_TOKEN` | 前端访问令牌（与后端一致） | `frontend/.env.local`（可选） |

请勿将真实 API Key 提交到 Git。`backend/.env` 已在 `.gitignore` 中。

## 安全说明

- **仅本机使用**：默认配置仅供本地使用，不要将后端暴露到公网
- **局域网访问**：如需手机访问，请配置 `SAVEMONEY_ACCESS_TOKEN` 并在前端设置 `NEXT_PUBLIC_SAVEMONEY_ACCESS_TOKEN`
- 未配置访问令牌时，所有接口无需认证即可访问

## 稳定性与工程化

- 后端 `main.py` 只负责创建 app、注册 CORS 和 routers
- 后端业务逻辑拆分到 `routers/`、`services/`、`utils/`
- 前端 `page.tsx` 只负责组合组件和页面级刷新状态
- 前端类型、API 请求、localStorage 逻辑已独立封装
- 首屏优先展示"记一笔消费"，按钮和输入框适配移动端操作
- 右侧消费列表和导出面板使用响应式宽度，避免日期、筛选项在侧栏中拥挤或截断
- AI 功能全部优雅降级：未配置 Key 时返回友好提示而非 500 错误
- AI 分类失败时回退本地规则，普通记账不依赖 AI
- AI JSON 返回支持 Markdown 代码块容错解析
- 生产环境不打印 API key 或完整 AI 响应
- 金额处理集中封装为 Decimal 边界处理，避免到处直接操作 float
- 后端启动时会自动补齐旧 SQLite 数据库缺失字段，避免存量空库或旧库查询时报错
- 所有查询参数使用 URLSearchParams 编码，避免特殊字符问题

## 金额精度说明

数据库同时保存 `amount`（浮点元）和 `amount_cents`（整数分）两个字段。新记录自动同步写入 `amount_cents`，API 继续对外接收和返回"元"。

后端启动时会自动为旧版 SQLite 数据库补齐 `amount_cents`、`payment_method`、`is_necessary` 等兼容字段。存量数据也可通过迁移脚本手动补填：

```bash
cd backend
python -m scripts.migrate_to_cents
```

## 数据存储与备份

消费记录保存在本地 SQLite 数据库中：

```text
backend/savemoney.db
```

常用信息（月收入、固定支出、最低生活费、身份）保存在浏览器 localStorage 中。数据库文件和环境变量文件都已加入 `.gitignore`，不会提交到 GitHub。

### 备份功能

前端提供完整的备份与恢复功能：

- **下载数据库备份**：一键下载整个 SQLite 数据库文件
- **从备份文件恢复**：上传 `.db` 文件覆盖当前数据库（自动备份旧库）
- **导入 CSV**：上传消费记录 CSV 文件批量导入

**迁移或重装环境前，务必先下载数据库备份！**

## 项目截图

<img src="docs/images/home1.png" alt="攒钱计划" width="600" />

<img src="docs/images/home2.png" alt="记录消费" width="600" />

<img src="docs/images/home3.png" alt="消费记录列表" width="600" />

## 常见问题

### 前端提示后端未响应

请确认后端已启动，并能访问：

```text
http://127.0.0.1:8000/health
```

如果后端端口不是 8000，请在 `frontend/.env.local` 设置 `NEXT_PUBLIC_API_BASE_URL`。

### AI 服务不可用

AI 月度分析、AI 分类建议和 AI 备注优化需要在 `backend/.env` 配置 `DEEPSEEK_API_KEY`。未配置时，普通记账、查询、导出仍可使用；AI 分类会回退到本地规则，AI 备注优化返回原始备注，AI 月度分析返回友好提示。

### 数据库文件在哪里

默认数据库文件是 `backend/savemoney.db`。迁移或重装环境前请先使用前端"备份与恢复"功能下载数据库备份。

### 消费记录或本月总览提示加载失败

如果你从旧版本升级，旧版 `backend/savemoney.db` 可能缺少新字段。当前版本会在后端启动时自动补齐 SQLite 表结构；也可以在 `backend/` 目录运行 `python -m scripts.migrate_to_cents` 手动迁移后再刷新页面。

## 后续计划

- 继续增强预算分析维度
- 增加前端组件测试
- 增加标签（tags）功能
- 如果需要移动端，单独开发 Android 原生版

## 注意事项

- 本项目主要用于个人学习和作品展示
- AI 结果仅作为辅助参考，不一定完全准确
- 不要提交 `.env`、真实 API Key 或本地数据库文件

## 许可证

MIT License，详见 [LICENSE](./LICENSE)。

## 作者

岁年
