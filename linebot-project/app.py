from flask import Flask, request, abort, jsonify
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from functools import wraps
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import time

# Import custom modules
import gemini_service
import firebase_service
import services

load_dotenv()

app = Flask(__name__)

# 配置日志
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('AI市民助手啟動')

def millis():
    return int(time.time() * 1000)

# LINE Bot configuration
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    app.logger.error("Error: LINE_CHANNEL_SECRET or LINE_CHANNEL_ACCESS_TOKEN not found in .env")
    exit()

handler = WebhookHandler(LINE_CHANNEL_SECRET)
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)

# Global variable to store Arduino data
latest_arduino_data = {
    'temperature': None,
    'humidity': None,
    'timestamp': None
}

# 错误处理装饰器
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            app.logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500
    return decorated_function

@app.route("/webhook", methods=['POST'])
@handle_errors
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    except Exception as e:
        app.logger.error(f"Error handling request: {e}")
        abort(500)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text
    reply_text = "抱歉，我不明白您的意思。"  # Default response

    try:
        # 檢查消息類型並處理
        if user_message.lower() == "arduino":
            if latest_arduino_data['temperature'] is not None and latest_arduino_data['humidity'] is not None:
                reply_text = f"""
感測器數據：
溫度：{latest_arduino_data['temperature']}°C
濕度：{latest_arduino_data['humidity']}%

最後更新時間：{latest_arduino_data['timestamp']}
"""
            else:
                reply_text = "目前尚未收到 Arduino 感測器的數據。"
                
        elif "天氣" in user_message or "天气" in user_message:
            location = "台北"  # Default location
            # 提取城市名称
            if "天氣" in user_message:
                parts = user_message.split("天氣")
                if len(parts) > 1 and parts[0].strip():
                    location = parts[0].strip()
            elif "天气" in user_message:
                parts = user_message.split("天气")
                if len(parts) > 1 and parts[0].strip():
                    location = parts[0].strip()
            
            app.logger.info(f"查询天气信息，地点：{location}")
            reply_text = services.get_weather(location)
            
        elif "新聞" in user_message or "新闻" in user_message:
            category = "general"
            if "科技" in user_message:
                category = "technology"
            elif "運動" in user_message or "运动" in user_message:
                category = "sports"
            elif "娛樂" in user_message or "娱乐" in user_message:
                category = "entertainment"
            reply_text = services.get_news(category)
            
        elif "交通" in user_message:
            location = "台北"
            if "交通" in user_message and len(user_message.split("交通")) > 1:
                location = user_message.split("交通")[0].strip()
            reply_text = services.get_traffic_info(location)
            
        elif "旅遊" in user_message or "景点" in user_message or "景點" in user_message:
            location = "台北"
            if "旅遊" in user_message and len(user_message.split("旅遊")) > 1:
                location = user_message.split("旅遊")[0].strip()
            elif "景点" in user_message and len(user_message.split("景点")) > 1:
                location = user_message.split("景点")[0].strip()
            elif "景點" in user_message and len(user_message.split("景點")) > 1:
                location = user_message.split("景點")[0].strip()
            reply_text = services.get_travel_info(location)
            
        elif "環境狀況" in user_message or "室内数据" in user_message or "室內數據" in user_message:
            if latest_arduino_data['temperature'] is not None and latest_arduino_data['humidity'] is not None:
                reply_text = gemini_service.report_environment_data(latest_arduino_data)
            else:
                reply_text = "目前尚未收到环境感测器的数据。"
        else:
            # General conversation with Gemini
            reply_text = gemini_service.generate_text(f"使用者說：「{user_message}」。請以市民助理的身份自然地回應。")

    except Exception as e:
        app.logger.error(f"Error processing message: {e}")
        reply_text = "处理您的请求时发生内部错误，请稍后再试。"

    # Save conversation to Firebase
    try:
        firebase_service.save_conversation(user_id, user_message, reply_text)
    except Exception as e:
        app.logger.error(f"Error saving to Firebase: {e}")

    # Send reply through LINE Bot
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
        except Exception as e:
            app.logger.error(f"Error sending LINE reply: {e}")

@app.route("/arduino/data", methods=['POST'])
@handle_errors
def receive_arduino_data():
    global latest_arduino_data
    try:
        data = request.get_json()
        app.logger.info(f"Received Arduino data: {data}")
        if data and 'temperature' in data and 'humidity' in data:
            latest_arduino_data = {
                'temperature': data.get('temperature'),
                'humidity': data.get('humidity'),
                'timestamp': data.get('timestamp', millis())
            }
            app.logger.info(f"Updated latest_arduino_data: {latest_arduino_data}")
            return "Data received successfully", 200
        else:
            app.logger.warning("Invalid Arduino data received.")
            return "Invalid data", 400
    except Exception as e:
        app.logger.error(f"Error receiving Arduino data: {e}")
        return "Error processing data", 500

@app.route('/sensor-data', methods=['POST'])
def receive_sensor_data():
    global latest_arduino_data
    try:
        app.logger.info("Received request to /sensor-data endpoint")
        app.logger.info(f"Request headers: {dict(request.headers)}")
        app.logger.info(f"Request data: {request.get_data(as_text=True)}")
        
        data = request.get_json()
        app.logger.info(f"Received sensor data: {data}")
        
        if not data or 'humidity' not in data or 'temperature' not in data:
            app.logger.warning("Invalid data format received")
            return jsonify({'error': 'Invalid data format'}), 400

        latest_arduino_data = {
            'temperature': data.get('temperature'),
            'humidity': data.get('humidity'),
            'timestamp': data.get('timestamp', millis())
        }
        app.logger.info(f"Updated latest_arduino_data: {latest_arduino_data}")

        # 準備回應
        response = jsonify({'status': 'success', 'message': 'Data received successfully'})
        app.logger.info(f"Sending response: {response.get_data(as_text=True)}")
        return response

    except Exception as e:
        app.logger.error(f"Error processing sensor data: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True) 