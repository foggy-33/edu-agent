# edu-agent-ai

面向个性化学习场景的多 Agent 教育应用。后端使用 FastAPI 和 LangGraph，前端使用 Vue 3，支持学生画像、学习分析、资源生成、学习评估以及课程知识库 RAG 检索。

## 项目结构

```text
edu-agent-ai/
├─ app/
│  ├─ main.py                       # FastAPI 应用入口
│  ├─ api/
│  │  ├─ routes.py                  # HTTP API 路由
│  │  └─ schemas.py                 # Pydantic 请求与响应模型
│  ├─ auth/
│  │  └─ service.py                 # 注册、登录、令牌和用户数据
│  ├─ core/
│  │  ├─ config.py                  # 环境变量和全局配置
│  │  └─ llm_client.py              # Mock、SiliconFlow、Spark 模型适配
│  ├─ agents/
│  │  ├─ profile_agent.py           # 从输入中提取基础学习画像
│  │  ├─ retriever_agent.py         # 关键词与 Chroma 混合检索
│  │  ├─ planner_agent.py           # 生成个性化学习路径
│  │  ├─ document_agent.py          # 生成 Markdown 讲解文档
│  │  ├─ mindmap_agent.py           # 生成 Mermaid 思维导图
│  │  ├─ quiz_agent.py              # 生成练习题
│  │  ├─ practice_agent.py          # 生成数据库实践案例
│  │  ├─ evaluator_agent.py         # 分析答题结果
│  │  └─ safety_agent.py            # 检查知识依据与内容安全
│  ├─ graph/
│  │  ├─ state.py                   # 多 Agent 共享状态结构
│  │  ├─ workflow.py                # RAG 资源生成主工作流
│  │  └─ fallback_workflow.py       # LangGraph 不可用时的顺序执行
│  ├─ rag/
│  │  ├─ loader.py                  # Markdown 知识文档加载
│  │  ├─ retriever.py               # 关键词检索
│  │  └─ vector_store.py            # Chroma、本地向量和索引维护
│  ├─ learning/
│  │  ├─ state.py                   # 协作资源生成状态
│  │  ├─ agents.py                  # 讲义、导图、习题、阅读等节点
│  │  ├─ llm.py                     # 协作生成模型调用
│  │  └─ workflow.py                # 可选资源类型生成工作流
│  ├─ profiles/
│  │  ├─ store.py                   # 分用户、分学科画像文件存储
│  │  └─ service.py                 # 对话画像、评估更新和雷达指标
│  ├─ resources/
│  │  └─ service.py                 # PDF 上传、解析、列表和引用上下文
│  └─ utils/
│     └─ response.py                # 通用响应辅助函数
├─ frontend/
│  ├─ src/
│  │  ├─ App.vue                    # 登录状态、导航和页面调度
│  │  ├─ api/                       # 后端接口请求封装
│  │  ├─ components/                # 业务页面和渲染组件
│  │  ├─ types/                     # TypeScript 数据结构
│  │  ├─ main.ts                    # Vue 应用入口
│  │  └─ style.css                  # 全局样式
│  ├─ Dockerfile                    # 前端镜像
│  └─ nginx.conf                    # 静态资源与 /api 反向代理
├─ knowledge_base/
│  └─ database_system/              # 数据库系统 Markdown 知识库
├─ scripts/
│  └─ ingest_knowledge_base.py      # 手动建立或重建 Chroma 索引
├─ tests/
│  ├─ test_api.py                   # API、资源库和画像测试
│  └─ test_rag.py                   # RAG 检索测试
├─ docs/                            # 工作流、接口、部署和差距分析文档
├─ data/                            # 运行时用户数据，不提交 Git
├─ chroma_db/                       # Chroma 持久化数据，不提交 Git
├─ Dockerfile                       # 后端镜像
├─ docker-compose.yml               # 生产式前后端编排
├─ docker-compose.dev.yml           # 开发环境编排
├─ requirements.txt                 # Python 依赖
└─ .env.example                     # 环境变量模板
```

## 整体架构

项目采用前后端分离架构。浏览器访问 Vue 单页应用，前端通过 `/api` 请求 FastAPI；FastAPI 再根据业务类型调用认证、画像、资源库或多 Agent 工作流。

