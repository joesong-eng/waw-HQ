# Requirements Document: Bill Acceptor Simulator

> **最後更新**：2026-05-11  
> **版本**：4.0（對齊 design.md v4，MQTT 直連架構）

## 重要概念：Kiosk 識別碼體系

> ⚠️ **必讀**：本文件中的所有需求都基於正確理解 Kiosk 識別碼體系。

### 識別碼定義

- **chip_id**：兌幣卡的 MAC 地址（硬體層級）
  - 範例：`test-esp32`
  - 用途：MQTT 通訊、API 參數

- **node_id**（也稱 kiosk_id）：Kiosk 產品的識別碼（產品層級）
  - 範例：`kiosk_000`
  - 格式：`kiosk_NNN`（小寫，3 位數字）
  - 用途：WebSocket 頻道、QR Code、Session 管理
  - **這是認證的標準號牌**

### 模擬器使用原則

- ✅ WebSocket 訂閱：`kiosk.kiosk_000`（使用 `node_id`）
- ✅ API 呼叫：`chip_id=test-esp32`（使用 `chip_id`）
- ❌ 錯誤：`engineering.N-000`（格式錯誤）
- ❌ 錯誤：`engineering.test-esp32`（層級錯誤）

詳細說明請參考：`brains/knowledge/kiosk_identification_system.md`

---

## Introduction

The Bill Acceptor Simulator is a standalone development tool designed to simulate the behavior of a physical bill acceptor (ICT 104U) for testing the Kiosk Exchange v2 system without requiring actual hardware. The simulator replicates the complete firmware state machine, MQTT communication patterns, and API interactions to provide a realistic testing environment for developers.

This tool enables developers to test the complete bill acceptance workflow including state transitions (DISABLED → IDLE → ESCROW → STACKING/STACKED/REJECTING/REJECTED), WebSocket event handling, and backend integration without physical hardware dependencies.

**v4 架構重點**：模擬器改用真實 MQTT 鏈路接收 stack/reject 指令（透過 iHub Server SSE 橋接），與真實韌體行為完全一致。WebSocket 僅用於接收會員綁定事件。

## Glossary

- **Simulator**: The Bill Acceptor Simulator web application
- **Kiosk_Firmware**: The ESP32-S3 firmware running on physical kiosk devices (IOTkiosk_v0)
- **Bill_Acceptor**: The physical ICT 104U bill acceptor hardware
- **Infra_API**: The infrastructure API endpoint at `https://api.tg25.win/api/kiosk/hardware-status`
- **iHub_Server**: The Node.js Express server that proxies API requests and bridges MQTT to SSE
- **WebSocket_Channel**: The kiosk channel at `kiosk.{node_id}` on Member Reverb server
- **SSE_Channel**: Server-Sent Events endpoint at `GET /api/simulator/events` on iHub Server
- **MQTT_Cmd_Topic**: `kiosk/{chip_id}/cmd`，iHub Server 訂閱後透過 SSE 推給前端
- **State_Machine**: The firmware state machine with states: DISABLED, IDLE, ESCROW, STACKING, STACKED, REJECTING, REJECTED
- **Escrow**: The temporary holding state when a bill is validated but not yet accepted or rejected
- **Stacking**: Intermediate state after receiving stack command, before MQTT stacked event is sent
- **Rejecting**: Intermediate state after receiving reject command, before MQTT rejected event is sent
- **Stack**: The action of accepting a bill into the cash box
- **Reject**: The action of returning a bill to the user
- **Chip_ID**: The unique identifier of the kiosk device (MAC address format)
- **Node_ID**: The product-level identifier of the kiosk (`kiosk_NNN` format)
- **ba_state**: Bill acceptor state parameter sent to Infra API

## Requirements

### Requirement 1: State Machine Simulation

**User Story:** As a developer, I want the simulator to replicate the complete firmware state machine, so that I can test all state transitions without physical hardware.

#### Acceptance Criteria

