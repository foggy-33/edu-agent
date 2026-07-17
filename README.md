# edu-agent-ai

面向个性化学习场景的多 Agent 教育应用。后端使用 FastAPI，资源生成链路优先使用 LangGraph，前端使用 Vue 3，支持直接对话、课程练习、PDF 资料上下文、学生画像和流式资源生成。

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

前端模型选择按照 SiliconFlow OpenAI-compatible API 传入：

```json
{
  "api_key": "sk-...",
  "base_url": "https://api.siliconflow.cn/v1",
  "model": "deepseek-ai/DeepSeek-V4-Pro"
}
```

当前首页只展示部分常用模型，例如 DeepSeek V4 Pro、DeepSeek V4 Flash、DeepSeek V3.2 Pro、GLM-5.2。请求中的模型配置不会写入代码仓库。

## 启动

本地启动后端：

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Docker 启动：

```bash
docker compose build
docker compose up -d
```

访问：

- 前端：`http://localhost:8080`
- API 文档：`http://localhost:8080/docs`
- 健康检查：`http://localhost:8080/health`

## 测试

```bash
pytest -q
```

RAG 专项：

```bash
pytest -q tests/test_rag.py
```
