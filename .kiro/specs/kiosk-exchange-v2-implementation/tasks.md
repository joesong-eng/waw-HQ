# Implementation Plan: Kiosk Exchange v2

## Overview

This implementation plan breaks down the Kiosk Exchange v2 system into actionable coding tasks across four main systems: Alliance (hardware pairing), Member (authentication and transactions), iHub (tablet interface), and Infra (infrastructure APIs). The implementation follows a phased approach from Phase 0 (hardware binding) through Phase 6 (session termination), with tasks organized by system ownership and dependency order.

**Key Implementation Areas:**
- **Alliance (Allie)**: Hardware pairing validation and node_id lowercase enforcement
- **Member (Mina)**: Complete rewrite of KioskController, InternalController, KioskTransaction model, scheduled tasks
- **iHub (Hubie)**: Confirmation screens, idle screen, event listeners, heartbeat timer
- **Infra (Ina)**: API migrations (node-id, kiosk/info), MQTT publish endpoint

**Programming Language**: PHP (Laravel 11) for backend, JavaScript for iHub frontend

---

## Tasks

### 1. Alliance: Hardware Pairing Validation

- [x] 1.1 Validate node_id lowercase enforcement in Alliance burning system
  - Verify `strtolower()` is applied to `node_id` before writing to `iotv9.kiosks`
  - Verify `strtolower()` is applied to `esp32_mac` before writing
  - Ensure `screen_mac` preserves original case
  - _Requirements: 1.3, 1.4_

- [ ]* 1.2 Write unit tests for Alliance pairing validation
  - Test node_id format validation (lowercase, kiosk_NNN pattern)
  - Test esp32_mac format validation (lowercase, no colons)
  - Test duplicate screen_mac prevention
  - _Requirements: 1.5, 1.6_

---

### 2. Infra: API Migration and Infrastructure

- [x] 2.1 Migrate GET /api/kiosk/node-id from Member to Infra
  - Create `KioskController@nodeId` in Infra project
  - Query `iotv9.kiosks` using `screen_mac` parameter
  - Return `node_id` (lowercase), `esp32_mac` (lowercase)
  - Implement `X-Internal-Key` authentication
  - _Requirements: 3.2, 3.3_

- [x] 2.2 Create GET /api/kiosk/info endpoint in Infra
  - Create `KioskController@kioskInfo` method
  - Query `iotv9.kiosks` using `node_id` parameter
  - Return `kiosk_no`, `node_id`, `esp32_mac`, `venue_id`, `status`
  - Force lowercase on `esp32_mac` in response
  - Implement `X-Internal-Key` authentication
  - _Requirements: 5.8, 5.9_
  - **Completed**: 2026-05-02 by Ina (Infra Master)

- [ ]* 2.3 Write integration tests for Infra kiosk APIs
  - Test node-id lookup with valid screen_mac
  - Test node-id lookup with non-existent screen_mac (404)
  - Test kiosk/info with valid node_id
  - Test kiosk/info with non-existent node_id (404)
  - _Requirements: 3.2, 5.8_

- [x] 2.4 Verify POST /api/internal/mqtt/publish endpoint
  - Confirm endpoint exists and handles QoS 2 for commands
  - Verify `X-Internal-Key` authentication
  - Test MQTT publish to `kiosk/{esp32_mac}/cmd` topic
  - _Requirements: 5.10, 18.5_
  - **Completed**: 2026-05-02 by Ina (Infra Master)

---

### 3. Member: Authentication and Session Management

- [-] 3.1 Verify LINE SSO authentication flow
  - Confirm `LineLoginController@redirect` and `@callback` work correctly
  - Verify Sanctum token generation (format: `{id}|{plaintext}`)
  - Test fallback mechanism using `PersonalAccessToken::findToken()`
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [ ]* 3.2 Write unit tests for LINE authentication
  - Test LINE OAuth redirect URL generation
  - Test callback handling with valid LINE code
  - Test member creation for new LINE users
  - Test token validation with auth:sanctum middleware
  - Test fallback token validation
  - _Requirements: 2.1, 2.2, 2.3, 2.7_

- [-] 3.3 Update POST /api/kiosk/token to use 300-second expiry
  - Modify `KioskController@refreshToken` method
  - Change `addSeconds(90)` to `addSeconds(300)`
  - Verify token reuse logic (only regenerate if expired)
  - _Requirements: 4.3, 4.4, 4.5_