1. THE Simulator SHALL implement seven states: DISABLED, IDLE, ESCROW, STACKING, STACKED, REJECTING, and REJECTED
2. WHEN the Simulator starts, THE Simulator SHALL initialize in DISABLED state
3. WHEN the Simulator is in DISABLED state, THE Simulator SHALL display a red status indicator
4. WHEN the Simulator is in IDLE state, THE Simulator SHALL display a green status indicator
5. WHEN the Simulator is in ESCROW state, THE Simulator SHALL display a flashing yellow status indicator
6. WHEN the Simulator is in STACKING state, THE Simulator SHALL display a flashing blue status indicator
7. WHEN the Simulator is in REJECTING state, THE Simulator SHALL display a flashing yellow status indicator
8. WHEN the Simulator transitions to STACKED state, THE Simulator SHALL return to IDLE state after 1.5 seconds
9. WHEN the Simulator transitions to REJECTED state, THE Simulator SHALL return to IDLE state after 1.5 seconds
10. THE Simulator SHALL maintain the current state until a valid transition event occurs
11. THE Simulator SHALL prevent invalid state transitions (e.g., DISABLED → ESCROW, IDLE → STACKING)

### Requirement 2: Automatic State Reporting

**User Story:** As a developer, I want the simulator to automatically report state changes to the Infra API, so that I can verify the backend receives correct state updates.

#### Acceptance Criteria

1. WHEN the Simulator initializes, THE Simulator SHALL send `ba_state=DISABLED` to Infra_API within 1 second
2. WHEN the Simulator transitions to any state, THE Simulator SHALL send the corresponding ba_state to Infra_API within 500 milliseconds
3. THE Simulator SHALL send heartbeat messages with `ba_state=IDLE` every 60 seconds while in IDLE state
4. WHEN the Simulator sends a state update, THE Simulator SHALL include the chip_id parameter
5. WHEN the Simulator sends a state update, THE Simulator SHALL use the iHub_Server proxy endpoint (`POST /api/simulator/bill`)
6. IF the API request fails, THEN THE Simulator SHALL log the error and display it in the UI

### Requirement 3: Member Binding Detection

**User Story:** As a developer, I want the simulator to automatically transition to IDLE when a member binds to the kiosk, so that I can test the complete binding workflow.

#### Acceptance Criteria

1. WHEN the Simulator starts, THE Simulator SHALL subscribe to WebSocket_Channel `kiosk.{node_id}` on Member Reverb server (`win.tg25.win`)
2. WHEN the Simulator receives a `.MemberBoundToKiosk` event with `status=bound`, THE Simulator SHALL transition from DISABLED to IDLE state
3. WHEN transitioning to IDLE state, THE Simulator SHALL send `ba_state=IDLE` to Infra_API
4. THE Simulator SHALL display the received WebSocket event in the event log
5. IF the WebSocket connection fails, THEN THE Simulator SHALL display a disconnected status indicator
6. THE Simulator SHALL NOT listen to `infra.cmd` events on WebSocket（v4 已移除，改由 MQTT 接收）

### Requirement 4: Bill Insertion Simulation

**User Story:** As a developer, I want to simulate bill insertion with different denominations, so that I can test the bill acceptance workflow.

#### Acceptance Criteria

1. THE Simulator SHALL provide buttons for inserting 100, 500, and 1000 TWD bills
2. WHEN the Simulator is in DISABLED state, THE Simulator SHALL disable all bill insertion buttons
3. WHEN the Simulator is in IDLE state, THE Simulator SHALL enable all bill insertion buttons
4. WHEN a bill insertion button is clicked, THE Simulator SHALL transition to ESCROW state
5. WHEN transitioning to ESCROW state, THE Simulator SHALL call `/api/simulator/bill` with `{ chip_id, amount }` — iHub Server 自動處理 ESCROW 狀態上報與 MQTT 事件發布
6. THE Simulator SHALL remain in ESCROW state until receiving a stack or reject command via SSE

### Requirement 5: Stack and Reject Command Handling via MQTT/SSE

**User Story:** As a developer, I want the simulator to respond to stack and reject commands from the backend via MQTT, so that I can test the complete bill acceptance flow with the same mechanism as real firmware.

#### Acceptance Criteria

1. THE Simulator SHALL connect to `GET /api/simulator/events` (SSE) on page load
2. WHEN the Simulator receives an SSE `mqtt_cmd` event with `action=stack`, THE Simulator SHALL transition from ESCROW to STACKING state
3. WHEN the Simulator is in STACKING state, after 500ms THE Simulator SHALL send a `stacked` MQTT event via `/api/simulator/bill` and transition to STACKED state
4. WHEN the Simulator receives an SSE `mqtt_cmd` event with `action=reject`, THE Simulator SHALL transition from ESCROW to REJECTING state
5. WHEN the Simulator is in REJECTING state, after 500ms THE Simulator SHALL send a `rejected` MQTT event via `/api/simulator/bill` and transition to REJECTED state
6. WHEN the Simulator receives an SSE `mqtt_cmd` event with `action=enable`, THE Simulator SHALL transition to IDLE state
7. WHEN the Simulator receives an SSE `mqtt_cmd` event with `action=disable`, THE Simulator SHALL transition to DISABLED state
8. WHEN in STACKED state, THE Simulator SHALL display a success message with the bill amount
9. WHEN in REJECTED state, THE Simulator SHALL display a rejection message with the bill amount
10. THE Simulator SHALL log all received MQTT cmd events in the event log
11. IF the SSE connection drops, THE Simulator SHALL display a warning and rely on EventSource auto-reconnect

