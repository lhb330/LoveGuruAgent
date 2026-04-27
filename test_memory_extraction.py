"""测试长期记忆提取功能

验证 t_user_memory 表能否正常写入数据。
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.memory.memory_service import MemoryService
from config.database import SessionLocal
from dao.user_memory_dao import UserMemoryDAO


def test_memory_extraction():
    """测试记忆提取功能"""
    print("=" * 60)
    print("测试长期记忆提取功能")
    print("=" * 60)
    
    # 测试数据：模拟一段对话
    test_conversation = """
用户: 我叫小明，今年25岁，刚谈了一个女朋友叫小红
AI: 恭喜你啊小明！和小红相处得怎么样？
用户: 我们交往3个月了，她很喜欢吃日料，我打算带她去约会
AI: 约会吃日料是个不错的选择呢！你知道附近有哪些好的日料店吗？
    """
    
    user_id = "test_user_001"
    conversation_id = "conv-test-001"
    
    # 1. 调用记忆提取服务
    print("\n【步骤1】调用 LLM 提取记忆...")
    memory_service = MemoryService()
    
    try:
        saved_count = memory_service.extract_and_save_memories(
            user_id=user_id,
            conversation_text=test_conversation,
            conversation_id=conversation_id,
        )
        print(f"✅ 记忆提取成功，保存了 {saved_count} 条记忆")
    except Exception as e:
        print(f"❌ 记忆提取失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. 查询数据库验证
    print("\n【步骤2】查询数据库验证...")
    with SessionLocal() as session:
        dao = UserMemoryDAO(session)
        memories = dao.get_memories_by_user(user_id)
        
        print(f"\n用户 {user_id} 共有 {len(memories)} 条记忆：")
        print("-" * 60)
        
        for i, mem in enumerate(memories, 1):
            print(f"{i}. [{mem.memory_key}]")
            print(f"   内容: {mem.memory_value}")
            print(f"   重要度: {mem.importance}")
            print(f"   来源会话: {mem.source_conversation_id}")
            print(f"   创建时间: {mem.create_time}")
            print()
    
    # 3. 测试记忆检索（模拟下次对话加载）
    print("\n【步骤3】测试记忆检索（下次对话加载）...")
    memory_context = memory_service.get_user_memories(user_id, "约会")
    print("加载的记忆上下文：")
    print(memory_context if memory_context else "（无记忆）")
    
    # 4. 测试记忆淘汰
    print("\n【步骤4】测试记忆淘汰（超过100条时自动清理）...")
    with SessionLocal() as session:
        dao = UserMemoryDAO(session)
        evicted = dao.evict_low_importance(user_id, max_entries=100)
        print(f"淘汰了 {evicted} 条低重要度记忆")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


def test_memory_update():
    """测试记忆更新功能（相同 key 自动覆盖）"""
    print("\n" + "=" * 60)
    print("测试记忆更新功能")
    print("=" * 60)
    
    user_id = "test_user_001"
    
    # 第一次保存
    print("\n【步骤1】第一次保存记忆...")
    with SessionLocal() as session:
        dao = UserMemoryDAO(session)
        mem1 = dao.save_memory(
            user_id=user_id,
            memory_key="partner_name",
            memory_value="女朋友叫小红",
            importance=0.9,
            source_conversation_id="conv-001",
        )
        print(f"保存: {mem1.memory_key} = {mem1.memory_value} (重要度: {mem1.importance})")
    
    # 第二次保存（相同 key）
    print("\n【步骤2】第二次保存（相同 key，内容更新）...")
    with SessionLocal() as session:
        dao = UserMemoryDAO(session)
        mem2 = dao.save_memory(
            user_id=user_id,
            memory_key="partner_name",
            memory_value="女朋友叫小红，交往3个月了",
            importance=0.9,
            source_conversation_id="conv-002",
        )
        print(f"更新: {mem2.memory_key} = {mem2.memory_value} (重要度: {mem2.importance})")
    
    # 验证更新
    print("\n【步骤3】验证记忆更新...")
    with SessionLocal() as session:
        dao = UserMemoryDAO(session)
        mem = dao.get_memory_by_key(user_id, "partner_name")
        if mem:
            print(f"✅ 更新成功: {mem.memory_key} = {mem.memory_value}")
        else:
            print("❌ 未找到记忆")
    
    print("=" * 60)


if __name__ == "__main__":
    # 测试记忆提取
    test_memory_extraction()
    
    # 测试记忆更新
    test_memory_update()
