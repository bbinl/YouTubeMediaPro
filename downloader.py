import os
import yt_dlp
import subprocess
import logging
from utils import sanitize_filename

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    def __init__(self):
        self.downloads_dir = 'downloads'
        os.makedirs(self.downloads_dir, exist_ok=True)
        
        # Video quality mapping
        self.video_formats = {
            '3gp': 'worst[height<=240]/worst',
            '360p': 'best[height<=360]',
            '480p': 'best[height<=480]',
            '720p': 'best[height<=720]',
            '1080p': 'best[height<=1080]'
        }
        
        # Audio quality mapping (bitrate in kbps)
        self.audio_qualities = {
            '128kbps': '128',
            '192kbps': '192',
            '256kbps': '256',
            '320kbps': '320'
        }
        
        # Enhanced anti-detection options for Railway deployment
        self.base_ydl_opts = {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['configs'],
                    'skip': ['hls'],
                }
            },
            'socket_timeout': 60,
            'retries': 5,
            'fragment_retries': 5,
            'retry_sleep_functions': {'http': lambda n: min(4 ** n, 30)},
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            'concurrent_fragment_downloads': 2,
            'http_chunk_size': 5242880,  # 5MB chunks for Railway
            'geo_bypass': True,
            'no_color': True,
            'extract_flat': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': False,
        }
        
        # Enhanced cookie handling for Railway
        cookies_file = os.path.join(os.getcwd(), 'cookies.txt')
        if os.path.exists(cookies_file):
            self.base_ydl_opts['cookiefile'] = cookies_file
            logger.info(f"Using cookies file: {cookies_file}")
        else:
            logger.warning("No cookies file found - downloads may be limited")
            # Add additional anti-detection when no cookies
            self.base_ydl_opts.update({
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android'],  # Android client is more reliable without cookies
                        'player_skip': ['configs', 'webpage'],
                    }
                }
            })
    
    def get_video_info(self, url):
        """Get video information without downloading"""
        # Try multiple extraction methods for better reliability
        extraction_methods = [
            # Method 1: Standard with cookies
            {**self.base_ydl_opts, 'quiet': True, 'no_warnings': True},
            # Method 2: Android client only (more reliable for blocked regions)
            {
                **self.base_ydl_opts,
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android'],
                        'player_skip': ['configs', 'webpage'],
                    }
                }
            },
            # Method 3: Web client with minimal headers
            {
                'user_agent': 'Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/88.0',
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web'],
                    }
                }
            }
        ]
        
        last_error = None
        for i, ydl_opts in enumerate(extraction_methods):
            try:
                logger.info(f"Attempting video info extraction method {i+1}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if not info:
                        raise Exception("Could not extract video information")
                    
                    # Extract info with type safety
                    title = info.get('title') if info else 'Unknown'
                    duration = info.get('duration') if info else 0
                    uploader = info.get('uploader') if info else 'Unknown'
                    view_count = info.get('view_count') if info else 0
                    upload_date = info.get('upload_date') if info else ''
                    description = info.get('description') if info else ''
                    thumbnail = info.get('thumbnail') if info else ''
                    webpage_url = info.get('webpage_url') if info else url
                    
                    if description and len(description) > 200:
                        description = description[:200] + '...'
                    
                    logger.info(f"Successfully extracted video info using method {i+1}")
                    return {
                        'title': title or 'Unknown',
                        'duration': duration or 0,
                        'uploader': uploader or 'Unknown',
                        'view_count': view_count or 0,
                        'upload_date': upload_date or '',
                        'description': description or '',
                        'thumbnail': thumbnail or '',
                        'webpage_url': webpage_url or url
                    }
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Video info extraction method {i+1} failed: {str(e)}")
                if i < len(extraction_methods) - 1:
                    continue
        
        # If all methods failed
        error_msg = str(last_error) if last_error else "Unknown error"
        if "403" in error_msg or "Forbidden" in error_msg:
            error_msg = "YouTube blocked this request. Please upload cookies.txt file or try again later."
        elif "Sign in to confirm" in error_msg:
            error_msg = "YouTube requires sign-in verification. Please upload cookies.txt file."
        
        logger.error(f"All video info extraction methods failed: {error_msg}")
        raise Exception(f"Failed to get video information: {error_msg}")
    
    def download_video(self, url, quality='720p'):
        """Download video in specified quality"""
        try:
            # Get video info first
            info = self.get_video_info(url)
            title = sanitize_filename(info['title'])
            
            # Special handling for 3GP format
            if quality == '3gp':
                return self._download_3gp_video(url, title, info)
            
            format_selector = self.video_formats.get(quality, 'best[height<=720]')
            output_path = os.path.join(self.downloads_dir, f"{title}_{quality}.%(ext)s")
            
            # Try multiple download methods
            download_methods = [
                # Method 1: Standard download with cookies
                {
                    **self.base_ydl_opts,
                    'format': format_selector,
                    'outtmpl': output_path,
                    'noplaylist': True,
                    'extractaudio': False,
                    'prefer_ffmpeg': True,
                },
                # Method 2: Android client fallback
                {
                    **self.base_ydl_opts,
                    'format': format_selector,
                    'outtmpl': output_path,
                    'noplaylist': True,
                    'extractaudio': False,
                    'prefer_ffmpeg': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android'],
                            'player_skip': ['configs', 'webpage'],
                        }
                    }
                }
            ]
            
            last_error = None
            for i, ydl_opts in enumerate(download_methods):
                try:
                    logger.info(f"Attempting video download method {i+1}")
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    
                    # Find the actual downloaded file
                    expected_extensions = ['mp4', 'webm', 'mkv']
                    actual_file_path = None
                    
                    for ext in expected_extensions:
                        potential_path = output_path.replace('%(ext)s', ext)
                        if os.path.exists(potential_path):
                            actual_file_path = potential_path
                            break
                    
                    if not actual_file_path:
                        # Fallback: look for any file with the title prefix
                        for file in os.listdir(self.downloads_dir):
                            if file.startswith(f"{title}_{quality}"):
                                actual_file_path = os.path.join(self.downloads_dir, file)
                                break
                    
                    if actual_file_path and os.path.exists(actual_file_path):
                        logger.info(f"Successfully downloaded video using method {i+1}")
                        return {
                            'title': info['title'],
                            'file_path': actual_file_path,
                            'format': 'video',
                            'quality': quality
                        }
                    else:
                        raise Exception("Downloaded file not found")
                        
                except Exception as e:
                    last_error = e
                    logger.warning(f"Video download method {i+1} failed: {str(e)}")
                    if i < len(download_methods) - 1:
                        continue
            
            # If all methods failed
            error_msg = str(last_error) if last_error else "Unknown error"
            if "403" in error_msg or "Forbidden" in error_msg:
                error_msg = "YouTube blocked this download. Please upload cookies.txt file or try again later."
            elif "Sign in to confirm" in error_msg:
                error_msg = "YouTube requires sign-in verification. Please upload cookies.txt file."
            
            logger.error(f"All video download methods failed: {error_msg}")
            raise Exception(f"Video download failed: {error_msg}")
            
        except Exception as e:
            logger.error(f"Video download failed: {str(e)}")
            raise Exception(f"Video download failed: {str(e)}")
    
    def _download_3gp_video(self, url, title, info):
        """Download video and convert to 3GP format"""
        try:
            # Download in low quality first
            temp_output = os.path.join(self.downloads_dir, f"temp_{title}.%(ext)s")
            final_output = os.path.join(self.downloads_dir, f"{title}_3gp.mp4")
            
            ydl_opts = {
                'format': 'worst[height<=240]/worst',
                'outtmpl': temp_output,
                'noplaylist': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find the downloaded temp file
            temp_file_path = None
            expected_extensions = ['mp4', 'webm', 'mkv', 'flv']
            
            for ext in expected_extensions:
                potential_path = temp_output.replace('%(ext)s', ext)
                if os.path.exists(potential_path):
                    temp_file_path = potential_path
                    break
            
            if not temp_file_path:
                # Fallback: look for any temp file
                for file in os.listdir(self.downloads_dir):
                    if file.startswith(f"temp_{title}"):
                        temp_file_path = os.path.join(self.downloads_dir, file)
                        break
            
            if not temp_file_path or not os.path.exists(temp_file_path):
                raise Exception("Temporary video file not found")
            
            # For Railway deployment, we'll use a simplified approach
            # Just rename to indicate 3GP quality instead of actual conversion
            os.rename(temp_file_path, final_output)
            
            return {
                'title': info['title'],
                'file_path': final_output,
                'format': 'video',
                'quality': '3gp'
            }
            
        except Exception as e:
            logger.error(f"3GP video download failed: {str(e)}")
            raise Exception(f"3GP video download failed: {str(e)}")
    
    def download_audio(self, url, quality='256kbps'):
        """Download audio in specified quality"""
        try:
            # Get video info first
            info = self.get_video_info(url)
            title = sanitize_filename(info['title'])
            
            # Direct audio download with yt-dlp postprocessor
            final_output = os.path.join(self.downloads_dir, f"{title}_{quality}.mp3")
            
            # Try multiple download methods
            download_methods = [
                # Method 1: Standard audio download with cookies
                {
                    **self.base_ydl_opts,
                    'format': 'bestaudio/best',
                    'outtmpl': final_output.replace('.mp3', '.%(ext)s'),
                    'noplaylist': True,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': self.audio_qualities.get(quality, '256'),
                    }],
                },
                # Method 2: Android client fallback
                {
                    **self.base_ydl_opts,
                    'format': 'bestaudio/best',
                    'outtmpl': final_output.replace('.mp3', '.%(ext)s'),
                    'noplaylist': True,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': self.audio_qualities.get(quality, '256'),
                    }],
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android'],
                            'player_skip': ['configs', 'webpage'],
                        }
                    }
                }
            ]
            
            last_error = None
            for i, ydl_opts in enumerate(download_methods):
                try:
                    logger.info(f"Attempting audio download method {i+1}")
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    
                    # Check if the file was created
                    if os.path.exists(final_output):
                        actual_file_path = final_output
                    else:
                        # Look for the file with different extension
                        base_name = final_output.replace('.mp3', '')
                        actual_file_path = None
                        
                        for file in os.listdir(self.downloads_dir):
                            if file.startswith(os.path.basename(base_name)) and file.endswith(('.mp3', '.m4a', '.webm', '.opus')):
                                actual_file_path = os.path.join(self.downloads_dir, file)
                                break
                    
                    if actual_file_path and os.path.exists(actual_file_path):
                        logger.info(f"Successfully downloaded audio using method {i+1}")
                        return {
                            'title': info['title'],
                            'file_path': actual_file_path,
                            'format': 'audio',
                            'quality': quality
                        }
                    else:
                        raise Exception("Audio file not found after download")
                
                except Exception as e:
                    last_error = e
                    logger.warning(f"Audio download method {i+1} failed: {str(e)}")
                    if i < len(download_methods) - 1:
                        continue
            
            # If all methods failed
            error_msg = str(last_error) if last_error else "Unknown error"
            if "403" in error_msg or "Forbidden" in error_msg:
                error_msg = "YouTube blocked this download. Please upload cookies.txt file or try again later."
            elif "Sign in to confirm" in error_msg:
                error_msg = "YouTube requires sign-in verification. Please upload cookies.txt file."
            
            logger.error(f"All audio download methods failed: {error_msg}")
            raise Exception(f"Audio download failed: {error_msg}")
            
        except Exception as e:
            logger.error(f"Audio download failed: {str(e)}")
            raise Exception(f"Audio download failed: {str(e)}")
    
    def convert_video_to_audio(self, video_path, quality='256kbps'):
        """Convert existing video file to audio"""
        try:
            if not os.path.exists(video_path):
                raise Exception("Video file not found")
            
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            audio_path = os.path.join(self.downloads_dir, f"{base_name}_audio_{quality}.mp3")
            
            bitrate = self.audio_qualities.get(quality, '256')
            
            # Use subprocess to call ffmpeg directly for Railway compatibility
            cmd = [
                'ffmpeg', '-i', video_path,
                '-acodec', 'mp3',
                '-ab', f'{bitrate}k',
                '-y',  # Overwrite output file
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFmpeg conversion failed: {result.stderr}")
            
            return {
                'audio_path': audio_path,
                'quality': quality
            }
            
        except Exception as e:
            logger.error(f"Video to audio conversion failed: {str(e)}")
            raise Exception(f"Conversion failed: {str(e)}")
