import requests
from typing import Optional
from langchain_core.tools import tool


@tool
def search_nearby_places(
    query: str,
    location: str = "",
    radius: int = 2000
) -> str:
    """
    搜索指定位置附近的地点。当用户询问附近的某个地点时调用此工具。
    
    Args:
        query: 搜索关键词，如 "餐厅"、"ATM机"、"加油站"、"酒店"
        location: 地址信息，如 "北京"、"朝阳区"、"深圳市龙华区"。如果为空则基于query智能搜索
        radius: 搜索半径(米)，默认2000米
    
    Returns:
        格式化后的搜索结果字符串
    """
    from config.settings import get_settings
    
    settings = get_settings()
    ak = settings.baidu_map_ak
    
    base_url = "https://api.map.baidu.com/place/v2/search"
    
    # 判断location是经纬度还是地址
    is_coordinate = location and "," in location and location.replace(",", "").replace(".", "").isdigit()
    
    if is_coordinate:
        # 使用圆形区域检索(经纬度)
        params = {
            "query": query,
            "location": location,  # 经纬度: "纬度,经度"
            "ak": ak,
            "output": "json",
            "radius": radius,
            "scope": 2  # 返回详细信息
        }
    else:
        # 使用城市内检索(地址)
        params = {
            "query": query,
            "region": location if location else "全国",
            "ak": ak,
            "output": "json",
            "scope": 2  # 返回详细信息
        }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # 格式化返回结果
        if result.get("status") == 0 and result.get("results"):
            places = result["results"]
            output = f"找到{len(places)}个{query}:\n\n"
            for i, place in enumerate(places[:5], 1):  # 最多显示5个结果
                output += f"{i}. {place.get('name', '未知')}\n"
                output += f"   地址: {place.get('address', '未知')}\n"
                if place.get('telephone'):
                    output += f"   电话: {place['telephone']}\n"
                if place.get('detail_info', {}).get('overall_rating'):
                    output += f"   评分: {place['detail_info']['overall_rating']}\n"
                output += "\n"
            return output
        else:
            return f"未找到附近的{query}。"
            
    except requests.exceptions.RequestException as e:
        return f"搜索失败: {str(e)}"


def search_nearby(
    query: str,
    location: str,
    ak: str,
    tag: Optional[str] = None,
    radius: int = 2000,
    output: str = "json"
) -> dict:
    """
    搜索指定位置附近的地点 (旧版兼容接口)
    
    Args:
        query: 搜索关键词，如 "餐厅"、"ATM机"、"加油站"
        location: 地址或经纬度，如 "北京"、"朝阳区" 或 "39.915,116.404"
        ak: 百度地图API密钥
        tag: 可选的标签过滤，如 "银行"、"美食"
        radius: 搜索半径(米)，默认2000米
        output: 输出格式，默认json
    
    Returns:
        包含搜索结果的字典
    """
    base_url = "https://api.map.baidu.com/place/v2/search"
    
    # 判断location是经纬度还是地址
    is_coordinate = "," in location and location.replace(",", "").replace(".", "").isdigit()
    
    if is_coordinate:
        # 使用圆形区域检索(经纬度)
        params = {
            "query": query,
            "location": location,  # 经纬度: "纬度,经度"
            "ak": ak,
            "output": output,
            "radius": radius,
            "scope": 2  # 返回详细信息
        }
    else:
        # 使用城市内检索(地址)
        params = {
            "query": query,
            "region": location,
            "ak": ak,
            "output": output,
            "scope": 2  # 返回详细信息
        }
    
    if tag:
        params["tag"] = tag
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "status": -1,
            "message": f"请求失败: {str(e)}",
            "results": []
        }


def search_nearby_restaurants(
    location: str,
    ak: str,
    cuisine: Optional[str] = None,
    radius: int = 2000
) -> dict:
    """
    搜索指定位置附近的餐厅(便捷方法)
    
    Args:
        location: 地址或经纬度
        ak: 百度地图API密钥
        cuisine: 可选的菜系，如 "川菜"、"粤菜"
        radius: 搜索半径(米)，默认2000米
    
    Returns:
        包含餐厅列表的字典
    """
    return search_nearby(
        query="餐厅",
        location=location,
        ak=ak,
        tag=cuisine,
        radius=radius
    )
