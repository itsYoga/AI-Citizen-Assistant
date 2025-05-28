import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
from functools import lru_cache
import time

load_dotenv()

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini API 配置
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY 未在環境變數中找到")
    model = None
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        logger.info("Gemini API 初始化成功")
    except Exception as e:
        logger.error(f"初始化 Gemini API 時發生錯誤: {e}")
        model = None

# 重試裝飾器
def retry_on_error(max_retries=3, delay=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if model is None:
                return "抱歉，AI 服務暫時無法使用。"
                
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"重試 {max_retries} 次後失敗: {e}")
                        return "抱歉，AI 服務暫時無法使用，請稍後再試。"
                    logger.warning(f"第 {attempt + 1} 次嘗試失敗: {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@retry_on_error()
@lru_cache(maxsize=100)
def generate_text(prompt, temperature=0.7):
    """生成文字回應"""
    if model is None:
        return "抱歉，AI 服務暫時無法使用。"
        
    try:
        # 添加系統提示，確保使用繁體中文
        system_prompt = """請使用繁體中文回應，並以友善、專業的市民助理身份回答。
請注意以下幾點：
1. 保持友善和專業的語氣
2. 回答要簡潔明瞭
3. 如果是問候語，要熱情回應
4. 如果是問題，要給出實用的建議"""
        
        full_prompt = f"{system_prompt}\n\n使用者訊息：{prompt}"
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                top_p=0.8,
                top_k=40,
                max_output_tokens=1024,
            )
        )
        
        if not response.text:
            return "您好！我是 AI 市民助理，很高興為您服務。"
            
        return response.text
    except Exception as e:
        logger.error(f"生成文字時發生錯誤: {e}")
        return "您好！我是 AI 市民助理，很高興為您服務。"

@retry_on_error()
def report_environment_data(data):
    """生成環境數據報告"""
    if model is None:
        return "抱歉，AI 服務暫時無法使用。"
        
    try:
        prompt = f"""請根據以下環境數據生成一份簡要報告：
溫度：{data.get('temperature', 'N/A')}°C
濕度：{data.get('humidity', 'N/A')}%

請以市民助理的身份，用簡潔的語言說明當前環境狀況，並給出適當的建議。"""
        
        return generate_text(prompt, temperature=0.5)
    except Exception as e:
        logger.error(f"生成環境報告時發生錯誤: {e}")
        return "抱歉，無法生成環境報告，請稍後再試。"

@retry_on_error()
def analyze_user_sentiment(text):
    """分析使用者情緒"""
    if model is None:
        return "抱歉，AI 服務暫時無法使用。"
        
    try:
        prompt = f"""請分析以下使用者訊息的情緒傾向：
"{text}"

請以市民助理的身份，簡要說明使用者可能的情緒狀態，並給出適當的回應建議。"""
        
        return generate_text(prompt, temperature=0.3)
    except Exception as e:
        logger.error(f"分析情緒時發生錯誤: {e}")
        return "抱歉，無法分析情緒，請稍後再試。"

@retry_on_error()
def generate_help_message():
    """生成幫助訊息"""
    if model is None:
        return """您好！我是 AI 市民助理，我可以為您提供以下服務：
1. 天氣查詢：輸入「天氣」或「台北天氣」等
2. 新聞資訊：輸入「新聞」或「最新新聞」
3. 交通資訊：輸入「交通」或「台北交通」
4. 旅遊建議：輸入「景點」或「台北景點」
5. 環境狀況：輸入「環境」或「空氣品質」
6. 一般對話：直接輸入您想說的話

目前 AI 對話功能暫時無法使用，但其他功能都可以正常使用。"""
        
    try:
        prompt = """請以市民助理的身份，生成一份簡潔的幫助訊息，說明我可以提供的服務：
1. 天氣查詢
2. 新聞資訊
3. 交通資訊
4. 旅遊建議
5. 環境狀況
6. 一般對話

請用友好的語氣說明如何使用這些功能。"""
        
        return generate_text(prompt, temperature=0.5)
    except Exception as e:
        logger.error(f"生成幫助訊息時發生錯誤: {e}")
        return "抱歉，無法生成幫助訊息，請稍後再試。"