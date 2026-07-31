# HQ 標準部署 SOP v1

> 最後更新: 2026-05-18
> Owner: HHQM
> 適用範圍: sysWawIot 全模組部署治理
> 狀態: Active

---

## 0. 核心原則

部署不是一條 shell command。部署必須走 HQ 閘門：

Proposal -> Approval -> Execution -> Audit -> Close

任何 GitHub push、server pull/reset、build、migration、restart/reload、`.env` 修改，都屬於有副作用行為。除非 Joe 明確批准該範圍，否則不得執行。

本 SOP 的目的：

1. 固定 GitHub 與 server pull 流程，避免再靠猜測或臨場試錯。
2. 把 build / migration / restart 拆成獨立 gate，不讓一鍵部署越權。
3. 所有部署都能回到 HQ `DISPATCH_BOARD.md` 查到狀態與審計結果。
4. MCP 或自動化工具可以用，但必須被此 SOP 包住，不能繞過治理。

---

## 1. 部署角色分工

| 角色 | 責任 | 禁止事項 |
|---|---|---|
| Joe | 最高批准者 | 無 |
| HHQM | 提案、全域風險分析、登記任務、審計、關板 | 未批准不得 push/SSH/build/migrate/restart |
| hMina | Member 模組實作與回報 | 不得自行部署 production |
| hIna | Infra 模組實作與回報 | 不得越界修改 Member/Owner |
| 其他 h-Agent | 各自模組實作與回報 | 不得跨模組越權 |

---

## 2. Phase 0 — Deployment Proposal

部署前必須先建立或更新 HQ 任務板：

`/Users/ilawusong/Documents/sysWawIot/HQ/brains/registry/DISPATCH_BOARD.md`

Proposal 至少包含：

- Target module: Member / tg25-infra / Owner / iHub / Alliance / HQ
- Local repo path
- Production server alias
- Production project path
- 準備出貨的檔案列表
- 是否需要 GitHub push
- 是否需要 server pull/reset
- 是否需要 frontend build
- 是否需要 migration
- 是否需要 service restart/reload
- 是否需要 `.env` / secret 設定
- 回滾方案
- 驗證方案

如果任何一項答案是「需要 migration」、「需要 restart/reload」、「需要 `.env` secret 變更」，必須視為高風險部署，單獨列出並等 Joe 明確批准。

---

## 3. Phase 1 — Local Audit

GitHub push 前必須做本地審計。

### 3.1 Git 狀態

```bash
git status --short
git diff --stat
```

要求：

- 不可盲目 `git add .`。
- 必須只 stage 已審計過的檔案。
- scratch files、backup、emergency script、agent trigger、臨時測試檔不得混入 commit。
- 若發現 unrelated drift，先回報並隔離，不可靜默一起部署。

### 3.2 精準 diff 審查

```bash
git diff -- <file1> <file2>
```

審查重點：

- 是否符合已批准任務範圍。
- 是否引入跨模組直連。
- 是否寫入 secret / token / password。
- 是否修改 package.json build 指令。
- 是否改動 migration、queue、scheduler、websocket、nginx 相關檔案。

### 3.3 Lint / syntax check

依模組執行適當檢查：

Laravel / PHP：

```bash
php -l <changed_php_file>
```

Node / frontend：

```bash
npm run build
# 或依模組使用 pnpm run build
```

Python / Infra：

```bash
python -m py_compile <changed_py_file>
```

注意：本地 build 是驗證，不等於 production build。production build 仍需 Phase 3 gate 批准。

---

## 4. Phase 2 — GitHub Publish Gate

### 4.1 直接 main push 條件

只有在 Joe 批准「低風險直接部署」時，才允許：

```bash
git add <approved_file1> <approved_file2>
git commit -m "type(scope): summary"
git push origin main
```

### 4.2 預設安全模式：Branch + PR

若風險較高，或涉及跨模組契約，預設使用 GitHub PR workflow：

```bash
git checkout -b fix/<short-description>
git add <approved_files>
git commit -m "fix(scope): summary"
git push -u origin HEAD
```

後續使用 `github-pr-workflow` skill 管理 PR、CI、merge。

### 4.3 Commit message 規範

建議格式：

```text
type(scope): short summary

- What changed
- Why changed
- Risk / verification note
```

常用 type：

- fix
- feat
- refactor
- docs
- chore
- ci

---

## 5. Phase 3 — Server Pull / Build / Migration / Restart Gate

所有 server 指令必須使用 SSH alias，不得猜 IP。alias 參考：

`INFRASTRUCTURE_REFERENCE.md`

### 5.1 Member baseline deploy

適用：PHP / Blade / config 類變更，且不需要前端資源 build。

```bash
ssh yd47 "cd /www/wwwroot/win.tg25.win && git fetch origin main && git reset --hard origin/main && php artisan optimize:clear"
```

### 5.2 Member with frontend build

適用：修改 `resources/css/`、`resources/js/`、Vite 打包資源，或 `VITE_` 前綴環境變數。

```bash
ssh yd47 "cd /www/wwwroot/win.tg25.win && git fetch origin main && git reset --hard origin/main && npm install && npm run build && php artisan optimize:clear"
```

Member 特別規則：

- Blade 模板中的 CDN Vue 代碼通常不需要 build。
- `resources/css/` 或 `resources/js/` 修改必須 build。
- 不得修改 `package.json` 的 `build` 指令；若真的需要，必須單獨批准。

### 5.3 Owner baseline deploy

```bash
ssh yd174 "cd /www/wwwroot/iot.tg25.win/wawv9 && git fetch origin main && git reset --hard origin/main && sudo -u www php artisan optimize:clear"
```

### 5.4 Owner with frontend build

