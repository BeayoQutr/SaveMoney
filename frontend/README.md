# SaveMoney Frontend

这是 SaveMoney 的 Next.js 前端，负责攒钱计划、消费记录、统计总览、CSV 导出和 AI 辅助功能的浏览器界面。

## 本地运行

```powershell
cd frontend
npm install
npm run dev
```

项目已默认使用 webpack 启动 Next 开发服务器，避免 Turbopack 在部分 Windows 电脑上导致高 CPU/内存占用。

默认访问地址：

```text
http://localhost:3000
```

前端默认连接后端：

```text
http://127.0.0.1:8000
```

如需修改后端地址，可创建 `frontend/.env.local`：

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## 常用命令

```bash
npm run lint
npm run build
```

## 结构说明

- `app/page.tsx`：页面组合入口
- `app/types.ts`：前端类型定义
- `app/lib/api-client.ts`：API 请求封装
- `app/hooks/usePreset.ts`：常用信息 localStorage 读写
- `app/components/`：页面功能组件
