# 🔍 Search RAG System

基于 **Corrective RAG (CRAG)** 的学术论文智能问答系统，支持 PDF 文档上传、向量检索、智能问答和会话管理。

## ✨ 功能特性

- 📄 **PDF 文档管理** — 上传、解析、向量化存储学术论文
- 🤖 **CRAG 智能问答** — 基于 LangGraph 的纠正检索增强生成管线
- 🔎 **自动纠错** — 文档检索质量不佳时自动触发网络搜索补充
- 💬 **多会话管理** — 支持创建、切换和管理多个对话会话
- 👤 **用户认证** — 注册 / 登录 / 登出，基于 Flask Session Cookie
- ⚙️ **会话设置** — 每个会话可独立配置模型参数

## 🏗️ 项目结构

```
search_RAG_system/
├── day_3/                      # Python Flask 后端
│   ├── app/                    # 应用入口
│   │   ├── app.py              # Flask 启动、Injector 创建
│   │   └── module.py           # 依赖注入模块
│   ├── config/                 # 配置文件
│   ├── data/                   # 示例论文 PDF
│   ├── instance/               # SQLite 数据库 (开发)
│   ├── internal/               # 核心业务代码
│   │   ├── handler/            # 请求处理器 (CRAG 管线、会话、认证)
│   │   ├── service/            # 业务服务层
│   │   ├── model/              # SQLAlchemy 数据模型
│   │   ├── router/             # Flask 路由定义
│   │   ├── schema/             # 数据验证 Schema
│   │   ├── middleware/         # 中间件
│   │   ├── exception/          # 异常处理
│   │   ├── extension/          # Flask 扩展 (数据库、迁移)
│   │   ├── schedule/           # 定时任务
│   │   └── server/             # HTTP 服务器配置
│   ├── pkg/                    # 公共工具包
│   ├── storage/                # 向量存储服务
│   ├── study/                  # 学习笔记
│   ├── test/                   # 单元测试
│   ├── Zlearn_test/            # 实验代码
│   └── requirements.txt        # Python 依赖
│
├── day_4_UI/
│   └── LLMOps-ui/              # Vue 3 + TypeScript 前端
│       ├── src/
│       │   ├── views/          # 页面组件
│       │   ├── components/     # 通用组件
│       │   ├── services/       # API 调用封装
│       │   ├── stores/         # Pinia 状态管理
│       │   ├── router/         # Vue Router 路由
│       │   ├── models/         # TypeScript 类型定义
│       │   ├── utils/          # 工具函数
│       │   └── config/         # 前端配置
│       └── package.json        # Node.js 依赖
│
└── instance/
    └── session_assets/         # 会话资产 (文档元数据、上传文件)
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Yarn
- PostgreSQL
- Pinecone 账号 (向量数据库)

### 1. 克隆项目

```bash
git clone <repo-url>
cd search_RAG_system
```

### 2. 启动后端

```bash
cd day_3

# 安装依赖
pip install -r requirements.txt

# 配置环境变量 (复制模板并填入你的 API Key)
cp .env.example .env
# 编辑 .env 填写以下配置:
# - SQLALCHEMY_DATABASE_URI (PostgreSQL 连接串)
# - OPENAI_API_KEY
# - PINECONE_API_KEY
# - NVIDIA_API_KEY
# - SERPER_API_KEY
# - LANGSMITH_API_KEY

# 启动服务
PYTHONPATH=. python app/app.py
```

后端默认运行在 `http://localhost:5000`

### 3. 启动前端

```bash
cd day_4_UI/LLMOps-ui

# 安装依赖
yarn

# 启动开发服务器
yarn dev
```

前端默认运行在 `http://localhost:5173`，自动代理 `/api` 请求到后端。

## 🔧 常用命令

### 后端 (day_3/)

| 命令 | 说明 |
|------|------|
| `PYTHONPATH=. python app/app.py` | 启动 Flask 服务 |
| `pip install -r requirements.txt` | 安装 Python 依赖 |

### 前端 (day_4_UI/LLMOps-ui/)

| 命令 | 说明 |
|------|------|
| `yarn` | 安装依赖 |
| `yarn dev` | 启动开发服务器 |
| `yarn build` | 类型检查 + 生产构建 |
| `yarn test:unit` | 运行单元测试 (Vitest) |
| `yarn lint` | ESLint + oxlint 代码检查 |
| `yarn format` | Prettier 代码格式化 |

## 📐 技术架构

### 后端技术栈

| 技术 | 用途 |
|------|------|
| **Flask 3** | Web 框架 |
| **SQLAlchemy** | ORM 数据库操作 |
| **Injector** | 依赖注入 |
| **LangChain** | LLM 应用框架 |
| **LangGraph** | CRAG 管线编排 |
| **Pinecone** | 向量数据库 |
| **NVIDIA AI Endpoints** | 嵌入模型 |
| **OpenAI** | LLM 推理 |
| **PyMuPDF** | PDF 文档解析 |

### 前端技术栈

| 技术 | 用途 |
|------|------|
| **Vue 3** | 前端框架 |
| **TypeScript** | 类型安全 |
| **Vite** | 构建工具 |
| **Arco Design** | UI 组件库 |
| **Pinia** | 状态管理 |
| **Vue Router** | 路由管理 |

### CRAG 处理流程

```
用户提问 → 加载历史 → 文档检索 → 相关性评估
                                        │
                           ┌────────────┴────────────┐
                           ▼                         ▼
                      文档相关                  文档不相关
                           │                         │
                           ▼                         ▼
                      生成回答                 网络搜索补充
                           │                         │
                           └────────────┬────────────┘
                                        ▼
                                  生成最终回答
                                        │
                                        ▼
                                  保存消息记录
```

## 📝 API 规范

- 基础路径: 后端不含 `/api` 前缀，前端通过 Vite 代理添加
- 认证方式: Flask Session Cookie (浏览器自动携带)
- 响应格式:

```json
{
  "code": "success | fail | validateError | unauthorized | forbidden",
  "message": "操作说明",
  "data": { ... }
}
```

## 🔐 环境变量

在 `day_3/.env` 中配置以下变量:

| 变量名 | 说明 |
|--------|------|
| `SQLALCHEMY_DATABASE_URI` | PostgreSQL 连接字符串 |
| `OPENAI_API_KEY` | OpenAI API 密钥 |
| `PINECONE_API_KEY` | Pinecone 向量数据库密钥 |
| `NVIDIA_API_KEY` | NVIDIA AI Endpoints 密钥 |
| `SERPER_API_KEY` | Serper 搜索 API 密钥 |
| `LANGSMITH_API_KEY` | LangSmith 追踪密钥 (可选) |

> ⚠️ **注意**: `.env` 文件包含敏感信息，已被 `.ignore` 排除，请勿提交到版本控制。

## 📄 License

MIT
