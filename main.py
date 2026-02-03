"""FastAPI 应用入口"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.logger import logger
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # 检查 Ollama 连接
    from app.services.ollama_client import get_ollama_client
    ollama_client = get_ollama_client()
    health = await ollama_client.health_check()
    
    if health["connected"]:
        logger.info(f"Ollama 已连接，可用模型: {health['available_models']}")
        if not health["embedding_model_ready"]:
            logger.warning(f"嵌入模型 {settings.ollama_embedding_model} 未找到，请执行: ollama pull {settings.ollama_embedding_model}")
        if not health["llm_model_ready"]:
            logger.warning(f"LLM模型 {settings.ollama_llm_model} 未找到，请执行: ollama pull {settings.ollama_llm_model}")
    else:
        logger.error("Ollama 连接失败，请确保 Ollama 服务已启动")
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down...")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于Ollama的AI健身教练RAG问答智能体",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 注册路由
app.include_router(router, prefix="/api")


# 根路由 - 返回 Web UI
@app.get("/")
async def root():
    """根路由 - 返回Web界面"""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs_url": "/docs",
        "api_prefix": "/api"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