- [-] 3.4 Create POST /api/kiosk/heartbeat endpoint
  - Create `KioskController@kioskHeartbeat` method
  - Accept `kiosk_id` parameter with `X-Internal-Key` authentication
  - Update `kiosk_sessions.last_active_at` for active sessions
  - Return success silently if no active session exists
  - _Requirements: 9.3, 9.4, 9.5_

- [ ]* 3.5 Write unit tests for kiosk heartbeat
  - Test heartbeat updates last_active_at
  - Test heartbeat with no active session (silent success)
  - Test heartbeat with invalid kiosk_id
  - _Requirements: 9.3, 9.4_

---

### 4. Checkpoint - Verify Infrastructure APIs

- [ ] 4. Ensure all tests pass, ask the user if questions arise.

---

### 5. Member: Kiosk Binding Implementation

- [-] 5.1 Update POST /api/kiosk/bind to call Infra GET /api/kiosk/info
  - Remove direct query to `iotv9.kiosks` (DB::connection('mysql_v9'))
  - Replace with HTTP call to `https://api.tg25.win/api/kiosk/info?node_id={kiosk_id}`
  - Use `X-Internal-Key` for authentication
  - Handle Infra API errors (500 response)
  - _Requirements: 5.8, 5.9, 18.1_

- [-] 5.2 Implement multi-kiosk seamless switching in bind logic
  - Check for existing active session for the member
  - If found, automatically end old session with `end_reason='new_session_started'`
  - Send disable command to old kiosk firmware
  - Broadcast `.KioskSessionEnded` to old kiosk WebSocket channel
  - Continue with new session creation
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8_

- [-] 5.3 Verify bind API uses lockForUpdate for race condition protection
  - Confirm `lockForUpdate()` is used when querying kiosk_sessions
  - Verify member_id null check prevents concurrent binds
  - Test concurrent bind attempts return 409 for second request
  - Verify `.MemberBoundToKiosk` payload includes `member.id`, `member.name`, `member.phone` (full number)
  - _Requirements: 5.4, 5.5, 17.5_

- [ ]* 5.4 Write integration tests for kiosk bind
  - Test successful bind with valid token
  - Test bind with expired token (422)
  - Test bind with busy kiosk (409)
  - Test multi-kiosk switching (old session ends, new session starts)
  - Test concurrent bind attempts (race condition)
  - _Requirements: 5.1-5.14, 15.1-15.8_

---

### 6. Member: Bill Acceptance Flow - Escrow Phase

- [-] 6.1 Create POST /internal/kiosk/escrow endpoint
  - Create `InternalController@kioskEscrow` method
  - Accept `kiosk_id`, `esp32_mac`, `amount`, `event_id` parameters
  - Query active session using `kiosk_id`
  - Return member name, phone (full), and tokens_credited
  - Return 404 if no active session found
  - Implement `X-Internal-Key` authentication
  - _Requirements: 6.3, 6.4, 6.5_

- [-] 6.2 Create POST /api/kiosk/escrow/confirm endpoint
  - Create `KioskController@escrowConfirm` method
  - Accept `kiosk_id` and `event_id` parameters
  - Verify session exists and is active
  - Return `{"action":"stack"}` for Infra to forward to firmware
  - Implement `X-Internal-Key` authentication
  - _Requirements: 6.8_

- [-] 6.3 Create POST /api/kiosk/escrow/reject endpoint
  - Create `KioskController@escrowReject` method
  - Accept `kiosk_id` and `event_id` parameters
  - Verify session exists
  - Return `{"action":"reject","reason":"user_cancelled"}`
  - Implement `X-Internal-Key` authentication
  - _Requirements: 6.9_

- [ ]* 6.4 Write unit tests for escrow endpoints
  - Test escrow returns correct member information
  - Test escrow with no active session (404)
  - Test confirm returns stack action
  - Test reject returns reject action with reason
  - _Requirements: 6.3-6.9_

---

### 7. Member: Bill Acceptance Flow - Stacked Phase

- [-] 7.1 Implement POST /internal/kiosk/stacked with idempotency
  - Create `InternalController@kioskStacked` method
  - Check `kiosk_transactions` for existing `event_id` (idempotency)
  - If exists, return success with `idempotent: true`
  - Query active session using **`kiosk_id`** (not esp32_mac) with `lockForUpdate()`
  - Calculate `tokens_credited = amount / venue.token_value_twd`
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.6, 17.1, 17.2, 17.3_

