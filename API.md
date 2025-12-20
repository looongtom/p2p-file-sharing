# Tài liệu API Chia sẻ File P2P

Các nút peer hiện cung cấp Flask REST API thay vì giao diện dòng lệnh tương tác.

## Base URL

Mỗi peer cung cấp API trên cổng 5000 bên trong container. Các cổng được ánh xạ như sau:
- **peer1**: `http://localhost:5001`
- **peer2**: `http://localhost:5002`
- **peer3**: `http://localhost:5003`

## Xác thực

API sử dụng **HTTP Basic Authentication**. Hầu hết các endpoint yêu cầu xác thực, ngoại trừ:
- `/api/register` - Đăng ký người dùng (không yêu cầu xác thực)
- `/api/login` - Endpoint đăng nhập (sử dụng Basic Auth để xác minh thông tin đăng nhập)
- `/health` - Kiểm tra sức khỏe (không yêu cầu xác thực)

**Tất cả các endpoint khác yêu cầu Basic Auth** với tên người dùng và mật khẩu hợp lệ.

Để sử dụng Basic Auth với curl, sử dụng cờ `-u username:password` hoặc bao gồm header `Authorization`.

## Endpoints

### 1. Đăng ký Người dùng (Đăng ký lần đầu)

**POST** `/api/register`

Đăng ký tài khoản người dùng mới. Endpoint này không yêu cầu xác thực.

**Request Body:**
```json
{
  "username": "myuser",
  "password": "mypassword123"
}
```

**Response:**
```json
{
  "ok": true,
  "message": "User myuser registered successfully"
}
```

**Ví dụ:**
```bash
curl -X POST http://localhost:5001/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword123"}'
```

**Phản hồi Lỗi:**
- `400` - Thiếu tên người dùng hoặc mật khẩu, hoặc xác thực thất bại
- `409` - Tên người dùng đã tồn tại

**Quy tắc Xác thực:**
- Tên người dùng phải có ít nhất 3 ký tự
- Mật khẩu phải có ít nhất 6 ký tự

---

### 2. Đăng nhập

**POST** `/api/login`

Đăng nhập bằng Basic Auth để xác minh thông tin đăng nhập. Endpoint này sử dụng Basic Auth để xác thực.

**Request:**
Bao gồm header Basic Auth với tên người dùng và mật khẩu.

**Response:**
```json
{
  "ok": true,
  "message": "Login successful for user myuser",
  "username": "myuser"
}
```

**Ví dụ:**
```bash
curl -X POST http://localhost:5001/api/login \
  -u myuser:mypassword123
```

**Phản hồi Lỗi:**
- `401` - Tên người dùng hoặc mật khẩu không hợp lệ

---

### 3. Chia sẻ File (Seed)

**POST** `/api/torrent/send` ⚠️ **Yêu cầu Basic Auth**

Chia sẻ file bằng cách:
1. **Tải file lên** (multipart/form-data) - File được lưu vào download_dir, sau đó sao chép vào seed_dir và chia sẻ
2. **Sử dụng file hiện có** (JSON) - Chia sẻ file đã tồn tại trong thư mục seed

**Tùy chọn 1: Tải file lên (multipart/form-data)**

**Request:**
- Content-Type: `multipart/form-data`
- Tên trường: `file`
- Bao gồm thông tin đăng nhập Basic Auth

**Response:**
```json
{
  "ok": true,
  "message": "File Xshell5.rar uploaded and is now being shared",
  "filename": "Xshell5.rar",
  "size": 12345678
}
```

**Ví dụ (tải file lên):**
```bash
curl -X POST http://localhost:5001/api/torrent/send \
  -u myuser:mypassword123 \
  -F "file=@/path/to/Xshell5.rar"
```

**Tùy chọn 2: Chia sẻ file hiện có (JSON)**

**Request Body:**
```json
{
  "filename": "Xshell5.rar"
}
```

**Response:**
```json
{
  "ok": true,
  "message": "File Xshell5.rar is now being shared"
}
```

**Ví dụ (file hiện có):**
```bash
curl -X POST http://localhost:5001/api/torrent/send \
  -u myuser:mypassword123 \
  -H "Content-Type: application/json" \
  -d '{"filename": "Xshell5.rar"}'
```

**Lưu ý:** Khi tải file lên, file được lưu vào `download_dir` trước, sau đó sao chép vào `seed_dir` để chia sẻ.

---

### 4. Liệt kê File trên Tracker

**GET** `/api/torrent/list` ⚠️ **Yêu cầu Basic Auth**

Lấy danh sách tất cả các file có sẵn trên tracker.

**Response:**
```json
{
  "ok": true,
  "items": [
    {
      "filename": "Xshell5.rar",
      "size": 12345678,
      "peers": 2,
      "infohash": "a1b2c3d4e5.."
    }
  ],
  "count": 1
}
```