```text
┌──────────────────────────────────────────────────────────┐
│                     Vue 3 前端                           │
│ 登录 / 首页 / 课程 / 资源生成 / 资源库 / 评估 / 学生画像    │
└──────────────────────────┬───────────────────────────────┘
                           │ HTTP /api
                           ▼
┌──────────────────────────────────────────────────────────┐
│                  FastAPI API 层                          │
│ Auth │ Profile │ Resource │ Evaluation │ Agent Workflow │
└──────┬──────────┬──────────┬────────────┬───────────────┘
       │          │          │            │
       ▼          ▼          ▼            ▼
 用户数据文件  学科画像文件  PDF资源文件   多 Agent / RAG
                                             │
                              ┌──────────────┴─────────────┐
                              ▼                            ▼
                    Markdown 课程知识库              LLMClient
                              │                 Mock / SiliconFlow
                              ▼
                         Chroma 向量库
```

### 后端入口与 API 层

`app/main.py` 创建 FastAPI 实例，并将 `app/api/routes.py` 挂载到 `/api`。

主要接口分组如下：

| 功能 | 接口 | 实现模块 |
|---|---|---|
| 注册登录 | `/api/auth/register`、`/api/auth/login`、`/api/auth/me` | `app/auth/service.py` |
| 基础画像分析 | `POST /api/analyze` | `ProfileAgent` |
| RAG 资源包生成 | `POST /api/generate` | `app/graph/workflow.py` |
| 可选资源协作生成 | `POST /api/learning/generate`、`POST /api/learning/generate/stream` | `app/learning/workflow.py` |
| PDF 资源库 | `/api/resources/*` | `app/resources/service.py` |
| 学习评估 | `/api/evaluate`、`/api/evaluate/smart` | `EvaluatorAgent`、`DynamicProfileService` |
| 在线测验 | `/api/evaluate/quiz/*` | `app/api/routes.py` |
| 分学科画像 | `/api/profiles/*` | `app/profiles/service.py` |
| 模型连接测试 | `/api/settings/siliconflow/test` | `LLMClient` |

请求和响应结构集中定义在 `app/api/schemas.py`，用于输入校验和接口类型约束。

### 两条资源生成链路

项目目前保留两套用途不同的资源生成工作流。

第一条是带课程知识库 RAG 的完整资源包生成：

```text
POST /api/generate
→ ProfileAgent
→ RetrieverAgent
→ PlannerAgent
→ DocumentAgent
→ MindMapAgent
→ QuizAgent
→ PracticeAgent
→ SafetyCheckAgent
```

该链路会读取 `knowledge_base/database_system`，适用于数据库系统课程的画像分析、知识检索、学习路径和完整资源包生成。

第二条是按用户勾选类型生成资源：

```text
POST /api/learning/generate
POST /api/learning/generate/stream
→ profile
→ planner
→ lecture
→ mindmap
→ exercise
→ reading
→ review
→ integration
```

该链路由 `app/learning/workflow.py` 管理。用户可以只生成讲义、思维导图、习题或拓展阅读，也可以把资源库中的 PDF 文本作为额外上下文。响应中的 `agentTrace` 用于展示各节点执行过程。首页当前使用流式接口 `/api/learning/generate/stream`，前端逐段接收 `content` 事件，并用小字展示 `status` 事件中的 Agent 处理进度。

两套工作流都优先使用 LangGraph；如果 LangGraph 无法导入，则使用普通 Python 顺序执行，保证基础功能仍可运行。

### 模型调用层

`app/core/llm_client.py` 是统一的大模型适配层：

- `LLM_MODE=mock`：默认模式，无需 API Key，适合开发和演示。
- `LLM_MODE=siliconflow`：调用兼容 OpenAI Chat Completions 格式的 SiliconFlow 接口。
- `LLM_MODE=spark`：预留讯飞星火适配入口。

协作资源生成链路的模型调用封装在 `app/learning/llm.py`，页面提交的模型、地址和 API Key 会随请求传入，不写入代码仓库。

### 动态学生画像

学生画像由 `DynamicProfileService` 管理。画像按照“用户 + 学科”隔离，避免不同课程的学习特征互相覆盖：

```text
data/profiles/<user_id>/<course>.json
```

