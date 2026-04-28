# SaveMoney AI 攒钱软件

## 这是什么

这是我做的一个攒钱和消费记录项目。输入月收入、固定支出、最低生活费、攒钱目标和截止日期，它会帮你算一下每天应该存多少钱、目标是否可行，然后你可以每天在上面记录开销、看统计、调计划。

目前主要用于学习、展示和个人使用，代码放在 GitHub 上公开。

## 项目定位

当前这个是 Web 全栈版，前端用 Next.js，后端用 FastAPI + SQLite。跑起来方便，适合在电脑上体验和调试。

它不是 Android APK 版本。如果后面想做手机 APP，我会单独开一个原生 Android 项目重新实现，这个仓库保持 Web 版本不做 APK 适配。

## 技术栈

**前端**
- Next.js
- TypeScript
- Tailwind CSS

**后端**
- Python FastAPI
- SQLite
- SQLAlchemy
- Pydantic

## 已实现功能

- 生成攒钱计划
- 后端连接状态检测
- 常用信息保存到 localStorage
- 记录消费
- 消费自动分类
- 查询最近消费记录
- 编辑消费记录
- 删除消费记录
- 每日消费汇总
- 消费分类统计
- 本月总览
- 本月消费建议
- 动态调整攒钱计划
- CSV 导出
- 数据存储说明

## 本地怎么跑

前提：装好 Python 3.10+ 和 Node.js 18+，装好后端依赖（`backend/requirements.txt`）和前端依赖（`frontend/package.json`）。

**启动后端**

```bash
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

后端默认跑在 `http://127.0.0.1:8000`，接口文档在 `http://127.0.0.1:8000/docs`。

**启动前端**

```bash
cd frontend
npm run dev
```

前端默认跑在 `http://localhost:3000`，启动后会自动连后端。

## 环境变量

前端 API 地址写在 `frontend/app/lib/api.ts` 里，默认是 `http://127.0.0.1:8000`。如果想改后端地址，可以在前端目录下创建 `.env.local` 文件：

```
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## 数据存储

消费记录默认保存在本地 SQLite 数据库里，文件路径是 `backend/savemoney.db`。这个文件已经在 `.gitignore` 里了，不会上传到 GitHub。

## 后续计划

- 优化页面体验（尤其是手机上看起来怎么样）
- 补充一些项目截图放到 README 里
- 后续考虑单独做一个 Android 版本

## 许可证

MIT License，详见 [LICENSE](./LICENSE)。

## 作者

岁年