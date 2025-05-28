# AI 市民助手 LINE Bot

這是一個基於 LINE Bot 平台的智能市民助手，整合了多種功能，包括天氣查詢、新聞資訊、交通資訊、旅遊建議等。

## 功能特點

- 🌤️ 天氣查詢：支援台灣地區天氣資訊查詢
- 📰 新聞資訊：提供最新台灣新聞
- 🚗 交通資訊：即時交通狀況查詢
- 🏞️ 旅遊建議：景點推薦和旅遊資訊
- 🌡️ 環境監測：室內環境數據監測
- 💬 智能對話：基於 Gemini AI 的自然語言互動

## 技術

- Python 3.8+
- Flask
- LINE Bot SDK
- Google Maps API
- Gemini AI API
- Firebase
- OpenWeatherMap API
- NewsAPI

## 安裝步驟

1. Clone Project
```bash
git clone [your-repository-url]
cd linebot-project
```

2. 建立虛擬環境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安裝依賴套件
```bash
pip install -r requirements.txt
```

4. 設定環境變數
建立 `.env` 檔案並設定以下環境變數：
```env
# LINE Bot 設定
LINE_CHANNEL_SECRET=你的_line_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=你的_line_channel_access_token

# API 金鑰
WEATHER_API_KEY=你的_openweathermap_api_key
NEWS_API_KEY=你的_newsapi_key
Maps_API_KEY=你的_Maps_api_key
GEMINI_API_KEY=你的_gemini_api_key

# Firebase 設定
FIREBASE_CREDENTIALS_PATH=你的_firebase_憑證檔案路徑.json
```

## 執行專案

```bash
python app.py
```

## 環境變數說明

- `LINE_CHANNEL_SECRET`: LINE Bot 的 Channel Secret
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Bot 的 Channel Access Token
- `WEATHER_API_KEY`: OpenWeatherMap API 金鑰
- `NEWS_API_KEY`: NewsAPI 金鑰
- `GOOGLE_MAPS_API_KEY`: Google Maps API 金鑰
- `GEMINI_API_KEY`: Google Gemini AI API 金鑰
- `FIREBASE_CREDENTIALS_PATH`: Firebase 服務帳號金鑰檔案路徑

## 安全注意事項

1. 永遠不要將  `.env` 檔案提交到版本控制系統
2. 確保  `firebase_credentials.json` 檔案安全儲存
3. 定期輪換 API 金鑰
4. 使用環境變數而非寫死在程式碼中的金鑰

## API 使用限制

- Google Maps API: 每日 1000 次請求
- OpenWeatherMap API: 每分鐘 60 次請求
- NewsAPI: 每日 100 次請求
- Gemini AI API: 每分鐘 60 次請求

## 貢獻指南

1. Fork 專案
2. 建立特性分支 (git checkout -b feature/AmazingFeature)
3. 提交變更 (git commit -m 'Add some AmazingFeature')
4.推送到分支 (git push origin feature/AmazingFeature)
5. 建立 Pull Request

## 授權條款

MIT License

## 聯絡方式

[Yoga Liang] - [ch993115@gmail.com] 