画像可以通过两种方式更新：

- 画像对话：`POST /api/profiles/chat`
- 学习评估：`POST /api/evaluate`

画像包含维度数据、证据、置信度、近期评估、学习进度、模型可读摘要 `llm_context` 和前端雷达图使用的 `radar_metrics`。前端可以先调用 `/api/profiles/{user_id}/subjects` 获取该用户已有的学科画像列表。

### PDF 资源库

`ResourceService` 提供用户自己的 PDF 资料管理：

```text
data/resources/<file_id>/
├─ source.pdf
├─ content.txt
└─ metadata.json
```

上传时会校验 PDF 类型和 20 MB 大小限制，通过 `pypdf` 提取文字。调用 `/api/learning/generate` 时，前端可提交 `fileIds`，后端将所选 PDF 的文本拼接为 `source_context`，并在响应的 `sources` 中返回引用文件。

当前只支持包含可提取文字的 PDF，纯扫描图片 PDF 需要后续增加 OCR。

### 登录与本地数据

认证逻辑位于 `app/auth/service.py`。用户、登录令牌、学生画像、上传资源和 Chroma 索引都使用本地持久化目录：

```text
data/auth/users.json
data/profiles/
data/resources/
chroma_db/
```

这些目录通过 `.gitignore` 排除。Docker Compose 使用独立命名卷保存数据，普通 `docker compose down` 不会删除；只有带 `-v` 才会清除数据卷。

### 前端页面结构

`frontend/src/App.vue` 负责登录检查、侧边导航和页面切换。主要页面组件如下：

| 页面 | 组件 | 作用 |
|---|---|---|
| 登录注册 | `AuthPage.vue` | 用户注册、登录和会话恢复 |
| 首页 / 个性化资源生成 | `CollaborativeGeneratePage.vue` | 居中对话入口、流式问答、选择资源类型和 PDF 后生成内容 |
| 资源库 | `ResourceLibrary.vue` | 上传、查看、下载和删除 PDF |
| 学习评估 | `EvaluatePage.vue` | 答题评估和薄弱点分析 |
| 课程管理 | `CoursePage.vue` | 课程列表和进度入口 |
| 课程详情 | `CourseDetailPage.vue` | 章节、分析和练习入口 |
| 课程练习 | `CourseExercisePage.vue` | 在线测验 |
| 学习分析 | `AnalyzePage.vue` | 当前课程画像分析 |
| 画像对话 | `PortraitPage.vue` | 分学科画像浏览和对话更新 |
| 个人中心 | `UserCenterPage.vue`、`HomePage.vue` | 用户资料、原首页学习仪表盘和画像摘要 |
| 设置 | `SettingsPage.vue` | SiliconFlow 模型配置测试 |

`MarkdownRenderer.vue` 和 `MermaidRenderer.vue` 分别负责讲义 Markdown 与思维导图展示。`frontend/src/api` 封装后端请求，`frontend/src/types` 保存前后端共享的数据结构。

### 部署结构

Docker Compose 包含两个服务：

```text
浏览器
   ↓ :8080
frontend（Nginx + Vue 静态文件）
   ↓ /api 反向代理
backend（Uvicorn + FastAPI）
   ├─ knowledge_base
   ├─ chroma_data
   ├─ profile_data
   ├─ resource_data
   └─ auth_data
```

前端 Nginx 对外暴露端口，后端只在 Compose 网络中提供 `8000` 端口。前端会等待后端健康检查成功后启动。

## RAG 与多 Agent 实现说明

项目中的 RAG 和多 Agent 不是单独存在的两个模块，而是通过两条资源生成链路组合使用：

- `POST /api/generate` 是“RAG 支撑的完整多 Agent 资源包生成”。它面向内置数据库系统知识库，先检索课程资料，再让多个 Agent 基于检索结果生成学习路径、讲义、思维导图、练习题、实践案例和安全检查结果。
- `POST /api/learning/generate` 与 `POST /api/learning/generate/stream` 是“可选资源类型的协作生成”。它不走内置 Chroma RAG，而是根据用户选择的 PDF 文件拼接 `source_context`，再让讲义、导图、习题、阅读等 Agent 分工生成结果。首页使用的是流式版本。

### 1. RAG 在项目中怎么工作

