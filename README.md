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
