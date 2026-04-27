"""长期记忆服务模块

LangGraph 全面记忆（Comprehensive Memory）核心实现：
1. 记忆检索：在对话开始时加载与当前话题相关的长期记忆
2. 记忆提取：在对话结束后从对话内容中提取关键事实
3. 记忆管理：记忆去重、更新、淘汰

记忆提取策略：
- 使用 LLM 从对话中提取用户的关键信息（偏好、关系状态、重要事件等）
- 按重要度评分，高重要度的记忆优先保留
- 支持记忆更新（当同一 key 出现新信息时覆盖）
"""
import json
import logging
from typing import Optional

from config.database import SessionLocal
from config.settings import get_settings
from dao.user_memory_dao import UserMemoryDAO
from services.llm.factory import get_llm_service

logger = logging.getLogger(__name__)

# 记忆提取 Prompt 模板
MEMORY_EXTRACTION_PROMPT = """你是一个信息提取助手。请从以下对话中提取用户的关键信息，以 JSON 数组格式返回。

提取规则：
1. 只提取与用户个人相关的、可跨会话使用的长期事实
2. 注意：不仅要从用户的直接表述中提取，还要从用户的问题/关注点中推断隐含信息
   - 例如：用户问"第一次约会" → 可能推断出"用户正在准备第一次约会"或"用户可能单身/刚开始恋爱"
   - 例如：用户问"如何哄老婆开心" → 可以推断出"用户已婚"
3. 每条记忆包含 memory_key（简短标识）、memory_value（具体内容）、importance（0.0~1.0 重要度）
4. 重要度评分标准：
   - 1.0: 核心身份信息（姓名、性别、年龄）
   - 0.9: 重要关系信息（伴侣、婚姻状态）
   - 0.8: 关键偏好和价值观
   - 0.7: 重要经历和事件、当前状态（如"准备第一次约会"）
   - 0.6: 日常偏好和习惯、关注的话题领域
   - 0.5: 一般性信息、可能的兴趣点（需要标注为推测）
5. 不要提取临时的、一次性的信息
6. 如果对话中确实没有任何值得长期记住的信息，返回空数组 []
7. 对于从问题中推断的信息，在 memory_value 中标注"（推测）"

对话内容：
{conversation}

请仅返回 JSON 数组，不要包含任何其他文字：
[{{"memory_key": "...", "memory_value": "...", "importance": 0.8}}]
"""

# 记忆格式化 Prompt 模板（注入到系统提示词）
MEMORY_CONTEXT_TEMPLATE = """## 用户长期记忆
以下是关于该用户的重要信息，请在回答时参考：

{memories}

请基于以上用户信息，提供个性化的回答。
"""


