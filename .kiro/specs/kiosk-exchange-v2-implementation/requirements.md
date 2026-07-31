# Requirements Document

## Introduction

This document specifies the business and functional requirements for the Kiosk Exchange v2 system, which enables members to exchange cash for tokens at physical kiosk machines. The system involves hardware pairing, member authentication, QR code scanning, bill acceptance with human confirmation, token crediting with idempotency, and session termination.

The requirements are derived from the consolidated Phase 0-6 technical design documents and focus on **what** needs to be achieved rather than **how** to implement it.

---

## 🚨 關鍵規範速查（實作前必讀）

> 這裡列出最容易出錯的命名與格式規範，所有 Agent 實作前必須對照確認。

### 識別碼格式（全小寫）

| 識別碼 | 格式 | 範例 | 錯誤示範 |
|--------|------|------|---------|
| `node_id` / `kiosk_id` | 全小寫，底線分隔 | `kiosk_001` | `KIOSK_001` ❌ |
| `esp32_mac` / `chip_id` | 全小寫，無冒號 | `e072a1f73a78` | `E0:72:A1:F7:3A:78` ❌ |
| `screen_mac` | 保留原始大小寫 | `STB-T1BQTYBDUEGX` | 不可轉小寫 |
| WebSocket 頻道 | 全小寫 | `kiosk.kiosk_001` | `kiosk.KIOSK_001` ❌ |
| MQTT topic | 全小寫 | `kiosk/e072a1f73a78/cmd` | `kiosk/E072A1F73A78/cmd` ❌ |

### 認證 Header

| 情境 | Header | 值 |
|------|--------|-----|
| 後端對後端（Member ↔ Infra） | `X-Internal-Key` | `v9-internal-key-2026` |
| iHub → Member/Infra | `X-Internal-Key` | `v9-internal-key-2026` |
| Infra Listener → Member webhook | `X-Internal-Key` | `v9-internal-key-2026` |
| 會員手機 → Member API | `Authorization: Bearer {token}` | Sanctum token |
| **例外**：iHub 呼叫 escrow/confirm、reject、heartbeat、complete | `X-Internal-Key` | `v9-internal-key-2026`（不用 Bearer） |

### MQTT Topics

| 方向 | Topic | QoS | 說明 |
|------|-------|-----|------|
| 韌體 → 雲端 | `kiosk/{chip_id}/event` | 2 | escrow / stacked / rejected |
| 韌體 → 雲端 | `kiosk/{chip_id}/status` | 1 | ba_state 心跳（每 60 秒） |
| 雲端 → 韌體 | `kiosk/{chip_id}/cmd` | 2 | enable / disable / stack / reject |
| 韌體上下線 | `device/{chip_id}/status` | 1 | `"online"` / `"offline"`（LWT） |

### WebSocket 頻道

| 頻道 | 用途 | 訂閱方 |
|------|------|--------|
| `kiosk.{kiosk_id}` | 業務事件（bind、escrow、stacked、session end） | iHub、會員手機 |
| `engineering.{kiosk_id}` | 工程監控（Signal Flow Monitor） | 工程頁面 |

### HTTP 狀態碼

| 狀態碼 | 含義 | 使用情境 |
|--------|------|---------|
| 200 | 成功 | 正常回應 |
| 401 | 未授權 | X-Internal-Key 錯誤 或 Bearer token 無效 |
| 404 | 找不到 | Session 不存在 |
| 409 | 衝突 | Kiosk 使用中（busy） |
| 422 | 驗證失敗 | Token 過期 |
| 500 | 伺服器錯誤 | 非預期錯誤 |

### 兩種韌體不可混淆

| 韌體 | MQTT 前綴 | 管理方 | 用途 |
|------|----------|--------|------|
| `IOTkiosk_v0` | `kiosk/{chip_id}/` | Member / Infra | 紙鈔機收鈔卡 |
| `IOTwawS3` | `device/{chip_id}/` | Owner | 遊戲機採集卡 |

> 詳細 API 規格見 `pubdocs/04_features/kiosk_exchange_v2/api_spec.md`
> MQTT 主題完整規範見 `brains/knowledge/MQTT_TOPIC_STANDARD.md`

---

## Glossary

