"""测试配置文件是否正确加载"""
from config.settings import get_settings

def test_config():
    settings = get_settings()
    
    print("=" * 50)
    print("配置加载测试")
    print("=" * 50)
    
    # 测试 OpenAI 配置
    print(f"\n✅ LLM_PROVIDER: {settings.llm_provider}")
    print(f"✅ OPENAI_BASE_URL: {settings.openai_base_url}")
    print(f"✅ OPENAI_MODEL: {settings.openai_model}")
    print(f"✅ OPENAI_EMBEDDING_MODEL: {settings.openai_embedding_model}")
    
    # 安全地显示 API Key（只显示前10个字符）
    api_key = settings.openai_api_key.get_secret_value()
    masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "太短"
    print(f"✅ OPENAI_API_KEY: {masked_key}")
    
    # 测试 DashScope 配置
    dash_key = settings.dashscope_api_key.get_secret_value()
    masked_dash = dash_key[:10] + "..." + dash_key[-4:] if len(dash_key) > 14 else "太短"
    print(f"✅ DASHSCOPE_API_KEY: {masked_dash}")
    
    print("\n" + "=" * 50)
    print("配置加载成功！")
    print("=" * 50)

if __name__ == "__main__":
    test_config()
