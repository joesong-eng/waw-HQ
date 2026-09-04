# HQ 裁決：waw-business 去留決策

時間：2026-08-31
裁決者：HQ
執行者：Ina

---

## 裁決：選項 A — 繼續維持，補上部署

waw-business（PROJECT/Owner，Sophie 負責）是現行主要商戶後台，必須部署。
不退役，理由如下。

---

## 釐清現況認知

Ina 發現 iot.tg25.win 實際跑的是 waw-iot，這個觀察需要確認：

請 Ina 執行以下指令再回報：

  ssh yd174
  sudo nginx -T 2>/dev/null | grep -E "root|server_name|proxy_pass" | head -30
  ls /var/www/waw-iot/public 2>/dev/null | head -5
  ls /www/wwwroot/iot.tg25.win/public 2>/dev/null | head -5

---

## 背景說明

V9_SYSTEM_SPLITTING_DESIGN.md 描述的是「計劃中的拆分架構」，
目前系統實際上仍是單一 Laravel 專案（waw-core/waw-business），
尚未完成物理拆分。

現實狀態：
  waw-business（PROJECT/Owner）= 實際提供服務的商戶後台
  waw-iot = Infra 的 Python/MQTT 採集後端，在不同路徑
  兩者不是互相取代，而是各自負責不同層

這是 HQ 的統一立場：
  iot.tg25.win 應該跑的是 waw-business（Laravel）
  若 Ina 發現 nginx 指向 waw-iot，可能是路徑別名問題或早期設定，需確認

---

## Ina 的任務

1. 執行上方 nginx 確認指令，把實際結果回報 HQ
2. 確認 /www/wwwroot/iot.tg25.win 目錄是否存在、是否有 Laravel artisan 檔案
3. 不需要做任何部署動作，先回報現況

HQ 拿到確認結果後，若真的沒部署，會派任務給 Sophie 協同 Ina 補上。

---

HQ 指令：先確認，不要動，等回報。
