# 用戶身份驗證標準 (User Identity Validation Standard)


**[On-Demand]** — 上下文注入策略

> **版本**：v1.0  
> **建立日期**：2026-06-18  
> **狀態**：Draft / 待實施  
> **編寫角色**：HQ (Hera)

為防止用戶在錯誤的系統中註冊，導致業務邏輯混亂與安全風險，特制定此用戶身份驗證標準。

---

## 一、系統角色定義

### Owner 系統 (iot.tg25.win)
- **用戶類型**：客戶
- **業務角色**：購買機器設備的店家、場地主、機台主
- **權限範圍**：管理自己的機台、查看營收、設定分潤

### Alliance 系統 (ali.tg25.win)  
- **用戶類型**：盟友
- **業務角色**：供應商、代理商、合作夥伴
- **權限範圍**：管理代理商品、查看分潤報表、客戶介紹

---

## 二、身份驗證規則

### 註冊前驗證
1. **Email 域名檢查**：
   - Alliance 用戶應使用企業域名 (非 @gmail.com 等個人域名)
   - Owner 用戶可使用個人域名

2. **邀請碼機制**：
   - Alliance 註冊需要邀請碼
   - Owner 註冊開放或透過推薦

3. **身份確認文件**：
   - Alliance 需提供營業登記證明
   - Owner 需提供場地相關證明

### 系統間隔離檢查
```sql
-- 檢查是否有跨系統重複註冊
SELECT email FROM iotv9.users 
WHERE email IN (
  SELECT email FROM alliance_db.users
);
```

---

## 三、實施方案

### Phase 1：立即修正 (本週完成)
- [ ] 審查現有用戶身份
- [ ] 移除錯置用戶或調整權限
- [ ] 建立跨系統重複檢查

### Phase 2：機制建立 (下週完成)
- [ ] 實施註冊前身份驗證
- [ ] 建立邀請碼系統
- [ ] 加強 Email 域名驗證

### Phase 3：長期監控 (持續進行)
- [ ] 定期跨系統身份審查
- [ ] 異常註冊自動警報
- [ ] 用戶行為模式分析

---

## 四、技術實施

### 註冊前檢查 API
```php
// 檢查 Email 是否已在其他系統註冊
public function checkCrossSystemEmail($email) {
    // 呼叫其他系統 API 檢查
    $response = Http::withHeaders([
        'X-Internal-Key' => env('INTERNAL_KEY')
    ])->get('https://ali.tg25.win/api/internal/check-email', [
        'email' => $email
    ]);
    
    return $response->json();
}
```

### 跨系統通知機制
當用戶在一個系統註冊時，自動通知其他系統避免重複註冊。

---

## 🔗 文件神經連結

### 強關聯（必讀）
- `01_agent_governance/INCIDENT_LOG_20260618.md` - 觸發此標準的安全事件記錄
- `03_system_architecture_designs/WAW_2.0_ARCHITECTURE_SPEC.md` - 系統架構與資料庫隔離設計

### 中關聯（建議讀）
- `TECHNICAL_NAMING_AND_PAYLOAD_STANDARD.md` - API 呼叫標準
- `04_ops_and_deployments/INFRASTRUCTURE_REFERENCE.md` - 系統部署參考

---

**維護者**：HQ (協調者)  
**實施負責**：Sophie (Owner), Allie (Alliance)  
**最後更新**：2026-06-18
