# 回報：TASK_20260921_SIDNEY_LOCK_SIMULATOR_OWNER_SCOPE

**回報時間**：2026-09-21
**執行者**：Sidney
**狀態**：碼審完成 + 已 push（未 deploy）

---

## Commit

- `35d4cee` — User::effectiveOwnerId() + V9 Controller 26 處
- `3a033ad` — SignalHubApiController 全面鎖 owner scope（本單）
- **已 push** 至 origin/main

---

## 改動內容（`3a033ad`，1 檔 +30/-18）

### queryEvents
加 `whereIn('profile_id', $ownerProfileIds)`，ownerProfileIds 來自 `effectiveOwnerId()`。
技術帳只看到機台主名下 profile 的事件。

### simulateGpio
findOrFail 後加 owner 檢查：`(int) $profile->owner_id !== $ownerId` → 403。

### 移除 request->input('owner_id') 覆寫
| 方法 | 改前 | 改後 |
|---|---|---|
| indexProfiles | request->input('owner_id', ... ?? 11) | effectiveOwnerId() |
| storeProfile | request->input('owner_id', 1) | effectiveOwnerId() |
| copyProfile | request->input('owner_id', 1) | effectiveOwnerId() |
| indexWebhooks | request->input('owner_id', 1) | effectiveOwnerId() |
| storeWebhook | request->input('owner_id', 1) | effectiveOwnerId() |

### 其他 bare findOrFail → 加 owner scope
showProfile / updateProfile / destroyProfile / indexPins / batchUpdatePins /
indexRules / storeRule / updateRule / destroyRule /
updateWebhook / destroyWebhook / testWebhook — 全部加 where('owner_id', effectiveOwnerId())。

### 未動
storeEvent / storeBatch / storeSnapshotEvent — 內部 MQTT 路徑（verify.internal.key middleware），無 web session。

---

## grep 結果

```
$ grep -rn "request->input('owner_id'" app/Http/Controllers/ --include='*.php'
（零結果）

$ grep -rn 'auth()->id()' app/Http/Controllers/ --include='*.php'
（零結果）
```

---

## Deploy 狀態

❌ 未 deploy（依任務指示等 HQ 開燈）
