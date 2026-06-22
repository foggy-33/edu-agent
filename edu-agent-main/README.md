# edu-agent-ai

`edu-agent-ai` 当前阶段聚焦 backend-ai，提供可运行的 FastAPI + LangGraph 多 Agent 工作流，并使用 Mock LLM 生成结构完整的学习资源。

## 目录结构
```text
edu-agent-ai/
├─ app/
│  ├─ main.py
│  ├─ core/
│  ├─ api/
│  ├─ agents/
│  ├─ graph/
│  ├─ rag/
│  └─ utils/
├─ knowledge_base/database_system/
├─ tests/
├─ docs/
├─ requirements.txt
├─ .env.example
└─ README.md
```

## 安装依赖
```bash
pip install -r requirements.txt
```

## 启动命令
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：
- `GET /`
- `GET /health`
- Swagger 文档：`http://localhost:8000/docs`

## 接口说明
- `GET /`：服务状态。
- `GET /health`：健康检查。
- `POST /api/analyze`：输入学生学习需求，返回学生画像。
- `POST /api/generate`：执行完整多 Agent 工作流，返回资源包。
- `POST /api/evaluate`：输入答题结果，返回学习效果分析。
- `GET /api/courses`：返回支持课程列表。
- `GET /api/workflow`：返回工作流说明。

## 示例请求
```json
{
  "user_id": "demo_user_001",
  "course": "数据库系统",
  "message": "我是计算机专业大二学生，正在学习数据库系统。我对函数依赖、候选码和范式判断不太会，希望通过例题和步骤化讲解准备考试。"
}
```

## 多 Agent 工作流
```text
用户输入
→ ProfileAgent
→ RetrieverAgent
→ PlannerAgent
→ DocumentAgent
→ MindMapAgent
→ QuizAgent
→ PracticeAgent
→ SafetyCheckAgent
→ 完整 JSON
```

如果 LangGraph 可用，系统会通过 `StateGraph` 执行；如果导入失败，会自动使用普通 Python 顺序调用，保证项目可运行。

## Mock LLM 与后续接入
默认 `LLM_MODE=mock`，无需真实 API Key。后续可以在 `app/core/llm_client.py` 中实现 `spark_generate`，通过 `.env` 读取科大讯飞星火 API 配置。

## 后续扩展方向
- 接入星火 API 或其他真实大模型。
- 使用 Chroma 存储课程知识库向量。
- 增加用户学习记录、错题本和长期画像。
- 增加课程管理后台与前端展示页面。
- 为 Agent 输出增加更严格的结构化解析和质量评估。



### 成员 A：后端智能体与大模型接入

负责方向：FastAPI 后端、LangGraph 工作流、星火 API、智能体能力增强。

主要任务：
- 实现 `app/core/llm_client.py` 中的 `spark_generate`，接入科大讯飞星火 API。
- 增加 Prompt 模板目录，例如 `app/prompts/`，把画像、文档、题库、安全检查等提示词独立管理。
- 增强 Agent 输出的结构化能力，减少手写固定内容，支持真实 LLM 生成。
- 新增 `/api/tutor` 智能辅导接口，支持学生针对知识点进行即时问答。
- 新增流式输出或任务进度接口，避免资源生成时长时间等待。
- 完善 `/api/evaluate`，让评估结果能够反向更新学生薄弱点和学习建议。

建议分支：
```bash
git checkout -b feature/backend-llm-agents
```

阶段交付物：
- 星火 API 可配置接入，mock 模式仍可用。
- 至少一个真实 LLM 生成链路可跑通。
- `/api/tutor` 可用。
- Agent 输出结构稳定，接口不破坏现有前端调用。

### 成员 B：知识库、RAG 与安全机制

负责方向：课程知识库、Chroma 向量检索、防幻觉、内容安全和数据基础。

主要任务：
- 扩充 `knowledge_base/database_system`，补充完整课程章节、例题、实验、常见错误和复习资料。
- 实现 `app/rag/vector_store.py` 中的 Chroma 向量库能力。
- 增加知识库导入脚本，例如 `scripts/ingest_knowledge_base.py`。
- 将 `RetrieverAgent` 从关键词检索升级为“关键词 + 向量检索”的混合检索。
- 为生成结果增加引用来源，返回知识库依据片段。
- 增强 `SafetyCheckAgent`，检查内容是否脱离课程知识库、是否存在明显事实错误、是否包含不适合教学的内容。
- 设计学生画像、学习记录、答题记录的数据结构，为动态画像做准备。

建议分支：
```bash
git checkout -b feature/rag-safety-profile
```

阶段交付物：
- Chroma 检索可运行。
- 知识库内容明显丰富，能够覆盖数据库系统主要章节。
- `/api/generate` 返回拓展阅读和引用来源。
- 安全检查报告更具体，可说明风险原因。

### 成员 C：前端演示、测试与比赛文档

负责方向：可视化演示界面、接口联调、测试说明、系统开发文档和答辩材料。

主要任务：
- 新建前端项目，例如 `frontend/`，实现比赛演示页面。
- 支持学习需求输入、学生画像展示、学习路径展示、资源包展示。
- 支持 Markdown 渲染、Mermaid 思维导图渲染、题库卡片展示、SQL 案例展示。
- 增加生成进度展示或流式输出展示效果。
- 编写测试说明书，覆盖健康检查、画像生成、资源生成、评估接口等。
- 编写系统开发说明书，包含需求分析、架构设计、智能体设计、接口设计、部署说明。
- 整理开源组件与协议说明，标注 FastAPI、LangGraph、Chroma、Mermaid 等工具来源。
- 准备演示脚本、系统截图和答辩 PPT 提纲。

建议分支：
```bash
git checkout -b feature/frontend-docs-demo
```

阶段交付物：
- 前端可调用后端接口并完成完整演示流程。
- `docs/` 下补齐开发说明、测试说明、部署说明、开源协议说明。
- 演示脚本清晰，能够按“输入需求 -> 生成资源 -> 学习评估”展示闭环。

## 任务优先级

### P0：必须完成

- 前端演示页面。
- 星火 API 或至少一个真实大模型接入。
- Chroma/RAG 知识库检索。
- 学生画像、学习路径、文档、思维导图、题库、SQL 案例完整展示。
- 基础防幻觉与安全检查。
- 系统开发说明书和测试说明书。

### P1：重要加分

- `/api/tutor` 智能辅导。
- 动态学生画像和学习记录。
- 生成进度追踪或流式输出。
- 引用来源和依据片段展示。
- PPT 大纲、视频脚本、动画分镜等多模态资源。

### P2：时间充足再做

- 用户登录和权限管理。
- 更完整的后台管理。
- 多课程支持。
- 自动化部署脚本。
- 更细粒度的学习行为分析看板。

## 推荐协作流程

1. 每个人从 `main` 创建自己的功能分支。
2. 开发前先执行 `git pull origin main` 同步最新代码。
3. 每个功能尽量小步提交，提交信息写清楚改了什么。
4. 功能完成后推送分支并创建 Pull Request。
5. 至少一名队友检查后再合并到 `main`。
6. 不要提交 `.env`、API Key、临时缓存和本地数据库文件。

常用命令：

```bash
git pull origin main
git checkout -b feature/your-task-name
git add .
git commit -m "Describe your change"
git push origin feature/your-task-name
```

合并完成后，其他成员同步：

```bash
git checkout main
git pull origin main
```
