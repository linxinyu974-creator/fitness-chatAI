# 🤖 AI 健身教练 - 基于 Ollama 的 RAG 智能问答系统

一款基于本地 Ollama 部署的 AI 健身教练问答智能体，采用 RAG（检索增强生成）架构，结合 bge-m3 嵌入模型和 deepseek-r1:7b 大语言模型，提供专业的健身指导和问答服务。

## ✨ 核心功能

- **🧠 RAG 检索增强**：使用 bge-m3 模型将健身知识库文档向量化，实现语义检索
- **💬 智能问答**：基于 deepseek-r1:7b 模型生成专业、准确的健身建议
- **🖥️ 多模态交互**：支持命令行交互、Web 界面和 RESTful API 三种使用方式
- **📚 知识库管理**：支持健身知识文档的导入、索引和更新
- **💾 对话历史**：保存用户对话记录，支持上下文理解

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户交互层 (Presentation)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  CLI 命令行  │  │  Web 界面   │  │    RESTful API      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    业务逻辑层 (Service)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  RAG 服务   │  │  对话管理   │  │    知识库管理        │  │
│  │  - 检索     │  │  - 上下文   │  │    - 文档导入        │  │
│  │  - 重排序   │  │  - 历史记录 │  │    - 索引构建        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    数据访问层 (Data Access)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  ChromaDB   │  │  Ollama API │  │    本地文件存储      │  │
│  │  向量存储   │  │  模型调用   │  │    对话历史/配置     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ 技术栈

- **后端框架**：Python 3.10+ + FastAPI
- **向量数据库**：ChromaDB（轻量级、无需额外服务）
- **嵌入模型**：bge-m3（通过 Ollama 调用）
- **生成模型**：deepseek-r1:7b（通过 Ollama 调用）
- **前端界面**：原生 HTML + CSS + JavaScript
- **异步支持**：asyncio + httpx
- **数据验证**：Pydantic v2

## 📋 环境要求

- Python 3.10+
- Ollama 服务（本地或远程）
- 8GB+ 内存（推荐 16GB）

## 🚀 快速开始

### 1. 安装 Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# 下载安装包: https://ollama.com/download/windows
```

### 2. 下载所需模型

```bash
# 下载嵌入模型
ollama pull bge-m3

# 下载大语言模型
ollama pull deepseek-r1:7b
```

### 3. 克隆项目并安装依赖

```bash
# 克隆项目
git clone <项目地址>
cd ai-fitness-coach

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，根据你的环境修改配置
```

默认配置：
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_LLM_MODEL=deepseek-r1:7b
```

### 5. 初始化知识库

```bash
# 将示例健身知识文档导入向量数据库
python init_knowledge_base.py
```

### 6. 启动服务

#### 方式一：Web 界面 + API

```bash
python main.py
```

访问 http://localhost:8000 使用 Web 界面

#### 方式二：命令行交互

```bash
python cli.py chat
```

## 📖 使用指南

### Web 界面

1. 打开浏览器访问 http://localhost:8000
2. 点击"新建对话"开始新的健身咨询
3. 在输入框中输入你的健身问题
4. AI 健身教练会基于知识库给出专业回答

**功能特点：**
- 💬 实时流式响应
- 📚 显示参考来源
- 💾 自动保存对话历史
- 📂 知识库管理（上传文档）
- 📱 响应式设计，支持移动端

### 命令行工具

```bash
# 启动交互式对话
python cli.py chat

# 查看帮助
python cli.py --help

# 查看知识库统计
python cli.py knowledge-stats

# 添加知识文档
python cli.py add-knowledge ./docs/fitness_guide.md

# 搜索知识库
python cli.py search-knowledge "减脂训练"

# 列出所有对话
python cli.py list-conversations

# 检查服务健康状态
python cli.py health
```

### API 接口

启动服务后，访问 http://localhost:8000/docs 查看完整的 API 文档。

**主要接口：**

```bash
# 健康检查
GET /api/health

# 创建对话
POST /api/conversations

# 发送消息（流式）
POST /api/chat/stream
Content-Type: application/json

{
  "message": "如何制定减脂计划？",
  "conversation_id": "optional-conversation-id",
  "stream": true
}

# 获取对话列表
GET /api/conversations

# 获取知识库统计
GET /api/knowledge/stats

# 上传文档
POST /api/knowledge/upload
Content-Type: multipart/form-data
```

## 📁 项目结构

```
ai-fitness-coach/
├── app/
│   ├── core/              # 核心配置
│   │   ├── config.py      # 配置管理
│   │   └── logger.py      # 日志配置
│   ├── models/            # 数据模型
│   │   └── schemas.py     # Pydantic 模型
│   ├── services/          # 业务服务
│   │   ├── ollama_client.py    # Ollama API 客户端
│   │   ├── vector_store.py     # 向量数据库服务
│   │   ├── rag_service.py      # RAG 服务
│   │   └── conversation_manager.py  # 对话管理
│   ├── api/               # API 路由
│   │   └── routes.py      # FastAPI 路由
│   └── static/            # 静态文件
│       ├── index.html     # Web 界面
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── app.js
├── data/                  # 数据目录
│   ├── knowledge_base/    # 知识库文档
│   ├── vector_db/         # 向量数据库
│   └── conversations/     # 对话历史
├── main.py                # FastAPI 入口
├── cli.py                 # 命令行工具
├── init_knowledge_base.py # 知识库初始化
├── requirements.txt       # 依赖列表
├── .env.example           # 环境变量示例
└── README.md              # 项目说明
```

## ⚙️ 配置说明

编辑 `.env` 文件自定义配置：

```env
# Ollama 配置
OLLAMA_HOST=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_LLM_MODEL=deepseek-r1:7b
OLLAMA_TIMEOUT=120

# 应用配置
APP_NAME=AI Fitness Coach
DEBUG=false

# 向量数据库配置
VECTOR_DB_PATH=./data/vector_db
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=5

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 对话配置
MAX_HISTORY_LENGTH=10
```

## 📝 添加自定义知识

### 方式一：通过 Web 界面

1. 打开 Web 界面
2. 点击左下角"知识库管理"
3. 选择"文件上传"或"文本输入"
4. 添加你的健身知识文档

### 方式二：通过命令行

```bash
# 添加单个文件
python cli.py add-knowledge ./my_fitness_guide.md

# 添加整个目录（批量）
for file in ./docs/*.md; do
    python cli.py add-knowledge "$file"
done
```

### 支持的文档格式

- `.txt` - 纯文本文件
- `.md` - Markdown 文件
- `.pdf` - PDF 文件
- `.docx` - Word 文档

## 🔧 故障排除

### Ollama 连接失败

```bash
# 检查 Ollama 服务状态
ollama list

# 重启 Ollama 服务
ollama serve
```

### 模型未找到

```bash
# 下载缺失的模型
ollama pull bge-m3
ollama pull deepseek-r1:7b
```

### 依赖安装失败

```bash
# 更新 pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [Ollama](https://ollama.com/) - 本地大模型运行框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Web 框架
- [ChromaDB](https://www.trychroma.com/) - 向量数据库
- [BGE-M3](https://github.com/FlagOpen/FlagEmbedding) - 嵌入模型
- [DeepSeek](https://github.com/deepseek-ai/DeepSeek-R1) - 大语言模型

---

💪 坚持锻炼，保持健康！
