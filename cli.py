#!/usr/bin/env python3
"""AI 健身教练 - 命令行交互工具"""

import asyncio
import sys
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

from app.core.config import settings
from app.core.logger import logger
from app.services.rag_service import get_rag_service
from app.services.conversation_manager import get_conversation_manager, MessageRole
from app.services.ollama_client import get_ollama_client


app = typer.Typer(help="AI 健身教练 - 命令行交互工具")
console = Console()


def print_banner():
    """打印欢迎横幅"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   💪  AI 健身教练  💪                                     ║
    ║                                                           ║
    ║   基于 Ollama + RAG 的智能健身问答系统                    ║
    ║   模型: deepseek-r1:7b + bge-m3                          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(f"[bold cyan]{banner}[/bold cyan]")


@app.command()
def chat(
    conversation_id: Optional[str] = typer.Option(None, "--conversation", "-c", help="继续指定对话"),
    no_rag: bool = typer.Option(False, "--no-rag", help="不使用知识库检索")
):
    """启动交互式对话"""
    print_banner()
    
    # 检查服务状态
    async def check_services():
        ollama_client = get_ollama_client()
        health = await ollama_client.health_check()
        
        if not health["connected"]:
            console.print("[red]❌ Ollama 服务未连接，请确保 Ollama 已启动[/red]")
            raise typer.Exit(1)
        
        console.print(f"[green]✓ Ollama 已连接[/green]")
        console.print(f"[dim]  嵌入模型: {settings.ollama_embedding_model}[/dim]")
        console.print(f"[dim]  生成模型: {settings.ollama_llm_model}[/dim]")
        
        if not health["embedding_model_ready"]:
            console.print(f"[yellow]⚠ 嵌入模型 {settings.ollama_embedding_model} 未找到[/yellow]")
            console.print(f"[dim]  请执行: ollama pull {settings.ollama_embedding_model}[/dim]")
        
        if not health["llm_model_ready"]:
            console.print(f"[yellow]⚠ LLM模型 {settings.ollama_llm_model} 未找到[/yellow]")
            console.print(f"[dim]  请执行: ollama pull {settings.ollama_llm_model}[/dim]")
    
    asyncio.run(check_services())
    
    # 初始化服务
    rag_service = get_rag_service()
    conversation_manager = get_conversation_manager()
    
    # 获取或创建对话
    if conversation_id:
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            console.print(f"[red]对话 {conversation_id} 不存在[/red]")
            raise typer.Exit(1)
        current_id = conversation_id
        console.print(f"[dim]继续对话: {conversation.title}[/dim]")
    else:
        conversation = conversation_manager.create_conversation()
        current_id = conversation.id
        console.print(f"[dim]创建新对话: {conversation.id[:8]}...[/dim]")
    
    console.print("\n[dim]输入你的健身问题，输入 'quit' 或 'exit' 退出，输入 'help' 查看帮助[/dim]\n")
    
    async def interactive_chat():
        while True:
            try:
                # 获取用户输入
                user_input = Prompt.ask("[bold blue]你[/bold blue]")
                
                if user_input.lower() in ["quit", "exit", "q"]:
                    console.print("[dim]再见！坚持锻炼，保持健康！💪[/dim]")
                    break
                
                if user_input.lower() == "help":
                    print_help()
                    continue
                
                if user_input.lower() == "history":
                    show_conversation_history(current_id)
                    continue
                
                if user_input.lower().startswith("new "):
                    new_title = user_input[4:].strip()
                    conversation = conversation_manager.create_conversation(new_title or None)
                    current_id = conversation.id
                    console.print(f"[green]✓ 创建新对话: {conversation.title}[/green]\n")
                    continue
                
                if not user_input.strip():
                    continue
                
                # 添加用户消息
                conversation_manager.add_message(
                    conversation_id=current_id,
                    role=MessageRole.USER,
                    content=user_input
                )
                
                # 获取对话历史
                history = conversation_manager.get_conversation_history(current_id)
                
                # 生成回答
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("[cyan]思考中...", total=None)
                    
                    if no_rag:
                        # 不使用RAG，直接生成
                        ollama_client = get_ollama_client()
                        answer = await ollama_client.generate(
                            prompt=user_input,
                            system_prompt=rag_service.FITNESS_COACH_SYSTEM_PROMPT
                        )
                        sources = []
                    else:
                        # 使用RAG
                        answer, sources = await rag_service.generate_answer(
                            query=user_input,
                            conversation_history=history[:-1]
                        )
                
                # 添加助手消息
                conversation_manager.add_message(
                    conversation_id=current_id,
                    role=MessageRole.ASSISTANT,
                    content=answer,
                    sources=sources
                )
                
                # 显示回答
                console.print(f"\n[bold green]AI 健身教练[/bold green]")
                console.print(Markdown(answer))
                
                # 显示引用来源
                if sources:
                    console.print(f"\n[dim]参考来源:[/dim]")
                    for i, source in enumerate(sources[:3], 1):
                        console.print(f"  [dim]{i}. {source.source} (相关度: {source.score:.2%})[/dim]")
                
                console.print()
                
            except KeyboardInterrupt:
                console.print("\n[dim]再见！坚持锻炼，保持健康！💪[/dim]")
                break
            except Exception as e:
                console.print(f"[red]错误: {e}[/red]")
    
    asyncio.run(interactive_chat())


def print_help():
    """打印帮助信息"""
    help_text = """
    [bold]可用命令:[/bold]
    
    [cyan]help[/cyan]      - 显示此帮助信息
    [cyan]history[/cyan]   - 显示当前对话历史
    [cyan]new <标题>[/cyan] - 创建新对话
    [cyan]quit/exit[/cyan] - 退出程序
    
    [bold]使用提示:[/bold]
    - 直接输入问题即可与 AI 健身教练对话
    - 可以询问训练计划、营养建议、运动技巧等问题
    - 支持多轮对话，AI 会记住上下文
    """
    console.print(Panel(help_text, title="帮助", border_style="blue"))


def show_conversation_history(conversation_id: str):
    """显示对话历史"""
    conversation_manager = get_conversation_manager()
    conversation = conversation_manager.get_conversation(conversation_id)
    
    if not conversation or not conversation.messages:
        console.print("[dim]暂无对话历史[/dim]")
        return
    
    console.print(f"\n[bold]对话历史: {conversation.title}[/bold]\n")
    
    for msg in conversation.messages:
        role_color = "blue" if msg.role == MessageRole.USER else "green"
        role_name = "你" if msg.role == MessageRole.USER else "AI"
        console.print(f"[bold {role_color}]{role_name}:[/bold {role_color}]")
        console.print(msg.content[:200] + "..." if len(msg.content) > 200 else msg.content)
        console.print()


@app.command()
def list_conversations(
    limit: int = typer.Option(20, "--limit", "-l", help="显示数量限制")
):
    """列出所有对话"""
    conversation_manager = get_conversation_manager()
    conversations = conversation_manager.list_conversations(limit=limit)
    
    if not conversations:
        console.print("[dim]暂无对话[/dim]")
        return
    
    table = Table(
        title="对话列表",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    
    table.add_column("ID", style="dim", width=12)
    table.add_column("标题", min_width=20)
    table.add_column("消息数", justify="center", width=8)
    table.add_column("更新时间", width=20)
    
    for conv in conversations:
        table.add_row(
            conv.id[:8] + "...",
            conv.title,
            str(conv.message_count),
            conv.updated_at.strftime("%Y-%m-%d %H:%M")
        )
    
    console.print(table)


@app.command()
def delete_conversation(
    conversation_id: str = typer.Argument(..., help="对话ID")
):
    """删除指定对话"""
    conversation_manager = get_conversation_manager()
    
    if not Confirm.ask(f"确定要删除对话 {conversation_id[:8]}... 吗?"):
        console.print("[dim]已取消[/dim]")
        return
    
    success = conversation_manager.delete_conversation(conversation_id)
    
    if success:
        console.print(f"[green]✓ 已删除对话[/green]")
    else:
        console.print(f"[red]✗ 对话不存在[/red]")


@app.command()
def knowledge_stats():
    """查看知识库统计信息"""
    rag_service = get_rag_service()
    stats = rag_service.get_knowledge_stats()
    
    table = Table(
        title="知识库统计",
        box=box.ROUNDED
    )
    
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="green")
    
    table.add_row("文档总数", str(stats["total_documents"]))
    table.add_row("知识块总数", str(stats["total_chunks"]))
    table.add_row("集合名称", stats["collection_name"])
    table.add_row("嵌入模型", stats["embedding_model"])
    
    console.print(table)


@app.command()
def add_knowledge(
    file_path: str = typer.Argument(..., help="知识文件路径"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="来源名称")
):
    """添加知识文档到知识库"""
    path = Path(file_path)
    
    if not path.exists():
        console.print(f"[red]文件不存在: {file_path}[/red]")
        raise typer.Exit(1)
    
    rag_service = get_rag_service()
    source_name = source or path.name
    
    async def add_doc():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]处理文档...", total=None)
            
            success, chunks_count = await rag_service.add_knowledge_from_file(
                str(path),
                metadata={"source_name": source_name}
            )
        
        if success:
            console.print(f"[green]✓ 成功添加文档[/green]")
            console.print(f"  来源: {source_name}")
            console.print(f"  切分块数: {chunks_count}")
        else:
            console.print(f"[red]✗ 添加文档失败[/red]")
    
    asyncio.run(add_doc())


@app.command()
def search_knowledge(
    query: str = typer.Argument(..., help="搜索关键词"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="返回结果数量")
):
    """搜索知识库"""
    rag_service = get_rag_service()
    
    async def do_search():
        results = await rag_service.retrieve(query, top_k=top_k)
        
        if not results:
            console.print("[dim]未找到相关结果[/dim]")
            return
        
        console.print(f"\n[bold]搜索结果: \"{query}\"[/bold]\n")
        
        for i, result in enumerate(results, 1):
            panel = Panel(
                result.content[:300] + "..." if len(result.content) > 300 else result.content,
                title=f"[cyan]{i}. {result.source}[/cyan]",
                subtitle=f"[dim]相关度: {result.score:.2%}[/dim]",
                border_style="blue"
            )
            console.print(panel)
    
    asyncio.run(do_search())


@app.command()
def clear_knowledge(
    force: bool = typer.Option(False, "--force", "-f", help="强制清空，不确认")
):
    """清空知识库"""
    if not force:
        if not Confirm.ask("[red]确定要清空知识库吗? 此操作不可恢复![/red]"):
            console.print("[dim]已取消[/dim]")
            return
    
    rag_service = get_rag_service()
    success = rag_service.clear_knowledge_base()
    
    if success:
        console.print("[green]✓ 知识库已清空[/green]")
    else:
        console.print("[red]✗ 清空失败[/red]")


@app.command()
def health():
    """检查服务健康状态"""
    async def check():
        ollama_client = get_ollama_client()
        health_status = await ollama_client.health_check()
        
        table = Table(
            title="服务健康状态",
            box=box.ROUNDED
        )
        
        table.add_column("服务", style="cyan")
        table.add_column("状态", style="green")
        table.add_column("详情", style="dim")
        
        # Ollama 状态
        if health_status["connected"]:
            table.add_row(
                "Ollama",
                "[green]✓ 正常[/green]",
                f"{len(health_status['available_models'])} 个模型"
            )
            
            # 嵌入模型
            if health_status["embedding_model_ready"]:
                table.add_row(
                    "嵌入模型",
                    "[green]✓ 就绪[/green]",
                    settings.ollama_embedding_model
                )
            else:
                table.add_row(
                    "嵌入模型",
                    "[red]✗ 未找到[/red]",
                    f"ollama pull {settings.ollama_embedding_model}"
                )
            
            # LLM 模型
            if health_status["llm_model_ready"]:
                table.add_row(
                    "LLM 模型",
                    "[green]✓ 就绪[/green]",
                    settings.ollama_llm_model
                )
            else:
                table.add_row(
                    "LLM 模型",
                    "[red]✗ 未找到[/red]",
                    f"ollama pull {settings.ollama_llm_model}"
                )
        else:
            table.add_row(
                "Ollama",
                "[red]✗ 未连接[/red]",
                "请检查 Ollama 服务是否启动"
            )
        
        # 向量数据库状态
        try:
            rag_service = get_rag_service()
            stats = rag_service.get_knowledge_stats()
            table.add_row(
                "向量数据库",
                "[green]✓ 正常[/green]",
                f"{stats['total_chunks']} 个知识块"
            )
        except Exception as e:
            table.add_row(
                "向量数据库",
                "[red]✗ 异常[/red]",
                str(e)
            )
        
        console.print(table)
    
    asyncio.run(check())


if __name__ == "__main__":
    app()