- [-] 7.2 Implement atomic transaction for stacked event
  - Use DB transaction to wrap all three operations
  - Increment `kiosk_sessions.total_deposited += amount`
  - Increment `members.token_balance += tokens_credited`
  - Insert record into `kiosk_transactions` with event_id
  - Rollback all changes if any operation fails
  - _Requirements: 7.7, 17.4, 17.6, 17.7_

- [-] 7.3 Broadcast .KioskSessionUpdated after stacked
  - Broadcast to WebSocket channel `kiosk.{kiosk_id}` (lowercase)
  - Include `session_id`, `total_deposited`, `tokens_credited`, `member_id`
  - Use Laravel Reverb for WebSocket broadcasting
  - _Requirements: 7.9, 19.6_

- [ ]* 7.4 Write property test for stacked idempotency
  - **Property 1: Idempotency - Same event_id processed multiple times results in single credit**
  - **Validates: Requirements 7.2, 17.2**
  - Generate random event_id and amount
  - Call stacked endpoint multiple times with same event_id
  - Verify only one transaction record exists
  - Verify member balance incremented only once

- [ ]* 7.5 Write unit tests for stacked endpoint
  - Test first stacked event creates transaction
  - Test duplicate event_id returns idempotent response
  - Test atomic transaction rollback on failure
  - Test balance calculation with different token_value_twd
  - Test WebSocket broadcast payload
  - _Requirements: 7.1-7.12, 17.1-17.7_

---

### 8. Member: Bill Acceptance Flow - Rejected Phase

- [-] 8.1 Create POST /internal/kiosk/rejected endpoint
  - Create `InternalController@kioskRejected` method
  - Accept `esp32_mac`, `amount`, `reason` parameters
  - Log rejection event without modifying session or balances
  - Return `{"status":"logged"}`
  - Implement `X-Internal-Key` authentication
  - _Requirements: 8.3, 8.4_

- [ ]* 8.2 Write unit tests for rejected endpoint
  - Test rejection logging
  - Test no balance changes occur
  - Test no session status changes
  - _Requirements: 8.1-8.5_

---

### 9. Checkpoint - Verify Bill Flow Implementation

- [ ] 9. Ensure all tests pass, ask the user if questions arise.

---

### 10. Member: Session Termination - Manual and Timeout

- [-] 10.1 Implement POST /api/kiosk/session/{id}/end endpoint
  - Create `KioskController@memberEndSession` method
  - Verify Bearer token and session ownership
  - Check idempotency: if status='ended', return 409 with existing ended_at
  - Update session: `status='ended'`, `ended_at=now()`, `end_reason` from request
  - Call Infra API to publish disable command to firmware
  - Broadcast `.KioskSessionEnded` to WebSocket channel
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9_

- [-] 10.2 Implement POST /api/kiosk/session/{id}/heartbeat endpoint
  - Create `KioskController@memberHeartbeat` method
  - Verify Bearer token and session ownership
  - Update `member_last_seen_at = now()` for active sessions
  - Return last_seen_at timestamp
  - _Requirements: 9.1, 9.2_

- [ ]* 10.3 Write unit tests for session termination
  - Test manual end with valid session
  - Test end with already ended session (idempotency)
  - Test end with invalid session_id (404)
  - Test heartbeat updates member_last_seen_at
  - Test WebSocket broadcast on session end
  - _Requirements: 10.1-10.9, 9.1-9.2_

---

### 11. Member: Session Termination - Scheduled Cleanup

- [-] 11.1 Create CheckOfflineSessions scheduled task
  - Create `app/Console/Commands/CheckOfflineSessions.php`
  - Query sessions: `status='active' AND member_last_seen_at < now() - 60 seconds`
  - For each session: update status, send disable, broadcast event
  - Set `end_reason='offline'`
  - Schedule to run every 1 minute
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [-] 11.2 Create CleanupStaleSessions scheduled task
  - Create `app/Console/Commands/CleanupStaleSessions.php`
  - Query sessions: `status='active' AND last_active_at < now() - 10 minutes`
  - For each session: update status, send disable, broadcast event
  - Set `end_reason='system_cleanup'`
  - Log alert for manual investigation
  - Schedule to run every 5 minutes
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