```bash
ssh yd174 "cd /www/wwwroot/iot.tg25.win/wawv9 && git fetch origin main && git reset --hard origin/main && pnpm install && pnpm run build && sudo -u www php artisan optimize:clear"
```

### 5.5 Infra deploy

Infra 屬高敏感基礎設施。部署前必須由 hIna/HHQM 明確列出影響：API、MQTT listener、Nginx、DB、Redis、credit-relay。

範例 baseline，只有在批准後才可執行：

```bash
ssh infra "cd /home/ubuntu/tg25-infra && git fetch origin main && git reset --hard origin/main"
```

如需 pip install、systemctl restart，必須單獨批准。

### 5.6 Migration gate

Migration 永遠是高風險 gate。

禁止：

- 未批准就把 migrate 包進一般部署。
- 在本地跑 production migration。
- 由非負責模組擅自跑 migration。

批准後才可使用：

```bash
ssh <alias> "cd <project_path> && php artisan migrate --force"
```

執行前需先提供：

- migration file list
- schema impact
- rollback/down method
- 是否需要備份
- 預期耗時

### 5.7 Restart / reload gate

restart/reload 不是一般部署的預設動作。

只有以下情況才考慮：

- Reverb/WebSocket 設定或事件服務變更。
- Supervisor / queue worker 代碼需要重載。
- Nginx config 變更。
- systemd service 檔或 daemon 行為變更。

Nginx reload 必須先測：

```bash
ssh <alias> "sudo nginx -t && sudo systemctl reload nginx"
```

---

## 6. Phase 4 — Post-deploy Verification

部署後不可只說「新功能 OK」。必須驗證舊功能與新功能。

### 6.1 基本驗證

- 首頁 / health endpoint HTTP status。
- 關鍵頁面或 API status。
- 新功能或 bugfix 對應案例。
- 若有 build，檢查前端資源是否載入。
- 若有 restart，檢查 service status。
- 必要時檢查 log，但不要輸出 secret。

### 6.2 Member baseline verification

```bash
curl -s -o /dev/null -w "%{http_code}" https://win.tg25.win
curl -s -o /dev/null -w "%{http_code}" "https://win.tg25.win/m/play?node_id=device_001"
```

預期：首頁 200；功能頁依路由可能 200/302，需依任務定義。

### 6.3 Infra verification

依任務使用 API health 或指定 endpoint。帶 API key 時不得把 key 寫入文件、log、commit message、最終回報。

---

## 7. Phase 5 — Audit Close

部署完成後更新：

1. HQ DISPATCH_BOARD.md
   - 狀態：已部署 / 已審計 / 已關板
   - 進度：100%

2. 模組 `_agent/status.md`
   - current_task
   - status
   - last_heartbeat
   - risk
   - audit_summary
   - next_action

Audit summary 應包含：

- commit / branch / PR（若有）
- deployed server alias
- deployed path
- build 是否執行
- migration 是否執行
- restart 是否執行
- verification 結果
- 若刻意未執行高風險動作，也要明確寫出

---

## 8. MCP / Automation 使用原則

可用工具：

- Hermes `github-pr-workflow` skill：GitHub branch / PR / CI / merge。
- Hermes `github-repo-management` skill：repo / secrets / workflow / releases。
- Hermes `native-mcp` skill：把 MCP server 接成 Hermes 原生工具。
- HQ 舊文件 `V9_OPS_AUTOMATION.md`：可作參考，但不能直接繞過部署 gate。

原則：

- MCP 只能是執行器，不是批准者。
- 一鍵部署工具必須包在 Proposal -> Approval -> Execution -> Audit 裡。
- 自動化工具輸出不是完成證據，HHQM 仍需獨立驗證。

---

## 9. 禁止清單

禁止：

- 未登記 DISPATCH_BOARD 就部署。
- 未批准就 SSH production。
- 未批准就 git push。
- 未批准就 server git pull/reset。
- 未批准就 npm/pnpm build production。
- 未批准就 migrate。
- 未批准就 restart/reload。
- 使用完整 IP 取代 SSH alias。
- `git add .` 混入未審計檔案。
- 把 secret 寫進文件、log、commit message、回報。
- 在 server 直接改檔案取代 GitHub 流程。
- 只驗證新功能，不驗證首頁與既有功能。

---

## 10. 快速決策表

| 變更類型 | GitHub push | Server pull | Build | Migration | Restart |
|---|---:|---:|---:|---:|---:|
| PHP controller/service | 需要 | 需要 | 通常不需要 | 不需要 | 不需要 |
| Blade only | 需要 | 需要 | 通常不需要 | 不需要 | 不需要 |
| resources/css/js | 需要 | 需要 | 需要 | 不需要 | 不需要 |
| VITE_ env | 可能需要 | 需要 | 需要 | 不需要 | 不需要 |
| DB schema | 需要 | 需要 | 視情況 | 高風險批准 | 視情況 |
| WebSocket/Reverb config | 需要 | 需要 | 視情況 | 不需要 | 高風險批准 |
| Nginx config | 需要或文件化 | 需要 | 不需要 | 不需要 | reload 高風險批准 |
| Infra API code | 需要 | 需要 | 不需要 | 視情況 | 視服務而定 |

---

## 11. 本次 hMina 相關注意事項

TASK_20260518_010 的 Member KioskController 變更已完成本地審計，但尚未部署。

若之後要部署此變更，至少需要：

1. 確認 Member production `.env` 補齊正式 `INFRA_KEY`。
2. 確認只 stage 本次批准檔案，避免混入 Member 目錄既有 drift。
3. GitHub push gate。
4. Member server pull gate。
5. 不需要 migration。
6. 不需要 Reverb restart，除非後續審計發現事件服務行為需要。
7. 驗證首頁、kiosk/info、kiosk/heartbeat、node-id 相關流程。
