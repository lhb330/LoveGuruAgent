"""文件工具模块

提供文件读写相关的工具函数。
"""
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def read_text_file(file_path: Path, encoding: str = "utf-8") -> str:
    """读取文本文件内容
    
    Args:
        file_path: 文件路径
        encoding: 文件编码，默认utf-8
        
    Returns:
        str: 文件内容
        
    Raises:
        FileNotFoundError: 文件不存在时抛出
        UnicodeDecodeError: 编码错误时抛出
        IOError: 读取失败时抛出
        
    Example:
        >>> from pathlib import Path
        >>> content = read_text_file(Path("docs/example.md"))
    """
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    if not file_path.is_file():
        raise IOError(f"路径不是文件: {file_path}")
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
            logger.debug(f"成功读取文件: {file_path}, 大小: {len(content)} 字符")
            return content
    except UnicodeDecodeError as e:
        logger.error(f"文件编码错误: {file_path}, 编码: {encoding}, 错误: {e}")
        raise
    except IOError as e:
        logger.error(f"读取文件失败: {file_path}, 错误: {e}")
        raise