- [-] 11.3 Create POST /api/kiosk/complete endpoint for iHub timeout
  - Create `KioskController@complete` method
  - Accept `kiosk_id` parameter with `X-Internal-Key` authentication
  - Accept optional `reason` parameter: `'ihub_timeout'` (default) or `'ihub_force_ended'`
  - Query active session for kiosk_id
  - End session with `end_reason` from request (default `'ihub_timeout'`)
  - Send disable command and broadcast event
  - **iHub side**: `completeSession(true)` must pass `reason='ihub_timeout'`, force-end button must pass `reason='ihub_force_ended'`
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 21.3, 21.4, 21.6_

- [ ]* 11.4 Write unit tests for scheduled cleanup tasks
  - Test offline detection finds sessions older than 60 seconds
  - Test stale cleanup finds sessions older than 10 minutes
  - Test iHub complete endpoint ends session
  - Test alert logging for system_cleanup
  - _Requirements: 12.1-12.5, 13.1-13.6, 14.1-14.5_

---

### 12. Member: Database Schema Updates

- [-] 12.1 Add end_reason column to kiosk_sessions table
  - Create migration to add `end_reason` enum column
  - Enum values: 'manual', 'timeout', 'new_session_started', 'offline', 'ihub_timeout', 'ihub_force_ended', 'system_cleanup'
  - Add after `ended_at` column
  - _Requirements: 10.4, 12.3, 13.3, 14.4, 15.2, 21.4_

- [-] 12.2 Verify kiosk_transactions table structure
  - Confirm UNIQUE index on `event_id` column exists
  - Confirm indexes on `session_id` and `member_id` exist
  - Verify all required columns exist: event_id, session_id, member_id, kiosk_id, amount_twd, tokens_credited, transaction_type
  - _Requirements: 17.1, 17.2_

---

### 13. Checkpoint - Verify Session Management

- [ ] 13. Ensure all tests pass, ask the user if questions arise.

---

### 14. iHub: Tablet Interface Implementation

> ⚠️ **重寫中（2026-05-09 UTC+8）**：main.js 已備份為 main.js.bak，從頭重寫。  
> 重寫前必讀：`IHUB_PITFALLS.md`（坑記錄）和 `design.md` 第 10 章（接口對照表）。

- [x] 14.1 Update iHub to call Infra GET /api/kiosk/node-id
  - Change API endpoint from `win.tg25.win` to `api.tg25.win`
  - Update `src/utils/iHubDevice.js` or equivalent
  - Verify `X-Internal-Key` header is included
  - Guard: if `deviceId` is falsy, show error instead of calling API（見 PITFALLS 坑 7）
  - _Requirements: 3.2_

- [x] 14.2 Implement idle screen component
  - Display "點擊螢幕開始兌幣" prompt
  - Detect screen tap to trigger QR code generation（立即切換畫面，背景取 token，見 PITFALLS 坑 11）
  - _Requirements: 3.7, 4.1_

- [x] 14.3 Implement QR code display with countdown
  - QR Code 格式：`KIOSK:{kiosk_id}:TOKEN:{token}`（純字串，不是 URL，見 PITFALLS Bug 3）
  - Show 5-minute (300 second) countdown timer（HTML 初始值由 JS 設定，見 PITFALLS 坑 9）
  - Return to idle screen when countdown reaches zero
  - Do not request new token when countdown expires
  - _Requirements: 4.6, 4.7, 4.8_

- [x] 14.4 Implement active screen with member information
  - Listen for `.MemberBoundToKiosk` WebSocket event，檢查 `e.status === 'bound'`（見 PITFALLS 坑 2）
  - 儲存 `currentSessionId = e.session_id`（complete 時需要，見 PITFALLS Bug 1）
  - Display member name, member ID (`#id`), and last 4 digits of phone (omit if `member.phone` is null)
  - Switch from QR code screen to active screen
  - _Requirements: 5.12, 5.13_

- [x] 14.4a Implement force-end button on active screen
  - Display button: `[✕ 結束 {name}（#{id} · {last4}）的兌換]`
  - On click: call `POST /api/kiosk/complete` with `X-Internal-Key`, `session_id`（不是 kiosk_id，見 PITFALLS Bug 1）, `reason='ihub_force_ended'`
  - No Bearer token required
  - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6_

- [x] 14.4b Implement complete-btn（確認完成兌換）
  - Call `POST /api/kiosk/complete` with `session_id`（不是 kiosk_id，見 PITFALLS Bug 1）, `reason='ihub_force_ended'`
  - _Requirements: 21.3, 21.4, 21.6_