### Requirement 6: Escrow Timeout Protection

**User Story:** As a developer, I want the simulator to automatically reject bills after a timeout period, so that I can test the fail-safe mechanism.

#### Acceptance Criteria

1. WHEN the Simulator enters ESCROW state, THE Simulator SHALL start a 15-second timeout timer
2. IF no stack or reject command is received within 15 seconds, THEN THE Simulator SHALL automatically transition to REJECTING state
3. WHEN the timeout occurs, THE Simulator SHALL follow the normal REJECTING → REJECTED → IDLE flow (including sending MQTT rejected event)
4. WHEN the timeout occurs, THE Simulator SHALL display a timeout message in the event log
5. IF a stack or reject command is received before timeout, THEN THE Simulator SHALL cancel the timeout timer

### Requirement 7: User Interface Display

**User Story:** As a developer, I want a clear and intuitive UI showing the current state and recent events, so that I can easily monitor the simulator behavior.

#### Acceptance Criteria

1. THE Simulator SHALL display the current state name (DISABLED/IDLE/ESCROW/STACKING/STACKED/REJECTING/REJECTED)
2. THE Simulator SHALL display a colored status indicator matching the current state
3. THE Simulator SHALL display the WebSocket connection status (connected/disconnected)
4. THE Simulator SHALL display the SSE connection status (connected/disconnected)
5. THE Simulator SHALL display the current chip_id and node_id being simulated
6. THE Simulator SHALL display an event log showing the most recent 20 events with timestamps
7. THE Simulator SHALL display bill insertion buttons with denomination labels (100/500/1000)
8. THE Simulator SHALL provide a configuration section for entering chip_id and node_id

### Requirement 8: API Proxy Security

**User Story:** As a developer, I want API requests to be proxied through the iHub server, so that internal API keys are not exposed in the browser.

#### Acceptance Criteria

1. THE Simulator SHALL send all Infra_API requests to the iHub_Server proxy endpoint (`/api/simulator/bill`)
2. THE iHub_Server SHALL add the `X-Internal-Key` header before forwarding to Infra_API
3. THE Simulator SHALL NOT contain any hardcoded API keys or secrets
4. THE Simulator SHALL be accessible only with `?key=dev` URL parameter
5. IF the proxy request fails, THEN THE Simulator SHALL display an error message with the HTTP status code

### Requirement 9: WebSocket Event Monitoring

**User Story:** As a developer, I want to monitor all WebSocket events related to the kiosk, so that I can debug event-driven workflows.

#### Acceptance Criteria

1. THE Simulator SHALL display all received WebSocket events in the event log
2. WHEN a WebSocket event is received, THE Simulator SHALL log the event type and payload
3. THE Simulator SHALL highlight `.MemberBoundToKiosk` events in the log
4. THE Simulator SHALL highlight SSE `mqtt_cmd` events in the log
5. THE Simulator SHALL display the timestamp for each logged event
6. THE Simulator SHALL automatically scroll the event log to show the most recent event

### Requirement 10: Configuration Persistence and Identifier Format

**User Story:** As a developer, I want my simulator configuration to persist across browser sessions and use correct identifier formats, so that I don't need to reconfigure every time and avoid identifier confusion.

#### Acceptance Criteria

1. THE Simulator SHALL save the chip_id to browser localStorage with key `sim_chip_id` when changed
2. THE Simulator SHALL save the node_id to browser localStorage with key `sim_node_id` when changed
3. WHEN the Simulator loads, THE Simulator SHALL restore chip_id and node_id from localStorage
4. THE Simulator SHALL provide default values: `chip_id=test-esp32`, `node_id=kiosk_000`
5. **THE Simulator SHALL display the node_id in the format `kiosk_NNN` (e.g., `kiosk_000`), NOT in any other format**
6. **THE Simulator SHALL use `node_id` for WebSocket channel subscription (e.g., `kiosk.kiosk_000`)**
7. **THE Simulator SHALL use `chip_id` for API requests and MQTT topics (e.g., `chip_id=test-esp32`)**
8. **THE Simulator SHALL clearly distinguish between chip_id (hardware level) and node_id (product level) in the UI**

