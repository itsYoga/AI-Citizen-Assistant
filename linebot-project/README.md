# AI 市民助手 LINE Bot

这是一个基于 LINE Bot 平台的智能市民助手，集成了多种功能，包括天气查询、新闻资讯、交通信息、旅游建议等。

## 功能特点

- 🌤️ 天气查询：支持台湾地区天气信息查询
- 📰 新闻资讯：提供最新台湾新闻
- 🚗 交通信息：实时交通状况查询
- 🏞️ 旅游建议：景点推荐和旅游信息
- 🌡️ 环境监测：室内环境数据监测
- 💬 智能对话：基于 Gemini AI 的自然语言交互

## 技术栈

- Python 3.8+
- Flask
- LINE Bot SDK
- Google Maps API
- Gemini AI API
- Firebase
- OpenWeatherMap API
- NewsAPI

## 安装步骤

1. 克隆项目
```bash
git clone [your-repository-url]
cd linebot-project
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
创建 `.env` 文件并配置以下环境变量：
```env
# LINE Bot 配置
LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token

# API Keys
WEATHER_API_KEY=your_openweathermap_api_key
NEWS_API_KEY=your_newsapi_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
GEMINI_API_KEY=your_gemini_api_key

# Firebase 配置
FIREBASE_CREDENTIALS_PATH=path_to_your_firebase_credentials.json
```

## 运行项目

```bash
python app.py
```

## 环境变量说明

- `LINE_CHANNEL_SECRET`: LINE Bot 的 Channel Secret
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Bot 的 Channel Access Token
- `WEATHER_API_KEY`: OpenWeatherMap API 密钥
- `NEWS_API_KEY`: NewsAPI 密钥
- `GOOGLE_MAPS_API_KEY`: Google Maps API 密钥
- `GEMINI_API_KEY`: Google Gemini AI API 密钥
- `FIREBASE_CREDENTIALS_PATH`: Firebase 服务账号密钥文件路径

## 安全注意事项

1. 永远不要将 `.env` 文件提交到版本控制系统
2. 确保 `firebase_credentials.json` 文件安全存储
3. 定期轮换 API 密钥
4. 使用环境变量而不是硬编码的密钥

## API 使用限制

- Google Maps API: 每日 1000 次请求
- OpenWeatherMap API: 每分钟 60 次请求
- NewsAPI: 每日 100 次请求
- Gemini AI API: 每分钟 60 次请求

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

[Your Name] - [Your Email] 