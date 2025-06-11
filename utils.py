import re
import os
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

def validate_youtube_url(url):
    """Validate if the URL is a valid YouTube URL"""
    if not url:
        return False
    
    # YouTube URL patterns
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/[\w-]+',
        r'(?:https?://)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+',
        r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=[\w-]+',
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url, re.IGNORECASE):
            return True
    
    return False

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    if not url:
        return None
    
    # Parse the URL
    parsed = urlparse(url)
    
    if parsed.hostname in ['youtu.be']:
        return parsed.path[1:]
    
    if parsed.hostname in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
        elif parsed.path.startswith('/embed/'):
            return parsed.path.split('/')[2]
        elif parsed.path.startswith('/v/'):
            return parsed.path.split('/')[2]
        elif parsed.path.startswith('/shorts/'):
            return parsed.path.split('/')[2]
    
    return None

def sanitize_filename(filename):
    """Sanitize filename for safe file system storage"""
    if not filename:
        return "unknown"
    
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove extra whitespace and dots
    filename = re.sub(r'\s+', ' ', filename.strip())
    filename = filename.strip('.')
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:97] + '...'
    
    # Ensure it's not empty
    if not filename:
        filename = "unknown"
    
    return filename

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if not seconds:
        return "Unknown"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def format_file_size(size_bytes):
    """Format file size in bytes to human readable format"""
    if not size_bytes:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"

def get_file_size(file_path):
    """Get file size in bytes"""
    try:
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {str(e)}")
    
    return 0

def cleanup_old_files(directory, max_age_hours=0.25):
    """Clean up files older than specified hours"""
    try:
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        cleaned_count = 0
        
        for filename in os.listdir(directory):
            if filename == '.gitkeep':
                continue
                
            file_path = os.path.join(directory, filename)
            
            try:
                file_age = current_time - os.path.getctime(file_path)
                
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    cleaned_count += 1
                    logger.info(f"Cleaned up old file: {file_path}")
                    
            except Exception as e:
                logger.error(f"Error cleaning up file {file_path}: {str(e)}")
        
        return cleaned_count
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return 0

def is_youtube_shorts_url(url):
    """Check if URL is a YouTube Shorts URL"""
    if not url:
        return False
    
    return '/shorts/' in url.lower()

def get_video_format_info(info_dict):
    """Extract available format information from yt-dlp info dict"""
    formats = []
    
    if 'formats' in info_dict:
        for f in info_dict['formats']:
            format_info = {
                'format_id': f.get('format_id'),
                'ext': f.get('ext'),
                'quality': f.get('quality'),
                'height': f.get('height'),
                'width': f.get('width'),
                'fps': f.get('fps'),
                'vcodec': f.get('vcodec'),
                'acodec': f.get('acodec'),
                'filesize': f.get('filesize'),
                'format_note': f.get('format_note')
            }
            formats.append(format_info)
    
    return formats
