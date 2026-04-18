"""测试地图搜索优化功能"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.chain_builder import ChatChainBuilder


def test_address_extraction():
    """测试地址提取功能"""
    print("=" * 60)
    print("测试1: 地址提取功能")
    print("=" * 60)
    
    builder = ChatChainBuilder()
    
    test_cases = [
        ("帮我找朝阳区附近的餐厅", "朝阳区"),
        ("深圳市龙华区地铁站附近有什么好吃的", "深圳市龙华区地铁站"),
        ("北京海淀区中关村大街附近找咖啡厅", "北京海淀区中关村大街"),
        ("广州市天河区体育中心附近", "广州市天河区"),
        ("上海浦东新区陆家嘴地铁站附近的银行", "上海浦东新区陆家嘴地铁站"),
        ("成都武侯区人民南路附近的酒店", "成都武侯区人民南路"),
        ("杭州西湖区附近找公园", "杭州西湖区"),
        ("南京鼓楼区新街口商场附近的停车场", "南京鼓楼区新街口商场"),
    ]
    
    for message, expected in test_cases:
        location = builder._extract_location(message)
        status = "✓" if expected in location or location in expected else "✗"
        print(f"{status} 输入: {message}")
        print(f"   期望: {expected}")
        print(f"   实际: {location}")
        print()


def test_place_type_detection():
    """测试地点类型识别"""
    print("=" * 60)
    print("测试2: 地点类型识别")
    print("=" * 60)
    
    test_cases = [
        ("附近有什么好吃的餐厅", "餐厅"),
        ("找个咖啡厅坐坐", "咖啡厅"),
        ("晚上想去酒吧", "酒吧"),
        ("附近有加油站吗", "加油站"),
        ("想找家酒店住宿", "酒店"),
        ("去电影院看电影", "电影院"),
        ("附近有健身房吗", "健身房"),
        ("找个停车场停车", "停车场"),
        ("附近有药店吗", "医院"),
        ("想去KTV唱歌", "KTV"),
    ]
    
    builder = ChatChainBuilder()
    
    for message, expected_type in test_cases:
        result = builder._try_map_search(message)
        # 检查是否触发了地图搜索
        if result:
            print(f"✓ 输入: {message}")
            print(f"   触发搜索: {result.get('status', 'N/A')}")
            print()
        else:
            print(f"✗ 输入: {message}")
            print(f"   未触发搜索")
            print()


def test_comprehensive():
    """综合测试"""
    print("=" * 60)
    print("测试3: 综合场景测试")
    print("=" * 60)
    
    test_cases = [
        "北京市朝阳区附近找餐厅",
        "深圳市南山区科技园附近的咖啡厅",
        "上海浦东新区陆家嘴地铁站附近的银行",
        "广州市天河区体育中心附近的酒店",
        "杭州西湖区附近的公园",
        "成都武侯区人民南路附近的停车场",
    ]
    
    builder = ChatChainBuilder()
    
    for message in test_cases:
        print(f"测试: {message}")
        result = builder._try_map_search(message)
        if result:
            print(f"  状态: {result.get('status', 'N/A')}")
            if result.get('results'):
                print(f"  找到 {len(result['results'])} 个结果")
                for i, place in enumerate(result['results'][:3], 1):
                    print(f"  {i}. {place.get('name', '未知')} - {place.get('address', '未知')}")
        else:
            print("  未触发搜索")
        print()


if __name__ == "__main__":
    test_address_extraction()
    print("\n")
    test_place_type_detection()
    print("\n")
    test_comprehensive()
    print("\n所有测试完成!")