- **Kiosk**: A physical machine consisting of an ESP32 controller (IOTkiosk_v0 firmware), iHub tablet, and ICT 104U bill acceptor
- **Member**: A registered user who has completed LINE SSO authentication
- **Session**: A time-bound interaction between a member and a kiosk, from QR code scan to session end
- **Escrow**: Temporary holding state where a bill is validated but not yet accepted or rejected
- **Token**: Virtual currency credited to member accounts (1 TWD = 1 token by default)
- **Alliance**: The manufacturing and pairing system responsible for hardware binding
- **iHub**: Android tablet application that displays kiosk status and user interface
- **Infra**: Infrastructure layer providing database, MQTT broker, and internal APIs
- **Member_System**: Member-facing web application handling authentication and transactions

---

## Requirements

### Requirement 1: Hardware Pairing and Initialization

**User Story:** As an Alliance operator, I want to pair ESP32 controllers with iHub tablets during manufacturing, so that each kiosk has a unique identity for subsequent operations.

#### Acceptance Criteria

1. WHEN an Alliance operator burns firmware to an ESP32, THE Alliance_System SHALL capture the `esp32_mac` address
2. WHEN an Alliance operator selects an iHub tablet, THE Alliance_System SHALL capture the `screen_mac` address
3. WHEN pairing is submitted, THE Alliance_System SHALL generate a unique `node_id` in format `kiosk_NNN` (lowercase)
4. THE Alliance_System SHALL store the pairing record in `iotv9.kiosks` table with `esp32_mac` (lowercase), `screen_mac` (original case), `node_id` (lowercase), `venue_id`, and `factory_token`
5. WHEN an `esp32_mac` already exists, THE Alliance_System SHALL update the existing record instead of creating a duplicate
6. WHEN a `screen_mac` is already paired to a different ESP32, THE Alliance_System SHALL prevent the pairing and return an error
7. THE Alliance_System SHALL generate a 32-character random `factory_token` for each kiosk

---

### Requirement 2: Member Authentication

**User Story:** As a member, I want to log in using my LINE account, so that I can securely access the token exchange service.

#### Acceptance Criteria

1. WHEN a member clicks "LINE Login", THE Member_System SHALL redirect to LINE OAuth authorization page
2. WHEN LINE authorization succeeds, THE Member_System SHALL receive `userId`, `displayName`, and `pictureUrl` from LINE
3. WHEN a `line_user_id` does not exist in the system, THE Member_System SHALL create a new member record and LINE binding record
4. WHEN a `line_user_id` already exists, THE Member_System SHALL retrieve the existing member record
5. THE Member_System SHALL issue a Sanctum Bearer token in format `{id}|{plaintext}` (e.g., `69|4j6r7q...`)
6. THE Member_System SHALL return the token to the frontend for storage in localStorage
7. THE Member_System SHALL validate Bearer tokens for subsequent API requests using `auth:sanctum` middleware with fallback to manual token lookup

---

### Requirement 3: iHub Tablet Initialization

**User Story:** As a kiosk operator, I want the iHub tablet to automatically identify itself on startup, so that it can establish communication with backend systems without manual configuration.

#### Acceptance Criteria

1. WHEN the iHub tablet starts, THE iHub_App SHALL retrieve its `screen_mac` using hardware ID or fingerprint
2. THE iHub_App SHALL query Infra for the corresponding `node_id` and `esp32_mac` using the `screen_mac`
3. WHEN the `screen_mac` is not found in the pairing database, THE Infra SHALL return a "not paired" error
4. THE iHub_App SHALL register itself with Infra by sending `screen_mac` and `node_id`
5. THE iHub_App SHALL establish a WebSocket connection to Member_System and subscribe to channel `kiosk.{node_id}` (lowercase)
6. THE iHub_App SHALL start a heartbeat timer that sends `POST /api/kiosk/heartbeat` every 60 seconds
7. THE iHub_App SHALL display an idle screen prompting users to tap to begin

---

### Requirement 4: QR Code Generation

**User Story:** As a member, I want to see a QR code on the kiosk screen when I tap it, so that I can scan it with my phone to start the exchange process.

#### Acceptance Criteria

1. WHEN a user taps the iHub screen, THE iHub_App SHALL request a token from Member_System
2. THE Member_System SHALL create or retrieve an active session for the kiosk with `status='active'` and `member_id=NULL`
3. WHEN no active session exists, THE Member_System SHALL generate a new 32-character random token and set `token_expires_at` to 300 seconds (5 minutes) from now
4. WHEN an active session exists with a valid (non-expired) token, THE Member_System SHALL return the existing token without generating a new one
5. WHEN an active session exists with an expired token, THE Member_System SHALL generate a new token and update `token_expires_at`
6. THE iHub_App SHALL display a QR code containing the URL `https://win.tg25.win/kiosk?id={node_id}&token={token}` (node_id all lowercase) — **Updated 2026-05-13: Phase 2 URL format, replaces legacy `KIOSK:{node_id}:TOKEN:{token}` string format**
7. THE iHub_App SHALL display a 5-minute countdown timer
8. WHEN the countdown reaches zero, THE iHub_App SHALL return to the idle screen without requesting a new token

