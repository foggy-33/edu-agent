# edu-agent-ai

面向个性化学习场景的多 Agent 教育应用。后端使用 FastAPI，资源生成链路优先使用 LangGraph，前端使用 Vue 3，支持直接对话、课程练习、PDF 资料上下文、学生画像和流式资源生成。

本地安装与运行请参阅：[本地部署流程](docs/本地部署流程.md)。Windows用户也可以直接使用项目根目录的`deploy.bat`。

## 当前代码结构

```text
edu-agent-ai/
├─ app/
│  ├─ api/
│  │  ├─ routes.py              # HTTP API、SSE 流式接口和兼容旧接口
│  │  └─ schemas.py             # Pydantic 请求与响应模型
│  ├─ auth/                     # 注册、登录、令牌和本地用户数据
│  ├─ core/                     # 配置与通用 LLMClient
│  ├─ learning/
│  │  ├─ agents.py              # 当前多 Agent 节点实现
│  │  ├─ workflow.py            # LangGraph/顺序执行工作流
│  │  ├─ state.py               # 协作生成共享状态
│  │  └─ llm.py                 # SiliconFlow/OpenAI-compatible 调用与流式输出
│  ├─ profiles/                 # 分学科画像、雷达指标和画像对话
│  ├─ rag/                      # 本地知识库加载、关键词检索、Chroma 向量库
│  ├─ resources/                # PDF 上传、解析和 source_context 构建
│  └─ main.py                   # FastAPI 应用入口
├─ frontend/
│  └─ src/
│     ├─ App.vue
│     ├─ api/
│     ├─ components/
│     └─ types/
├─ knowledge_base/              # 本地课程知识库
├─ scripts/                     # 知识库索引脚本
├─ tests/
├─ Dockerfile
├─ docker-compose.yml
├─ deploy.bat                   # Windows一键部署与运维脚本
└─ requirements.txt
```

旧版 `app/agents` 和 `app/graph` 已移除。当前真正的多 Agent 文件是 `app/learning/agents.py`，LangGraph 编排入口是 `app/learning/workflow.py`。

## 主要接口

| 功能 | 接口 | 实现 |
|---|---|---|
| 首页直接对话/资源生成 | `POST /api/learning/generate` | `app/learning/workflow.py` |
| 首页流式输出 | `POST /api/learning/generate/stream` | `app/api/routes.py` + `app/learning/llm.py` |
| 兼容旧资源生成 | `POST /api/generate` | 转发到当前 `app/learning` 工作流 |
| 基础画像分析 | `POST /api/analyze` | `app/api/routes.py` 轻量规则提取 |
| 学习评估 | `POST /api/evaluate` | `app/api/routes.py` + `DynamicProfileService` |
| 画像对话 | `POST /api/profiles/chat` | `app/profiles/service.py` |
| 管理端用户列表 | `GET /api/auth/admin/users` | 管理员鉴权后返回安全用户字段 |
| 课程目录 | `GET /api/courses` | `app/api/routes.py` |
| PDF 资源库 | `/api/resources/*` | `app/resources/service.py` |
| 工作流说明 | `GET /api/workflow` | 当前 `app.learning.workflow.NODES` |

## 多 Agent 协作

当前协作链路由 `app/learning/workflow.py` 组织。安装并可导入 LangGraph 时使用 `StateGraph`，否则自动退回普通 Python 顺序执行，保证基础功能可用。

执行节点定义在 `NODES`：

```text
profile
→ planner
→ lecture
→ mindmap
→ exercise
→ reading
→ review
→ integration
```

节点函数位于 `app/learning/agents.py`：

| 节点 | 函数 | 主要输出 |
|---|---|---|
| 学情分析 | `profile_agent` | `studentProfile`、`agentTrace` |
| 任务规划 | `planner_agent` | `taskPlan` |
| 课程讲解 | `lecture_agent` | `lectureDoc` |
| 思维导图 | `mindmap_agent` | `mindmap` |
| 分层练习 | `exercise_agent` | `exercises`、`exerciseItems` |
| 拓展阅读 | `reading_agent` | `reading` |
| 质量审核 | `review_agent` | `review` |
| 资源整合 | `integration_agent` | 最后一条 `agentTrace` |