RAG 入口是 `POST /api/generate`，路由位于 `app/api/routes.py`，实际工作流在 `app/graph/workflow.py`。执行顺序如下：

```text
用户问题 + 课程名称
        ↓
ProfileAgent
提取专业、课程、年级、学习目标、薄弱点、学习风格
        ↓
RetrieverAgent
组合用户问题、课程和 weak_points，形成检索 query
        ↓
KeywordRetriever + ChromaVectorStore
从 knowledge_base/database_system 中召回相关内容
        ↓
合并关键词分数和向量分数，写入 retrieved_docs 与 retrieval_meta
        ↓
PlannerAgent / DocumentAgent / MindMapAgent / QuizAgent / PracticeAgent
基于画像与 retrieved_docs 生成学习路径和资源
        ↓
SafetyCheckAgent
检查输出是否有知识依据和基本教学安全问题
        ↓
返回 profile、learning_path、resources、retrieval_meta、safety_report
```

知识库文件在 `knowledge_base/database_system/` 下，`app/rag/loader.py` 会递归读取 Markdown。每个文档保留 `title`、`source` 和 `content`，其中 `source` 使用项目相对路径，方便前端展示引用来源。

向量库由 `app/rag/vector_store.py` 实现，使用 Chroma 持久化到 `chroma_db/`。当前没有接外部 Embedding API，而是使用 `LocalHashEmbeddings`：

```text
文本分词
→ 英文、数字、中文单字、中文双字词
→ BLAKE2b 稳定哈希
→ 映射到固定维度向量桶
→ L2 归一化
→ 写入 Chroma
```

这种方案适合本地演示和离线测试，不需要 SiliconFlow Key。知识库写入 Chroma 前按段落切块，默认块大小 700 字符、重叠 100 字符；系统会把知识库目录指纹保存到 `chroma_db/.knowledge_fingerprint`，当 Markdown 文件变化时自动重建索引。

检索时，`RetrieverAgent` 同时执行两路召回：

```text
关键词召回：KeywordRetriever.search(query, top_k = RAG_TOP_K × 2)
向量召回：ChromaVectorStore.similarity_search(query, top_k = RAG_TOP_K × 2)
```

两路结果按 `source` 去重，并计算综合分：

```text
combined_score = keyword_score × 0.4 + vector_score × 0.6
```

最终取前 `RAG_TOP_K` 条写入 `retrieved_docs`。如果 Chroma 初始化、索引或查询失败，系统不会中断生成，而是记录 `vector_error`，降级为关键词检索，`retrieval_meta.mode` 会变成 `keyword`。

### 2. RAG 多 Agent 工作流怎么协作

`app/graph/workflow.py` 会优先尝试创建 LangGraph `StateGraph`。如果当前环境无法导入 LangGraph，则使用 `app/graph/fallback_workflow.py` 顺序执行相同节点。

共享状态结构在 `app/graph/state.py`，核心字段包括：

```text
user_id
course
message
profile
retrieved_docs
retrieval_meta
learning_path
document
mindmap
quiz
practice_case
safety_report
```

每个 Agent 只负责一个阶段，并把结果写回共享状态：

| Agent | 文件 | 职责 |
|---|---|---|
| `ProfileAgent` | `app/agents/profile_agent.py` | 从用户输入中抽取学习画像和薄弱点 |
| `RetrieverAgent` | `app/agents/retriever_agent.py` | 执行关键词 + Chroma 混合检索 |
| `PlannerAgent` | `app/agents/planner_agent.py` | 生成阶段化学习路径 |
| `DocumentAgent` | `app/agents/document_agent.py` | 生成 Markdown 讲解文档 |
| `MindMapAgent` | `app/agents/mindmap_agent.py` | 生成 Mermaid 思维导图 |
| `QuizAgent` | `app/agents/quiz_agent.py` | 生成多题型练习 |
| `PracticeAgent` | `app/agents/practice_agent.py` | 生成 SQL 实践案例 |
| `SafetyCheckAgent` | `app/agents/safety_agent.py` | 检查内容依据和安全提示 |

这条链路的特点是：RAG 检索发生在生成前，后续资源生成 Agent 都能使用 `retrieved_docs`，因此输出可以带上 `extended_reading` 和 `retrieval_meta` 作为知识来源说明。

