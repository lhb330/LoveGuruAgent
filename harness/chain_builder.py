"""聊天链编排模块

将RAG检索、工具调用、Prompt组装、LLM调用等环节串联成完整的处理链。
负责决定何时调用工具、如何整合多方信息生成最终回复。
"""
import re
from typing import Optional

from common.constants import place_types
from harness.prompt_manager import PromptManager
from services.chat.rag_service import RAGService
from services.llm.factory import get_llm_service


class ChatChainBuilder:
    """聊天处理链构建器
    
    将多个服务组合成一条处理链，执行完整的聊天流程：
    1. 检测是否需要调用工具（如地图搜索）
    2. 从知识库检索相关文档（RAG）
    3. 组装Prompt（包括工具结果和知识库内容）
    4. 调用LLM生成回复
    
    Attributes:
        rag_service: RAG检索服务实例
        llm_service: LLM服务实例
    """
    
    def __init__(self) -> None:
        """初始化聊天链
        
        创建RAG服务和LLM服务实例。
        """
        self.rag_service = RAGService()
        self.llm_service = get_llm_service()

    def run(self, user_message: str) -> tuple[str, list[dict]]:
        """执行聊天处理链
        
        主流程方法，协调各个组件完成聊天请求处理。
        
        Args:
            user_message: 用户消息文本
            
        Returns:
            tuple[str, list[dict]]: (AI回复文本, 参考文档列表)
        """
        # 检查是否需要调用地图工具
        map_result = self._try_map_search(user_message)
        
        if map_result:
            # 如果触发了地图搜索,将结果加入提示词
            references = self.rag_service.retrieve(user_message)
            prompt = PromptManager.build_chat_prompt_with_tools(
                user_message, references, map_result
            )
        else:
            # 常规RAG流程
            references = self.rag_service.retrieve(user_message)
            prompt = PromptManager.build_chat_prompt(user_message, references)
        
        answer = self.llm_service.invoke(prompt)
        return answer, references
    
    def _try_map_search(self, user_message: str) -> Optional[dict]:
        """检测用户消息是否需要地图搜索
        
        通过关键词匹配判断用户是否想查找附近的地点。
        支持20+种地点类型，每种类型有多个同义词。
        
        Args:
            user_message: 用户消息文本
            
        Returns:
            Optional[dict]: 如果需要搜索则返回搜索结果，否则返回None
        """
        from tools.baidu_map_tool import search_nearby
        from config.settings import get_settings

        
        # 检查用户消息是否包含地点类型关键词
        matched_type = None
        for standard_type, keywords in place_types.items():
            for keyword in keywords:
                if keyword in user_message:
                    matched_type = standard_type
                    break
            if matched_type:
                break
        
        if matched_type:
            # 智能提取地址信息
            location = self._extract_location(user_message)
            
            # 调用地图搜索
            settings = get_settings()
            ak = settings.baidu_map_ak
            return search_nearby(
                query=matched_type,
                location=location,
                ak=ak
            )
        
        return None
    
    def _extract_location(self, user_message: str) -> str:
        """从用户消息中提取地址信息(增强版)
        
        使用5层正则匹配策略，从用户消息中提取地址：
        1. 完整地址: "XX市XX区XX路/街/道"
        2. 行政区划: "XX市XX区"
        3. 附近表达: "XX区附近"
        4. 单独地名: "XX区"、"XX市"
        5. 地标建筑: "XX小区"、"XX大厦"
        
        Args:
            user_message: 用户消息文本
            
        Returns:
            str: 提取的地址文本，如果未提取到则返回空字符串
        """
        # 1. 优先匹配完整地址: "XX市XX区XX路/街/道"
        full_pattern = r"([\u4e00-\u9fa5]{2,}市[\u4e00-\u9fa5]{2,}(区|县|镇)[\u4e00-\u9fa5]{2,}(路|街|道|巷)?)"
        match = re.search(full_pattern, user_message)
        if match:
            return match.group(1)
        
        # 2. 匹配 "XX市XX区" 或 "XX市XX县"
        city_district_pattern = r"([\u4e00-\u9fa5]{2,}市[\u4e00-\u9fa5]{2,}(区|县|镇))"
        match = re.search(city_district_pattern, user_message)
        if match:
            return match.group(1)
        
        # 3. 匹配 "XX区附近"、"XX路附近"
        nearby_pattern = r"([\u4e00-\u9fa5]{2,}(区|县|镇|路|街|道|地铁站|站))附近"
        match = re.search(nearby_pattern, user_message)
        if match:
            return match.group(1)
        
        # 4. 匹配单独的 "XX区"、"XX市"、"XX地铁站"
        simple_pattern = r"([\u4e00-\u9fa5]{2,}(市|区|县|镇|地铁站|站))"
        match = re.search(simple_pattern, user_message)
        if match:
            return match.group(1)
        
        # 5. 匹配 "XX小区"、"XX大厦"、"XX商场"等具体地点
        landmark_pattern = r"([\u4e00-\u9fa5]{2,}(小区|大厦|商场|广场|公园|医院|学校))"
        match = re.search(landmark_pattern, user_message)
        if match:
            return match.group(1)
        
        # 默认返回空字符串,让百度地图API根据query智能匹配
        return ""
