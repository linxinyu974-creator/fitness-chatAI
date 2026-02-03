#!/usr/bin/env python3
"""初始化知识库 - 将示例文档导入向量数据库"""

import asyncio
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.core.logger import logger
from app.services.rag_service import get_rag_service

console = Console()


async def init_knowledge_base():
    """初始化知识库"""
    console.print("[bold cyan]初始化知识库...[/bold cyan]\n")
    
    rag_service = get_rag_service()
    
    # 知识库目录
    kb_dir = Path("./data/knowledge_base")
    
    if not kb_dir.exists():
        console.print("[yellow]知识库目录不存在，创建中...[/yellow]")
        kb_dir.mkdir(parents=True, exist_ok=True)
        return
    
    # 获取所有文档文件
    supported_extensions = ['.txt', '.md', '.pdf', '.docx']
    files = [
        f for f in kb_dir.iterdir() 
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]
    
    if not files:
        console.print("[yellow]知识库中没有文档文件[/yellow]")
        return
    
    console.print(f"发现 {len(files)} 个文档文件:\n")
    
    # 导入文档
    success_count = 0
    total_chunks = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        for file_path in files:
            task = progress.add_task(
                f"[cyan]导入 {file_path.name}...[/cyan]", 
                total=None
            )
            
            success, chunks = await rag_service.add_knowledge_from_file(
                str(file_path),
                metadata={"category": "fitness_knowledge"}
            )
            
            progress.remove_task(task)
            
            if success:
                success_count += 1
                total_chunks += chunks
                console.print(f"[green]✓[/green] {file_path.name} - {chunks} 个知识块")
            else:
                console.print(f"[red]✗[/red] {file_path.name} - 导入失败")
    
    # 显示统计
    console.print(f"\n[bold]导入完成:[/bold]")
    console.print(f"  成功: {success_count}/{len(files)}")
    console.print(f"  总知识块: {total_chunks}")
    
    # 显示知识库统计
    stats = rag_service.get_knowledge_stats()
    console.print(f"\n[bold]知识库统计:[/bold]")
    console.print(f"  文档数: {stats['total_documents']}")
    console.print(f"  知识块: {stats['total_chunks']}")
    console.print(f"  集合: {stats['collection_name']}")


if __name__ == "__main__":
    asyncio.run(init_knowledge_base())