共享状态类型在 `app/learning/state.py`。核心字段包括：

```text
major, course, chapter, weakness, goal
resourceTypes, fileIds, source_context, sources
lectureDoc, mindmap, exercises, exerciseItems, reading, review
agentTrace
```

如果 `resourceTypes=[]`，表示用户只想直接对话。此时 `generate_learning_resources()` 不执行完整资源链路，只调用 `direct_chat_agent`，并把回答写入 `lectureDoc`。

## 流式输出

首页使用 `POST /api/learning/generate/stream`。后端返回 Server-Sent Events：

```text
event: status    # 处理过程，例如资料检索、任务规划、讲解生成
event: content   # 分块输出 lectureDoc、mindmap、exercises、reading、review
event: done      # 返回完整结果
event: error     # 返回错误信息
```

前端在 `frontend/src/components/CollaborativeGeneratePage.vue` 中读取流式响应，逐段追加内容，并把 `status` 事件渲染为处理过程动画。

## RAG 与 PDF 上下文

项目保留两类资料来源：

1. 本地课程知识库：`knowledge_base/`，由 `app/rag/retriever.py` 和 `app/rag/vector_store.py` 支持关键词检索与 Chroma 向量索引。
2. 用户上传 PDF：`app/resources/service.py` 解析 PDF 文本，保存到 `data/resources/<file_id>/content.txt`。

在当前首页生成链路中，用户选择 PDF 后，`ResourceService.build_context()` 会把文本拼接为 `source_context`，并把引用文件放入 `sources`。`app/learning/agents.py` 的 `_context()` 会把 `source_context` 注入每个 Agent 提示词，要求优先依据用户资料生成回答。

本地知识库索引可通过脚本维护：

```bash
python scripts/ingest_knowledge_base.py --clear
```

Docker 中执行：

```bash
docker compose run --rm backend python scripts/ingest_knowledge_base.py --clear
```

## 模型配置

模型密钥统一保存在服务器根目录的 `.env` 中，不需要、也不应在个人中心填写。`.env` 已被 `.gitignore` 忽略，请勿提交到 Git 或发送给他人。

项目支持三类模型服务，可按实际情况配置一种或多种：

```dotenv
# 讯飞星火 X2
SPARK_API_PASSWORD=替换为讯飞控制台生成的APIPassword
SPARK_BASE_URL=https://spark-api-open.xf-yun.com/x2
SPARK_MODEL=spark-x

# 讯飞星火 Lite
SPARK_LITE_API_PASSWORD=替换为Lite服务APIPassword
SPARK_LITE_BASE_URL=https://spark-api-open.xf-yun.com/v1
SPARK_LITE_MODEL=lite

# 硅基流动（OpenAI Chat Completions兼容接口）
SILICONFLOW_API_KEY=sk-替换为实际密钥
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=Pro/deepseek-ai/DeepSeek-V3.2

# 其他OpenAI兼容接口，例如 https://ai.space.cx/v1
OPENAI_API_KEY=sk-替换为实际密钥
OPENAI_BASE_URL=https://ai.space.cx/v1
OPENAI_MODEL=gpt-5.6-sol
```

`BASE_URL`填写服务端点根地址即可，不要在结尾添加斜杠。后端会自动拼接 `/chat/completions`；如果服务商给出的是完整地址，也可以直接填写以 `/chat/completions` 结尾的URL。

修改 `.env` 后必须重新创建后端容器：

```bash
docker compose up -d --force-recreate backend
```

### 管理端账号

管理端默认不设置密码，也不会自动开放。需要在`.env`中配置管理员账号：

```dotenv
ADMIN_USERNAME=admin
ADMIN_PASSWORD=请设置至少8位的高强度密码
ADMIN_DISPLAY_NAME=系统管理员
```

保存后执行`docker compose up -d --build --force-recreate backend`。使用该账号登录后，左侧导航会显示“管理端”，可以查看全部注册用户。普通用户既不会看到入口，也无法访问管理接口。管理员密码只保存在服务器环境变量中，请勿提交到Git。

检查密钥是否已经注入容器时，不要直接输出密钥内容，可使用：

