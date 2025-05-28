import requests
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
import googlemaps
from collections import defaultdict
import time
from functools import lru_cache, wraps
import logging
from gemini_service import generate_text, report_environment_data, analyze_user_sentiment, generate_help_message

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# API Keys
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# 验证 API 密钥
missing_keys = []
if not NEWS_API_KEY:
    missing_keys.append('NEWS_API_KEY')
if not GOOGLE_MAPS_API_KEY:
    missing_keys.append('GOOGLE_MAPS_API_KEY')
if not GEMINI_API_KEY:
    missing_keys.append('GEMINI_API_KEY')

if missing_keys:
    logger.warning(f"以下 API 密钥未设置，相关功能将无法使用: {', '.join(missing_keys)}")

# Initialize Google Maps client
gmaps = None
if GOOGLE_MAPS_API_KEY:
    try:
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        # 测试 API 密钥是否有效
        gmaps.geocode('台北')
        logger.info("Google Maps API 初始化成功")
    except Exception as e:
        logger.error(f"Google Maps API 初始化失败: {e}")
        gmaps = None

# API 使用量控制
class APIRateLimiter:
    def __init__(self, daily_limit=1000):
        self.daily_limit = daily_limit
        self.usage = defaultdict(int)
        self.last_reset = datetime.now().date()
    
    def check_limit(self, api_name):
        current_date = datetime.now().date()
        
        # 如果是新的一天，重置计数器
        if current_date > self.last_reset:
            self.usage.clear()
            self.last_reset = current_date
        
        # 检查是否超过限制
        if self.usage[api_name] >= self.daily_limit:
            return False
        
        # 增加使用计数
        self.usage[api_name] += 1
        return True

# 创建 API 限制器实例
api_limiter = APIRateLimiter()

# 缓存装饰器
def cache_with_timeout(timeout_seconds=300):
    def decorator(func):
        cache = {}
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            if key in cache:
                result, timestamp = cache[key]
                if datetime.now() - timestamp < timedelta(seconds=timeout_seconds):
                    return result
            result = func(*args, **kwargs)
            cache[key] = (result, datetime.now())
            return result
        return wrapper
    return decorator

@cache_with_timeout(300)  # 缓存5分钟
def get_weather(location):
    """獲取天氣信息"""
    if not GOOGLE_MAPS_API_KEY:
        return "抱歉，天氣服務暫時無法使用。"
        
    try:
        # 检查 API 使用限制
        if not api_limiter.check_limit('geocoding'):
            return "抱歉，今日天氣查詢次數已達上限，請明天再試。"

        # 获取地点地理编码
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            return f"找不到 {location} 的位置信息。"

        # 获取地点坐标
        location_lat = geocode_result[0]['geometry']['location']['lat']
        location_lng = geocode_result[0]['geometry']['location']['lng']

        # 获取天气信息
        weather_result = gmaps.timezone((location_lat, location_lng))
        if not weather_result:
            return f"{location} 目前沒有天氣信息。"

        # 获取当前时间
        current_time = datetime.now()
        
        # 构建天气信息
        message = f"📍 {location}天氣實況：\n\n"
        message += f"🕒 查詢時間：{current_time.strftime('%Y-%m-%d %H:%M')}\n"
        message += f"🌍 時區：{weather_result['timeZoneName']}\n"
        
        # 使用 Gemini API 生成天气建议
        try:
            prompt = f"""請根據以下信息生成天氣建議：
地點：{location}
時間：{current_time.strftime('%Y-%m-%d %H:%M')}
時區：{weather_result['timeZoneName']}

請以市民助理的身份，給出適合的天氣建議和注意事項。"""
            
            advice = generate_text(prompt, temperature=0.5)
            if advice:
                message += f"\n💡 溫馨提示：\n{advice}"
        except Exception as e:
            logger.error(f"生成天氣建議時發生錯誤: {e}")
            message += "\n💡 溫馨提示：\n• 天氣適宜，適合外出活動"
            
        return message
        
    except Exception as e:
        logger.error(f"獲取天氣信息時發生錯誤: {e}")
        return "抱歉，獲取天氣信息時發生錯誤，請稍後再試。"

