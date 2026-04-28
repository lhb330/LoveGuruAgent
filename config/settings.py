"""应用配置管理模块

使用pydantic-settings从.env文件读取应用配置，提供类型安全的配置访问。
所有配置项都通过环境变量注入，支持默认值和类型校验。
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr
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

    database_user: str = Field(alias="DATABASE_USER")
    database_password: SecretStr = Field(alias="DATABASE_PASSWORD")
    database_url: str = Field(alias="DATABASE_URL")
    database_echo: bool = Field(alias="DATABASE_ECHO")

    llm_provider: str = Field(alias="LLM_PROVIDER")
    openai_api_key: SecretStr = Field(alias="OPENAI_API_KEY")
    openai_base_url: str = Field(alias="OPENAI_BASE_URL")
    openai_model: str = Field(alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(alias="OPENAI_EMBEDDING_MODEL")

    dashscope_api_key: SecretStr = Field(alias="DASHSCOPE_API_KEY")
    qwen_model: str = Field(alias="QWEN_MODEL")
    qwen_embedding_model: str = Field(alias="QWEN_EMBEDDING_MODEL")

    vector_dimension: int = Field(alias="VECTOR_DIMENSION")
    knowledge_docs_dir: str = Field(alias="KNOWLEDGE_DOCS_DIR")
    log_level: str = Field(alias="LOG_LEVEL")
    
    baidu_map_ak: str = Field(alias="BAIDU_MAP_AK")

    # 👇 LangSmith 配置（可选，开启可观测性）
    langchain_tracing_v2: bool = False
    langchain_api_key: Optional[str] = None
    langchain_project: str = Field(alias="LANGCHAIN_PROJECT")

    # 新增 checkpointer 相关配置
    checkpointer_uri: str = Field(alias="CHECKPOINTER_URI")
    # 是否启用检查点持久化
    enable_checkpointer: bool = True

    # 人机协同配置（敏感话题检测开关）
    # 是否开启敏感话题检测
    enable_sensitive_filter: bool = True
    # 可选自定义敏感词列表（逗号分隔字符串）
    sensitive_keywords: Optional[str] = None

    # 长期记忆相关配置（跨端存储）
    # 是否开启长期记忆
    enable_long_memory: bool = True
    # 每用户最多存储的记忆条目数
    long_memory_max_entries: int = 100

    # 可观测性配置（性能追踪与 debug）
    # 是否启用内置可观测性追踪
    enable_observability: bool = True
    # 追踪日志级别（debug/info）
    observability_log_level: str = "info"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
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
