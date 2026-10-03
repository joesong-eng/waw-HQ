# TASK 20260914 ALLIE BURNING STATION REFACTOR

**task_id**: TASK_20260914_ALLIE_BURNING_STATION_REFACTOR  
**dispatch_time**: 2026-09-14 10:30  
**dispatcher**: HQ (Taskflow)  
**executor**: Allie (Alliance Lead)  
**priority**: P0 (High)  
**source**: Allie proposal 20260914_092816, Joe approved  
**spec**: brains/knowledge/02_technical_standards/QRCODE_FORMAT_STANDARD.md v2.1.0  
**base**: Allie completed TASK_20260913_ALLIE_PUBLIC_TOKEN_QR_REFACTOR (commit d08c1d0)

---

## Background

Allie reported that the current burning station page at https://ali.tg25.win/devices has multiple serious issues affecting production line operator Lao Qiu daily efficiency and after-sale tablet replacement flow. HQ reviewed the proposal and dispatches this task.

Core principle: **Lao Qiu perspective - intuitive operation, coherent flow, must cover after-sale replacement.**

---

## Module 1: UI Immersive - Remove Terminal hex log

**Problem**: Right panel shows Terminal hex log (SYSTEM DIAGNOSTICS) and empty error states, confusing for production operator Lao Qiu.

**Requirements**:

1. Hide terminal log panel by default
   - In resources/views/devices/burning.blade.php, the .terminal-wrap / .terminal-body / .log-line blocks
   - Replace with Lao Qiu status cards: plain language progress (e.g. OK Comms card 1/3 burned, WAIT burning 2nd, BATTERY waiting for device)
   - Keep hex log as hidden debug mode (key toggle or dev flag), not shown by default

2. Empty state handling
   - Device not connected: show friendly guide, not error
   - Order not selected: hide Step 2/3

3. Stepped Progress Bar
   - Comms card (3 steps): 1.Burn > 2.Pair > 3.Shipping Label
   - Kiosk card (5 steps): 1.Burn > 2.Pair > 3.APK Install > 4.BOOT Verify > 5.Shipping Label

---

## Module 2: Smart Card Auto-Route by order type

**Problem**: Even for pure comms card orders, Step 3 tablet pairing is forced; accessory-only orders not filtered.

**Requirements**:

1. Auto detect order type
   - In DeviceController@index or frontend JS, based on order items product.firmware_type:
     - Pure comms card (all IOTwawS3): show Step 1+2+shipping label only, hide Step 3
     - Pure kiosk card (all IOTkiosk): show full 5 steps
     - Mixed order: segment display, comms first then kiosk
     - Pure accessory (no has_firmware): skip burning page entirely

2. Step 3 conditional display
   - Only show when order contains tablet-pairing device types
   - Drag-and-drop pairing pool hidden when not needed

3. Accessory order filter
   - Orders without any has_firmware=true product: no Go to Burning button
   - Go directly to ready_to_ship status

---

## Module 3: Shipping Label Automation

**Problem**: After burning, must manually click Submit Record then open preview separately, broken workflow.

**Requirements**:

1. Auto-commit on burn complete
   - Web Serial burn progress reaches 100%: auto call POST /api/devices/commit-registration
   - No need for Lao Qiu to click Submit Record button
   - Auto generate public_token (already implemented by Allie, keep)

2. Auto preview label after commit
   - On commit-registration success: auto call showQrPreview(publicToken)
   - Lao Qiu sees QR preview popup, confirm then print
   - QR content: https://win.tg25.win/m/play?t={public_token} (already implemented, keep)

3. Batch print optimization
   - Keep existing Batch Print PDF button
   - Add per-record Print Label button in burning history
   - After print, auto mark qr_printed_at

4. One-click shipping labels
   - All devices burned: show Shipping Labels Ready button at top
   - Click to generate all QR label PDFs for the order at once

---

## Module 4: After-Sale Tablet Replacement

**Problem**: When customer (e.g. Boss Li) old tablet breaks, buys new tablet from Lao Qiu, order has no card to burn, system cannot bind new tablet to existing machine. Customer sees 404 on new tablet.

**Requirements**:

1. Add After-Sale Replacement mode entry
   - On burning station page, add After-Sale Replacement button/mode toggle
   - After-sale mode UI simplifies to:
     - Select customer (search by name/phone)
     - Select existing machine (list installed devices)
     - Bind new tablet Android ID to existing machine

2. After-sale pair API
   - New endpoint: POST /api/devices/after-sale-pair
   - Params: customer_id (or binding_id), tablet_android_id
   - Logic:
     - Find customer device bindings (ali_device_bindings with node_id)
     - Write new tablet Android ID to waw_core.tablets and associate
     - Update waw_core.kiosks.screen_mac to new tablet Android ID
     - Return pair success + public_token for label printing

3. No burning flow needed
   - After-sale does not need Web Serial (card already at customer site)
   - Only: Select customer > Select machine > Input new tablet ID > Bind > Print label

4. UI flow (Lao Qiu perspective):
   Step 1: Search customer (name/phone)
   Step 2: Select machine (dropdown with machine name+node_id)
   Step 3: Input new tablet Android ID (or scan barcode)
   Step 4: Click Bind
   Done: Pair success - show QR preview > Print

---

## Suggested Phase Order

| Phase | Module | Effort | Dependency |
|-------|--------|--------|------------|
| Phase 1 | Module 1: UI Immersive | Medium | None |
| Phase 2 | Module 2: Smart Card Route | Medium | Phase 1 |
| Phase 3 | Module 3: Label Automation | Small | Phase 1 |
| Phase 4 | Module 4: After-Sale Replacement | Large | Phase 1-3 (can design in parallel) |

---

## Files to Modify

| File | Change | Description |
|------|--------|-------------|
| resources/views/devices/burning.blade.php | Refactor | UI main (terminal removal, conditional steps, auto-commit, after-sale mode) |
| app/Http/Controllers/DeviceController.php | Extend | After-sale endpoint, smart route logic, auto-preview |
| routes/web.php | Add | After-sale pair API route |
| app/Models/AliDeviceBinding.php | Maybe extend | After-sale query scope |
| resources/views/devices/partials/ | New | After-sale mode partial view if needed |

---

## Acceptance Criteria

1. UI Immersive: No terminal hex log by default, plain language status, friendly empty states
2. Smart Route: Pure comms hides Step 3, pure accessory skips burning, mixed segments
3. Label Automation: 100% auto-commit, auto QR preview, one-click batch print
4. After-Sale: Select customer > machine > tablet ID > bind > no more 404
5. QR Compliance: All labels use https://win.tg25.win/m/play?t={public_token}, no raw JSON/chip_id/MAC

---

## Report Requirements

Place report in .taskflow/alliance/outbox/, named:
REPORT_{timestamp}_ALLIE_BURNING_STATION_REFACTOR.md

Include:
1. Each Phase status (done/failed)
2. Git commit hash
3. Remote deploy status (view:clear/config:cache/cache:clear)
4. Test screenshots or API logs (no verbal reports)
5. Issues and solutions

---

**Dispatcher**: HQ  
**Dispatch Time**: 2026-09-14 10:30  
**Task ID**: TASK_20260914_ALLIE_BURNING_STATION_REFACTOR
