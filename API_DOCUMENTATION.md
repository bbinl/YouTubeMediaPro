# YouTube Downloader API Documentation

This YouTube downloader can be used as a REST API for downloading YouTube videos and Shorts in various formats and qualities.

## Base URL
```
http://your-domain.com
```

## Available Endpoints

### 1. Get Video Information

#### POST Method
**Endpoint:** `POST /api/info`

**Request Body:**
```json
{
    "url": "https://youtu.be/VIDEO_ID"
}
```

#### GET Method
**Endpoint:** `GET /api/get/info?url=YOUTUBE_URL`

**Parameters:**
- `url` (required): YouTube video URL

**Response:**
```json
{
    "success": true,
    "info": {
        "title": "Video Title",
        "duration": 300,
        "uploader": "Channel Name",
        "view_count": 1000000,
        "upload_date": "20230101",
        "description": "Video description...",
        "thumbnail": "https://thumbnail-url.jpg",
        "webpage_url": "https://youtube.com/watch?v=VIDEO_ID"
    }
}
```

### 2. Download Video/Audio

#### POST Method
**Endpoint:** `POST /api/download`

**Request Body:**
```json
{
    "url": "https://youtu.be/VIDEO_ID",
    "format": "video",  // "video" or "audio"
    "quality": "720p"   // See quality options below
}
```

#### GET Method
**Endpoint:** `GET /api/get/download?url=YOUTUBE_URL&format=FORMAT&quality=QUALITY`

**Parameters:**
- `url` (required): YouTube video URL
- `format` (optional): "video" or "audio" (default: "video")
- `quality` (optional): Quality setting (defaults: "720p" for video, "256kbps" for audio)

**Video Quality Options:**
- `3gp` - 3GP format (Mobile, small file size)
- `360p` - 360p resolution
- `480p` - 480p (SD) resolution
- `720p` - 720p (HD) resolution
- `1080p` - 1080p (Full HD) resolution

**Audio Quality Options:**
- `128kbps` - 128 kbps MP3
- `192kbps` - 192 kbps MP3
- `256kbps` - 256 kbps MP3
- `320kbps` - 320 kbps MP3

**Response:**
```json
{
    "success": true,
    "download_id": 123,
    "title": "Video Title",
    "file_path": "/path/to/file.mp4",
    "download_url": "/api/download/123/file",
    "direct_download": "/api/get/file?id=123"
}
```

### 3. Check Download Status
**Endpoint:** `GET /api/download/{download_id}/status`

Check the status of a download.

**Response:**
```json
{
    "id": 123,
    "url": "https://youtu.be/VIDEO_ID",
    "title": "Video Title",
    "format_type": "video",
    "quality": "720p",
    "status": "completed",  // "pending", "completed", "failed"
    "file_path": "/path/to/file.mp4",
    "error_message": null,
    "created_at": "2023-01-01T12:00:00",
    "completed_at": "2023-01-01T12:01:00"
}
```

### 4. Download File

#### Standard Method
**Endpoint:** `GET /api/download/{download_id}/file`

#### GET Method with Parameters
**Endpoint:** `GET /api/get/file?id=DOWNLOAD_ID`

**Parameters:**
- `id` (required): Download ID from previous download request

**Response:** Binary file download

### 5. Get Download History
**Endpoint:** `GET /api/history`

Get list of recent downloads.

**Response:**
```json
{
    "downloads": [
        {
            "id": 123,
            "url": "https://youtu.be/VIDEO_ID",
            "title": "Video Title",
            "format_type": "video",
            "quality": "720p",
            "status": "completed",
            "created_at": "2023-01-01T12:00:00"
        }
    ]
}
```

## Example Usage

### Python Example
```python
import requests

# Get video info
info_response = requests.post('http://your-domain.com/api/info', 
    json={'url': 'https://youtu.be/dQw4w9WgXcQ'})
video_info = info_response.json()

# Download audio
download_response = requests.post('http://your-domain.com/api/download', 
    json={
        'url': 'https://youtu.be/dQw4w9WgXcQ',
        'format': 'audio',
        'quality': '192kbps'
    })
download_data = download_response.json()

# Check status
status_response = requests.get(f'http://your-domain.com/api/download/{download_data["download_id"]}/status')
status = status_response.json()

# Download file when ready
if status['status'] == 'completed':
    file_response = requests.get(f'http://your-domain.com/api/download/{download_data["download_id"]}/file')
    with open('audio.mp3', 'wb') as f:
        f.write(file_response.content)
```

### JavaScript Example
```javascript
// Get video info
const infoResponse = await fetch('/api/info', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url: 'https://youtu.be/dQw4w9WgXcQ'})
});
const videoInfo = await infoResponse.json();

// Download video
const downloadResponse = await fetch('/api/download', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        url: 'https://youtu.be/dQw4w9WgXcQ',
        format: 'video',
        quality: '480p'
    })
});
const downloadData = await downloadResponse.json();

// Poll for completion
const checkStatus = async () => {
    const statusResponse = await fetch(`/api/download/${downloadData.download_id}/status`);
    const status = await statusResponse.json();
    
    if (status.status === 'completed') {
        window.location.href = `/api/download/${downloadData.download_id}/file`;
    } else if (status.status === 'failed') {
        console.error('Download failed:', status.error_message);
    } else {
        setTimeout(checkStatus, 5000); // Check again in 5 seconds
    }
};

checkStatus();
```

### cURL Examples

#### Using GET Methods (Simpler)
```bash
# Get video information
curl "http://your-domain.com/api/get/info?url=https://youtu.be/dQw4w9WgXcQ"

# Download audio (192kbps)
curl "http://your-domain.com/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=audio&quality=192kbps"

# Download video (480p)
curl "http://your-domain.com/api/get/download?url=https://youtu.be/dQw4w9WgXcQ&format=video&quality=480p"

# Download file directly
curl -O "http://your-domain.com/api/get/file?id=123"
```

#### Using POST Methods
```bash
# Get video information
curl -X POST http://your-domain.com/api/info \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtu.be/dQw4w9WgXcQ"}'

# Download audio
curl -X POST http://your-domain.com/api/download \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtu.be/dQw4w9WgXcQ",
    "format": "audio",
    "quality": "192kbps"
  }'

# Check download status
curl http://your-domain.com/api/download/123/status

# Download the file
curl -O http://your-domain.com/api/download/123/file
```

## Error Responses

All endpoints may return error responses in this format:
```json
{
    "error": "Error message description"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad request (invalid parameters)
- `404` - Not found
- `500` - Internal server error

## Features

- **Multiple Formats**: Download as video (MP4) or audio (MP3)
- **Quality Options**: Various quality levels for both video and audio
- **YouTube Shorts Support**: Full support for YouTube Shorts URLs
- **Download History**: Track all downloads with status
- **File Management**: Automatic file cleanup options
- **Progress Tracking**: Monitor download status via API
- **Error Handling**: Comprehensive error reporting

## Supported URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://youtube.com/shorts/VIDEO_ID`
- `https://m.youtube.com/watch?v=VIDEO_ID`
- Various other YouTube URL formats

## Rate Limiting

This API does not implement rate limiting by default. For production use, consider implementing rate limiting to prevent abuse.

## File Storage

Downloaded files are stored in the `downloads/` directory. Consider implementing automatic cleanup for production use to manage disk space.