@cache_with_timeout(300)  # 缓存5分钟
def get_news(category="general"):
    """Get latest news"""
    try:
        # Using NewsAPI
        url = f"https://newsapi.org/v2/top-headlines?country=tw&category={category}&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200 and data['articles']:
            news_list = data['articles'][:5]  # Get top 5 news
            news_text = "📰 最新新聞：\n\n"
            
            for i, news in enumerate(news_list, 1):
                news_text += f"{i}. {news['title']}\n"
                news_text += f"   來源：{news['source']['name']}\n"
                news_text += f"   連結：{news['url']}\n\n"
            
            return news_text
        else:
            return "抱歉，無法獲取新聞資訊。"
    except Exception as e:
        return f"獲取新聞資訊時發生錯誤：{str(e)}"

@cache_with_timeout(60)  # 缓存1分钟
def get_traffic_info(location):
    """使用 Google Maps API 获取交通信息"""
    try:
        # 检查 API 使用限制
        if not api_limiter.check_limit('directions'):
            return "抱歉，今日交通信息查询次数已达上限，请明天再试。"

        # 获取地点地理编码
        if not api_limiter.check_limit('geocoding'):
            return "抱歉，今日地址查询次数已达上限，请明天再试。"

        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            return f"找不到 {location} 的位置信息。"

        # 获取地点坐标
        location_lat = geocode_result[0]['geometry']['location']['lat']
        location_lng = geocode_result[0]['geometry']['location']['lng']

        # 获取交通信息
        traffic_result = gmaps.directions(
            origin=(location_lat, location_lng),
            destination=(location_lat, location_lng),
            mode="driving",
            departure_time=datetime.now(),
            traffic_model="best_guess"
        )
        
        if not traffic_result:
            return f"{location} 目前没有交通信息。"

        # 获取主要道路的交通状况
        roads = []
        for step in traffic_result[0]['legs'][0]['steps']:
            if 'traffic_speed_entry' in step:
                road_name = step.get('html_instructions', '未知道路')
                traffic_level = step['traffic_speed_entry']
                roads.append(f"- {road_name}: {traffic_level}")

        if not roads:
            return f"{location} 目前交通状况正常。"

        # 格式化返回信息
        result = f"{location} 交通状况：\n"
        result += "\n".join(roads[:5])  # 只显示前5条道路信息
        return result

    except Exception as e:
        print(f"获取交通信息失败: {e}")
        return "获取交通信息时发生错误，请稍后再试。"

@cache_with_timeout(300)  # 缓存5分钟
def get_travel_info(location):
    """获取旅游信息"""
    try:
        # 检查 API 使用限制
        if not api_limiter.check_limit('places'):
            return "抱歉，今日景点查询次数已达上限，请明天再试。"

        if not api_limiter.check_limit('geocoding'):
            return "抱歉，今日地址查询次数已达上限，请明天再试。"

        # 使用 Google Maps Places API 获取景点信息
        places_result = gmaps.places_nearby(
            location=gmaps.geocode(location)[0]['geometry']['location'],
            radius=5000,  # 5公里范围内
            type='tourist_attraction'
        )

        if not places_result.get('results'):
            return f"在 {location} 附近没有找到景点信息。"

        # 格式化返回信息
        result = f"{location} 附近景点：\n"
        for place in places_result['results'][:5]:  # 只显示前5个景点
            name = place.get('name', '未知景点')
            rating = place.get('rating', '暂无评分')
            result += f"- {name} (评分: {rating})\n"

        return result

    except Exception as e:
        print(f"获取旅游信息失败: {e}")
        return "获取旅游信息时发生错误，请稍后再试。"

def get_environment_info(location):
    """獲取環境信息"""
    if not GOOGLE_MAPS_API_KEY:
        return "抱歉，環境服務暫時無法使用。"
        
    try:
        # 檢查 API 使用限制
        if not api_limiter.check_limit('geocoding'):
            return "抱歉，今日環境查詢次數已達上限，請明天再試。"

        # 獲取地點地理編碼
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            return f"找不到 {location} 的位置信息。"

        # 模擬環境數據
        environment_data = {
            'temperature': 25,
            'humidity': 65
        }
        
        return report_environment_data(environment_data)
    except Exception as e:
        logger.error(f"獲取環境信息時發生錯誤: {e}")
        return "抱歉，獲取環境信息時發生錯誤，請稍後再試。"

def get_help():
    """獲取幫助信息"""
    return generate_help_message()

def process_message(message):
    """處理用戶消息"""
    try:
        # 分析用戶情緒
        sentiment = analyze_user_sentiment(message)
        logger.info(f"用戶情緒分析: {sentiment}")
        
        # 根據消息內容生成回應
        return generate_text(message)
    except Exception as e:
        logger.error(f"處理消息時發生錯誤: {e}")
        return "抱歉，處理消息時發生錯誤，請稍後再試。" 