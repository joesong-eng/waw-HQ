# IOTwawS3 MQTT Payload Specification

> **Status**: Verified by hColi  
> **Last Updated**: 2026-06-04  

## 1. Device Command (Cloud -> ESP32)

**Topic**: `device/{chip_id}/cmd`

### 1.1 Set Signal Polarity (`set_signal_polarity`)
Used to manually override or lock the signal polarity for coin-in and payout counters.

**Payload**:
```json
{
  "command": "set_signal_polarity",
  "transaction_id": "req_123456",
  "params": {
    "polarity": "active_low"
  }
}
```

- `polarity`: `"active_high"` | `"active_low"`

**Device Response**:
```json
{
  "transaction_id": "req_123456",
  "command": "set_signal_polarity",
  "status": "ok",
  "data": {
    "message": "Polarity updated to active_low. Rebooting..."
  }
}
```

## 2. Adaptive Logic Implementation

### 2.1 Boot-time Auto-Detection
1. **Delay**: 500ms after boot (wait for hardware stabilization).
2. **Sampling**: 5 consecutive samples with 10ms intervals.
3. **Logic**:
   - If all 5 samples == `1` (High) -> Assume **Active High** machine (Normal state is High/Pull-up).
   - If all 5 samples == `0` (Low) -> Assume **Active Low** machine (Normal state is Low/Optocoupler conduction).
4. **Persistence**: Result is stored in NVS (Non-Volatile Storage).

### 2.2 GPIO Edge Triggering Mapping
Based on optocoupler inversion characteristics:

| Machine Type | Logic | ESP32 Normal GPIO | Event Trigger | PCNT Action |
| :--- | :--- | :--- | :--- | :--- |
| **kingapple** | Active High | `1` (High) | Pulse (Low) | **NEGEDGE** |
| **Huga** | Active Low | `0` (Low) | Pulse (High) | **POSEDGE** |