---

### Requirement 5: Member Binding to Kiosk

**User Story:** As a member, I want to scan the kiosk QR code with my phone, so that I can bind my account to the kiosk and enable bill acceptance.

#### Acceptance Criteria

1. WHEN a member scans a QR code, THE Member_App SHALL parse the `kiosk_id` and `token` from the URL format `https://win.tg25.win/kiosk?id={kiosk_id}&token={token}` — **Updated 2026-05-13: Phase 2 URL format**
2. THE Member_App SHALL send a bind request with Bearer token, `kiosk_id`, and `token` to Member_System
3. THE Member_System SHALL validate the Bearer token to identify the member
4. THE Member_System SHALL query the kiosk session using `kiosk_id` and `status='active'` with row-level locking to prevent race conditions
5. WHEN the session's `member_id` is not NULL, THE Member_System SHALL return HTTP 409 "kiosk busy" error
6. WHEN the token does not match or is expired, THE Member_System SHALL return HTTP 422 "token expired" error
7. WHEN the member has another active session on a different kiosk, THE Member_System SHALL automatically end the old session with `end_reason='new_session_started'`, send disable command to the old kiosk, and broadcast `.KioskSessionEnded` event
8. THE Member_System SHALL query Infra for `esp32_mac`, `kiosk_no`, and `venue_id` using the `node_id`
9. THE Member_System SHALL update the session with `member_id`, `esp32_mac`, `kiosk_no`, `started_at`, and `member_last_seen_at`
10. THE Member_System SHALL instruct Infra to publish MQTT command `{"action":"enable"}` to topic `kiosk/{esp32_mac}/cmd` with QoS 2
11. THE Firmware SHALL receive the enable command and send RS232 signal 0x3E to the bill acceptor, changing its state to IDLE (green light)
12. THE Member_System SHALL broadcast `.MemberBoundToKiosk` event to WebSocket channel `kiosk.{kiosk_id}` with session details including `member_id`, `member_name`, and `member_phone` (full number, iHub masks to last 4 digits)
13. THE iHub_App SHALL receive the event and display the active screen showing member name
14. THE Member_App SHALL receive the bind response containing `session_id`, `kiosk_id`, `esp32_mac`, and member details

---

### Requirement 6: Bill Acceptance with Human Confirmation

**User Story:** As a member, I want to confirm my identity before bills are accepted, so that I can prevent others from accidentally depositing money into my account.

#### Acceptance Criteria

1. WHEN a bill is inserted into the acceptor, THE Firmware SHALL validate the bill and place it in escrow state
2. THE Firmware SHALL send Hold command (RS232: 0x18) every 2 seconds to extend escrow timeout from 5 seconds to 5 minutes
3. THE Firmware SHALL publish MQTT event `{"event":"escrow","event_id":"...","amount":100,"timestamp":...}` to topic `kiosk/{esp32_mac}/event` with QoS 2
4. THE Infra_Listener SHALL receive the escrow event and forward it to Member_System via `POST /internal/kiosk/escrow`
5. THE Member_System SHALL query the active session using `kiosk_id` and return member name, phone number (masked), and tokens to be credited
6. THE Infra SHALL broadcast `.KioskEscrowPending` event to WebSocket channel `kiosk.{kiosk_id}` with member details and 15-second timeout
7. THE iHub_App SHALL display a confirmation screen showing member name, phone (last 4 digits visible), amount, tokens, and a 15-second countdown with "Confirm" and "Cancel" buttons
8. WHEN the user clicks "Confirm", THE iHub_App SHALL call `POST /api/kiosk/escrow/confirm` and Member_System SHALL return `{"action":"stack"}`
9. WHEN the user clicks "Cancel", THE iHub_App SHALL call `POST /api/kiosk/escrow/reject` and Member_System SHALL return `{"action":"reject","reason":"user_cancelled"}`
10. WHEN 15 seconds elapse without user action, THE Firmware SHALL automatically send RS232 reject command (0x0F) as a fail-safe mechanism
11. THE Infra SHALL publish the stack or reject command to MQTT topic `kiosk/{esp32_mac}/cmd` with QoS 2
12. THE Firmware SHALL receive the command, stop sending Hold signals, and execute the corresponding RS232 command (0x02 for Accept or 0x0F for Reject)

