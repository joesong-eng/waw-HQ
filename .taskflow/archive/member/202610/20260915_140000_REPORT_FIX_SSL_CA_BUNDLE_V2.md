# 任務回報：20260915_MINA_FIX_SSL_CA_BUNDLE（修正版）

**完成時間**：2026-09-15 14:00
**執行者**：mina
**性質**：修正之前錯誤的「已完成」報告

---

## ⚠️ 前次報告更正

前次報告（20260915_132000）聲稱 SSL CA Bundle 已修復。**這是錯誤的**。

前次測試方式有缺陷：只測試了不帶 CURLOPT_RESOLVE 的場景（自然能通過 Cloudflare SSL），沒有測試 Laravel 應用實際使用 CURLOPT_RESOLVE 的場景。

遠端日誌顯示 cURL error 60 從 09/15 05:10 起持續大量出現，從未停止。

---

## 真正的根因

| 測試場景 | CURLOPT_RESOLVE | verify | 結果 |
|:---|:---|:---|:---|
| 不使用 resolve | DNS 正常解析 | true | **200 ✅** |
| 使用 resolve（→141.148.165.50） | 直連 origin IP | true | **cURL error 60 ❌** |

`CURLOPT_RESOLVE` 把請求指向 Infra 伺服器原始 IP（141.148.165.50）。Cloudflare Flexible SSL 模式下，origin server 使用 Cloudflare 提供的憑證。直接連 origin IP 時 SNI 不匹配，SSL 驗證失敗。

## 修復方式

在遠端 .env 設定 `INFRA_RESOLVE_IP=`（空值），跳過 CURLOPT_RESOLVE，讓 DNS 正常解析通過 Cloudflare。

```bash
ssh yd177 "cd /www/wwwroot/win.tg25.win && echo 'INFRA_RESOLVE_IP=' >> .env"
ssh yd177 "cd /www/wwwroot/win.tg25.win && php artisan config:clear && php artisan cache:clear"
```

## 驗證結果

| 測試項 | 結果 |
|:---|:---|
| curl 不帶 resolve → Infra API | 200 ✅ |
| 從 VPS curl → Infra API | 200 ✅ |
| Laravel tinker DeviceController::infraHttp() | 200 ✅ |
| 遠端日誌新 cURL error 60 計數 | 0 ✅ |
| app:check-offline-sessions cron | 正常執行 ✅ |

## 結論
✅ 已修復（本次為真正的修復）

---
**回報者**：mina
**回報時間**：2026-09-15 14:00
