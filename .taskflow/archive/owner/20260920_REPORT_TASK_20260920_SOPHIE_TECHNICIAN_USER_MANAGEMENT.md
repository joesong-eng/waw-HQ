# 回報：TASK_20260920_SOPHIE_TECHNICIAN_USER_MANAGEMENT

**回報時間**：2026-09-20
**執行者**：Sophie
**狀態**：✅ commit + push 完成，等 HQ 核准後 deploy

---

## Commit

```
bfb7b48  feat(users): technician account management (TASK_20260920_SOPHIE_TECHNICIAN_USER_MANAGEMENT)
```

Push 到 `origin/main`（waw-business）成功。

---

## 改動檔案（6 個）

| 檔案 | 改動說明 |
|---|---|
| `app/Http/Controllers/Iot/UserManagementController.php` | store() 接受 role/expires_at；index() 擋 technician；新增 destroy()；update() 允許 technician 改 expires_at |
| `app/Http/Middleware/CheckUserManagementAccess.php` | technician 加入封鎖清單 |
| `app/Http/Middleware/EnsureIotAccess.php` | technician redirect 到 signal.tg25.win 說明，JSON 回 403 |
| `app/Http/Controllers/Iot/Authv9Controller.php` | login() 接 isExpired() 擋過期帳號 |
| `routes/web.php` | 加 DELETE /users/{id} |
| `resources/views/iot/modules/m1/users.blade.php` | 角色下拉（員工/子代理/技術工程師）、效期欄、technician 刪除鈕、紫色 legend、expires 欄位 |

---

## 功能摘要

### 1. 建立帳號 POST /users
- `role` 必填，`in:staff,sub_agent,technician`
- `expires_at` 僅 technician 可帶，非 technician 帶 expires_at 回 422
- owner 建帳 root_id = 自己；admin 建帳需給 root_id（維持現況）
- 不再寫死 sub_agent

### 2. 列表
- owner：看 `root_id = 自己` 且 role in `staff, sub_agent, technician`
- admin：看全部
- technician/staff/sub_agent：index() redirect to profile

### 3. 刪除 DELETE /users/{id}
- 僅刪 technician
- owner 只刪 root_id = 自己的
- 不刪自己、不刪非 technician
- 硬刪（`$target->delete()`）；同一 email 可重開新帳

### 4. 更新 PUT /users/{id}
- technician 允許改 expires_at（null = 永不過期）
- role、root_id 禁改

### 5. 擋技術帳進營運後台
- EnsureIotAccess：technician redirect login 頁並帶 flash 說明（JSON → 403）
- CheckUserManagementAccess：technician 加入封鎖
- index()：technician 也 redirect profile

### 6. 過期帳號不可登入
- login() 在 Auth::attempt 成功後立即呼叫 isExpired()
- 過期 → logout + 錯誤訊息「帳號已過期，請聯絡機台主重新開立。」

### 7. UI
- 新增 Modal：角色下拉（預設員工）、選技術工程師顯效期日期輸入 + 說明文字
- 表格新增「效期」欄（技術工程師顯日期或「永久」，其他顯「—」）
- Legend 加紫色 ● 技術工程師
- 技術工程師列顯示紅色「刪除」按鈕，二次確認含姓名/信箱
- 技術工程師名稱顯示 violet 色

---

## 驗證（等 HQ deploy 後需遠端確認）

1. owner 登入 /users，新增技術工程師 → DB 確認 role=technician, expires_at, root_id
2. 新增員工 → role=staff（不再默寫 sub_agent）
3. 列表見技術工程師；刪除後消失（硬刪，email 可重用）
4. 技術帳登 iot.tg25.win → redirect login 頁，flash 提示前往 signal.tg25.win
5. expires_at 設過去時間 → 登入失敗「帳號已過期」
6. owner 不能刪別人 technician；不能刪 staff

---

## 注意事項

- **本單未 deploy**，等 HQ 核准後執行 `../../dev_tools/waw_ops.sh deploy owner`
- 軟刪策略：本單使用硬刪（`delete()`）；若未來需軟刪請在 User model 加 `SoftDeletes` 並補 migration
- 無新 migration、未改 ENUM（遵守工單限制）

