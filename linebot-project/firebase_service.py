import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
from functools import wraps
import time

load_dotenv()

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Firebase 配置
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-service-account-key.json')

# 初始化 Firebase
try:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase 初始化成功")
except Exception as e:
    logger.error(f"初始化 Firebase 時發生錯誤: {e}")
    raise

# 重試裝飾器
def retry_on_error(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"重試 {max_retries} 次後失敗: {e}")
                        raise
                    logger.warning(f"第 {attempt + 1} 次嘗試失敗: {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@retry_on_error()
def save_conversation(user_id, user_message, bot_response):
    """儲存對話記錄到 Firestore"""
    try:
        conversation_ref = db.collection('conversations').document()
        conversation_ref.set({
            'user_id': user_id,
            'user_message': user_message,
            'bot_response': bot_response,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        logger.info(f"已儲存使用者 {user_id} 的對話記錄")
    except Exception as e:
        logger.error(f"儲存對話記錄時發生錯誤: {e}")
        raise

@retry_on_error()
def get_user_conversations(user_id, limit=10):
    """獲取使用者的最近對話記錄"""
    try:
        conversations = db.collection('conversations')\
            .where('user_id', '==', user_id)\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .stream()
        
        return [doc.to_dict() for doc in conversations]
    except Exception as e:
        logger.error(f"獲取使用者對話記錄時發生錯誤: {e}")
        raise

@retry_on_error()
def save_environment_data(data):
    """儲存環境感測器數據"""
    try:
        data_ref = db.collection('environment_data').document()
        data_ref.set({
            **data,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        logger.info("環境數據儲存成功")
    except Exception as e:
        logger.error(f"儲存環境數據時發生錯誤: {e}")
        raise

@retry_on_error()
def get_latest_environment_data():
    """獲取最新的環境數據"""
    try:
        data = db.collection('environment_data')\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(1)\
            .stream()
        
        for doc in data:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"獲取最新環境數據時發生錯誤: {e}")
        raise

# 清理舊數據的函數
@retry_on_error()
def cleanup_old_data(days=30):
    """清理指定天數前的數據"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_timestamp = firestore.SERVER_TIMESTAMP
        
        # 清理對話記錄
        conversations = db.collection('conversations')\
            .where('timestamp', '<', cutoff_timestamp)\
            .stream()
        
        for doc in conversations:
            doc.reference.delete()
        
        # 清理環境數據
        env_data = db.collection('environment_data')\
            .where('timestamp', '<', cutoff_timestamp)\
            .stream()
        
        for doc in env_data:
            doc.reference.delete()
            
        logger.info(f"已清理 {days} 天前的舊數據")
    except Exception as e:
        logger.error(f"清理舊數據時發生錯誤: {e}")
        raise 