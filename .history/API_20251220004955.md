# P2P File Sharing API Documentation

The peer nodes now expose a Flask REST API instead of an interactive command-line interface.

## Base URL

Each peer exposes its API on port 5000 inside the container. The ports are mapped as follows:
- **peer1**: `http://localhost:5001`
- **peer2**: `http://localhost:5002`
- **peer3**: `http://localhost:5003`

## Authentication

The API uses **HTTP Basic Authentication**. Most endpoints require authentication, except:
- `/api/register` - User registration (no auth required)
- `/api/login` - Login endpoint (uses Basic Auth to verify credentials)
- `/health` - Health check (no auth required)

**All other endpoints require Basic Auth** with valid username and password.

To use Basic Auth with curl, use the `-u username:password` flag or include the `Authorization` header.

## Endpoints

### 1. Register User (First-time Registration)

**POST** `/api/register`

Register a new user account. This endpoint does not require authentication.

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

**Example:**
```bash
curl -X POST http://localhost:5001/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword123"}'
```

**Error Responses:**
- `400` - Missing username or password, or validation failed
- `409` - Username already exists

**Validation Rules:**
- Username must be at least 3 characters
- Password must be at least 6 characters

---

### 2. Login

**POST** `/api/login`

Login using Basic Auth to verify credentials. This endpoint uses Basic Auth to authenticate.

**Request:**
Include Basic Auth header with username and password.

**Response:**
```json
{
  "ok": true,
  "message": "Login successful for user myuser",
  "username": "myuser"
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/api/login \
  -u myuser:mypassword123
```

**Error Responses:**
- `401` - Invalid username or password

---

### 3. Share a File (Seed)

**POST** `/api/torrent/send` ⚠️ **Requires Basic Auth**

Share a file from the node's seed directory.

### 1. Share a File (Seed)

**POST** `/api/torrent/send`

Share a file from the node's seed directory.

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

**Example:**
```bash
curl -X POST http://localhost:5001/api/torrent/send \
  -u myuser:mypassword123 \
  -H "Content-Type: application/json" \
  -d '{"filename": "Xshell5.rar"}'
```

---

### 4. List Files on Tracker

**GET** `/api/torrent/list` ⚠️ **Requires Basic Auth**

Get a list of all files available on the tracker.

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

**Example:**
```bash
curl -u myuser:mypassword123 http://localhost:5001/api/torrent/list
```

---

### 5. Download a File

**POST** `/api/torrent/download` ⚠️ **Requires Basic Auth**

Download a file by filename or infohash. The download runs asynchronously in the background.

**Request Body (by filename):**
```json
{
  "filename": "Xshell5.rar"
}
```

**Request Body (by infohash):**
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

**Example:**
```bash
curl -X POST http://localhost:5001/api/torrent/download \
  -u myuser:mypassword123 \
  -H "Content-Type: application/json" \
  -d '{"filename": "Xshell5.rar"}'
```

---

### 6. Get Node Status

**GET** `/api/status` ⚠️ **Requires Basic Auth**

Get the current status of the node, including active downloads and seeding information.

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

**Example:**
```bash
curl -u myuser:mypassword123 http://localhost:5001/api/status
```

---

### 7. Exit Gracefully

**POST** `/api/exit` ⚠️ **Requires Basic Auth**

Notify the tracker about all active downloads before exiting. This sends exit signals for all downloads.

**Response:**
```json
{
  "ok": true,
  "message": "Exit signal sent to tracker"
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/api/exit \
  -u myuser:mypassword123
```

---

### 8. Health Check

**GET** `/health`

Simple health check endpoint.

**Response:**
```json
{
  "ok": true,
  "status": "healthy"
}
```

**Example:**
```bash
curl http://localhost:5001/health
```

---

## Error Responses

All endpoints return standard HTTP status codes:
- `200` - Success
- `400` - Bad Request (missing or invalid parameters)
- `401` - Unauthorized (authentication required or invalid credentials)
- `404` - Not Found (file not found)
- `409` - Conflict (username already exists)
- `500` - Internal Server Error

Error response format:
```json
{
  "ok": false,
  "error": "Error message here"
}
```

## Quick Start Guide

1. **Register a new user:**
```bash
curl -X POST http://localhost:5001/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword123"}'
```

2. **Login to verify credentials:**
```bash
curl -X POST http://localhost:5001/api/login \
  -u myuser:mypassword123
```

3. **Use authenticated endpoints:**
```bash
# List files
curl -u myuser:mypassword123 http://localhost:5001/api/torrent/list

# Share a file
curl -X POST http://localhost:5001/api/torrent/send \
  -u myuser:mypassword123 \
  -H "Content-Type: application/json" \
  -d '{"filename": "Xshell5.rar"}'

# Download a file
curl -X POST http://localhost:5001/api/torrent/download \
  -u myuser:mypassword123 \
  -H "Content-Type: application/json" \
  -d '{"filename": "Xshell5.rar"}'
```

## Notes

- User credentials are stored in `/app/users.json` inside each peer container
- Passwords are hashed using SHA256
- Each peer maintains its own user database (users are not shared between peers)
- Basic Auth credentials must be provided with each API call to protected endpoints