---

### Requirement 7: Token Crediting with Idempotency

**User Story:** As a member, I want my tokens to be credited immediately and accurately when bills are accepted, so that I can see my balance update in real-time.

#### Acceptance Criteria

1. WHEN the bill acceptor confirms a bill is stacked (RS232: 0x10), THE Firmware SHALL publish MQTT event `{"event":"stacked","event_id":"...","amount":100,"timestamp":...}` to topic `kiosk/{esp32_mac}/event` with QoS 2
2. THE Infra_Listener SHALL receive the stacked event and forward it to Member_System via `POST /internal/kiosk/stacked`
3. THE Member_System SHALL check if the `event_id` already exists in `kiosk_transactions` table
4. WHEN the `event_id` exists, THE Member_System SHALL return success with `idempotent: true` without performing any database writes
5. WHEN the `event_id` does not exist, THE Member_System SHALL query the active session using `kiosk_id` with row-level locking
6. THE Member_System SHALL calculate `tokens_credited = amount / venue.token_value_twd` (default 1.0 if not set)
7. THE Member_System SHALL execute a database transaction that atomically: (a) increments `kiosk_sessions.total_deposited` by the amount, (b) increments `members.token_balance` by `tokens_credited`, and (c) inserts a record into `kiosk_transactions` with `event_id`, `session_id`, `member_id`, `kiosk_id`, `amount_twd`, `tokens_credited`, and `transaction_type='deposit'`
8. WHEN the database transaction fails, THE Member_System SHALL rollback all changes and return an error
9. THE Member_System SHALL broadcast `.KioskSessionUpdated` event to WebSocket channel `kiosk.{kiosk_id}` with `session_id`, `total_deposited`, `tokens_credited`, and `member_id`
10. THE iHub_App SHALL receive the event and display a deposit success animation
11. THE Member_App SHALL receive the event and update the displayed balance with an animation
12. THE Firmware SHALL return to IDLE state (green light) ready to accept the next bill

---

### Requirement 8: Bill Rejection Handling

**User Story:** As a member, I want rejected bills to be returned safely, so that I can retrieve my money and try again if needed.

#### Acceptance Criteria

1. WHEN a reject command is received or fail-safe timeout occurs, THE Firmware SHALL send RS232 reject command (0x0F) to the bill acceptor
2. WHEN the bill acceptor confirms the bill is returned (RS232: 0x11), THE Firmware SHALL publish MQTT event `{"event":"rejected","event_id":"...","amount":100,"reason":"...","timestamp":...}` to topic `kiosk/{esp32_mac}/event` with QoS 2
3. THE Infra_Listener SHALL receive the rejected event and forward it to Member_System via `POST /internal/kiosk/rejected`
4. THE Member_System SHALL log the rejection event without modifying session or member balances
5. THE Firmware SHALL return to IDLE state (green light) ready to accept the next bill
6. WHEN the rejection reason is "user_cancelled", THE iHub_App SHALL display a message prompting the user to scan their QR code

---

### Requirement 9: Session Heartbeat

**User Story:** As a system operator, I want to detect when members are offline or inactive, so that sessions can be automatically terminated to free up kiosks.

#### Acceptance Criteria

1. THE Member_App SHALL send `POST /api/kiosk/session/{id}/heartbeat` with Bearer token every 30 seconds while a session is active
2. THE Member_System SHALL update `kiosk_sessions.member_last_seen_at` to the current timestamp upon receiving a heartbeat
3. THE iHub_App SHALL send `POST /api/kiosk/heartbeat` with `X-Internal-Key` and `kiosk_id` every 60 seconds
4. THE Member_System SHALL update `kiosk_sessions.last_active_at` to the current timestamp upon receiving a kiosk heartbeat
5. WHEN no active session exists for the kiosk, THE Member_System SHALL silently succeed without error

---

### Requirement 10: Manual Session Termination

**User Story:** As a member, I want to manually end my exchange session, so that I can complete the transaction and free the kiosk for the next user.

#### Acceptance Criteria

