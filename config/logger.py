"""日志配置模块

配置应用的日志系统，支持控制台输出和文件轮转。
日志文件会自动轮转，避免单个文件过大。
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import Settings


def setup_logging(settings: Settings) -> None:
    """配置应用日志系统
    
    创建日志目录并配置日志处理器：
    1. 控制台处理器：实时输出日志到终端
    2. 文件处理器：轮转文件，单个文件最大2MB，保留3个备份
    
    Args:
        settings: 应用配置实例，用于获取日志级别
        
    Note:
        - 日志格式：时间 | 级别 | 模块名 | 消息
        - 文件路径：logs/app.log
        - 自动避免重复添加处理器
        
    Example:
        >>> settings = get_settings()
        >>> setup_logging(settings)
        >>> logging.getLogger(__name__).info("应用启动")
    """
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    # 配置日志格式
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # 获取根日志器
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())

    # 检查是否已经添加过处理器，避免重复
    has_console_handler = any(isinstance(handler, logging.StreamHandler) for handler in root.handlers)
    has_file_handler = any(
        isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename) == log_file.resolve()
        for handler in root.handlers
    )

    # 添加控制台处理器
    if not has_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

    # 添加文件处理器（轮转文件）
    if not has_file_handler:
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=2 * 1024 * 1024,  # 单个文件最大2MB
            backupCount=3,  # 保留3个备份文件
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
