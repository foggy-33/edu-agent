# Docker 部署说明

项目使用 Docker Compose 启动两个服务：

- `frontend`：Nginx 托管 Vue 静态页面，并将 `/api`、`/health` 和 `/docs` 转发到后端。
- `backend`：FastAPI + Uvicorn 服务。

## 环境要求

- Docker Engine 24+
- Docker Compose v2+
- 至少 2 GB 可用内存

服务器只需要开放应用端口，默认是 `8080`。

## 快速部署

在项目根目录执行：

```bash
cp .env.example .env
docker compose up -d --build
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

部署完成后访问：

- 前端页面：`http://localhost:8080`
- 健康检查：`http://localhost:8080/health`
- API 文档：`http://localhost:8080/docs`

## 配置

默认使用 Mock LLM，无需 API Key。可以在 `.env` 中调整：

```dotenv
LLM_MODE=mock
APP_PORT=8080

SPARK_APP_ID=
SPARK_API_KEY=
SPARK_API_SECRET=
SPARK_API_URL=
```

修改 `APP_PORT` 可以改变对外访问端口。真实模型接入代码完成后，再将 `LLM_MODE` 改为对应模式并填写密钥。

## 常用命令

```bash
# 查看状态
docker compose ps

# 查看日志
docker compose logs -f

# 重新构建并启动
docker compose up -d --build

# 停止服务
docker compose down

# 更新代码后重新部署
git pull
docker compose up -d --build
```

Chroma 数据存储在 Docker 命名卷 `chroma_data` 中。执行 `docker compose down` 不会删除数据；只有执行 `docker compose down -v` 才会删除该数据卷。

## 生产服务器建议

- 使用云安全组或防火墙只开放实际需要的端口。
- 对公网服务建议在前面增加 HTTPS 反向代理，例如 Caddy、Nginx Proxy Manager 或云负载均衡。
- 不要提交包含真实 API Key 的 `.env` 文件。
