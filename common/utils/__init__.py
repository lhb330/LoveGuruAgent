"""工具模块包

提供通用的工具函数和类。
"""
from .FileUtil import read_text_file
from .DateUtil import DateUtil

__all__ = ["read_text_file", "DateUtil"]