- [x] 14.5 Implement escrow confirmation screen
  - Listen for `.KioskEscrowPending` WebSocket event
  - Display member name, phone (masked), amount, tokens
  - Show 15-second countdown timer
  - Provide "確認入帳" and "取消退鈔" buttons
  - _Requirements: 6.6, 6.7_

- [x] 14.6 Implement escrow confirmation actions
  - On "確認入帳" click: call `POST /api/kiosk/escrow/confirm` with `{ kiosk_id }`
  - On "取消退鈔" click: call `POST /api/kiosk/escrow/reject` with `{ kiosk_id }`
  - On 15-second timeout: display timeout message（不自動 reject，韌體 Fail-Safe 會處理）
  - _Requirements: 6.8, 6.9, 6.10_

- [x] 14.7 Implement deposit success animation
  - Listen for `.KioskSessionUpdated` WebSocket event
  - 讀取 `e.member_balance`（不是 `e.balance`）和 `e.tokens_credited`（不是 `e.amount`）（見 PITFALLS Bug 2）
  - Display deposit success animation
  - Update total deposited amount display
  - _Requirements: 7.10_

- [x] 14.8 Implement session end screen
  - Listen for `.KioskSessionEnded` WebSocket event
  - Display completion message based on end_reason
  - Show total deposited and tokens credited
  - Display for 8 seconds, then return to idle screen
  - _Requirements: 10.7, 10.8_

- [x] 14.9 Implement iHub idle timer
  - Start **5-minute (300-second)** timer when member binds (on `.MemberBoundToKiosk`)
  - Reset timer on each `.KioskSessionUpdated` event
  - On timer expiry: call `POST /api/kiosk/complete` with `session_id`, `reason='ihub_timeout'`（見 PITFALLS Bug 1）
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [x] 14.10 Implement WebSocket engineering heartbeat（whisper）
  - Send whisper `tablet-heartbeat` to `engineering.{kiosk_id}` every 30 seconds
  - Payload: `{ device_id, kiosk_id, timestamp }`
  - HTTP heartbeat 已廢棄，不要加回來
  - _Requirements: 25.1, 25.2_

- [x] 14.11 Implement all stage layouts for landscape/portrait responsive
  - 所有尺寸用 `clamp()` 或 `vw/vh`，不硬編碼 px（見 PITFALLS 坑 8）
  - Escrow modal: portrait/landscape dual layout
  - _Requirements: 3.7_

---

### 15. Member Frontend: Mobile App Implementation

> ⚠️ **本 Phase 不在此 spec 範圍內。**  
> 此 spec 負責 iHub 平板端的實作。Member 手機 App 已另開獨立 spec，功能已開發完成，尚待驗證。

---

### 16. Infra: MQTT Listener Implementation

- [x] 16.1 Verify Infra Listener subscribes to kiosk/+/event
  - Confirm subscription to `kiosk/+/event` topic with QoS 2
  - Verify listener handles escrow, stacked, rejected events
  - _Requirements: 6.4, 7.1, 8.2_
  - **Completed**: 2026-05-03 by Ina (Infra Master)

- [x] 16.2 Verify escrow event forwarding
  - Confirm Listener forwards to `POST /internal/kiosk/escrow` (Member)
  - `.KioskEscrowPending` broadcast handled by Member (correct — Member holds session/mask info)
  - Verify event_id, amount, kiosk_id are included
  - _Requirements: 6.4, 6.6, 19.5_
  - **Completed**: 2026-05-03 by Ina (Infra Master)

- [x] 16.3 Verify stacked event forwarding
  - Confirm Listener forwards to `POST /internal/kiosk/stacked` (Member)
  - Verify event_id, amount, kiosk_id, esp32_mac are included
  - _Requirements: 7.1_
  - **Completed**: 2026-05-03 by Ina (Infra Master)

- [x] 16.4 Verify rejected event forwarding
  - Confirm Listener forwards to `POST /internal/kiosk/rejected` (Member)
  - Verify event_id, amount, reason are included
  - _Requirements: 8.2_
  - **Completed**: 2026-05-03 by Ina (Infra Master)

---

### 17. Firmware: Verification Tasks

