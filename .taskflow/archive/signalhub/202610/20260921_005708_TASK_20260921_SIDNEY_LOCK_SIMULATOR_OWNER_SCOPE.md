# 補單：模擬器／事件 API 必須鎖 effectiveOwnerId，禁止請求覆寫 owner_id

**派工時間**：2026-09-21
**派工者**：HQ
**執行者**：Sidney
**優先級**：high
**前置**：`35d4cee` V9 `SignalHubController` 碼審過。**禁止 deploy。先 push 再開下一輪核。**

---

## HQ 核過的事實

- 本地 `35d4cee`：`User::effectiveOwnerId()` + V9 Controller 約 26 處已改。technician 登入允許、過期擋登入。
- **沒 push**：`origin/main` 與遠端仍 `d10d3a0`。
- `app/` 已無 `auth()->id()`。問題不在 V9 主路徑，在 **仍被路由打到的** `SignalHubApiController`。

實際路由（`routes/api.php`）：

- `GET /events` → `SignalHubApiController::queryEvents`
- `POST /simulator/gpio` → `SignalHubApiController::simulateGpio`
- 前端 `simulator.blade.php` 會打 `/api/v9/signal-hub/events` 與 simulator gpio

這兩條是技術工程師主路徑。工單寫「若仍被打到就要改」，這輪沒改。

---

## 必改

### 1. 先 push `35d4cee` 到 origin/main

不要只停本地 ahead 1。

### 2. `queryEvents`

現況：只靠 `chip_id` / `pin_code` / `profile_id`，**沒有 owner 過濾**。猜 `profile_id` 能看別人事件。

改：結果必須屬於 `auth()->user()->effectiveOwnerId()`。建議 join profile 或 `whereIn profile_id` 限該 owner。沒登入 401。technician 用 root_id 那台機台主的資料，不是空、也不是全世界。

### 3. `simulateGpio`

現況：`SignalProfile::findOrFail(profile_id)`，不查 owner。

改：profile 必須 `owner_id === effectiveOwnerId()`，否則 403。禁止對別人的 profile 寫模擬事件。

### 4. 拿掉請求 `owner_id` 覆寫

同檔現況：

- `indexProfiles`：`$request->input('owner_id', effectiveOwnerId() ?? 11)` — 請求可看別人，還有 `?? 11`
- `storeProfile` / webhook 等：`$request->input('owner_id', 1)` — 預設寫進 owner 1

本單至少：凡 **web/auth 會打到的** 方法，`owner_id` 只來自 `effectiveOwnerId()`，**忽略** request 的 `owner_id`。

`storeEvent` / internal MQTT 若走內部 key、無 web session，不要誤用 effectiveOwnerId 弄壞 Infra 寫入。那條維持裝置歸屬，不要改成「登入者的 owner」。若不確定，**不要動** `storeEvent`，回報寫明。

### 5. grep 回報

回報必須含：

```
rg -n "request->input('owner_id'|auth\(\)->id\(\)" app/Http/Controllers --glob '*.php'
```

auth 路徑不應再出現「request 決定 owner_id」。

---

## 不做

- 不改 Owner
- 不新 migration
- **不 deploy**（等 HQ 開燈）
- 不做 SSO

---

## 驗證（碼審即可，因未上線）

1. commit + **push** hash
2. `queryEvents` / `simulateGpio` 的 owner 檢查片段
3. 上述 grep 結果
4. 明確寫：未 deploy