**Ví dụ:**
```bash
curl -u myuser:mypassword123 http://localhost:5001/api/torrent/list
```

---

### 5. Tải File

**POST** `/api/torrent/download` ⚠️ **Yêu cầu Basic Auth**

Tải file theo tên file hoặc infohash. Quá trình tải chạy bất đồng bộ trong nền.

**Request Body (theo tên file):**
```json
{
  "filename": "Xshell5.rar"
}
```

**Request Body (theo infohash):**
```json
{
  "infohash": "a1b2c3d4e5f6..."
}
```

**Response:**
```json
{
  "ok": true,
  "message": "Download started for filename Xshell5.rar"
}
```

**Ví dụ:**
```bash
curl -X POST http://localhost:5001/api/torrent/download \
  -u myuser:mypassword123 \
  -H "Content-Type: application/json" \
  -d '{"filename": "Xshell5.rar"}'
```

---

### 6. Lấy Trạng thái Node

**GET** `/api/status` ⚠️ **Yêu cầu Basic Auth**

Lấy trạng thái hiện tại của node, bao gồm thông tin tải xuống đang hoạt động và seeding.

**Response:**
```json
{
  "ok": true,
  "node_id": 1,
  "seeding_count": 1,
  "active_downloads": [
    {
      "infohash": "a1b2c3d4e5..",
      "filename": "Xshell5.rar",
      "progress": "10/50",
      "size": 12345678
    }
  ],
  "downloads_count": 1
}
```

**Ví dụ:**
```bash
curl -u myuser:mypassword123 http://localhost:5001/api/status
```

---

### 7. Thoát An toàn

**POST** `/api/exit` ⚠️ **Yêu cầu Basic Auth**

Thông báo cho tracker về tất cả các tải xuống đang hoạt động trước khi thoát. Điều này gửi tín hiệu thoát cho tất cả các tải xuống.

**Response:**
```json
{
  "ok": true,
  "message": "Exit signal sent to tracker"
}
```

**Ví dụ:**
```bash
curl -X POST http://localhost:5001/api/exit \
  -u myuser:mypassword123
```

---

### 8. Kiểm tra Sức khỏe

**GET** `/health`

Endpoint kiểm tra sức khỏe đơn giản.

**Response:**
```json
{
  "ok": true,
  "status": "healthy"
}
```

**Ví dụ:**
```bash
curl http://localhost:5001/health
```

---

## Phản hồi Lỗi

Tất cả các endpoint trả về mã trạng thái HTTP tiêu chuẩn:
- `200` - Thành công
- `400` - Yêu cầu không hợp lệ (thiếu hoặc tham số không hợp lệ)
- `401` - Không được phép (yêu cầu xác thực hoặc thông tin đăng nhập không hợp lệ)
- `404` - Không tìm thấy (file không tồn tại)
- `409` - Xung đột (tên người dùng đã tồn tại)
- `500` - Lỗi máy chủ nội bộ

Định dạng phản hồi lỗi:
```json
{
  "ok": false,
  "error": "Error message here"
}
```

## Hướng dẫn Bắt đầu Nhanh

1. **Đăng ký người dùng mới:**
```bash
curl -X POST http://localhost:5001/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword123"}'
```

2. **Đăng nhập để xác minh thông tin đăng nhập:**
```bash
curl -X POST http://localhost:5001/api/login \
  -u myuser:mypassword123
```

3. **Sử dụng các endpoint được xác thực:**
```bash
# Liệt kê file
curl -u myuser:mypassword123 http://localhost:5001/api/torrent/list

# Tải lên và chia sẻ file
curl -X POST http://localhost:5001/api/torrent/send \
  -u myuser:mypassword123 \
  -F "file=@/path/to/Xshell5.rar"

# Hoặc chia sẻ file hiện có trong thư mục seed
curl -X POST http://localhost:5001/api/torrent/send \
  -u myuser:mypassword123 \
  -H "Content-Type: application/json" \
  -d '{"filename": "Xshell5.rar"}'

# Tải file
curl -X POST http://localhost:5001/api/torrent/download \
  -u myuser:mypassword123 \
  -H "Content-Type: application/json" \
  -d '{"filename": "Xshell5.rar"}'
```

## Lưu ý

- Thông tin đăng nhập người dùng được lưu trong `/app/users.json` bên trong mỗi container peer
- Mật khẩu được băm bằng SHA256
- Mỗi peer duy trì cơ sở dữ liệu người dùng riêng (người dùng không được chia sẻ giữa các peer)
- Thông tin đăng nhập Basic Auth phải được cung cấp với mỗi lần gọi API đến các endpoint được bảo vệ
