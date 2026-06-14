# edu-agent-ai

基于大模型的个性化资源生成与学习多智能体系统。

## 📋 功能特性

- **对话式学习画像构建**：通过自然语言对话持续构建动态学生画像
- **多智能体协同资源生成**：文档摘要、思维导图、练习题、实践案例
- **个性化学习路径规划**：根据学生薄弱环节提供定制化学习建议
- **资源库管理**：支持按课程和类型分类浏览、搜索、下载学习资料
- **学习效果评估**：实时跟踪学习行为，提供改进建议

## 🛠️ 技术栈

| 分类 | 技术 | 版本 |
|------|------|------|
| 前端 | Vue 3 | 3.4+ |
| 前端框架 | TypeScript | 5.4+ |
| 构建工具 | Vite | 6.5+ |
| UI框架 | TailwindCSS | 3.4+ |
| 后端 | FastAPI | 0.104+ |
| 工作流 | LangGraph | 0.2+ |
| 向量数据库 | Chroma | 0.5+ |
| 容器 | Docker | 24+ |

## 📁 项目结构

```text
edu-agent-ai/
├─ app/                    # 后端应用
│  ├─ main.py              # FastAPI入口
│  ├─ core/               # 核心配置与LLM客户端
│  ├─ api/                # API路由与schema
│  ├─ agents/              # 智能体实现
│  ├─ graph/              # LangGraph工作流
│  ├─ rag/                # RAG检索模块
│  ├─ profiles/           # 用户画像管理
│  └─ utils/               # 工具函数
├─ frontend/               # 前端应用
│  ├─ src/
│  │  ├─ components/       # Vue组件
│  │  ├─ api/             # API调用
│  │  └─ types/           # TypeScript类型
│  ├─ Dockerfile          # 前端Docker配置
│  └─ nginx.conf          # Nginx配置
├─ knowledge_base/        # 课程知识库
├─ tests/                 # 测试用例
├─ docs/                   # 文档
├─ docker-compose.yml     # 生产环境配置
├─ docker-compose.dev.yml # 开发环境配置
└─ requirements.txt       # Python依赖
```

## 🚀 快速开始

### 方式一：Docker Compose（生产环境）

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f
```

访问地址：`http://localhost:8080`

### 方式二：Docker Compose（开发模式）

开发模式支持代码热重载，修改本地文件后自动更新：

```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 停止服务
docker-compose -f docker-compose.dev.yml down
```

### 方式三：本地运行

**后端：**
```bash
cd edu-agent-ai
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**
```bash
cd frontend
npm install
npm run dev
```

## 🔧 环境配置

复制 `.env.example` 并配置环境变量：

```bash
cp .env.example .env
```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| LLM_MODE | LLM模式（mock/spark） | mock |
| SPARK_APP_ID | 讯飞星火APP ID | - |
| SPARK_API_KEY | 讯飞星火API Key | - |
| SPARK_API_SECRET | 讯飞星火API Secret | - |
| SPARK_API_URL | 讯飞星火API地址 | - |
| APP_PORT | 前端访问端口 | 8080 |

## 🌐 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务状态 |
| `/health` | GET | 健康检查 |
| `/api/analyze` | POST | 分析学习需求，生成学生画像 |
| `/api/generate` | POST | 执行多智能体工作流，生成资源包 |
| `/api/evaluate` | POST | 评估学习效果 |
| `/api/courses` | GET | 获取课程列表 |
| `/api/workflow` | GET | 获取工作流说明 |
| `/api/profiles/{user_id}` | GET | 获取用户画像 |
| `/api/profiles/chat` | POST | 画像对话 |

### 示例请求

```json
{
  "user_id": "demo_user_001",
  "course": "数据库系统",
  "message": "我对函数依赖、候选码和范式判断不太会，希望通过例题准备考试。"
}
```

## 🧠 智能体工作流

```
用户输入
  │
  ▼
┌─────────────┐
│ProfileAgent│  → 构建学生画像
└─────┬───────┘
      │
      ▼
┌─────────────┐
│RetrieverAgent│ → 检索知识库
└─────┬───────┘
      │
      ▼
┌─────────────┐
│PlannerAgent │  → 规划学习路径
└─────┬───────┘
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│DocumentAgent│    │MindMapAgent │    │ QuizAgent   │    │PracticeAgent│
│  文档摘要   │    │ 思维导图    │    │   题库生成  │    │ 实践案例    │
└─────┬───────┘    └─────┬───────┘    └─────┬───────┘    └─────┬───────┘
      │                  │                  │                  │
      └──────────────────┴──────────────────┴──────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │SafetyAgent  │  → 安全检查
                    └─────┬───────┘
                          │
                          ▼
                    返回完整资源包
```

## 📱 前端功能

| 页面 | 功能 |
|------|------|
| 首页 | 学习概览、统计数据、学习记录 |
| 画像共建 | 对话式画像构建 |
| 学习分析 | 薄弱环节分析、学习趋势 |
| 资源库 | 资料浏览、搜索、下载 |
| 资源生成 | AI生成学习资料 |
| 学习评估 | 答题测试、效果评估 |
| 课程管理 | 课程列表、学习进度 |

## 📚 知识库

知识库目录结构：

```
knowledge_base/
└─ database_system/
    ├─ 01_database_intro.md
    ├─ 02_relation_model.md
    ├─ 03_sql_basic.md
    ├─ 04_function_dependency.md
    ├─ 05_candidate_key.md
    ├─ 06_normal_form.md
    ├─ 07_transaction.md
    ├─ 08_concurrency_control.md
    ├─ 09_index.md
    └─ 10_storage_management.md
```

## 🧪 测试

```bash
# 运行测试
pytest tests/

# 测试特定文件
pytest tests/test_api.py -v
```

## 📝 开发指南

### 代码规范

- Python：遵循 PEP 8 规范
- TypeScript：使用 ESLint 检查
- 提交信息：使用 Conventional Commits 格式

### 分支管理

```bash
# 创建功能分支
git checkout -b feature/your-feature

# 提交代码
git add .
git commit -m "feat: 描述你的修改"
git push origin feature/your-feature
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

*基于 FastAPI + LangGraph + Vue 3 构建*
