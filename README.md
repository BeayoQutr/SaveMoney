# SaveMoney

一个用于攒钱计划生成、消费记录、消费分析和 AI 辅助记账的 Web 全栈项目。

这是我做的完整学习项目，从前端到后端到数据库到 AI 接入，涵盖了一个 Web 应用的各个环节。代码放在 GitHub 上公开，主要用于学习、展示和个人使用。

## 项目定位

当前版本是 **Web 全栈版**，前端用 Next.js，后端用 FastAPI + SQLite，适合在电脑浏览器上使用和调试。

这不是 Android APK 版本。如果后面想做手机 App，会单独开一个原生 Android 项目重新实现，本仓库保持 Web 版本。

## 已完成功能

- 攒钱计划生成（根据收入、支出、目标、截止日期计算每日存钱金额）
- 常用信息保存（月收入、固定支出等存到浏览器 localStorage）
- 消费记录入库（金额、备注、日期、分类写入数据库）
- 消费记录列表展示（最近记录，含编辑和删除按钮）
- 编辑消费记录
- 删除消费记录
- 每日消费汇总（按日期查询消费总额和笔数）
- 消费分类统计（按日期范围统计各类别金额和笔数）
- 本月总览（本月总消费、日均消费、分类明细）
- 动态调整攒钱计划（已攒金额和今日消费动态调整每日需存）
- CSV 导出消费记录
- AI 月度消费分析（调用 DeepSeek 生成本月消费报告）
- AI 消费分类建议（根据金额和备注自动推荐分类）
- AI 分类结果入库（分类推荐结果随消费记录写入数据库）
- AI 分类防重复请求（相同金额和备注不重复请求 AI）
- AI 消费备注优化（优化消费备注文本，让记录更简洁规范）
- 前后端分离架构
- SQLite 本地数据库
- DeepSeek API 接入
- 后端接口回归测试
- 前端 lint 和生产构建检查

## 技术栈

- **前端**：Next.js / React / TypeScript / Tailwind CSS
- **后端**：FastAPI / Python
- **数据库**：SQLite
- **AI**：DeepSeek API
- **版本管理**：Git / GitHub

## 稳定性与工程化

- 后端数据库默认固定到 `backend/savemoney.db`，避免从不同目录启动时生成多个数据库文件
- 支持通过 `SAVEMONEY_DATABASE_URL` 指定数据库连接，便于测试和临时环境隔离
- 消费记录和 AI 请求增加输入清洗与校验，避免空备注、非法金额和过长文本进入业务逻辑
- 分类统计和 CSV 导出会校验日期范围，开始日期晚于结束日期时返回明确错误
- AI JSON 返回增加容错解析，可兼容模型返回 Markdown 代码块包裹 JSON 的情况
- 新增后端回归测试，覆盖消费记录 CRUD、日期范围校验、月份参数校验和 AI JSON 解析
- 前端页面元信息已改为项目名称，页面语言标记为 `zh-CN`

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

```
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

没有配置 API Key 也可以正常使用攒钱计划、消费记录等基础功能，只是 AI 相关功能（AI 月度分析、AI 分类建议、AI 备注优化）会返回服务不可用。

### 3. 启动后端

```bash
cd backend
.\\.venv\\Scripts\\Activate.ps1   # Windows PowerShell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

后端跑在 `http://127.0.0.1:8000`，接口文档在 `http://127.0.0.1:8000/docs`。

### 4. 启动前端

```bash
cd frontend
npm run dev
```

前端跑在 `http://localhost:3000`，启动后自动连接后端。

### 5. 运行检查

```bash
# 后端回归测试
cd backend
python -m unittest discover -s tests -v

# 前端代码检查和生产构建
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
| `SAVEMONEY_DATABASE_URL` | 后端数据库连接地址，默认使用 `backend/savemoney.db` | 后端环境变量（可选，主要用于测试） |
| `NEXT_PUBLIC_API_BASE_URL` | 前端连接的后端地址，默认 `http://127.0.0.1:8000` | `frontend/.env.local`（可选） |

请勿将真实 API Key 提交到 Git。`backend/.env` 已在 `.gitignore` 中。

## 数据存储说明

消费记录保存在本地 SQLite 数据库中，文件路径是 `backend/savemoney.db`。常用信息保存在浏览器的 localStorage 中。这两个存储位置都已在 `.gitignore` 中，不会上传到 GitHub。

## 项目截图

![攒钱计划](docs/images/home1.png)

![记录消费](docs/images/home2.png)

![消费记录列表](docs/images/home3.png)

![AI 月度分析](docs/images/home4.png)

## 后续计划

- 根据需要优化页面细节
- 拆分前端大页面组件，提升长期维护性
- 增加更多预算分析维度和测试覆盖
- 如果需要移动端，单独开发 Android 原生版

## 注意事项

- 本项目主要用于个人学习和作品展示
- AI 结果仅作为辅助参考，不一定完全准确
- 不要提交 `.env` 和真实 API Key

## 许可证

MIT License，详见 [LICENSE](./LICENSE)。

## 作者

岁年
