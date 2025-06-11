# GET Method API Examples

Your YouTube downloader now supports simple GET method APIs that are easier to use than POST methods.

## Quick Start

### 1. Get Video Information
```bash
curl "http://your-domain.com/api/get/info?url=https://youtu.be/VIDEO_ID"
```

### 2. Download Audio (192kbps)
```bash
curl "http://your-domain.com/api/get/download?url=https://youtu.be/VIDEO_ID&format=audio&quality=192kbps"
```

### 3. Download Video (480p)
```bash
curl "http://your-domain.com/api/get/download?url=https://youtu.be/VIDEO_ID&format=video&quality=480p"
```

### 4. Download File
```bash
curl -O "http://your-domain.com/api/get/file?id=DOWNLOAD_ID"
```

## Browser Examples

You can test these URLs directly in your browser:

### Get Video Info:
```
http://your-domain.com/api/get/info?url=https://youtu.be/-vopPrJQcyY
```

### Download Audio:
```
http://your-domain.com/api/get/download?url=https://youtu.be/-vopPrJQcyY&format=audio&quality=192kbps
```

### Download Video:
```
http://your-domain.com/api/get/download?url=https://youtu.be/-vopPrJQcyY&format=video&quality=480p
```

## Quality Options

### Video Qualities:
- `3gp` - 3GP format (Mobile, small file size)
- `360p` - Standard definition
- `480p` - Enhanced definition
- `720p` - High definition (default)
- `1080p` - Full high definition

### Audio Qualities:
- `128kbps` - Standard quality
- `192kbps` - Good quality
- `256kbps` - High quality (default)
- `320kbps` - Premium quality

## URL Encoding

For complex URLs with special characters, encode them:
```bash
# Original URL: https://youtu.be/VIDEO_ID?t=123
# Encoded URL: https%3A//youtu.be/VIDEO_ID%3Ft%3D123

curl "http://your-domain.com/api/get/download?url=https%3A//youtu.be/VIDEO_ID%3Ft%3D123&format=audio"
```

## Python Example with GET Methods
```python
import requests
import urllib.parse

# URL to download
youtube_url = "https://youtu.be/-vopPrJQcyY"
encoded_url = urllib.parse.quote(youtube_url, safe='')

# Get video info
info_url = f"http://your-domain.com/api/get/info?url={encoded_url}"
response = requests.get(info_url)
video_info = response.json()
print(f"Title: {video_info['info']['title']}")

# Download audio
download_url = f"http://your-domain.com/api/get/download?url={encoded_url}&format=audio&quality=192kbps"
response = requests.get(download_url)
download_data = response.json()

if download_data['success']:
    download_id = download_data['download_id']
    print(f"Download ID: {download_id}")
    
    # Download file
    file_url = f"http://your-domain.com/api/get/file?id={download_id}"
    file_response = requests.get(file_url)
    
    with open('audio.mp3', 'wb') as f:
        f.write(file_response.content)
    print("Audio downloaded successfully!")
```

## JavaScript Example with GET Methods
```javascript
async function downloadYouTubeAudio(url) {
    const encodedUrl = encodeURIComponent(url);
    
    // Get video info
    const infoResponse = await fetch(`/api/get/info?url=${encodedUrl}`);
    const videoInfo = await infoResponse.json();
    console.log('Title:', videoInfo.info.title);
    
    // Download audio
    const downloadResponse = await fetch(
        `/api/get/download?url=${encodedUrl}&format=audio&quality=192kbps`
    );
    const downloadData = await downloadResponse.json();
    
    if (downloadData.success) {
        // Direct download
        window.location.href = `/api/get/file?id=${downloadData.download_id}`;
    }
}

// Usage
downloadYouTubeAudio('https://youtu.be/-vopPrJQcyY');
```

## Advantages of GET Methods

1. **Simpler**: No need for JSON payloads
2. **Browser Compatible**: Can test directly in browser
3. **URL Shareable**: Easy to share download links
4. **Cache Friendly**: Can be cached by browsers/proxies
5. **Easier Integration**: Works with simple HTTP clients

## Use Cases

- **Web Scrapers**: Easy integration with scraping tools
- **Browser Extensions**: Simple fetch() calls
- **Mobile Apps**: Direct URL construction
- **Command Line Tools**: Simple curl commands
- **Testing**: Quick browser-based testing