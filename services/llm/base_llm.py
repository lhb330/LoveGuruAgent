"""LLM服务抽象基类

定义所有LLM服务必须实现的接口。
提供聊天调用、向量化等核心方法的抽象定义。
"""
from abc import ABC, abstractmethod


class BaseLLMService(ABC):
    """LLM服务抽象基类
    
    所有LLM服务实现都应该继承此类，并实现所有抽象方法。
    确保不同模型提供商的API调用接口统一。
    """
    
    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """调用LLM生成文本回复
        
        Args:
            prompt: 提示词文本
            
        Returns:
            str: LLM生成的回复文本
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_llm(self):
        """获取底层LLM实例
        
        用于绑定工具等高级功能。不同的LLM服务返回的对象类型不同。
        
        Returns:
            object: 底层LLM对象（如ChatOpenAI实例）
            
        Raises:
            NotImplementedError: 如果不支持此功能
        """
        raise NotImplementedError

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """将文本转换为向量（embedding）
        
        Args:
            text: 要转换的文本
            
        Returns:
            list[float]: 浮点数向量，维度取决于使用的embedding模型
        """
        raise NotImplementedError
