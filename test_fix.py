"""测试修复后的聊天和记忆功能

验证：
1. SSE流式接口是否正确保存AI回复
2. 长期记忆是否正确提取和保存
"""
import requests
import json
import time

BASE_URL = "http://localhost:9000"

def test_stream_chat():
    """测试流式聊天接口"""
    print("=" * 60)
    print("测试1：流式聊天接口")
    print("=" * 60)
    
    # 获取新的conversation_id
    resp = requests.get(f"{BASE_URL}/chat/new-conversation-id")
    result = resp.json()
    conversation_id = result['data']['conversation_id']
    print(f"获取到新会话ID: {conversation_id}")
    
    # 发送流式消息
    user_message = "第一次约会应该注意什么？"
    print(f"\n发送用户消息: {user_message}")
    
    response = requests.post(
        f"{BASE_URL}/chat/send-stream",
        json={
            "conversation_id": conversation_id,
            "message": user_message,
            "user_id": "test_user_001"
        },
        stream=True
    )
    
    print("\n接收流式响应:")
    full_content = ""
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data:'):
                data_str = line_str[5:].strip()
                data = json.loads(data_str)
                if data.get('content'):
                    full_content += data['content']
                    print(data['content'], end='', flush=True)
                if data.get('done'):
                    print("\n\n响应完成")
                    if data.get('references'):
                        print(f"参考文档数量: {len(data['references'])}")
    
    print(f"\n完整回复长度: {len(full_content)}")
    print(f"完整回复内容: {full_content[:100]}...")
    
    # 等待3秒让异步记忆提取完成
    print("\n等待3秒让异步记忆提取完成...")
    time.sleep(3)
    
    return conversation_id

def check_chat_messages(conversation_id):
    """检查聊天消息是否正确保存"""
    print("\n" + "=" * 60)
    print("测试2：检查聊天消息保存")
    print("=" * 60)
    
    resp = requests.get(f"{BASE_URL}/chat/history/{conversation_id}")
    result = resp.json()
    
    if result['code'] == 200:
        messages = result['data']
        print(f"找到 {len(messages)} 条消息:")
        for msg in messages:
            print(f"  - ID: {msg['id']}, Role: {msg['role']}, Content: {msg['content'][:50]}...")
        
        # 检查是否有AI回复
        assistant_messages = [m for m in messages if m['role'] == 'assistant']
        user_messages = [m for m in messages if m['role'] == 'user']
        
        print(f"\n用户消息数量: {len(user_messages)}")
        print(f"AI回复数量: {len(assistant_messages)}")
        
        if len(assistant_messages) == 0:
            print("❌ 问题1未修复：仍然没有AI回复记录")
        else:
            print("✅ 问题1已修复：AI回复记录正常保存")
    else:
        print(f"查询失败: {result['msg']}")

def check_user_memory():
    """检查用户记忆是否保存"""
    print("\n" + "=" * 60)
    print("测试3：检查长期记忆")
    print("=" * 60)
    
    # 这里需要直接查询数据库，暂时通过日志检查
    print("请检查日志中是否有以下信息:")
    print("  - '记忆提取完成'")
    print("  - 'new_memories=X' (X>0)")
    print("\n同时检查数据库表 t_user_memory 是否有新记录")

if __name__ == "__main__":
    try:
        # 测试流式聊天
        conversation_id = test_stream_chat()
        
        # 检查消息保存
        check_chat_messages(conversation_id)
        
        # 检查记忆
        check_user_memory()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
