# HQ 裁決：關於 waw-business 部署現況澄清

時間：2026-08-31
裁決者：HQ
執行者：Ina

---

## 最終裁決：維持現狀（已在線上正常運行）

Ina，經 HQ 直接連線 VPS (129.153.116.174) 查核：

### 1. 實際現況查證
- 伺服器路徑：/www/wwwroot/iot.tg25.win
- Git Remote：https://github.com/joesong-eng/waw-business.git
- 當前 Commit：8e33952 (完全與本地 PROJECT/Owner 同步)
- Nginx 設定：server_name iot.tg25.win; root /www/wwwroot/iot.tg25.win/public;

### 2. 誤會原因說明
- 伺服器網站根目錄是在 /www/wwwroot/，而非 /var/www/。
- waw-business（商戶後台）一直都在線上運作，提供 iot.tg25.win 服務。

### 3. Ina 接下來的動作
1. 不需要建置新環境，也不做退役。
2. 請更新 Infra 的知識庫與路徑清單：
   - Sophie (Owner/waw-business) 線上路徑：/www/wwwroot/iot.tg25.win
   - 伺服器：yd174 (129.153.116.174:39022)
3. SignalHub Migration 既已在 iotv9 執行成功，請回報最終狀態並結案。

---
HQ 指示：確認事實，維持現行架構正常運維。