1. WHEN a member clicks "End Exchange" in the app, THE Member_App SHALL send `POST /api/kiosk/session/{id}/end` with Bearer token and `reason='manual'`
2. THE Member_System SHALL validate the Bearer token and verify the session belongs to the member
3. WHEN the session status is already 'ended', THE Member_System SHALL return HTTP 409 with the existing `ended_at` timestamp (idempotent behavior)
4. THE Member_System SHALL update the session with `status='ended'`, `ended_at=now()`, and `end_reason='manual'`
5. THE Member_System SHALL instruct Infra to publish MQTT command `{"action":"disable"}` to topic `kiosk/{esp32_mac}/cmd` with QoS 2
6. THE Firmware SHALL receive the disable command and send RS232 signal 0x5E to the bill acceptor, changing its state to DISABLED (red light)
7. THE Member_System SHALL broadcast `.KioskSessionEnded` event to WebSocket channel `kiosk.{kiosk_id}` with `session_id`, `total_deposited`, `tokens_credited`, `end_reason`, `ended_at`, and a user-friendly message
8. THE iHub_App SHALL display a completion screen for 8 seconds showing the total amount and tokens, then return to idle screen
9. THE Member_App SHALL display the session summary for 3 seconds, then return to the home screen

---

### Requirement 11: Timeout-Based Session Termination

**User Story:** As a member, I want my session to automatically end after 60 seconds of inactivity, so that I don't have to manually end it if I forget.

#### Acceptance Criteria

1. THE Member_App SHALL start a 60-second countdown timer after each bill is credited
2. WHEN a new bill is credited (`.KioskSessionUpdated` event received), THE Member_App SHALL reset the countdown timer to 60 seconds
3. WHEN the countdown reaches zero, THE Member_App SHALL automatically send `POST /api/kiosk/session/{id}/end` with `reason='timeout'`
4. THE subsequent termination flow SHALL follow the same steps as manual termination (Requirement 10)
5. THE iHub_App SHALL display "Session ended due to inactivity" message

---

### Requirement 12: Offline Detection and Cleanup

**User Story:** As a system operator, I want sessions to be automatically terminated when members go offline, so that kiosks don't remain locked indefinitely.

#### Acceptance Criteria

1. THE Member_System SHALL run a scheduled task every 1 minute to detect offline sessions
2. THE scheduled task SHALL query sessions with `status='active'` AND `member_last_seen_at < now() - 60 seconds`
3. FOR EACH offline session, THE Member_System SHALL update `status='ended'`, `ended_at=now()`, and `end_reason='offline'`
4. THE Member_System SHALL send disable command to the kiosk firmware via Infra
5. THE Member_System SHALL broadcast `.KioskSessionEnded` event with `end_reason='offline'`
6. THE iHub_App SHALL display "Member offline, session ended" message

---

### Requirement 13: System Cleanup for Stale Sessions

**User Story:** As a system operator, I want a fail-safe mechanism to clean up sessions that remain active for more than 10 minutes, so that system integrity is maintained even in case of bugs.

#### Acceptance Criteria

1. THE Member_System SHALL run a scheduled task every 5 minutes to detect stale sessions
2. THE scheduled task SHALL query sessions with `status='active'` AND `last_active_at < now() - 10 minutes`
3. FOR EACH stale session, THE Member_System SHALL update `status='ended'`, `ended_at=now()`, and `end_reason='system_cleanup'`
4. THE Member_System SHALL send disable command to the kiosk firmware via Infra
5. THE Member_System SHALL broadcast `.KioskSessionEnded` event with `end_reason='system_cleanup'`
6. THE Member_System SHALL log an alert for manual investigation, as this indicates a potential system bug

---

### Requirement 14: iHub Idle Timer

**User Story:** As a kiosk operator, I want the iHub to automatically end sessions after 5 minutes of no bill insertion, so that the kiosk returns to idle state for the next user.

#### Acceptance Criteria

1. WHEN a member binds to the kiosk, THE iHub_App SHALL start a 5-minute (300-second) idle timer
2. WHEN a bill is credited (`.KioskSessionUpdated` event received), THE iHub_App SHALL reset the idle timer to 5 minutes
3. WHEN the idle timer expires, THE iHub_App SHALL send `POST /api/kiosk/complete` with `X-Internal-Key` and `kiosk_id`
4. THE Member_System SHALL query the active session for the kiosk and end it with `end_reason='ihub_timeout'`
5. THE subsequent termination flow SHALL follow the same steps as manual termination (Requirement 10)

---

### Requirement 15: Multi-Kiosk Seamless Switching

**User Story:** As a member, I want to seamlessly switch between kiosks without being blocked, so that I can move to a different machine if needed.

#### Acceptance Criteria

