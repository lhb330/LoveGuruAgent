"""应用配置管理模块

使用pydantic-settings从.env文件读取应用配置，提供类型安全的配置访问。
所有配置项都通过环境变量注入，支持默认值和类型校验。
"""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类
    
    从.env文件中读取所有配置项，并提供类型安全的访问。
    使用pydantic的Field和alias机制映射环境变量。
    
    Attributes:
        app_name: 应用名称
        app_env: 运行环境（dev/test/prod）
        app_host: 服务监听地址
        app_port: 服务监听端口
        app_debug: 调试模式开关
        database_url: 数据库连接字符串
        database_echo: 是否打印SQL日志
        llm_provider: 大模型提供商（openai/qwen）
        openai_api_key: OpenAI API密钥
        openai_base_url: OpenAI API基础URL
        openai_model: OpenAI模型名称
        dashscope_api_key: 阿里云DashScope API密钥
        qwen_model: 通义千问聊天模型名称
        qwen_embedding_model: 通义千问Embedding模型名称
        vector_dimension: 向量维度
        knowledge_docs_dir: 知识库文档目录
        log_level: 日志级别
        baidu_map_ak: 百度地图API密钥
    """
    app_name: str = Field(alias="APP_NAME")
    app_env: str = Field(alias="APP_ENV")
    app_host: str = Field(alias="APP_HOST")
    app_port: int = Field(alias="APP_PORT")
    app_debug: bool = Field(alias="APP_DEBUG")

    database_url: str = Field(alias="DATABASE_URL")
    database_echo: bool = Field(alias="DATABASE_ECHO")

    llm_provider: str = Field(alias="LLM_PROVIDER")
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_base_url: str = Field(alias="OPENAI_BASE_URL")
    openai_model: str = Field(alias="OPENAI_MODEL")

    dashscope_api_key: str = Field(alias="DASHSCOPE_API_KEY")
    qwen_model: str = Field(alias="QWEN_MODEL")
    qwen_embedding_model: str = Field(alias="QWEN_EMBEDDING_MODEL")

    vector_dimension: int = Field(alias="VECTOR_DIMENSION")
    knowledge_docs_dir: str = Field(alias="KNOWLEDGE_DOCS_DIR")
    log_level: str = Field(alias="LOG_LEVEL")
    
    baidu_map_ak: str = Field(alias="BAIDU_MAP_AK")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def knowledge_docs_path(self) -> Path:
        """获取知识库文档的绝对路径
        
        Returns:
            Path: 知识库文档目录的绝对路径
        """
        return Path(self.knowledge_docs_dir).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取应用配置实例（单例模式）
    
    使用LRU缓存确保全局只创建一个Settings实例，避免重复读取.env文件。
    
    Returns:
        Settings: 应用配置实例
        
    Example:
        >>> settings = get_settings()
        >>> print(settings.app_name)
        'LoveGuruAgent'
    """
    return Settings()