### Requirement 11: Deployment and Access

**User Story:** As a developer, I want to access the simulator through a simple URL, so that I can quickly start testing without complex setup.

#### Acceptance Criteria

1. THE Simulator SHALL be accessible as a standalone HTML page at `https://ihub.tg25.win/sim-bill/?key=dev`
2. THE Simulator SHALL NOT require any build process or compilation
3. THE Simulator SHALL be served by the iHub_Server with nginx static serving `/sim-bill/`
4. THE Simulator SHALL load all required JavaScript libraries from CDN or inline
5. THE Simulator SHALL display a clear title indicating it is a development tool

### Requirement 12: Error Handling and Logging

**User Story:** As a developer, I want comprehensive error logging, so that I can diagnose issues when the simulator behaves unexpectedly.

#### Acceptance Criteria

1. WHEN an API request fails, THE Simulator SHALL log the error details to the browser console
2. WHEN a WebSocket connection fails, THE Simulator SHALL log the error and display a reconnection message
3. WHEN an SSE connection fails, THE Simulator SHALL log the error (EventSource auto-reconnects)
4. WHEN an invalid state transition is attempted, THE Simulator SHALL log a warning and ignore the transition
5. THE Simulator SHALL display API response status codes in the event log
6. THE Simulator SHALL provide a "Clear Log" button to reset the event log

## Non-Functional Requirements

### Performance Requirements

1. THE Simulator SHALL respond to user interactions within 100 milliseconds
2. THE Simulator SHALL send API requests within 500 milliseconds of state transitions
3. THE Simulator SHALL maintain WebSocket connection with automatic reconnection on failure
4. THE Simulator SHALL maintain SSE connection with EventSource auto-reconnect on failure
5. THE Simulator SHALL handle up to 100 events in the event log without performance degradation

### Security Requirements

1. THE Simulator SHALL NOT expose any internal API keys in client-side code
2. THE Simulator SHALL require `?key=dev` URL parameter for access
3. THE Simulator SHALL use HTTPS for all API communications
4. THE Simulator SHALL use WSS (WebSocket Secure) for WebSocket connections

### Usability Requirements

1. THE Simulator SHALL provide clear visual feedback for all state transitions
2. THE Simulator SHALL use color coding: red=DISABLED/REJECTED, green=IDLE/STACKED, yellow=ESCROW/REJECTING, blue=STACKING
3. THE Simulator SHALL display error messages in plain language without technical jargon
4. THE Simulator SHALL provide tooltips or help text for configuration fields

### Compatibility Requirements

1. THE Simulator SHALL work in Chrome, Firefox, Safari, and Edge browsers (latest 2 versions)
2. THE Simulator SHALL be responsive and usable on desktop screens (minimum 1024x768 resolution)
3. THE Simulator SHALL NOT require any browser plugins or extensions
4. THE Simulator SHALL be compatible with the existing iHub server infrastructure

### Maintainability Requirements

1. THE Simulator code SHALL be well-commented with clear explanations of state machine logic
2. THE Simulator SHALL use semantic HTML and CSS class names
3. THE Simulator SHALL separate concerns (UI, state management, API communication)
4. THE Simulator SHALL include inline documentation for all configuration parameters

## Technical Requirements

### API Integration

1. THE Simulator SHALL use the proxy endpoint: `POST /api/simulator/bill` on iHub Server
2. THE Simulator SHALL send requests with Content-Type: `application/json`
3. For state updates: body `{ chip_id: string, ba_state: string }`
4. For bill insertion: body `{ chip_id: string, amount: number }` — iHub Server handles ESCROW reporting and MQTT event publishing
5. THE iHub_Server SHALL proxy state updates to `https://api.tg25.win/api/kiosk/hardware-status`
6. THE iHub_Server SHALL proxy bill events to `https://api.tg25.win/api/internal/mqtt/publish` (topic: `kiosk/{chip_id}/event`, QoS 2)

### SSE Integration (v4 新增)