### 3. 协作式多 Agent 资源生成怎么实现

首页“个性化资源生成”使用的是第二条链路，入口在 `app/api/routes.py`：

```text
POST /api/learning/generate          # 普通 JSON 返回
POST /api/learning/generate/stream   # 首页使用，SSE 流式返回
```

前端在 `frontend/src/components/CollaborativeGeneratePage.vue` 中提交：

```json
{
  "user_id": "当前用户",
  "major": "未指定",
  "course": "自定义学习主题",
  "chapter": "用户当前问题",
  "weakness": "用户输入的问题",
  "goal": "理解并掌握相关知识",
  "resourceTypes": ["lecture", "mindmap", "exercise", "reading"],
  "fileIds": ["用户选择的 PDF 文件 ID"],
  "api_key": "前端设置中的模型 Key",
  "base_url": "OpenAI-compatible API 地址",
  "model": "模型名"
}
```

如果用户选择了资源库 PDF，`ResourceService.build_context()` 会读取 `data/resources/<file_id>/content.txt`，拼成 `source_context`，并把引用文件放到 `sources`。`app/learning/agents.py` 中的 `_context()` 会把 `source_context` 追加到每个 Agent 的提示词中，要求优先依据 PDF 原文生成内容。

协作链路的节点定义在 `app/learning/workflow.py`：

```text
profile_agent
→ planner_agent
→ lecture_agent
→ mindmap_agent
→ exercise_agent
→ reading_agent
→ review_agent
→ integration_agent
```

共享状态结构在 `app/learning/state.py`，主要字段包括：

```text
major、course、chapter、weakness、goal
resourceTypes、fileIds、source_context、sources
lectureDoc、mindmap、exercises、exerciseItems、reading、review
agentTrace
```

各节点职责如下：

| 节点 | 输出字段 | 说明 |
|---|---|---|
| `profile_agent` | `studentProfile` | 整理专业、课程、章节、短板和学习目标 |
| `planner_agent` | `taskPlan` | 根据 `resourceTypes` 规划要生成哪些资源 |
| `lecture_agent` | `lectureDoc` | 生成 Markdown 课程讲解 |
| `mindmap_agent` | `mindmap` | 生成 Mermaid mindmap 源码 |
| `exercise_agent` | `exercises`、`exerciseItems` | 生成 Markdown 练习题和可在线作答的结构化题目 |
| `reading_agent` | `reading` | 生成拓展阅读和学习路径 |
| `review_agent` | `review` | 检查所选资源是否覆盖短板、目标和难度 |
| `integration_agent` | `agentTrace` | 追加整合完成记录，返回统一 JSON |

如果 `resourceTypes` 为空，表示用户只想直接对话。此时 `generate_learning_resources()` 不跑完整资源链，而是只调用 `direct_chat_agent`，把回答写入 `lectureDoc`，前端显示为“对话回答”。

每个节点都会通过 `_trace()` 追加一条 `agentTrace`：

```json
{
  "order": 1,
  "agent": "学情分析 Agent",
  "status": "completed",
  "summary": "已识别知识短板与学习目标",
  "timestamp": "..."
}
```

流式接口 `/api/learning/generate/stream` 使用 `StreamingResponse` 返回 Server-Sent Events：

```text
event: status   # 小字显示处理过程，例如“正在读取问题和已选资料”
event: content  # 按块输出 lectureDoc、mindmap、exercises、reading、review
event: done     # 返回完整 result，前端用于练习题判题和最终状态
event: error    # 返回错误信息
```

前端用 `ReadableStream.getReader()` 逐块读取响应，把 `content` 事件追加到当前标签页内容中；`status` 事件显示在回答区上方的小字“处理过程”中。Nginx 在 `frontend/nginx.conf` 中关闭了 `/api/` 的代理缓冲，避免 SSE 被缓存到最后才显示。

### 4. 两条链路的区别