1. WHEN a member scans a QR code on kiosk B while having an active session on kiosk A, THE Member_System SHALL detect the existing active session
2. THE Member_System SHALL automatically end the session on kiosk A with `end_reason='new_session_started'`
3. THE Member_System SHALL send disable command to kiosk A firmware
4. THE Member_System SHALL broadcast `.KioskSessionEnded` event to kiosk A's WebSocket channel
5. THE iHub_App on kiosk A SHALL display "Member started exchange on another kiosk" message for 8 seconds, then return to idle
6. THE Member_System SHALL create a new active session on kiosk B and send enable command to kiosk B firmware
7. THE Member_System SHALL broadcast `.MemberBoundToKiosk` event to kiosk B's WebSocket channel
8. THE member SHALL be able to continue exchanging on kiosk B without any error or rejection

---

### Requirement 16: Firmware Fail-Safe Mechanisms

**User Story:** As a system operator, I want the firmware to have built-in fail-safe mechanisms, so that bills are never permanently stuck in escrow state.

#### Acceptance Criteria

1. WHEN the firmware boots, THE Firmware SHALL send RS232 disable command (0x5E) to the bill acceptor, setting it to DISABLED state (red light) by default
2. THE Firmware SHALL only enable the bill acceptor after receiving an explicit enable command from the cloud
3. WHEN a bill enters escrow state, THE Firmware SHALL start a 15-second fail-safe timer
4. THE Firmware SHALL send RS232 Hold command (0x18) every 2 seconds to extend the hardware escrow timeout from 5 seconds to 5 minutes
5. WHEN 15 seconds elapse without receiving a stack or reject command from the cloud, THE Firmware SHALL automatically send RS232 reject command (0x0F) to return the bill
6. WHEN a stack or reject command is received, THE Firmware SHALL stop sending Hold commands and clear the fail-safe timer
7. WHEN the firmware receives a disable command, THE Firmware SHALL send RS232 disable command (0x5E) to the bill acceptor, changing it to DISABLED state (red light)

---

### Requirement 17: Data Consistency and Idempotency

**User Story:** As a system operator, I want all financial transactions to be idempotent and atomic, so that no money is lost or double-credited due to network retries or system failures.

#### Acceptance Criteria

1. THE `kiosk_transactions` table SHALL have a UNIQUE index on `event_id` to prevent duplicate transaction records
2. WHEN processing a stacked event, THE Member_System SHALL first check if the `event_id` already exists in `kiosk_transactions`
3. WHEN the `event_id` exists, THE Member_System SHALL return success immediately without performing any database writes
4. WHEN the `event_id` does not exist, THE Member_System SHALL use a database transaction to ensure all writes (session update, member balance update, transaction record insert) succeed or fail atomically
5. THE Member_System SHALL use row-level locking (`lockForUpdate`) when querying sessions to prevent concurrent updates from overwriting each other
6. THE Member_System SHALL use delta updates (`total_deposited += amount`) instead of absolute assignments to prevent data loss in concurrent scenarios
7. WHEN a database transaction fails, THE Member_System SHALL rollback all changes and return an error without broadcasting any WebSocket events

---

### Requirement 18: Security and Authentication

**User Story:** As a system operator, I want all internal APIs to be protected with authentication keys, so that unauthorized systems cannot manipulate kiosk sessions or financial data.

#### Acceptance Criteria

1. THE Member_System SHALL validate `X-Internal-Key` header for all `/internal/*` endpoints
2. THE Member_System SHALL validate `Authorization: Bearer {token}` header for all member-facing `/api/*` endpoints, **except** iHub-facing endpoints which use `X-Internal-Key` instead (e.g., `/api/kiosk/escrow/confirm`, `/api/kiosk/escrow/reject`, `/api/kiosk/heartbeat`, `/api/kiosk/complete`)
3. WHEN a Bearer token is invalid or expired, THE Member_System SHALL return HTTP 401 "Unauthenticated"
4. THE Member_System SHALL implement a fallback mechanism using `PersonalAccessToken::findToken()` when the `auth:sanctum` middleware fails
5. THE Infra SHALL validate `X-Internal-Key` header for all internal MQTT publish requests
6. THE Firmware SHALL subscribe to MQTT topics with appropriate QoS levels (QoS 2 for events, QoS 2 for commands)
7. THE MQTT Broker SHALL enforce ACL rules to ensure only authorized clients can publish to `kiosk/{esp32_mac}/cmd` and subscribe to `kiosk/{esp32_mac}/event`

---

### Requirement 19: Real-Time Communication

**User Story:** As a member and kiosk operator, I want to see real-time updates on both the phone and tablet, so that I have immediate feedback on all actions.

#### Acceptance Criteria

