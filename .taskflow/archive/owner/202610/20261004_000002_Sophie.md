# 回報：Owner Git 清理 + README 修正 + 訂閱驗證（合併三任務）

## 任務 ID
TASK_20261003_SOPHIE_CONSOLIDATED

## 執行者
Sophie（Owner / wawOwner, iot.tg25.win）

## 完成時間
2026-10-03（Asia/Taipei）

## 結論摘要
- 階段一（Git 清理）：✅ 完成
- 階段二（README 修正）：✅ 完成
- 階段三（訂閱驗證）：⚠️ 驗證完成，**發現資料異常與架構落差，建議 HQ 裁定**（未修改任何程式碼）

---

## 階段一：Git 清理

### 執行結果
| 項目 | 值 |
|------|-----|
| 變更檔案 | `.taskbox`（D, symlink, mode 120000） |
| Commit | `5ffd4378a75236a2c5c40a09aca7b9df0d3739ea` |
| Commit message | `chore: remove legacy .taskbox symlink` |
| Push | `ce76cb3..5ffd437  main -> main`（github.com/joesong-eng/waw-business.git） |

### 驗證佐證
```
$ git status --short
 D .taskbox
$ ls -la .taskbox
ls: .taskbox: No such file or directory
$ git commit -m 'chore: remove legacy .taskbox symlink'
[main 5ffd437] chore: remove legacy .taskbox symlink
 1 file changed, 1 deletion(-)
 delete mode 120000 .taskbox
$ git push origin main
To https://github.com/joesong-eng/waw-business.git
   ce76cb3..5ffd437  main -> main
$ git status --short
(空)
```

---

## 階段二：修正 README 過時 Model 引用

### 執行結果
| 項目 | 值 |
|------|-----|
| 變更檔案 | `README.md`（僅此一檔，未動任何程式碼） |
| Commit | `7a8df8bee57fafc2a8ce4c8947e377b8736e373d` |
| Commit message | `docs: fix README stale Machine model references` |
| Push | `5ffd437..7a8df8b  main -> main` |
| Diff stat | 1 file changed, 2 insertions(+), 15 deletions(-) |

### 修改內容
1. 移除 `### Machine.php` 整節（原 L188-192）
2. 移除 `### MachineExtensions.php` 整節（原 L200-203）
3. 移除「待補測試清單」中 `- [ ] `Machine.php` 模型測試` 及其 2 子項（原 L238-240）
4. 將仍存在的業務概念改掛到 `Device.php`：
   - `- 參數配置 (parameters JSON)` → `- 參數配置 (parameters / config_json)`
   - 新增 `- 營運狀態與交易統計`

### 驗收佐證
```
$ grep -nE 'MachineExtensions|Machine\.php' README.md
(0 hits)  ← PASS

$ grep -n -i 'machine' README.md
(0 hits)  ← 全文已無 Machine 殘留

$ git diff --stat
 README.md | 17 ++---------------
 1 file changed, 2 insertions(+), 15 deletions(-)
```

### 文件所述 Model 存在性檢查（皆存在於 app/Models/）
```
OK   app/Models/Device.php
OK   app/Models/OwnerSubscription.php
（README 其餘引用為 app/Services/* 與 tests/*，皆存在）
```

---

## 階段三：驗證訂閱機制涵蓋 SignalHub owner

架構依據：`brains/knowledge/03_system_architecture/ADR-001_SIGNALHUB_SUBSCRIPTION.md`
本階段僅驗證、未改程式碼。

### 驗證環境
- Owner 站點：`yd174` / `/www/wwwroot/iot.tg25.win`
- SignalHub 站點：`yd174` / `/www/wwwroot/signal.tg25.win`（**與 Owner 同一主機**）
- DB：兩站 `.env` 皆為 `DB_HOST=141.148.165.50` / `DB_DATABASE=iotv9`

### 項目 1：users 表共用性 — ✅ 同一套
```
OWNER     : DB=iotv9  users_table=users  users_total=8
SIGNALHUB : DB=iotv9  users_table=users  users_total=8
```
兩站 Tinker 讀取同一 `iotv9.users`，資料集完全相同（8 筆）。**SignalHub owner 與 Owner users 為同一套（同一張表）→ 符合「共用」前提，無需停止任務。**

users 實際內容（id/name/email/role）：
```
1  | 系統管理員   | admin@tg25.win   | role=admin
2  | 老闆 (Owner) | owner@tg25.win   | role=owner
3  | 場地人員     | staff@tg25.win   | role=staff
5  | 長義娛樂事業 | abc@tg25.win     | role=owner
12 | 家寶科技     | ttest1@tg25.win  | role=owner
16 | 遊戲商       | IEX@tg25.win     | role=technician (root_id=2)
18 | 李董團隊     | lee01@tg25.win   | role=owner
19 | 老李技術     | ttest@tg25.win   | role=technician (root_id=18)
```

> ⚠️ **工單假設修正**：工單所述「user_id=11 ttest」**已過時/不正確**。
> `id=11` 在 users 表**不存在**；`ttest` 實為 **id=19**（technician, root_id=18），`ttest1` 為 **id=12**（owner, 家寶科技）。

