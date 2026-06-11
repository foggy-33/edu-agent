# edu-agent-ai

基于大模型的个性化资源生成与学习多智能体系统，提供对话式学习画像构建、多智能体协同资源生成、个性化学习路径规划等核心功能。

## 📋 项目概述

`edu-agent-ai` 是一个面向大学生的智能学习辅助系统，采用 FastAPI + LangGraph + Vue 3 技术栈，支持 Mock 模式运行，无需真实 API Key 即可体验完整功能。

## 🛠️ 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端 | Python | 3.11+ |
| 后端框架 | FastAPI | 0.136+ |
| 工作流引擎 | LangGraph | 1.2+ |
| 向量数据库 | ChromaDB | 1.5+ |
| 前端框架 | Vue | 3.4+ |
| 前端构建 | Vite | 6.5+ |
| 样式 | Tailwind CSS | 3.4+ |
| 容器 | Docker | 24+ |

## 📁 项目结构

```text
edu-agent-ai/
├─ app/                    # 后端应用
│  ├─ main.py             # FastAPI 入口
│  ├─ core/               # 核心配置与LLM客户端
│  ├─ api/                # API路由与数据模型
│  ├─ agents/             # 智能体模块
│  ├─ graph/              # LangGraph工作流
│  ├─ rag/                # RAG向量检索
│  └─ profiles/           # 学生画像管理
├─ frontend/               # 前端应用
│  ├─ src/
│  │  ├─ components/      # Vue组件
│  │  ├─ api/             # API客户端
│  │  └─ types/           # TypeScript类型定义
│  └─ docker-compose.yml  # 开发环境配置
├─ knowledge_base/         # 课程知识库
├─ docs/                   # 项目文档
├─ docker-compose.yml      # 生产环境配置
├─ docker-compose.dev.yml  # 开发环境配置
└─ README.md               # 项目说明
```

## 🚀 快速开始

### 方式一：生产模式（Docker Compose）

```bash
# 启动生产环境
docker-compose up -d

# 访问地址
# 前端：http://localhost:8080
# API文档：http://localhost:8080/docs
```

### 方式二：开发模式（代码热重载）

```bash
# 停止生产环境（如果正在运行）
docker-compose down

# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 访问地址：http://localhost:8080
```

### 方式三：本地开发

```bash
# 后端
cd edu-agent-ai
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

## 🔧 环境配置

复制 `.env.example` 并根据需要修改：

```bash
cp .env.example .env
```

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| LLM_MODE | LLM模式（mock/spark） | mock |
| SPARK_APP_ID | 讯飞星火App ID | 空 |
| SPARK_API_KEY | 讯飞星火API Key | 空 |
| SPARK_API_SECRET | 讯飞星火API Secret | 空 |
| APP_PORT | 前端端口 | 8080 |

## 📱 功能模块

### 1. 对话式学习画像构建
- 自然语言对话持续构建动态学生画像
- 学习目标、知识水平、学习风格评估
- 薄弱环节识别

### 2. 多智能体协同资源生成
- 文档摘要生成
- 思维导图绘制
- 练习题生成
- 实践案例设计

### 3. 个性化学习路径规划
- 基于画像的学习路径推荐
- 学习进度追踪
- 智能辅导答疑

### 4. 学习效果评估
- 实时学习行为跟踪
- 答题结果分析
- 改进建议生成

### 5. 资源库管理
- 按课程分类浏览
- 按类型筛选
- 资源搜索

## 🔌 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务状态 |
| `/health` | GET | 健康检查 |
| `/api/analyze` | POST | 分析学习需求，生成学生画像 |
| `/api/generate` | POST | 执行多Agent工作流，生成学习资源 |
| `/api/evaluate` | POST | 评估答题结果 |
| `/api/courses` | GET | 获取课程列表 |
| `/api/workflow` | GET | 获取工作流说明 |
| `/api/profiles/{user_id}` | GET | 获取学生画像 |
| `/api/profiles/chat` | POST | 画像对话 |

### 示例请求

```json
{
  "user_id": "demo_user_001",
  "course": "数据库系统",
  "message": "我对函数依赖、候选码和范式判断不太理解，希望通过例题准备考试。"
}
```

## 🐳 Docker 配置说明

### 开发模式 vs 生产模式

| 特性 | 开发模式 | 生产模式 |
|------|----------|----------|
| 代码热重载 | ✅ | ❌ |
| 本地代码挂载 | ✅ | ❌ |
| 构建方式 | 增量 | 完整构建 |
| 启动命令 | `docker-compose -f docker-compose.dev.yml up -d` | `docker-compose up -d` |

### Docker Compose 配置

**开发环境 (`docker-compose.dev.yml`)**：
- 前端：Vite 开发服务器，支持热更新
- 后端：Uvicorn 自动重载
- 代码挂载：本地文件实时同步

**生产环境 (`docker-compose.yml`)**：
- 前端：Nginx 静态文件服务
- 后端：Uvicorn 生产模式
- 健康检查：自动服务监控

## 🧠 多 Agent 工作流

```text
用户输入
    │
    ▼
┌─────────────┐
│ProfileAgent │