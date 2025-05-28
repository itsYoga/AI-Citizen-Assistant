import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
from functools import wraps
import time

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Firebase 配置
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-service-account-key.json')

# 初始化 Firebase
try:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Firebase: {e}")
    raise

# 重试装饰器
def retry_on_error(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed after {max_retries} attempts: {e}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@retry_on_error()
def save_conversation(user_id, user_message, bot_response):
    """保存对话记录到 Firestore"""
    try:
        conversation_ref = db.collection('conversations').document()
        conversation_ref.set({
            'user_id': user_id,
            'user_message': user_message,
            'bot_response': bot_response,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        logger.info(f"Conversation saved for user {user_id}")
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        raise

@retry_on_error()
def get_user_conversations(user_id, limit=10):
    """获取用户的最近对话记录"""
    try:
        conversations = db.collection('conversations')\
            .where('user_id', '==', user_id)\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .stream()
        
        return [doc.to_dict() for doc in conversations]
    except Exception as e:
        logger.error(f"Error getting user conversations: {e}")
        raise

@retry_on_error()
def save_environment_data(data):
    """保存环境传感器数据"""
    try:
        data_ref = db.collection('environment_data').document()
        data_ref.set({
            **data,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        logger.info("Environment data saved successfully")
    except Exception as e:
        logger.error(f"Error saving environment data: {e}")
        raise

@retry_on_error()
def get_latest_environment_data():
    """获取最新的环境数据"""
    try:
        data = db.collection('environment_data')\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(1)\
            .stream()
        
        for doc in data:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error getting latest environment data: {e}")
        raise

# 清理旧数据的函数
@retry_on_error()
def cleanup_old_data(days=30):
    """清理指定天数前的数据"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_timestamp = firestore.SERVER_TIMESTAMP
        
        # 清理对话记录
        conversations = db.collection('conversations')\
            .where('timestamp', '<', cutoff_timestamp)\
            .stream()
        
        for doc in conversations:
            doc.reference.delete()
        
        # 清理环境数据
        env_data = db.collection('environment_data')\
            .where('timestamp', '<', cutoff_timestamp)\
            .stream()
        
        for doc in env_data:
            doc.reference.delete()
            
        logger.info(f"Cleaned up data older than {days} days")
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        raise 