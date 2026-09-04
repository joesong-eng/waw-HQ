# API 設計規範

> **適用對象**：Sophie (Owner), Mina (Member), Allie (Alliance)  
> **最後更新**：2026-08-16  
> **版本**：v1.0

---

## 🎯 REST API 設計原則

### URL 命名規範
```
GET    /api/v1/venues           # 取得列表
GET    /api/v1/venues/:id       # 取得單一資源
POST   /api/v1/venues           # 新增資源
PUT    /api/v1/venues/:id       # 完整更新
PATCH  /api/v1/venues/:id       # 部分更新
DELETE /api/v1/venues/:id       # 刪除資源
```

### 命名慣例
- **使用複數名詞**：`/venues` 而非 `/venue`
- **使用小寫加底線**：`device_id` 而非 `deviceId` 或 `DeviceId`
- **巢狀資源**：`/venues/:venue_id/devices`
- **動作用動詞**：`/devices/:id/reboot`（非 CRUD 操作）

---

## 📦 回應格式

### 成功回應
```json
{
  "success": true,
  "data": {
    "id": 123,
    "name": "測試場館"
  },
  "message": "操作成功"
}
```

### 錯誤回應
```json
{
  "success": false,
  "error": {
    "code": "VENUE_NOT_FOUND",
    "message": "找不到場館",
    "details": "場館 ID 123 不存在"
  }
}
```

### 列表回應（含分頁）
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

## 🔐 認證與授權

### Bearer Token
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 角色權限
- `owner` - 營運商：可管理自己的場館和設備
- `agent` - 代理商：可管理授權的場館
- `member` - 玩家：只能查看自己的資料
- `admin` - 系統管理員：全權限

---

## 📊 HTTP 狀態碼

### 成功回應
- `200 OK` - 請求成功
- `201 Created` - 資源已建立
- `204 No Content` - 請求成功但無內容回傳

### 客戶端錯誤
- `400 Bad Request` - 請求格式錯誤
- `401 Unauthorized` - 未認證
- `403 Forbidden` - 無權限
- `404 Not Found` - 資源不存在
- `422 Unprocessable Entity` - 驗證失敗

### 伺服器錯誤
- `500 Internal Server Error` - 伺服器錯誤
- `503 Service Unavailable` - 服務暫時無法使用

---

## 🕐 時間格式

### 統一使用 ISO 8601 UTC
```json
{
  "created_at": "2026-08-16T07:29:30Z",
  "updated_at": "2026-08-16T07:29:30Z"
}
```

### 時區處理
- 資料庫儲存：UTC
- API 回應：UTC (帶 Z 後綴)
- 前端顯示：轉換為使用者時區

---

## 🔍 查詢參數

### 分頁
```
GET /api/v1/venues?page=1&page_size=20
```

### 排序
```
GET /api/v1/venues?sort=created_at&order=desc
```

### 篩選
```
GET /api/v1/devices?status=online&venue_id=123
```

### 欄位選擇
```
GET /api/v1/venues?fields=id,name,address
```

---

## ⚠️ 錯誤代碼規範

### 命名格式
```
{RESOURCE}_{ACTION}_{REASON}
```

### 常用錯誤代碼
- `VENUE_NOT_FOUND` - 場館不存在
- `DEVICE_ALREADY_BOUND` - 設備已綁定
- `INSUFFICIENT_BALANCE` - 餘額不足
- `INVALID_CREDENTIALS` - 認證失敗
- `PERMISSION_DENIED` - 權限不足

---

## 🧪 測試規範

### 每個 API 需要測試
1. 正常情況回應
2. 缺少必填欄位
3. 資源不存在
4. 權限不足
5. 驗證失敗

---

## 📚 API 文檔

各專案的詳細 API 文檔位置：
- **Owner API**: `PROJECT/Owner/docs/api/`
- **Member API**: `PROJECT/Member/docs/api/`
- **Alliance API**: `PROJECT/Alliance/docs/api/`

---

**維護者**：HQ  
**建立日期**：2026-08-16

