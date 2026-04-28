# SaveMoney AI 攒钱软件

## 项目简介
SaveMoney AI 攒钱软件是一个基于 Web 的个人攒钱与消费记录工具，用于学习、展示和个人财务管理原型。
它可以根据收入、固定支出、最低生活费、攒钱目标和截止日期生成每日攒钱计划，并支持消费记录、统计、建议和 CSV 导出。

## 项目定位
- 当前版本是 **Web 全栈展示版**
- 适合本地运行、学习和功能展示
- 后续如果开发安卓 APP，计划另开原生 Android 项目实现
- 当前项目暂不作为 APK 版本维护

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
- 作者署名

## 本地运行方法

### 前提条件
- 已安装 Python 3.10+ 与 Node.js 18+
- 后端依赖已安装（参考 `backend/requirements.txt`）
- 前端依赖已安装（参考 `frontend/package.json`）

### 启动后端
```bash
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```
- 后端默认地址：`http://127.0.0.1:8000`
- API 文档地址：`http://127.0.0.1:8000/docs`

### 启动前端
```bash
cd frontend
npm run dev
```
- 前端默认地址：`http://localhost:3000`
- 前端启动后会自动连接后端 API

## 环境变量说明
前端 API 地址集中配置在 `frontend/app/lib/api.ts`。

可通过环境变量 `NEXT_PUBLIC_API_BASE_URL` 自定义后端地址（默认值为 `http://127.0.0.1:8000`）。

示例（`.env.local` 文件）：
```
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## 数据存储说明
- 消费记录保存在本地 SQLite 数据库中
- 默认数据库文件是 `backend/savemoney.db`
- 数据库文件已加入 `.gitignore`
- 不应提交真实消费数据到 GitHub

## GitHub 公开注意事项
请勿将以下内容提交到公开仓库：

- `backend/savemoney.db`（数据库文件）
- `.env`（环境变量文件）
- `.env.local`（本地环境变量文件）
- 密钥、Token
- 服务器密码
- 真实消费记录

以上文件已通过 `.gitignore` 排除，但仍需注意不要手动强制提交。

## 后续计划
- 完善 README 和项目截图
- 增加开源许可证 LICENSE
- 优化移动端页面体验
- 如果需要安卓 APP，另开原生 Android 项目
- 长期多人使用时考虑云端后端和 PostgreSQL

## 作者
作者：岁年