### 項目 2：owner_subscriptions 涵蓋性 — ⚠️ 有孤兒記錄
```
owner_subscriptions  count = 2
{"id":1,"owner_id":12,...,"plan_name":"device_service","status":"active"}
{"id":2,"owner_id":11,...,"plan_name":"device_service","status":"active"}   ← 孤兒

JOIN users:
id=1 owner_id=12 → 家寶科技 / ttest1@tg25.win / owner   ✅ 有效
id=2 owner_id=11 → (name=null, email=null, role=null)    ❌ 無對應用戶（孤兒）
```
- `owner_subscriptions.owner_id` 有 FK → `users.id`，但 DB 內存在 `owner_id=11` 而 users 無 id=11 的記錄（**歷史資料不一致**）。
- 實際 owner（如 id=12 家寶科技）**已有訂閱記錄**；但 `owner_id=11` 為無主資料，需清理或補正。

### 項目 3：Owner 後台訂閱管理 — ⚠️ 只管理「雙軌表」，不管理 owner_subscriptions
`iotv9` 內同時存在**兩套訂閱表**：

| 表 | 用途 | 筆數 | Owner 後台管理 |
|----|------|------|----------------|
| `subscriptions` | WAW 2.0 雙軌（device/venue, subscriber_id, tier_code, quota_limit） | 35 | ✅ 有 admin API：`/api/v9/admin/subscription/list`、`/{id}/extend`、`/audit/{id}` + UI `resources/views/iot/modules/m2/{list,plans,status}.blade.php` |
| `owner_subscriptions` | ADR-001 指定之 SignalHub 訂閱 SSOT（owner_id, plan_name, started_at, expires_at） | 2 | ❌ **無任何後台 API/UI** |

`subscriptions` 訂閱者分佈（實際）：subscriber_id=1(admin,2)、2(老闆,24)、5(長義,1)、12(家寶,2)、18(李董,6)。

> ⚠️ **架構落差**：ADR-001 決策一將 `owner_subscriptions` 定為共用 SSOT，但 Owner 後台的訂閱管理（admin list/extend）實際操作的是 `subscriptions` 表。**Owner 後台目前無法列出/管理 SignalHub 所用的 `owner_subscriptions` 記錄**（僅 `OwnerSubscription` Model 供程式內部使用，見 `OtaController`、`CheckSubscriptionExpiry`、`User::subscription()`）。

### 項目 4：config/subscription.php 一致性 — ✅ 完全一致
```
本機  : diff PROJECT/Owner/config/subscription.php PROJECT/SignalHub/config/subscription.php  → SAME
遠端  : diff /www/wwwroot/iot.tg25.win/config/subscription.php /www/wwwroot/signal.tg25.win/config/subscription.php → SAME
md5   : 538b3dcb10aa841b83871dd8fa874294  (兩站相同)
```
定價內容一致：device 1200/台/月；venue tier_20~500（2500/5000/10000/15000/25000）；grace_days=3；reminder_days=[7,3,1]。

### 項目 5：SignalHub 端現況（補充）
- `app/Models/OwnerSubscription.php`：**不存在**（幽靈引用）
- `app/Http/Middleware/EnsureSubscriptionActive.php`：**不存在**
- 訂閱相關路由：**無**（`route:list | grep subscription` = NONE）
→ 與 ADR-001「決策五：短期不啟用攔截」一致，Sidney 端尚未落地。

---

## 驗收對照（ADR-001 §4）
| # | 驗收項 | 結果 |
|---|--------|------|
| 1 | OwnerSubscription Model 可載入 | ✅ Owner 端存在且 Tinker 可讀（SignalHub 端尚未建，屬 Sidney 任務） |
| 2 | 訂閱狀態 API 回 200 | ✅ Owner `/api/v9/subscription/status` 路由存在 |
| 3 | 幽靈引用解除 | ❌ SignalHub `User.php:127` 仍引用不存在的 Model（Sidney 未完成） |
| 4 | 攔截預設停用 | ✅ 兩站 config 無啟用 flag，SignalHub 亦無 middleware |
| 5 | 站點存活 | 待補（本階段未執行 curl，如需可補） |

---

## 建議 / 待 HQ 裁定事項
1. **孤兒記錄**：`owner_subscriptions.owner_id=11` 無對應 users，建議清理或更正為實際 owner id（如 id=12 家寶科技）。
2. **SSOT 落差**：ADR-001 以 `owner_subscriptions` 為 SignalHub 訂閱 SSOT，但 Owner 後台 admin 訂閱管理操作的是 `subscriptions` 表。請裁定：
   - (a) 於 Owner 後台補上 `owner_subscriptions` 的 list/extend 管理介面；或
   - (b) 修訂 ADR-001，改以 `subscriptions` 為 SSOT。
3. **工單文件修正**：後續工單請將「user_id=11 ttest」更正為「id=12 ttest1（家寶科技, owner）」。
4. **幽靈引用**：SignalHub `User.php:127` 引用不存在的 `OwnerSubscription`，屬 Sidney SH-1 範疇，提醒其補齊。

---

## 結論
- ✅ 階段一、階段二完成並已 push（commit 5ffd437、7a8df8b）。
- ⚠️ 階段三驗證完成：users 表共用 ✅、config 一致 ✅；但發現 (1) owner_subscriptions 孤兒記錄、(2) Owner 後台未管理 owner_subscriptions 的架構落差，已如實回報，**未修改任何程式碼**，待 HQ 裁定。

## 執行者簽章
Sophie（Owner）