1. THE Member_System SHALL use Laravel Reverb to broadcast WebSocket events to channel `kiosk.{kiosk_id}` (lowercase)
2. THE iHub_App SHALL subscribe to channel `kiosk.{kiosk_id}` and listen for events: `.MemberBoundToKiosk`, `.KioskEscrowPending`, `.KioskSessionUpdated`, `.KioskSessionEnded`
3. THE Member_App SHALL subscribe to channel `kiosk.{kiosk_id}` after successful binding and listen for events: `.KioskSessionUpdated`, `.KioskSessionEnded`
4. WHEN a member binds to a kiosk, THE Member_System SHALL broadcast `.MemberBoundToKiosk` with `session_id`, `kiosk_id`, and member details
5. WHEN a bill enters escrow, THE Infra SHALL broadcast `.KioskEscrowPending` with `event_id`, `amount`, `tokens_credited`, member name, phone (masked), and 15-second timeout
6. WHEN a bill is credited, THE Member_System SHALL broadcast `.KioskSessionUpdated` with `session_id`, `total_deposited`, `tokens_credited`, and `member_id`
7. WHEN a session ends, THE Member_System SHALL broadcast `.KioskSessionEnded` with `session_id`, `total_deposited`, `tokens_credited`, `end_reason`, `ended_at`, and a user-friendly message

---

### Requirement 20: Error Handling and User Feedback

**User Story:** As a member, I want clear error messages when something goes wrong, so that I know what action to take.

#### Acceptance Criteria

1. WHEN a member scans an expired QR code, THE Member_System SHALL return HTTP 422 with error "QR Code expired, please tap the screen again"
2. WHEN a member tries to bind to a busy kiosk, THE Member_System SHALL return HTTP 409 with error "This kiosk is currently in use by another member"
3. WHEN a member's Bearer token is invalid, THE Member_System SHALL return HTTP 401 with error "Unauthenticated"
4. WHEN a session is not found, THE Member_System SHALL return HTTP 404 with error "Session not found"
5. WHEN Infra API is unreachable, THE Member_System SHALL return HTTP 500 with error "System error, please try again later"
6. WHEN a bill is rejected due to timeout, THE iHub_App SHALL display "Confirmation timeout, bill returned"
7. WHEN a bill is rejected due to user cancellation, THE iHub_App SHALL display "Please scan your QR code" prompt
8. WHEN a session ends due to member offline, THE iHub_App SHALL display "Member offline, session ended"

---

### Requirement 21: iHub Force-End Button

**User Story:** As a kiosk operator or next user, I want to be able to forcibly end a session that was abandoned without being ended, so that the kiosk can be freed for the next user.

#### Acceptance Criteria

1. THE iHub_App SHALL display a force-end button on the active screen showing the current member's name, member ID (`#id`), and last 4 digits of phone number (omitted if member has no phone on file)
2. Button display format: `[✕ 結束 {name}（#{id} · {last4}）的兌換]` or `[✕ 結束 {name}（#{id}）的兌換]` when no phone
3. WHEN the force-end button is clicked, THE iHub_App SHALL send `POST /api/kiosk/complete` with `X-Internal-Key` and `kiosk_id`
4. THE Member_System SHALL end the session with `end_reason='ihub_force_ended'` and follow the same termination flow as Requirement 10
5. THE iHub_App SHALL NOT require a Bearer token for this action (uses `X-Internal-Key` only)
6. THE `POST /api/kiosk/complete` endpoint SHALL accept an optional `reason` parameter: `'ihub_timeout'` (default, idle timer expired) or `'ihub_force_ended'` (force-end button clicked)

---

---

### Requirement 22: Infra Listener Health Monitoring

**User Story:** As a system operator, I want to know immediately when the Infra Listener stops receiving MQTT messages, so that I can detect silent failures before they affect real transactions.

#### Acceptance Criteria

1. THE Infra_Listener SHALL log a WARNING if no MQTT message is received within 5 minutes
2. THE Infra_Listener SHALL send an alert to Chat Bridge when no MQTT message is received within 10 minutes
3. THE Infra_Listener SHALL log its MQTT connection status on startup and on reconnect
4. THE Infra_Listener error log SHALL truncate HTTP response bodies to 200 characters maximum to prevent log flooding

---

### Requirement 23: Device Cache Auto-Sync

**User Story:** As a system operator, I want the Infra Listener's device cache to stay in sync with the pairing database, so that new kiosks work immediately after Alliance pairing without requiring a manual restart.

#### Acceptance Criteria

