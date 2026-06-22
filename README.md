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
| 可选资源协作生成 | `POST /api/learning/generate` | `app/learning/workflow.py` |
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
→ profile
→ planner
→ lecture
→ mindmap
→ exercise
→ reading
→ review
→ integration
```

该链路由 `app/learning/workflow.py` 管理。用户可以只生成讲义、思维导图、习题或拓展阅读，也可以把资源库中的 PDF 文本作为额外上下文。响应中的 `agentTrace` 用于展示各节点执行过程。

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
| 首页 | `HomePage.vue` | 学习工作台和入口导航 |
| 个性化资源生成 | `CollaborativeGeneratePage.vue` | 选择资源类型和 PDF 后生成内容 |
| 资源库 | `ResourceLibrary.vue` | 上传、查看、下载和删除 PDF |
| 学习评估 | `EvaluatePage.vue` | 答题评估和薄弱点分析 |
| 课程管理 | `CoursePage.vue` | 课程列表和进度入口 |
| 课程详情 | `CourseDetailPage.vue` | 章节、分析和练习入口 |
| 课程练习 | `CourseExercisePage.vue` | 在线测验 |
| 学习分析 | `AnalyzePage.vue` | 当前课程画像分析 |
| 画像对话 | `PortraitPage.vue` | 分学科画像浏览和对话更新 |
| 个人中心 | `UserCenterPage.vue` | 用户资料和画像摘要 |
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