- [x] 17.1 Verify firmware subscribes to kiosk/{esp32_mac}/cmd
  - Confirm subscription with QoS 2 ✅
  - Verify firmware handles enable, disable, stack, reject actions ✅
  - _Requirements: 5.10, 6.11, 7.12, 8.1, 10.6, 16.1_
  - **Completed**: 2026-05-03 by Fio (Firmware Specialist)

- [x] 17.2 Verify firmware publishes to kiosk/{esp32_mac}/event
  - Confirm escrow event includes event_id, amount, timestamp ✅
  - Confirm stacked event includes event_id, amount, timestamp ✅
  - Confirm rejected event includes event_id, amount, reason, timestamp ✅
  - Verify QoS 2 for all events ✅
  - _Requirements: 6.3, 7.1, 8.2_
  - **Completed**: 2026-05-03 by Fio (Firmware Specialist)

- [ ] 17.3 Verify firmware Hold mechanism for escrow
  - Hold interval modified during verification — pending physical hardware test to confirm
  - Fail-Safe timeout 15 seconds ✅
  - _Requirements: 6.2, 6.3, 16.1, 16.2, 16.3, 16.4, 16.5, 16.6_

- [x] 17.4 Verify firmware default state is DISABLED
  - Confirm firmware sends RS232 Disable (0x5E) on boot ✅
  - Verify bill acceptor shows red light by default ✅
  - _Requirements: 16.1_
  - **Completed**: 2026-05-03 by Fio (Firmware Specialist)

---

### 18. Integration and Wiring

- [x] 18.1 Wire Member bind to Infra kiosk/info API
  - `KioskController@bind` calls `api.tg25.win/api/kiosk/info` ✅
  - No direct DB::connection('mysql_v9') usage ✅
  - _Requirements: 5.8, 5.9, 18.1_
  - **Completed**: 2026-05-03 by Mina (MemberOps)

- [x] 18.2 Wire Member escrow confirm/reject to Infra MQTT publish
  - `escrowConfirm` calls `callInfraMqtt` with action `stack` ✅
  - `escrowReject` calls `callInfraMqtt` with action `reject` ✅
  - _Requirements: 6.8, 6.9, 6.11_
  - **Completed**: 2026-05-03 by Mina (MemberOps)

- [x] 18.3 Wire Member session end to Infra MQTT publish
  - `KioskSession@terminate` sends `{"action":"disable"}` to `kiosk/{mac}/cmd` (QoS 2) ✅
  - Covers: manual end, offline cleanup, stale cleanup, iHub complete ✅
  - _Requirements: 10.5, 10.6_
  - **Completed**: 2026-05-03 by Mina (MemberOps)

- [x] 18.4 Verify WebSocket broadcasting configuration
  - Laravel Reverb running on yd47 ✅
  - Channel: `kiosk.{kiosk_id}` (lowercase) ✅
  - All 4 events confirmed: .MemberBoundToKiosk, .KioskEscrowPending, .KioskSessionUpdated, .KioskSessionEnded ✅
  - _Requirements: 19.1, 19.2, 19.3_
  - **Completed**: 2026-05-03 by Mina (MemberOps)

- [ ]* 18.5 Write integration tests for complete flow
  - Test end-to-end flow from QR scan to deposit
  - Test multi-kiosk switching scenario
  - Test offline detection and cleanup
  - Test concurrent operations (race conditions)
  - _Requirements: All requirements_

---

### 20. Infra: Listener Hardening

- [x] 20.1 Fix Listener error log truncation
  - Truncate HTTP response body in error log to 200 characters maximum
  - Change `logger.error(f"... {response.text}")` to `logger.error(f"... {response.text[:200]}")`
  - Prevents HTML error pages from flooding journalctl
  - _Requirements: 22.4_
  - **Completed**: 2026-05-04 by Ina (Infra Master)

- [x] 20.2 Implement Listener health watchdog
  - Track timestamp of last received MQTT message
  - Log WARNING if no message received within 5 minutes
  - Send Chat Bridge alert if no message received within 10 minutes
  - _Requirements: 22.1, 22.2_
  - **Completed**: 2026-05-04 by Ina (Infra Master)

- [x] 20.3 Fix device cache: remove chip_id fallback
  - WHEN chip_id not found in cache, log STRICT_MATCH_FAILURE and skip event
  - Removed `using chip_id as node_id fallback` logic
  - _Requirements: 23.4_
  - **Completed**: 2026-05-04 by Ina (Infra Master)