1. THE Simulator SHALL connect to `GET /api/simulator/events` on page load
2. THE iHub_Server SHALL subscribe to MQTT topic `kiosk/{chip_id}/cmd` (QoS 2) on startup
3. THE iHub_Server SHALL push received MQTT cmd messages to all connected SSE clients as `event: mqtt_cmd`
4. THE SSE data format SHALL be: `{"action": "stack|reject|enable|disable", "chip_id": "..."}`
5. nginx SHALL proxy `/api/simulator/events` with `proxy_buffering off` to support SSE streaming

### WebSocket Integration

1. THE Simulator SHALL connect to Member Reverb WebSocket at `win.tg25.win` (WSS, port 443)
2. THE Simulator SHALL use Laravel Echo with pusher mode, App Key `waw-member-key`
3. THE Simulator SHALL subscribe to public channel: `kiosk.{node_id}`
4. THE Simulator SHALL listen ONLY for `.MemberBoundToKiosk` event (NOT `infra.cmd`)
5. THE Simulator SHALL handle WebSocket reconnection with exponential backoff

### State Machine Implementation

1. THE Simulator SHALL implement state transitions according to the table in design.md Section 8
2. THE Simulator SHALL prevent invalid state transitions
3. THE Simulator SHALL maintain state consistency between UI, API, and internal state
4. THE Simulator SHALL use localStorage keys `sim_chip_id` and `sim_node_id` (NOT `sim_kiosk_id`)

## Testing Requirements

### Manual Testing Scenarios

1. **Scenario 1: Complete Bill Acceptance Flow**
   - Start simulator → Verify DISABLED state → Member binds via QR → Verify IDLE state → Insert 100 TWD → Verify ESCROW state → iHub confirms → MQTT stack cmd → SSE → Verify STACKING → STACKED → IDLE

2. **Scenario 2: Bill Rejection Flow**
   - Start in IDLE → Insert 500 TWD → Verify ESCROW → iHub rejects → MQTT reject cmd → SSE → Verify REJECTING → REJECTED → IDLE

3. **Scenario 3: Timeout Protection**
   - Start in IDLE → Insert 1000 TWD → Verify ESCROW → Wait 15 seconds → Verify automatic REJECTING → REJECTED → IDLE

4. **Scenario 4: WebSocket Disconnection**
   - Start simulator → Disconnect WebSocket → Verify disconnected indicator → Reconnect → Verify connected indicator

5. **Scenario 5: SSE Disconnection**
   - Start simulator → Kill iHub Server → Verify SSE disconnected warning → Restart server → Verify SSE auto-reconnects

6. **Scenario 6: API Error Handling**
   - Start simulator → Simulate API failure → Verify error message in log → Verify simulator remains functional

### Integration Testing

1. THE Simulator SHALL be tested with the actual Kiosk Exchange v2 backend
2. THE Simulator SHALL be tested with the actual iHub WebSocket server
3. THE Simulator SHALL be tested with multiple concurrent instances (different chip_ids)
4. THE Simulator SHALL be verified to produce the same MQTT/API patterns as real firmware
5. THE Simulator SHALL be verified that `infra.cmd` WebSocket events no longer trigger any behavior

### Verification Criteria

1. All state transitions SHALL match the firmware state machine specification (7 states)
2. All API calls SHALL match the format and timing of real firmware
3. Stack/reject commands SHALL arrive via MQTT → SSE, NOT via WebSocket `infra.cmd`
4. The simulator SHALL successfully complete all manual testing scenarios
5. The simulator SHALL NOT expose any security vulnerabilities (API keys, CORS issues)

## Dependencies

1. **iHub Server**: Required for API proxying, SSE endpoint, and MQTT subscription
2. **Infra API**: Required for hardware status reporting and MQTT event publishing
3. **MQTT Broker**: `mqtt.tg25.win:8883` (TLS) — iHub Server maintains persistent connection
4. **Member Reverb WebSocket**: Required for `.MemberBoundToKiosk` event
5. **Browser**: Modern browser with WebSocket, SSE (EventSource), and localStorage support

## Constraints

1. The simulator is intended for development and testing only, not for production use
2. The simulator does not simulate physical hardware failures or RS232 communication
3. The simulator assumes network connectivity and does not simulate offline scenarios
4. The simulator does not persist state across page reloads (except configuration)
5. The `infra.cmd` WebSocket event is no longer used in v4; any legacy code relying on it must be removed

## Future Enhancements (Out of Scope)

1. Simulation of hardware errors (jam, sensor failure)
2. Simulation of RS232 protocol details
3. Multi-kiosk simulation dashboard
4. Automated test script recording and playback
5. Integration with automated testing frameworks