| 对比项 | `/api/generate` | `/api/learning/generate`、`/api/learning/generate/stream` |
|---|---|---|
| 主要用途 | 数据库系统课程的完整 RAG 资源包 | 首页自由问答和可选资源生成 |
| 知识来源 | `knowledge_base/database_system` + Chroma + 关键词检索 | 用户上传 PDF 的 `source_context` + 用户问题 |
| 是否返回 `retrieval_meta` | 是 | 否 |
| 是否返回 `agentTrace` | 否 | 是 |
| 是否可选择资源类型 | 否，固定生成完整资源包 | 是，可选讲义、导图、练习、阅读 |
| 是否支持直接对话 | 否 | 是，`resourceTypes=[]` 时走 `direct_chat_agent` |
| 是否支持流式输出 | 当前普通 JSON 返回 | 首页使用 SSE 流式输出 |
| 练习题形式 | `resources.quiz` | `exercises` Markdown + `exerciseItems` 可作答题卡 |

## 当前 RAG 实现

项目当前使用“关键词检索 + Chroma 向量检索”的混合 RAG。完整调用链如下：

```text
POST /api/generate
        ↓
ProfileAgent 生成当前学生画像
        ↓
RetrieverAgent 组合检索查询
        ├─ KeywordRetriever 关键词召回
        └─ ChromaVectorStore 向量召回
                 ↓
          去重、归一化和加权排序
                 ↓
DocumentAgent 等生成 Agent 使用检索片段
                 ↓
返回生成内容、引用来源和 retrieval_meta
```

### 1. 知识库

知识库位于：

```text
knowledge_base/database_system/
```

当前内容包括数据库基础、关系模型、SQL、函数依赖、候选码、范式、事务、并发控制、索引、存储管理、复习笔记和常见错误等 Markdown 文档。

文档由 `app/rag/loader.py` 递归读取。每条文档记录包含：

```json
{
  "title": "文档标题",
  "source": "knowledge_base/database_system/文件名.md",
  "content": "Markdown 正文"
}
```

`source` 使用项目相对路径，避免把服务器或开发者本机的绝对路径返回给前端。

### 2. 本地向量生成

向量实现位于 `app/rag/vector_store.py` 的 `LocalHashEmbeddings`。

当前方案不依赖外部 Embedding API，也不要求 SiliconFlow API Key：

1. 提取英文单词、数字、中文单字和中文双字词。
2. 使用 BLAKE2b 对 token 做稳定哈希。
3. 将 token 映射到固定维度的向量桶。
4. 对最终向量进行 L2 归一化。

默认向量维度为 384，可通过环境变量修改：

```env
RAG_EMBEDDING_DIMENSION=384
```

这种实现适合本地演示、离线部署和自动化测试。它比纯关键词检索有更好的近似匹配能力，但语义能力弱于专用 Embedding 模型。后续可以替换向量生成器，同时保留 Chroma 存储和混合排序接口。

### 3. 文档分块与 Chroma 索引

`ChromaVectorStore` 使用 `chromadb.PersistentClient` 持久化索引，默认目录为：

```text
./chroma_db
```

Docker 环境中对应：

```text
/app/chroma_db
```

Markdown 文档写入向量库前按段落分块：

- 默认块大小：700 字符
- 默认重叠：100 字符
- 每个块保留 `title` 和 `source`
- 块 ID 由来源、序号和内容计算 SHA-256 得到
- 使用 `upsert` 避免相同块重复写入

项目会计算整个知识库目录的 SHA-256 指纹，并保存到：

```text
chroma_db/.knowledge_fingerprint
```

当知识库文件发生变化时，下一次检索会自动清空旧集合并重建索引；知识库没有变化时直接复用持久化索引。

### 4. 自动导入

默认配置：

```env
RAG_AUTO_INGEST=true
```

首次调用 `/api/generate` 时，`RetrieverAgent` 会调用 `ensure_indexed()`：

- Chroma 中没有数据时自动导入知识库。
- 知识库指纹变化时自动重建。
- 索引已是最新状态时直接执行检索。

也可以手动重建：

```bash
python scripts/ingest_knowledge_base.py --clear
```

自定义知识库目录和分块参数：

```bash
python scripts/ingest_knowledge_base.py \
  --directory ./knowledge_base/database_system \
  --clear \
  --chunk-size 700 \
  --chunk-overlap 100
```

Docker 中执行：

```bash
docker compose run --rm backend \
  python scripts/ingest_knowledge_base.py --clear
```

### 5. 关键词检索