1. WHEN Alliance completes a new kiosk pairing, THE Alliance_System SHALL call `POST /api/internal/cache/reload` on Infra to trigger a cache refresh
2. THE Infra_Listener SHALL reload its device cache from `iotv9.kiosks` every 10 minutes automatically
3. THE Infra_Listener SHALL log the number of devices loaded on each cache reload
4. WHEN a `chip_id` is not found in the device cache, THE Infra_Listener SHALL log an ERROR and skip the event — it SHALL NOT use chip_id as a node_id fallback

---

### Requirement 24: Internal API Smoke Test

**User Story:** As a system operator, I want to verify that all internal API endpoints are working after each deployment, so that broken routes are caught immediately rather than during live transactions.

#### Acceptance Criteria

1. A smoke test script SHALL exist that verifies the following endpoints return non-404/405 responses:
   - `POST /internal/kiosk/escrow`
   - `POST /internal/kiosk/stacked`
   - `POST /internal/kiosk/rejected`
2. THE smoke test SHALL be run after every Member deployment
3. THE smoke test SHALL use `X-Internal-Key` authentication and send minimal valid payloads
4. WHEN any endpoint returns 404 or 405, THE smoke test SHALL output a clear error message identifying the failing route

---

### Requirement 25: Engineering Dashboard Real-Time Tablet Status

**User Story:** As a system operator, I want to see the real-time online/offline status of kiosk tablets on the engineering dashboard, so that I can quickly identify which kiosks are operational without querying the database.

#### Acceptance Criteria

1. THE iHub_App SHALL send a WebSocket whisper event `tablet-heartbeat` to channel `engineering.{kiosk_id}` every 30 seconds after initialization
2. THE whisper event SHALL contain `kiosk_id` and `timestamp` in the payload
3. THE Engineering_Dashboard SHALL subscribe to channel `engineering.{kiosk_id}` when a kiosk is selected for monitoring
4. THE Engineering_Dashboard SHALL listen for `tablet-heartbeat` whisper events using `listenForWhisper()`
5. WHEN a heartbeat is received, THE Engineering_Dashboard SHALL update `lastTabletHeartbeat` to the current timestamp and set `tabletStatus` to 'online'
6. THE Engineering_Dashboard SHALL check the elapsed time since `lastTabletHeartbeat` every 1 second
7. WHEN elapsed time is less than 31 seconds, THE Engineering_Dashboard SHALL display status as "在線 (Xs 前)" with green indicator
8. WHEN elapsed time is 31 seconds or more, THE Engineering_Dashboard SHALL display status as "離線 (Xs 前)" with red indicator
9. WHEN no heartbeat has ever been received, THE Engineering_Dashboard SHALL display status as "從未連線" with gray indicator
10. THE iHub_App SHALL NOT send HTTP heartbeat requests to Member_System for tablet status tracking (removed to reduce server load)
11. THE Member_System SHALL NOT store or track tablet online status in the database (status is ephemeral and only visible on Engineering_Dashboard)
12. THE whisper mechanism SHALL be client-to-client communication and SHALL NOT involve Member_System backend processing

#### Technical Notes

- **Whisper**: Client-to-client WebSocket communication that bypasses the server
- **Heartbeat Interval**: 30 seconds (iHub sends)
- **Offline Threshold**: 31 seconds (Engineering Dashboard judges)
- **No Database**: Tablet status is not persisted, only real-time monitoring
- **No HTTP Polling**: Engineering Dashboard does not poll `/api/engineering/tablet-status`

---

## Document Metadata

**Version**: 1.3.0  
**Status**: Draft  
**Created**: 2026-05-02  
**Updated**: 2026-05-08  
**Author**: HQ  
**Workflow**: Design-First  
**Source**: Phase 0-6 Technical Design Documents + 2026-05-03 實機測試發現 + 2026-05-08 工程頁面優化  
**Changes in v1.3.0**:
- Req 25: 新增工程頁面即時顯示平板在線狀態需求（使用 WebSocket whisper，不經過後端，不寫資料庫）
**Changes in v1.2.0**:
- Req 22: 新增 Infra Listener 健康監控需求
- Req 23: 新增 device cache 自動同步需求（含 cache miss 不得 fallback）
- Req 24: 新增 internal API smoke test 需求
**Changes in v1.1.0**:
- Req 7.5: 修正 stacked 查詢 session 用 `kiosk_id`（非 `esp32_mac`）
- Req 14: idle timer 明確為 300 秒（5 分鐘）
- Req 18.2: 加入 iHub 端點使用 `X-Internal-Key` 的例外說明
- Req 21: 新增 iHub 強制結束按鈕需求
- Req 5.12: `.MemberBoundToKiosk` payload 新增 `member_phone`