- [x] 20.4 Implement device cache auto-reload
  - Reload cache from `iotv9.kiosks` every 10 minutes automatically
  - Log number of devices loaded on each reload
  - _Requirements: 23.2, 23.3_
  - **Completed**: 2026-05-04 by Ina (Infra Master)

- [x] 20.5 Add cache reload API endpoint
  - Created `POST /api/internal/cache/reload` in Infra (Credit Relay API)
  - Triggers immediate device cache reload via file signal mechanism
  - Implements `X-Internal-Key` authentication
  - _Requirements: 23.1_
  - **Completed**: 2026-05-04 by Ina (Infra Master)

---

### 21. Alliance: Trigger Cache Reload After Pairing

- [x] 21.1 Call Infra cache reload after kiosk pairing
  - Added call to `POST https://api.tg25.win/api/internal/cache/reload` after successful pair
  - Uses `X-Internal-Key` authentication
  - Non-blocking try-catch, does not affect pairing flow on failure
  - _Requirements: 23.1_
  - **Completed**: 2026-05-04 by Allie (Alliance)

---

### 22. Member: Internal API Smoke Test

- [x] 22.1 Create smoke test script for internal endpoints
  - Created `php artisan smoke:test-internal`
  - Tests `POST /internal/kiosk/escrow`, `/stacked`, `/rejected` — all return 200 ✅
  - Uses `X-Internal-Key` authentication with minimal valid payloads
  - _Requirements: 24.1, 24.2, 24.3, 24.4_
  - **Completed**: 2026-05-04 by Mina (MemberOps)

---

### 23. Engineering Dashboard: Real-Time Tablet Status

> ⚠️ **已暫停（2026-05-08 UTC+8）**：工程頁面新功能開發造成多次 regression，決定暫停。等基礎功能穩定後再評估是否繼續。

- [x] 23.1 Remove HTTP heartbeat from iHub
  - Delete or comment out `setupHeartbeat()` function in `src/main.js`
  - Remove `setupHeartbeat()` call from `init()` function
  - HTTP heartbeat is no longer needed for tablet status tracking
  - _Requirements: 25.10_

- [x] 23.2 Implement WebSocket whisper heartbeat in iHub
  - Create `setupEngineeringHeartbeat()` function in `src/main.js`
  - Send whisper event `tablet-heartbeat` to channel `engineering.{kiosk_id}` every 30 seconds
  - Payload: `{ kiosk_id: KIOSK_ID, timestamp: Date.now() }`
  - Call `setupEngineeringHeartbeat()` in `init()` after `setupWebSocket()`
  - Use try-catch to ensure whisper failure does not affect main flow
  - _Requirements: 25.1, 25.2_

- [x] 23.3 Remove HTTP polling from Engineering Dashboard
  - Remove `fetch('/api/engineering/tablet-status/...')` call in `resources/views/engineering/kiosk.blade.php`
  - Remove any setInterval that polls tablet status via HTTP
  - _Requirements: 25.11_
  - **⚠️ 已暫停**：工程頁面新功能開發已暫停（2026-05-08 UTC+8），等基礎功能穩定後再繼續

- [x] 23.4 Implement WebSocket whisper listener in Engineering Dashboard
  - In `subscribe()` method, add `listenForWhisper('tablet-heartbeat', callback)`
  - On whisper received: update `lastTabletHeartbeat = Date.now()` and `tabletStatus = 'online'`
  - Add `lastTabletHeartbeat`, `tabletStatus`, `tabletStatusText` to Vue data()
  - _Requirements: 25.3, 25.4, 25.5_
  - **Completed**: 2026-05-08 by Hubie (iHub)
  - **⚠️ 已暫停**：工程頁面新功能開發已暫停（2026-05-08 UTC+8），等基礎功能穩定後再繼續

- [x] 23.5 Implement status check timer in Engineering Dashboard
  - In Vue `mounted()`, add `setInterval()` that runs every 1 second
  - Calculate `elapsed = (Date.now() - lastTabletHeartbeat) / 1000`
  - If `elapsed < 31`: set `tabletStatus = 'online'`, `tabletStatusText = '在線 (Xs 前)'`
  - If `elapsed >= 31`: set `tabletStatus = 'offline'`, `tabletStatusText = '離線 (Xs 前)'`
  - If `lastTabletHeartbeat === null`: set `tabletStatus = 'never'`, `tabletStatusText = '從未連線'`
  - _Requirements: 25.6, 25.7, 25.8, 25.9_
  - **Completed**: 2026-05-08 by Hubie (iHub)
  - **⚠️ 已暫停**：工程頁面新功能開發已暫停（2026-05-08 UTC+8），等基礎功能穩定後再繼續

