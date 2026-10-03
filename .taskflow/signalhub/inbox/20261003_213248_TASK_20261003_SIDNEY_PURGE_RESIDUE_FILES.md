# 任務工單：清除 SignalHub 版控殘留備份檔（.bak / .old / .contaminated / .new_template）

- **工單編號**：TASK_20261003_SIDNEY_PURGE_RESIDUE_FILES
- **派發時間**：2026-10-03
- **負責人**：Sidney (SignalHub)
- **優先級**：P3 (Low)
- **關聯模組**：SignalHub (signal.tg25.win / yd174)
- **來源**：HQ 全域盤點（Joe 指示先清低風險待辦）

---

## 一、背景

HQ 盤點發現 SignalHub repo 內殘留多個備份/污染檔，屬版控噪音，會誤導後續開發（尤其 `routes/api.php.contaminated` 內含指向不存在 Controller 的訂閱路由）。正式檔皆已確認存在，可安全清除。

---

## 二、清理清單（共 11 檔，已確認正式版存在）

### 已納入版控（需 `git rm`）
| # | 檔案 | 正式版 |
|:--|:---|:---|
| 1 | `app/Jobs/ProcessWebhookDelivery.php.bak.archive` | ✅ 存在 |
| 2 | `app/Models/SignalProfile.php.bak.archive` | ✅ 存在 |
| 3 | `app/Services/SignalNotificationService.php.bak.archive` | ✅ 存在 |
| 4 | `config/subscription.php.old` | ✅ 存在 |
| 5 | `resources/views/signal-hub/profiles.blade.php.bak` | ✅ 存在 |
| 6 | `routes/api.php.bak.archive` | ✅ 存在 |
| 7 | `routes/api.php.bak2` | ✅ 存在 |
| 8 | `routes/api.php.bak3` | ✅ 存在 |

### 未納版控（直接刪檔，`api.php.contaminated` 已被 .gitignore 第 46 行忽略）
| # | 檔案 |
|:--|:---|
| 9 | `app/Http/Controllers/Api/V9/SignalHubController.php.bak` |
| 10 | `resources/views/signal-hub/profiles.blade.php.new_template` |
| 11 | `routes/api.php.contaminated` |

---

## 三、執行步驟

1. 再次確認每個殘留檔對應的正式檔（去掉後綴）存在且非空。
2. 對已納版控者執行 `git rm <file>`；未納版控者 `rm -f <file>`。
3. 提交：`chore(signalhub): purge residue backup files (.bak/.old/.contaminated/.new_template)`。
4. Push `origin/main`。

---

## 四、驗收指標（必須附實際指令輸出）

| # | 驗收項 | 方式 | 期望 |
|:--|:---|:---|:---|
| 1 | 殘留檔歸零 | `git ls-files \| grep -E '\.bak\|\.old\|\.contaminated\|\.new_template\|\.orig'` | 0 hits |
| 2 | 工作區殘留歸零 | `find . -type f \( -name '*.bak*' -o -name '*.old' -o -name '*.contaminated' -o -name '*.new_template' \) -not -path './vendor/*' -not -path './node_modules/*'` | 0 hits |
| 3 | 正式檔仍在 | `ls routes/api.php config/subscription.php resources/views/signal-hub/profiles.blade.php` | 三檔皆存在 |
| 4 | 站點存活 | `curl -sI https://signal.tg25.win/` | HTTP 2xx |
| 5 | 無新增錯誤 | 部署後 log 無新增 ERROR | 通過 |

---

## 五、回報要求

完工後寫入 `.taskflow/signalhub/outbox/`，附：Commit SHA、驗收指令與實際輸出、curl 狀態碼。

---

## 六、注意

- **只清備份檔，不得改動任何正式檔內容。**
- 若發現某正式檔不存在或為空，立即停止並回報 HQ，不得直接刪除。
