# 常用程式碼模式

> **適用對象**：所有 Agent  
> **最後更新**：2026-08-16  
> **版本**：v1.0

---

## 🗄️ 資料庫查詢模式

### 基本查詢（Laravel/Eloquent）
```php
// 取得單一資源
$venue = Venue::find($id);
if (!$venue) {
    return response()->json([
        'success' => false,
        'error' => ['code' => 'VENUE_NOT_FOUND']
    ], 404);
}

// 取得列表（含分頁）
$venues = Venue::where('owner_id', $ownerId)
    ->orderBy('created_at', 'desc')
    ->paginate(20);
```

### 交易 (Transaction)
```php
DB::beginTransaction();
try {
    // 更新餘額
    $member->decrement('balance', $amount);
    
    // 記錄交易
    Transaction::create([...]);
    
    DB::commit();
} catch (\Exception $e) {
    DB::rollBack();
    throw $e;
}
```

---

## 🔐 認證模式

### 檢查權限
```php
// Middleware 或 Controller
if (!$user->can('manage', $venue)) {
    return response()->json([
        'success' => false,
        'error' => ['code' => 'PERMISSION_DENIED']
    ], 403);
}
```

### Token 驗證
```php
$user = auth('api')->user();
if (!$user) {
    return response()->json([
        'success' => false,
        'error' => ['code' => 'UNAUTHORIZED']
    ], 401);
}
```

---

## 📨 MQTT 發布模式

### 發布狀態更新
```php
use App\Services\MqttService;

$mqtt = app(MqttService::class);
$mqtt->publish(
    "v9/kiosk/{$deviceId}/status",
    json_encode([
        'device_id' => $deviceId,
        'online' => true,
        'timestamp' => now()->toIso8601String()
    ]),
    1, // QoS
    true // Retained
);
```

### 發送指令
```php
$mqtt->publish(
    "v9/kiosk/{$deviceId}/command",
    json_encode([
        'command' => 'reboot',
        'timestamp' => now()->toIso8601String()
    ]),
    1,
    false
);
```

---

## 🧪 錯誤處理模式

### Controller 統一錯誤格式
```php
try {
    // 業務邏輯
    $result = $service->doSomething();
    
    return response()->json([
        'success' => true,
        'data' => $result
    ]);
    
} catch (\Illuminate\Validation\ValidationException $e) {
    return response()->json([
        'success' => false,
        'error' => [
            'code' => 'VALIDATION_FAILED',
            'message' => '驗證失敗',
            'details' => $e->errors()
        ]
    ], 422);
    
} catch (\Exception $e) {
    \Log::error('Unexpected error', [
        'message' => $e->getMessage(),
        'trace' => $e->getTraceAsString()
    ]);
    
    return response()->json([
        'success' => false,
        'error' => [
            'code' => 'INTERNAL_ERROR',
            'message' => '系統錯誤'
        ]
    ], 500);
}
```

---

## 📝 日誌記錄模式

### 結構化日誌
```php
\Log::info('Device status updated', [
    'device_id' => $deviceId,
    'status' => 'online',
    'venue_id' => $venueId,
    'timestamp' => now()->toIso8601String()
]);

\Log::error('MQTT publish failed', [
    'topic' => $topic,
    'error' => $e->getMessage(),
    'device_id' => $deviceId
]);
```

---

## 🔄 前端 API 呼叫模式 (Vue.js)

### Axios 基本模式
```javascript
// 取得資料
async fetchVenues() {
  try {
    const response = await this.$axios.get('/api/v1/venues');
    if (response.data.success) {
      this.venues = response.data.data;
    }
  } catch (error) {
    this.$message.error(error.response?.data?.error?.message || '載入失敗');
  }
}

// 提交資料
async createVenue(formData) {
  try {
    const response = await this.$axios.post('/api/v1/venues', formData);
    if (response.data.success) {
      this.$message.success('新增成功');
      return response.data.data;
    }
  } catch (error) {
    if (error.response?.status === 422) {
      // 顯示驗證錯誤
      const errors = error.response.data.error.details;
      Object.values(errors).flat().forEach(msg => {
        this.$message.error(msg);
      });
    } else {
      this.$message.error('新增失敗');
    }
    throw error;
  }
}
```

---

## 🎨 Vue 組件模式

### 資料載入生命週期
```javascript
export default {
  data() {
    return {
      loading: false,
      data: null,
      error: null
    }
  },
  
  async mounted() {
    await this.loadData();
  },
  
  methods: {
    async loadData() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await this.$axios.get('/api/v1/data');
        this.data = response.data.data;
      } catch (error) {
        this.error = error.response?.data?.error?.message || '載入失敗';
      } finally {
        this.loading = false;
      }
    }
  }
}
```

---

## 📱 Android (Kotlin) 模式

### ViewModel + LiveData
```kotlin
class DeviceViewModel : ViewModel() {
    private val _devices = MutableLiveData<List<Device>>()
    val devices: LiveData<List<Device>> = _devices
    
    private val _loading = MutableLiveData<Boolean>()
    val loading: LiveData<Boolean> = _loading
    
    fun loadDevices(venueId: Int) {
        viewModelScope.launch {
            _loading.value = true
            try {
                val response = apiService.getDevices(venueId)
                _devices.value = response.data
            } catch (e: Exception) {
                // 處理錯誤
            } finally {
                _loading.value = false
            }
        }
    }
}
```

---

## 🔌 ESP32 (Arduino) 模式

### MQTT 連線與重連
```cpp
void reconnectMQTT() {
    while (!mqtt.connected()) {
        Serial.println("Attempting MQTT connection...");
        
        String clientId = "KIOSK_" + String(DEVICE_ID);
        
        if (mqtt.connect(clientId.c_str(), MQTT_USER, MQTT_PASS,
                        lwt_topic.c_str(), 1, true, lwt_payload.c_str())) {
            Serial.println("MQTT connected");
            
            // 訂閱指令主題
            String cmdTopic = "v9/kiosk/" + String(DEVICE_ID) + "/command";
            mqtt.subscribe(cmdTopic.c_str(), 1);
            
        } else {
            Serial.print("Failed, rc=");
            Serial.println(mqtt.state());
            delay(5000);
        }
    }
}
```

---

## 🧪 測試模式

### PHPUnit 基本測試
```php
public function test_can_create_venue()
{
    $owner = User::factory()->create(['role' => 'owner']);
    
    $response = $this->actingAs($owner, 'api')
        ->postJson('/api/v1/venues', [
            'name' => 'Test Venue',
            'address' => 'Test Address'
        ]);
    
    $response->assertStatus(201)
        ->assertJsonStructure([
            'success',
            'data' => ['id', 'name', 'address']
        ]);
    
    $this->assertDatabaseHas('venues', [
        'name' => 'Test Venue',
        'owner_id' => $owner->id
    ]);
}
```

---

## 📚 參考資源

- **Laravel 文檔**: https://laravel.com/docs
- **Vue.js 文檔**: https://vuejs.org/guide/
- **ESP32 文檔**: https://docs.espressif.com/

---

**維護者**：HQ  
**建立日期**：2026-08-16