- [ ]* 23.6 Test tablet status display
  - Open Engineering Dashboard and select `kiosk_000`
  - Verify initial status is "從未連線" (gray)
  - Open iHub on tablet or browser
  - Verify status changes to "在線" (green) within 30 seconds
  - Close iHub
  - Verify status changes to "離線" (red) after 31 seconds
  - _Requirements: 25.1-25.12_

---

### 24. Final Checkpoint and Deployment

- [ ] 24. Ensure all tests pass, ask the user if questions arise.

---

### 25. Rollback: Remove Non-Essential Engineering Features

**Context**: 2026-05-08 UTC+8 - 工程頁面新功能開發造成多次 regression（iHub QR code 500 錯誤、sim-bill 心跳 405 錯誤、Member 燈號異常），決定暫停工程頁面新功能開發，移除不在原始 requirements 中的廣播功能。

- [x] 25.1 Remove firmware.ba_state WebSocket broadcast from Member
  - Remove `firmware.ba_state` broadcast in `CallbackController@kioskStatus`
  - Restore to only broadcast `firmware.idle` when `ba_state === 'IDLE'`
  - This broadcast was added for engineering dashboard but not in original requirements
  - _Decision: 2026-05-08 UTC+8_
  - **Completed**: 2026-05-08 by Mina (MemberOps)
  - **Commit**: `e8e3f94`

- [x] 25.2 Remove member.session_ended WebSocket broadcast from Member
  - Remove `member.session_ended` broadcast in `KioskSession@terminate()`
  - Keep `KioskSessionEnded` event (iHub depends on it)
  - This broadcast was added for engineering dashboard but not in original requirements
  - _Decision: 2026-05-08 UTC+8_
  - **Completed**: 2026-05-08 by Mina (MemberOps)
  - **Commit**: `e8e3f94`

- [x] 25.3 Fix Member zombie session issue
  - Root cause: `refreshToken()` creates `member_id=NULL` sessions (tablet online but no user), but `sessionStatus` API didn't filter `member_id IS NOT NULL`
  - Fix: Add `->whereNotNull('member_id')` condition in `EngineeringController::sessionStatus`
  - Cleanup: Mark id=900 zombie session as `ended` with `end_reason='zombie_cleanup'`
  - _Decision: 2026-05-08 UTC+8_
  - **Completed**: 2026-05-08 by Mina (MemberOps)
  - **Commit**: `af89b57`

---

### 26. Final Checkpoint and Deployment

- [ ] 26. Ensure all tests pass, ask the user if questions arise.

---

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties from the design
- Integration tests validate end-to-end flows across system boundaries
- Implementation should follow the existing Laravel project structure and coding standards
- All MQTT topics and JSON keys must use lowercase format as specified in requirements
- **Value 大小寫規則**（來自韌體原始碼查證）：
  - `ba_state` 值：全大寫（`IDLE`, `ESCROW`, `STACKING`, `REJECTING`, `DISABLED`, `FAULT`）
  - `ba_error` 值：全大寫（`NONE`, `BILL_JAM`, `MOTOR_FAILURE`, `STACKER_OPEN`, `COMM_FAILURE`）
  - `event` 值：全小寫（`escrow`, `stacked`, `rejected`）
  - `action` 值：全小寫（`stack`, `reject`, `enable`, `disable`, `reboot`, `ota_update`）
- Database transactions must be used for all financial operations to ensure atomicity
- WebSocket events must be broadcast to lowercase channel names: `kiosk.{kiosk_id}`

## Implementation Order Rationale

1. **Phase 1-2**: Infrastructure foundation (Alliance validation, Infra APIs, Member auth)
2. **Phase 3-4**: Session management (QR code, binding, heartbeat)
3. **Phase 5**: Bill flow (escrow, stacked, rejected) - most complex, requires careful testing
4. **Phase 6**: Session termination (manual, timeout, cleanup)
5. **Phase 7**: Frontend integration (iHub screens, member app)
6. **Phase 8**: Integration testing and deployment

This order ensures dependencies are satisfied before dependent components are implemented, and allows for incremental testing at each checkpoint.
