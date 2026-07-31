# 用戶身份錯置清理與遷移計劃


**[On-Demand]** — 上下文注入策略

> **計劃版本**：v1.0  
> **制定日期**：2026-06-18  
> **執行期限**：2026-06-20 (2天內完成)  
> **計劃狀態**：待執行  
> **負責協調**：HQ (Hera)

---

## 🎯 清理目標

### 立即目標
- 確認並處理 `david@tg25.win` 的身份錯置問題
- 檢查並修正其他可能的跨系統用戶錯置

### 長期目標  
- 建立用戶身份驗證機制，防止未來發生類似問題
- 確保業務邏輯清晰：客戶在 Owner 系統，盟友在 Alliance 系統

---

## 📋 執行步驟

### Phase 1：緊急調查 (今日完成)

#### Sophie 任務清單
- [ ] 登入 `https://iot.tg25.win` 管理後台
- [ ] 導出完整用戶列表並分析身份
- [ ] 特別確認 `david@tg25.win` 的註冊時間、權限、活動記錄
- [ ] 檢查是否有其他疑似盟友身份的用戶

#### Allie 任務清單  
- [ ] 檢查 `https://ali.tg25.win` 是否有 `david@tg25.win` 帳號
- [ ] 確認 Alliance 系統的完整用戶列表
- [ ] 檢查是否有疑似客戶身份的用戶錯誤註冊

### Phase 2：身份確認 (明日上午)

#### 跨系統比對
```sql
-- Sophie 執行：從 Owner 系統導出可疑用戶
SELECT id, email, name, created_at, last_login_at 
FROM users 
WHERE email LIKE '%@%.com' 
  AND email NOT LIKE '%@gmail.com'
  AND email NOT LIKE '%@yahoo.com'
ORDER BY created_at DESC;

-- Allie 執行：從 Alliance 系統導出用戶列表  
SELECT id, email, company_name, role_type, created_at
FROM users
ORDER BY created_at DESC;
```

#### 人工確認流程
1. **HQ 協調**：整合兩邊的用戶列表
2. **業務確認**：Joe 確認每個用戶的真實身份
3. **決策制定**：確定哪些用戶需要遷移或刪除

### Phase 3：清理執行 (明日下午)

#### 選項A：用戶遷移
- 如果 `david@tg25.win` 確實是盟友，從 Owner 系統刪除
- 協助他在 Alliance 系統重新註冊

#### 選項B：權限調整
- 如果他有雙重身份，調整權限設定
- 確保不會看到不該看的資料

#### 選項C：帳號清理
- 如果是無效帳號，直接刪除
- 保留審計日誌

---

## ⚠️ 安全注意事項

### 資料備份
```bash
# 執行任何刪除操作前，必須先備份
mysqldump -u root -p iotv9 users > users_backup_20260618.sql
mysqldump -u root -p alliance_db users > alliance_users_backup_20260618.sql
```

### 權限檢查
- 確保刪除用戶前，該用戶沒有關聯的重要業務資料
- 檢查機台擁有者關係、交易記錄等

### 通知機制
- 如需刪除用戶，必須提前通知當事人
- 提供帳號遷移或資料導出選項

---

## 📊 執行檢查清單

### 今日 (2026-06-18)
- [ ] Sophie 完成 Owner 系統用戶審查
- [ ] Allie 完成 Alliance 系統用戶審查  
- [ ] HQ 整合分析報告
- [ ] Joe 確認問題用戶身份

### 明日 (2026-06-19)
- [ ] 制定具體清理方案
- [ ] 通知相關用戶
- [ ] 執行清理操作
- [ ] 驗證清理結果

### 後日 (2026-06-20)  
- [ ] 實施身份驗證機制
- [ ] 建立定期審查流程
- [ ] 更新操作文檔

---

## 🔄 回報機制

### 每日回報
- Sophie 和 Allie 透過 HQ Message Hub 回報進度
- HQ 整合進度並通知 Joe

### 完成確認
- 所有清理操作必須經 Joe 最終確認
- 建立完整的操作記錄

---

**制定者**：HQ (Hera)  
**執行者**：Sophie, Allie  
**最終確認**：Joe  
**最後更新**：2026-06-18 08:11