class MemoryService:
    """长期记忆服务

    提供记忆的全生命周期管理：
    - 检索：加载用户长期记忆供 LLM 参考
    - 提取：从对话中提取关键事实
    - 存储：持久化到数据库
    - 淘汰：按重要度清理旧记忆
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm_service = get_llm_service()

    def get_user_memories(
        self, user_id: str, user_message: str = ""
    ) -> str:
        """获取用户长期记忆（格式化为 Prompt）

        检索用户的长期记忆，并通过简单的关键词匹配筛选与当前话题相关的记忆。

        Args:
            user_id: 用户标识
            user_message: 当前用户消息（用于相关性匹配）

        Returns:
            str: 格式化后的记忆文本，可直接注入 Prompt
        """
        if not self.settings.enable_long_memory:
            return ""

        try:
            with SessionLocal() as session:
                dao = UserMemoryDAO(session)
                memories = dao.get_memories_by_user(
                    user_id,
                    min_importance=0.3,
                    limit=self.settings.long_memory_max_entries,
                )

                if not memories:
                    return ""

                # 格式化记忆
                memory_lines = []
                for mem in memories:
                    memory_lines.append(
                        f"- [{mem.memory_key}] {mem.memory_value} "
                        f"(重要度: {mem.importance:.1f})"
                    )

                return MEMORY_CONTEXT_TEMPLATE.format(
                    memories="\n".join(memory_lines)
                )

        except Exception as e:
            logger.error(f"检索用户记忆失败: user_id={user_id}, error={str(e)}", exc_info=True)
            return ""

    def extract_and_save_memories(
        self,
        user_id: str,
        conversation_text: str,
        conversation_id: Optional[str] = None,
    ) -> int:
        """从对话中提取关键信息并保存为长期记忆

        使用 LLM 分析对话内容，提取关键事实，存储到数据库。

        Args:
            user_id: 用户标识
            conversation_text: 完整的对话文本（用户消息 + AI 回复）
            conversation_id: 来源会话ID

        Returns:
            int: 新创建的记忆数量
        """
        if not self.settings.enable_long_memory:
            return 0

        if not conversation_text or len(conversation_text) < 20:
            return 0

        try:
            # 1. 使用 LLM 提取记忆
            logger.info(f"开始调用LLM提取记忆, conversation_text长度={len(conversation_text)}")
            prompt = MEMORY_EXTRACTION_PROMPT.format(conversation=conversation_text)
            logger.debug(f"发送给LLM的Prompt:\n{prompt[:800]}")
            response = self.llm_service.invoke(prompt)
            logger.info(f"LLM返回响应长度={len(response)}")
            logger.info(f"LLM原始响应: {response}")

            # 2. 解析 JSON 响应
            extracted = self._parse_memory_json(response)
            logger.info(f"解析出记忆数量: {len(extracted)}")
            if extracted:
                logger.info(f"提取的记忆内容: {extracted}")

            if not extracted:
                logger.warning(f"未提取到记忆，可能原因：1)对话中无个人信息 2)LLM返回格式错误 3)Prompt需优化")
                return 0

            # 3. 存储到数据库
            saved_count = 0
            with SessionLocal() as session:
                dao = UserMemoryDAO(session)
                try:
                    for item in extracted:
                        memory_key = item.get("memory_key", "").strip()
                        memory_value = item.get("memory_value", "").strip()
                        importance = float(item.get("importance", 0.5))

                        if not memory_key or not memory_value:
                            continue

                        # 保存或更新记忆
                        dao.save_memory(
                            user_id=user_id,
                            memory_key=memory_key,
                            memory_value=memory_value,
                            importance=min(max(importance, 0.0), 1.0),
                            source_conversation_id=conversation_id,
                        )
                        saved_count += 1

                    # 4. 淘汰低重要度记忆
                    dao.evict_low_importance(
                        user_id,
                        max_entries=self.settings.long_memory_max_entries,
                    )

                    session.commit()
                    logger.info(
                        f"记忆提取完成: user_id={user_id}, "
                        f"conversation_id={conversation_id}, "
                        f"extracted={len(extracted)}, saved={saved_count}"
                    )

                except Exception:
                    session.rollback()
                    raise

        except Exception as e:
            logger.error(f"记忆提取失败: user_id={user_id}, error={str(e)}", exc_info=True)
            return 0

        return saved_count

    def _parse_memory_json(self, response: str) -> list[dict]:
        """解析 LLM 返回的记忆 JSON

        处理 LLM 可能返回的各种格式（纯 JSON、markdown 代码块等）。

        Args:
            response: LLM 原始响应

        Returns:
            list[dict]: 解析后的记忆列表
        """
        # 尝试提取 JSON 代码块
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end > start:
                response = response[start:end]
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                response = response[start:end]

        # 去除首尾空白
        response = response.strip()

        try:
            data = json.loads(response)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return [data]
        except json.JSONDecodeError:
            # 尝试修复常见 JSON 问题
            try:
                # 有时 LLM 会在 JSON 前后添加文字
                # 找到第一个 [ 和最后一个 ]
                start = response.find("[")
                end = response.rfind("]") + 1
                if start >= 0 and end > start:
                    data = json.loads(response[start:end])
                    if isinstance(data, list):
                        return data
            except json.JSONDecodeError:
                logger.warning(f"无法解析记忆 JSON: {response[:200]}")

        return []
