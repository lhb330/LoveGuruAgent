"""日志配置模块

配置应用的日志系统，支持控制台输出和按日期分割的文件输出。
日志文件会按天自动分割，格式为 app-yyyy-MM-dd.log。
"""
import logging
from datetime import datetime
from pathlib import Path

from config.settings import Settings


class DailyFileHandler(logging.FileHandler):
    """按日期分割的日志文件处理器
    
    每天自动生成新的日志文件，文件名格式为 app-yyyy-MM-dd.log
    """
    
    def __init__(self, log_dir: Path, encoding: str = "utf-8"):
        self.log_dir = log_dir
        self.current_date = None
        self.encoding = encoding
        # 先不创建文件，在emit时动态创建
        super().__init__(self._get_log_file(), mode='a', encoding=encoding)
        self.update_file()
    
    def _get_log_file(self) -> Path:
        """获取当天的日志文件路径"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"app-{today}.log"
    
    def update_file(self):
        """检查是否需要切换到新的日志文件"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.current_date != today:
            # 关闭旧文件
            if self.stream:
                self.stream.close()
                self.stream = None
            
            # 打开新文件
            self.current_date = today
            log_file = self._get_log_file()
            self.baseFilename = str(log_file.resolve())
            self.stream = self._open()
    
    def emit(self, record):
        """写入日志记录前先检查是否需要切换文件"""
        self.update_file()
        super().emit(record)


def setup_logging(settings: Settings) -> None:
    """配置应用日志系统

    创建日志目录并配置日志处理器：
    1. 控制台处理器：实时输出日志到终端
    2. 文件处理器：按天分割日志文件，格式为 app-yyyy-MM-dd.log

    Args:
        settings: 应用配置实例，用于获取日志级别

    Note:
        - 日志格式：时间 | 级别 | 模块名 | 消息
        - 文件路径：logs/app-yyyy-MM-dd.log
        - 每天自动生成新的日志文件
        - 自动避免重复添加处理器

    Example:
        >>> settings = get_settings()
        >>> setup_logging(settings)
        >>> logging.getLogger(__name__).info("应用启动")
    """
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

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
        isinstance(handler, DailyFileHandler)
        for handler in root.handlers
    )

    # 添加控制台处理器
    if not has_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

    # 添加文件处理器（按天分割）
    if not has_file_handler:
        file_handler = DailyFileHandler(log_dir, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    # 抑制第三方库的冗余 INFO 日志
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)