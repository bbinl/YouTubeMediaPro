# Sample API Links - YouTube Downloader

## Base URL
Replace `localhost:5000` with your actual domain when deploying.

## 1. Get Video Information
```
http://localhost:5000/api/get/info?url=https://youtu.be/dQw4w9WgXcQ
```

## 2. Video Downloads

### 3GP Format (Mobile, smallest file size)
```
http://localhost:5000/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=video&quality=3gp
```

### 360p Quality
```
http://localhost:5000/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=video&quality=360p
```

### 480p Quality (SD)
```
http://localhost:5000/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=video&quality=480p
```

### 720p Quality (HD - Default)
```
http://localhost:5000/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=video&quality=720p
```

### 1080p Quality (Full HD)
```
http://localhost:5000/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=video&quality=1080p
```

## 3. Audio Downloads

### 128kbps Quality
```
http://localhost:5000/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=audio&quality=128kbps
```

### 192kbps Quality
```
http://localhost:5000/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=audio&quality=192kbps
```

### 256kbps Quality (Default)
```
http://localhost:5000/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=audio&quality=256kbps
```

### 320kbps Quality (High Quality)
```
http://localhost:5000/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=audio&quality=320kbps
```

## 4. Default Quality Downloads (No quality parameter)

### Default Video (720p)
```
http://localhost:5000/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=video
```

### Default Audio (256kbps)
```
http://localhost:5000/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=audio
```

## 5. Download File by ID
After getting a download response with `download_id`, use:
```
http://localhost:5000/api/get/file?id=DOWNLOAD_ID
```

Example:
```
http://localhost:5000/api/get/file?id=123
```

## Quick Test Commands

### Using curl:
```bash
# Get video info
curl "http://localhost:5000/api/get/info?url=https://youtu.be/dQw4w9WgXcQ"

# Download 3GP video (mobile format)
curl "http://localhost:5000/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=video&quality=3gp"

# Download 192kbps audio
curl "http://localhost:5000/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=audio&quality=192kbps"

# Download file (replace 123 with actual download ID)
curl -O "http://localhost:5000/api/get/file?id=123"
```

### Direct browser testing:
Copy and paste any of the above URLs directly into your browser address bar.

## URL Encoding
For URLs with special characters, encode them:
```bash
# Original: https://youtu.be/dQw4w9WgXcQ?t=30
# Encoded: https%3A//youtu.be/dQw4w9WgXcQ%3Ft%3D30

curl "http://localhost:5000/api/get/download?url=https%3A//youtu.be/dQw4w9WgXcQ%3Ft%3D30&format=video&quality=3gp"
```

## Supported Video Formats
- **3GP**: Mobile format, smallest file size, 240p resolution
- **360p**: Standard definition
- **480p**: Enhanced definition  
- **720p**: High definition (default)
- **1080p**: Full high definition

## Supported Audio Formats
- **128kbps**: Standard quality MP3
- **192kbps**: Good quality MP3
- **256kbps**: High quality MP3 (default)
- **320kbps**: Premium quality MP3

## Response Format
All download endpoints return JSON:
```json
{
    "success": true,
    "download_id": 123,
    "title": "Video Title",
    "file_path": "path/to/file.ext",
    "download_url": "/api/download/123/file",
    "direct_download": "/api/get/file?id=123"
}
```

## Error Handling
Errors return JSON with error message:
```json
{
    "error": "Error description"
}
```