"""测试记忆提取功能

验证优化后的记忆提取 Prompt 能否从对话中推断出用户信息
"""
import json
from services.memory.memory_service import MemoryService

def test_memory_extraction():
    """测试不同对话场景的记忆提取"""
    
    memory_service = MemoryService()
    
    # 测试场景1：用户问"第一次约会"
    print("=" * 60)
    print("测试场景1：用户问'第一次约会'")
    print("=" * 60)
    conversation1 = """用户: 第一次约会
AI: 第一次约会时，有几个重要的注意事项可以帮助你留下好印象并确保双方都度过愉快的时光：

1. **准时**：守时是尊重对方的表现。确保你提前出发，以应对可能遇到的交通延误。

2. **着装得体**：根据约会的性质选择合适的服装。如果是正式晚餐，那么穿得稍微正式一点；如果是休闲活动，则可以穿得休闲一些。

3. **选择好地点**：选择一个安静、舒适的环境，便于交流。咖啡厅、餐厅或者公园都是不错的选择。

4. **准备话题**：提前准备一些轻松的话题，避免尴尬的沉默。可以聊聊兴趣爱好、旅行经历、电影等。

5. **注意礼仪**：
   - **准时**：守时是尊重对方的表现。
   - **穿着得体**：根据约会场合选择适宜的着装，展现最好的自己。
   - **积极倾听**：多听少说，通过提问表达对对方的关注与兴趣。
   - **保持礼貌**：对待服务人员友好，展示你的良好教养。
   - **轻松自然**：尽量放松心情，让对话自然流畅。

这些建议有助于给对方留下好印象。"""
    
    result1 = memory_service.extract_and_save_memories(
        user_id="test_user_001",
        conversation_text=conversation1,
        conversation_id="test_conv_001"
    )
    print(f"提取到记忆数量: {result1}\n")
    
    # 测试场景2：用户问"如何哄老婆开心"
    print("=" * 60)
    print("测试场景2：用户问'如何哄老婆开心'")
    print("=" * 60)
    conversation2 = """用户: 如何哄老婆开心
AI: 哄老婆开心需要用心和技巧，以下是一些实用的建议：

1. **倾听和理解**：
   - 认真听她说话，不要急于给建议
   - 理解她的情绪和需求
   - 表达你的关心和在意

2. **小惊喜**：
   - 偶尔送一束花或小礼物
   - 准备一顿浪漫的晚餐
   - 写一封表达爱意的情书

3. **分担家务**：
   - 主动承担一些家务活
   - 减轻她的负担
   - 让她感受到你的体贴

4. **赞美和肯定**：
   - 经常表达对她的赞美
   - 肯定她的付出和努力
   - 让她知道你很珍惜她

5. **陪伴**：
   - 抽出时间陪她做她喜欢的事
   - 一起看电影、逛街、旅行
   - 质量时间比数量更重要"""
    
    result2 = memory_service.extract_and_save_memories(
        user_id="test_user_002",
        conversation_text=conversation2,
        conversation_id="test_conv_002"
    )
    print(f"提取到记忆数量: {result2}\n")
    
    # 测试场景3：用户分享个人信息
    print("=" * 60)
    print("测试场景3：用户分享个人信息")
    print("=" * 60)
    conversation3 = """用户: 我今年25岁，刚和女朋友在一起半年，她喜欢浪漫的感觉
AI: 恭喜你们！在一起半年是一个很甜蜜的阶段。既然她喜欢浪漫，这里有一些建议：

1. **纪念日活动**：为你们在一起的每个月纪念日准备小惊喜
2. **手写情书**：在这个数字时代，手写信显得格外珍贵
3. **惊喜约会**：偶尔安排一个她不知道的约会地点
4. **记住细节**：记住她喜欢的事物，在不经意间展现你的关心

浪漫不在于花费多少，而在于你的用心程度。"""
    
    result3 = memory_service.extract_and_save_memories(
        user_id="test_user_003",
        conversation_text=conversation3,
        conversation_id="test_conv_003"
    )
    print(f"提取到记忆数量: {result3}\n")


if __name__ == "__main__":
    test_memory_extraction()