```bash
docker compose exec backend sh -c 'test -n "$SPARK_API_PASSWORD" && echo "Spark X2 已配置"; test -n "$SILICONFLOW_API_KEY" && echo "SiliconFlow 已配置"; test -n "$OPENAI_API_KEY" && echo "OpenAI兼容接口已配置"'
```

## 使用Docker部署（推荐）

### 环境要求

- Windows 10/11：安装Docker Desktop，并启用Docker Compose v2；
- Ubuntu/Linux服务器：安装Docker Engine和Docker Compose插件；
- 建议至少2核CPU、4GB内存，生产环境建议8GB以上；
- 确保部署机器可以访问所配置的大模型API；
- 默认对外端口为`8080`，可在`.env`中通过`APP_PORT`修改。

### Windows一键部署

在项目根目录双击 `deploy.bat`，或在PowerShell/CMD中执行：

```bat
cd /d G:\agentstudy\edu-agent-ai
deploy.bat
```

脚本会自动检查Docker、创建`.env`、构建镜像、启动容器并等待健康检查。首次执行后请打开`.env`填入模型密钥，再执行：

```bat
deploy.bat restart
```

常用命令：

```bat
deploy.bat             rem 构建并启动
deploy.bat restart     rem 读取最新.env并重新创建容器
deploy.bat status      rem 查看容器状态
deploy.bat logs        rem 持续查看最近日志，Ctrl+C退出
deploy.bat stop        rem 停止容器，不删除数据卷
```

### Ubuntu/Linux服务器部署

注意：`G:\agentstudy\edu-agent-ai`是Windows路径，不能在Ubuntu终端中使用。Linux服务器应进入服务器上的真实目录，例如：

```bash
cd /home/ubuntu/edu-agent
cp .env.example .env
nano .env
sudo docker compose config --quiet
sudo docker compose up -d --build
sudo docker compose ps
```

如果项目已经部署过，更新代码后执行：

```bash
cd /home/ubuntu/edu-agent
git pull
sudo docker compose up -d --build --remove-orphans
```

如果出现`permission denied while trying to connect to the Docker daemon socket`，当前账户没有Docker权限。可以临时在Docker命令前添加`sudo`；也可以由服务器管理员执行：

```bash
sudo usermod -aG docker "$USER"
newgrp docker
```

重新登录后再运行`docker compose`。不要在Linux终端使用`notepad .env`，请使用`nano .env`或`vim .env`。

### 启动后的访问地址

假设`.env`中的`APP_PORT=8080`：

- 系统首页：`http://服务器IP:8080`
- API文档：`http://服务器IP:8080/docs`
- 健康检查：`http://服务器IP:8080/health`

本机部署时，服务器IP替换为`localhost`。云服务器还需要在安全组或防火墙中放行对应端口。正式公网环境建议在前面配置HTTPS反向代理，不要直接暴露后端容器端口。

### 验证部署

```bash
docker compose ps
curl -fsS http://127.0.0.1:8080/health
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend
```

正常情况下，`backend`和`frontend`均显示`healthy`。如果前端一直处于等待状态，应先查看后端日志，因为前端会等待后端健康检查通过后才启动。

### 更新与重建

仅修改`.env`：

```bash
docker compose up -d --force-recreate
```

修改后端代码、依赖或前端代码：

```bash
docker compose up -d --build --remove-orphans
```

查看实时日志：

```bash
docker compose logs -f --tail=200
```

停止服务但保留用户、画像、资料库和向量库数据：

```bash
docker compose down
```

不要随意执行`docker compose down -v`，该命令会删除项目的数据卷。

### 数据持久化与备份

生产配置使用以下Docker命名卷：

- `chroma_data`：向量知识库；
- `profile_data`：学科画像；
- `resource_data`：上传资料、PDF解析结果和批注；
- `auth_data`：用户、头像等认证数据。

重新构建镜像或执行普通`docker compose down`不会删除这些数据。迁移服务器前应使用Docker卷备份工具或运维平台对上述数据卷进行备份。

## 不使用Docker的本地开发

后端需要Python 3.11：

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端需要Node.js 20或更高版本：

```bash
cd frontend
npm ci
npm run dev
```

开发环境也可以直接使用：

```bash
docker compose -f docker-compose.dev.yml up --build
```

## 测试

```bash
pytest -q
```

RAG 专项：

```bash
pytest -q tests/test_rag.py
```
