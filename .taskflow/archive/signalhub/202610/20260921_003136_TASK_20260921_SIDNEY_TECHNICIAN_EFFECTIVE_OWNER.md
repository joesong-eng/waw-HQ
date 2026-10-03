# 任務：技術工程師登 signal.tg25.win，看到機台主的訊號設定，看不到營運帳務

**派工時間**：2026-09-21
**派工者**：HQ
**執行者**：Sidney
**優先級**：high
**前置（已完成，不要重做）**：
- Ina：`users.role` 已含 `technician`，`expires_at` 已在 `iotv9`，migration 冪等
- Sophie：`iot.tg25.win` 可開／刪技術工程師帳；該帳登 Owner **會被擋**（HQ 已獨立 curl 核過）
- Owner 與 SignalHub **共用** `iotv9.users`

**關聯**：Sophie 規格 `20260920_REPORT_TECH_OPERATOR_ROLE_SEPARATION_SPEC.md`

---

## 產品邊界（UI 用「技術工程師／機台主」，不要寫人名、暱稱）

| 系統 | 誰 | 做什麼 |
|---|---|---|
| `iot.tg25.win`（Sophie，已上） | 機台主 | 場地、一分多少錢、分潤；開／刪技術帳 |
| `signal.tg25.win`（**本單**） | 技術工程師 **或** 機台主自己 | GPIO、Webhook、Callback、模擬器 |

技術帳登 SignalHub 必須能設機台主名下設備。看不到營收、分潤、銀行、訂閱。沒有技術帳時，機台主用自己帳號登 SignalHub 即可（現況維持）。

---

## 現況（HQ 已讀碼，不要重盤成另一套）

`SignalHubController` 幾乎全部用 `auth()->id()` 當 `owner_id`：

- `indexProfiles` / `storeProfile` / webhook / events / devices 列表 等，約 20+ 處
- `storeProfile` 寫 `'owner_id' => auth()->id()`
- 設備檢查：`devices.where('owner_id', auth()->id())`

技術帳 `users.id` ≠ 機台主 id，資料在 `root_id` 那個人下面。現況登進去會看到空的，或寫出孤立在技術帳 id 下的 profile，機台主看不到。

`User::isExpired()` 已在 SignalHub model。`Authv9Controller::login` **還沒**擋過期，也沒處理 technician（這是對的：technician **要能**登 SignalHub）。

自行註冊仍 `role=owner`，不要改。

本站沒有營收／分潤頁。不要為了「隱藏帳務」去改 Owner。核側邊欄沒有營運入口即可。

---

## 必做

### 1. 一個 effective owner，全站共用

在 `User` 加方法，不要複製 20 次 if：

```php
public function effectiveOwnerId(): int
{
    if ($this->role === 'technician' && $this->root_id) {
        return (int) $this->root_id;
    }
    return (int) $this->id;
}
```

`SignalHubController`（以及同邏輯的 `SignalHubApiController` 若仍被打到）所有「這是誰的設備／profile／webhook」查詢與寫入，改 `auth()->user()->effectiveOwnerId()`。

包含但不限於：
- `SignalProfile::forOwner(...)`
- `devices.where('owner_id', ...)`
- 新建 profile / webhook 的 `owner_id`
- assignment `owner_id`
- events 過濾

**禁止**技術帳把 `owner_id` 寫成自己的 `users.id`。資料必須落在機台主。

### 2. 登入

`Authv9Controller::login`：
- `isExpired()` 為 true：logout + `withErrors`「帳號已過期，請聯絡機台主重新開立。」（與 Owner 文案一致）
- `role === 'technician'`：**允許**登入，進 profiles
- 其他現況維持（owner 自己登也要能用）

### 3. 權限邊界（夠用就好，不要做 SSO）

- technician 可讀寫 **effective owner** 名下的 profile / pin / webhook / simulator
- technician **不准**改 `users`、不准看銀行、不准打 Owner 營運 API（本來就不同 domain；不要跨站亂接）
- 不要做 Token 跳轉、不要做 SSO

### 4. 不做

- 不改 Owner 專案
- 不新 migration、不改 ENUM
- 不在本機跑 php artisan / 測 DB
- **先不要 deploy**，等 HQ 核碼再開燈（Sophie 上回自己 deploy，本次禁止）

---

## 驗證（遠端，回報必須貼輸出。HQ 未開燈前，可用遠端 tinker + 本機未上線碼對照；**不要**擅自 deploy）

若尚未 deploy，回報寫清「僅碼審 + 本地 diff」，並給 commit hash。HQ 會自己開燈再打。

若 HQ 後續開燈，必驗：

1. 機台主在 Owner 開一個 technician（`root_id=該 owner`）。該帳 **不能** 登 `iot.tg25.win`（已成立）。**能**登 `signal.tg25.win`，看到的 profile / device 是機台主的，不是空列表
2. 技術帳新建 webhook 或改 pin：`owner_id` = 機台主 id，不是 technician id
3. 機台主自己登 SignalHub 仍看到同一筆
4. `expires_at` 過去：SignalHub 登入失敗，文案過期
5. 側邊欄沒有營收／分潤／訂閱

回報含：改動檔案、commit hash、`auth()->id()` 殘留 grep（Controller 內不應再當 owner 範圍）、是否 deploy（應為否）。
