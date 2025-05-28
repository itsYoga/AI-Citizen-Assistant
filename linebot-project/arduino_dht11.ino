// #include "DHT.h"
// #include <ArduinoJson.h>
// #include <WiFiNINA.h>

// #define DHTPIN 10
// #define DHTTYPE DHT11

// // WiFi 設定
// char ssid[] = "Jesse";        // 你的 WiFi 名稱
// char pass[] = "00000000";        // 你的 WiFi 密碼
// int status = WL_IDLE_STATUS;        // WiFi 狀態

// // LINE Bot 設定
// const char* server = "192.168.121.84";  // 使用 Flask 應用程式的 IP 地址
// int port = 5001;                 // Flask 應用程式的端口

// // 初始化感測器和 WiFi
// DHT dht(DHTPIN, DHTTYPE);
// WiFiClient client;

// void printWifiStatus() {
//   // 印出 WiFi 狀態
//   Serial.print("SSID: ");
//   Serial.println(WiFi.SSID());

//   // 印出你的 IP 位址
//   IPAddress ip = WiFi.localIP();
//   Serial.print("IP 位址: ");
//   Serial.println(ip);

//   // 印出訊號強度
//   long rssi = WiFi.RSSI();
//   Serial.print("訊號強度 (RSSI):");
//   Serial.print(rssi);
//   Serial.println(" dBm");
// }

// void setup() {
//   Serial.begin(9600);
//   while (!Serial) {
//     ; // 等待序列埠連接
//   }

//   // 檢查 WiFi 模組
//   if (WiFi.status() == WL_NO_MODULE) {
//     Serial.println("WiFi 模組未找到！");
//     while (true); // 不要繼續
//   }

//   // 嘗試連接到 WiFi
//   while (status != WL_CONNECTED) {
//     Serial.print("嘗試連接到 WiFi 網路: ");
//     Serial.println(ssid);
//     status = WiFi.begin(ssid, pass);
//     delay(10000); // 等待 10 秒
//   }
//   Serial.println("已連接到 WiFi");
//   printWifiStatus();

//   // 初始化 DHT 感測器
//   dht.begin();
//   Serial.println("DHT11 溫濕度感測器測試");
// }

// void loop() {
//   delay(2000); // 等待 2 秒

//   float humidity = dht.readHumidity();
//   float temperature_c = dht.readTemperature();

//   if (isnan(humidity) || isnan(temperature_c)) {
//     Serial.println("讀取 DHT11 感測器失敗！");
//     return;
//   }

//   // 創建 JSON 文檔
//   StaticJsonDocument<200> doc;
//   doc["humidity"] = humidity;
//   doc["temperature"] = temperature_c;
//   doc["timestamp"] = millis();

//   // 序列化 JSON
//   String jsonString;
//   serializeJson(doc, jsonString);

//   Serial.println("正在發送數據到伺服器...");
//   Serial.println(jsonString);

//   // 連接到伺服器
//   Serial.print("正在連接到伺服器: ");
//   Serial.print(server);
//   Serial.print(":");
//   Serial.println(port);
  
//   if (client.connect(server, port)) {
//     Serial.println("已連接到伺服器");
    
//     // 發送 HTTP 請求
//     String request = "POST /sensor-data HTTP/1.1\r\n";
//     request += "Host: " + String(server) + ":" + String(port) + "\r\n";
//     request += "Content-Type: application/json\r\n";
//     request += "Content-Length: " + String(jsonString.length()) + "\r\n";
//     request += "Connection: close\r\n";
//     request += "\r\n";
//     request += jsonString;
    
//     Serial.println("發送請求:");
//     Serial.println(request);
    
//     client.print(request);
    
//     // 等待伺服器回應
//     unsigned long timeout = millis();
//     while (client.available() == 0) {
//       if (millis() - timeout > 5000) {
//         Serial.println(">>> 客戶端超時！");
//         client.stop();
//         return;
//       }
//     }
    
//     // 讀取回應
//     Serial.println("伺服器回應:");
//     while (client.available()) {
//       char c = client.read();
//       Serial.write(c);
//     }
//     Serial.println();
    
//     // 關閉連接
//     client.stop();
//     Serial.println("連接已關閉");
//   } else {
//     Serial.println("連接失敗");
//     Serial.println("錯誤代碼: " + String(client.status()));
    
//     // 檢查 WiFi 連接狀態
//     if (WiFi.status() != WL_CONNECTED) {
//       Serial.println("WiFi 連接已斷開。正在重新連接...");
//       status = WL_IDLE_STATUS;
//       while (status != WL_CONNECTED) {
//         status = WiFi.begin(ssid, pass);
//         delay(5000);
//       }
//       Serial.println("已重新連接到 WiFi");
//       printWifiStatus();
//     }
//   }

//   // 在序列監視器顯示數據
//   Serial.print("濕度: ");
//   Serial.print(humidity);
//   Serial.print("%  溫度: ");
//   Serial.print(temperature_c);
//   Serial.println(" °C");
// } 