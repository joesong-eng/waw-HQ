# HQ 工單整理與執行規劃

**整理時間**：2026-09-15 10:00
**負責人**：Mina (Member)
**工單來源**：`.taskflow/member/inbox/` 共 12 張（09/15 派發）

---

## 一、工單清單總覽

| # | 工單代號 | 優先級 | 審查項目 | 內容摘要 | 預估工時 |
|:---|:---|:---|:---|:---|:---|
| 1 | VENUE_AUTH_FIX | 🔴 high | UX-P0-4b | /devices /billing /subscriptions 加 auth middleware + 移除銀行帳號 | 15min |
| 2 | DEPRECATE_OLD_MACHINE_API | 🔴 high | P1-5 | 移除 MachineController + /api/machine/* 路由 | 20min |
| 3 | P2_QUICKFIX_BATCH | 🟡 normal | P2-5/P2-8/P3-1 | KioskSession URL寫死 + .gitignore補強 + .env.example補強 | 30min |
| 4 | TEST_COVERAGE_BOOTSTRAP | 🟡 normal | P3-3 | 建立測試基礎設施（MemberWallet + Auth + Venue） | 2h |
| 5 | P1_WELCOME_VUE_CDN | 🟡 normal | P2-1 | Vue CDN→Vite 打包 | 2h |
| 6 | P2P2_WELCOME_REFACTOR | 🟡 normal | P2-2 | 拆分 welcome.blade.php（2500+行→partials） | 1.5h |
| 7 | P2P3_REMAINING_BATCH | 🟡 normal | P2-4/P2-6/P2-7/P3-2/P3-4 | 剩餘7項批次（getColumnListing + PERF log + BillController + services.php + 雜物） | 2h |
| 8 | BOOTSTRAP_TESTING | 🟡 normal | P3-3 | 基礎測試框架（安全修復驗證 + 業務邏輯） | 2h |
| 9 | CLEANUP_ROOT_JUNK | 🟢 low | P3-4 | 清理 pyrefly.toml / hq_agent_tools / waw_test.html / firmware.bin | 20min |
| 10 | SERVICES_PHP_CLEANUP | 🟡 normal | P3-2 | config/services.php infra 鍵去重 + 統一命名 | 30min |
| 11 | SPLIT_WELCOME_BLADE | 🟡 normal | P2-2 | 拆分 welcome.blade.php（與 #6 重疊） | 1.5h |
| 12 | VUE_CDN_TO_VITE | 🟡 normal | P2-1 | Vue CDN→Vite（與 #5 重疊） | 2h |

---

## 二、重疊工單分析

HQ 派發的 12 張中有 **4 組重疊**，實際獨立任務為 **8 項**：

| 重疊組 | 工單 A | 工單 B | 建議合併方式 |
|:---|:---|:---|:---|
| Vue CDN→Vite | #5 P1_WELCOME_VUE_CDN | #12 VUE_CDN_TO_VITE | 合併為一個任務執行，回報時引用兩張工單代號 |
| 拆分 welcome.blade | #6 P2P2_WELCOME_REFACTOR | #11 SPLIT_WELCOME_BLADE | 合併為一個任務執行，回報時引用兩張工單代號 |
| 測試基礎 | #4 TEST_COVERAGE_BOOTSTRAP | #8 BOOTSTRAP_TESTING | #4 側重 Model/Feature Test，#8 側重安全驗證 Test，可合併為一個大任務分兩段做 |
| services.php / 雜物清理 | #7 P2P3_REMAINING_BATCH（項目五+六） | #10 SERVICES_PHP_CLEANUP + #9 CLEANUP_ROOT_JUNK | #7 是大包裹含這兩項，#9/#10 是 HQ 拆細重派。建議以 #9/#10 為準執行，#7 中對應項目標記「由 #9/#10 覆蓋」 |

---

## 三、建議執行順序（一步一步來）

### 第一梯隊：快速安全修復（~35 分鐘，無依賴）

| 順序 | 工單 | 原因 |
|:---|:---|:---|
| **①** | #1 VENUE_AUTH_FIX | high 優先，銀行帳號外露，10 分鐘可做完 |
| **②** | #2 DEPRECATE_OLD_MACHINE_API | high 優先，移除舊路由減少攻擊面 |

### 第二梯隊：快速配置修復（~30 分鐘，無依賴）

| 順序 | 工單 | 原因 |
|:---|:---|:---|
| **③** | #3 P2_QUICKFIX_BATCH | 3 項零碎修復打包，避免 context 切換 |
| **④** | #10 SERVICES_PHP_CLEANUP | 與 #3 有關聯（都碰 config），緊接著做 |
| **⑤** | #9 CLEANUP_ROOT_JUNK | 低風險清理，順手做掉 |

### 第三梯隊：測試基礎（~2-4 小時，依賴前兩梯隊完成）

| 順序 | 工單 | 原因 |
|:---|:---|:---|
| **⑥** | #4 + #8 合併（測試基礎） | 需在安全修復和配置清理完成後寫測試才有意義 |

### 第四梯隊：前端重構（~4-5 小時，有先後依賴）

| 順序 | 工單 | 原因 |
|:---|:---|:---|
| **⑦** | #5 + #12 合併（Vue CDN→Vite） | 必須先做，#6/#11 依賴此步 |
| **⑧** | #6 + #11 合併（拆分 welcome.blade） | 在 Vue 打包完成後再拆分，避免 merge conflict |

### 第五梯隊：剩餘批次（~1-2 小時）

| 順序 | 工單 | 原因 |
|:---|:---|:---|
| **⑨** | #7 P2P3_REMAINING_BATCH | 涵蓋 getColumnListing(9處) + PERF log + BillController 評估，與前面無依賴但也最不急 |

---

## 四、依賴關係圖

```
① VENUE_AUTH_FIX ─┐
② DEPRECATE_MACHINE ─┤
                      ▼
③ P2_QUICKFIX_BATCH ─┐
④ SERVICES_PHP ──────┤
⑤ CLEANUP_JUNK ──────┘
                      ▼
⑥ TEST_BOOTSTRAP ──────────────────── (獨立)
                      ▼
⑦ VUE_CDN_TO_VITE ──┐
                      ▼
⑧ SPLIT_WELCOME ─────┘
                      ▼
⑨ P2P3_REMAINING_BATCH ────────────── (獨立)
```

---

## 五、Mina 的建議

1. **先做①②**（high 優先 + 銀行帳號外露），做完部署回報，再繼續下一梯隊
2. **③④⑤一起做**（都是 config/gitignore 清理），一次 commit 或三個 commit 推上去
3. **⑥測試**可以和④⑤並行不衝突，但建議在安全修復部署後再寫
4. **⑦⑧前端重構**是大工程，建議獨立半天時間專心做
5. **⑨剩餘批次**隨時可插隊，不影響其他任務

等老大確認，我就從①開始做。