`app/rag/retriever.py` 中的 `KeywordRetriever` 会：

1. 从用户消息、课程名称和学生薄弱点中提取查询词。
2. 对英文单词、数字和中文双字词进行匹配。
3. 统计每个查询词在标题和正文中的出现次数。
4. 按匹配分数从高到低召回文档。

关键词检索不依赖 Chroma，因此也是向量服务异常时的降级路径。

### 6. 混合检索与排序

`app/agents/retriever_agent.py` 中的 `RetrieverAgent` 同时执行两路召回：

```text
关键词召回数量 = RAG_TOP_K × 2
向量召回数量   = RAG_TOP_K × 2
最终返回数量   = RAG_TOP_K
```

两路分数分别归一化到 `[0, 1]`，再按来源路径去重并计算综合分数：

```text
combined_score =
    keyword_score × 0.4
  + vector_score  × 0.6
```

结果按照 `combined_score` 降序排列。每条结果包含：

```json
{
  "title": "SQL 基础",
  "source": "knowledge_base/database_system/chapter2-sql.md",
  "content": "实际用于生成的知识片段",
  "keyword_score": 0.8,
  "vector_score": 1.0,
  "combined_score": 0.92,
  "retrieval_types": ["keyword", "vector"]
}
```

### 7. 自动降级

向量库初始化、索引构建或查询发生异常时，`RetrieverAgent` 不会让整个资源生成接口失败，而是：

1. 记录向量检索异常。
2. 保留关键词召回结果。
3. 将检索模式设置为 `keyword`。
4. 继续执行后续生成工作流。

因此，即使 Chroma 暂时不可用，`/api/generate` 仍可继续提供基础知识库检索能力。

### 8. 工作流接入

RAG 已接入两种工作流：

- 安装并可正常导入 LangGraph 时，使用 `StateGraph`。
- LangGraph 不可用时，使用 `app/graph/fallback_workflow.py` 中的顺序工作流。

两种路径都会按照以下顺序执行：

```text
ProfileAgent
→ RetrieverAgent
→ PlannerAgent
→ DocumentAgent
→ MindMapAgent
→ QuizAgent
→ PracticeAgent
→ SafetyCheckAgent
```

检索结果写入工作流状态中的 `retrieved_docs`，生成 Agent 会把知识片段作为上下文使用。

### 9. 接口返回

`POST /api/generate` 除学生画像和学习资源外，还会返回：

```json
{
  "retrieval_meta": {
    "query": "用户消息、课程和薄弱点组成的查询",
    "keyword_count": 8,
    "vector_count": 10,
    "mode": "hybrid",
    "vector_error": ""
  },
  "resources": {
    "extended_reading": [
      {
        "title": "chapter2-sql",
        "source": "knowledge_base/database_system/chapter2-sql.md",
        "reason": "与当前薄弱点匹配"
      }
    ]
  }
}
```

字段说明：

- `mode=hybrid`：关键词和向量检索都成功。
- `mode=keyword`：只使用关键词检索。
- `vector_error`：向量检索失败时的错误信息，成功时为空字符串。
- `extended_reading`：从最终检索结果中提取的引用来源。

### 10. RAG 配置

`.env` 可配置：

```env
KNOWLEDGE_BASE_DIR=./knowledge_base
CHROMA_PERSIST_DIR=./chroma_db
RAG_AUTO_INGEST=true
RAG_TOP_K=5
RAG_EMBEDDING_DIMENSION=384
```

| 配置项 | 作用 | 默认值 |
|---|---|---|
| `KNOWLEDGE_BASE_DIR` | 知识库根目录 | `./knowledge_base` |
| `CHROMA_PERSIST_DIR` | Chroma 持久化目录 | `./chroma_db` |
| `RAG_AUTO_INGEST` | 检索前是否自动检查并导入知识库 | `true` |
| `RAG_TOP_K` | 最终返回的检索文档数 | `5` |
| `RAG_EMBEDDING_DIMENSION` | 本地哈希向量维度 | `384` |

## 启动项目

复制环境变量：

```bash
cp .env.example .env
```

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

RAG 专项测试：

```bash
pytest -q tests/test_rag.py
```

测试覆盖本地向量稳定性、关键词检索来源以及混合检索去重和排序。
