"""通用工具函数模块

提供项目中常用的工具函数，如时间处理、文件读取等。
"""
from datetime import datetime
from pathlib import Path


def now_str() -> str:
    """获取当前时间的字符串表示
    
    Returns:
        str: 格式化为 'YYYY-MM-DD HH:MM:SS' 的当前时间字符串
        
    Example:
        >>> now_str()
        '2024-01-15 14:30:25'
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_text_file(path: Path) -> str:
    """读取文本文件内容
    
    使用UTF-8编码读取指定路径的文本文件。
    
    Args:
        path: 文件路径对象
        
    Returns:
        str: 文件的文本内容
        
    Raises:
        FileNotFoundError: 文件不存在时抛出
        UnicodeDecodeError: 文件编码不是UTF-8时抛出
        
    Example:
        >>> read_text_file(Path("docs/example.md"))
        '# 标题\\n这是文档内容...'
    """
    return path.read_text(encoding="utf-8")
