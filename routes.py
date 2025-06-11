import os
import logging
from flask import render_template, request, jsonify, send_file, flash, redirect, url_for
from app import app, db
from models import DownloadHistory
from downloader import YouTubeDownloader
from utils import validate_youtube_url, sanitize_filename
from datetime import datetime

logger = logging.getLogger(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint for Railway deployment"""
    return jsonify({
        'status': 'healthy',
        'service': 'youtube-downloader',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/')
def index():
    """Main page with download interface"""
    recent_downloads = DownloadHistory.query.order_by(DownloadHistory.created_at.desc()).limit(10).all()
    return render_template('index.html', recent_downloads=recent_downloads)

@app.route('/api/download', methods=['POST'])
def api_download():
    """API endpoint for downloading videos/audio"""
    import threading
    import time
    
    try:
        data = request.get_json()
        url = data.get('url')
        format_type = data.get('format', 'video')  # 'video' or 'audio'
        quality = data.get('quality', '720p' if format_type == 'video' else '256kbps')
        
        # Validate inputs
        if not url:
            return jsonify({'error': 'URL is required'}), 400
            
        if not validate_youtube_url(url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400
            
        if format_type not in ['video', 'audio']:
            return jsonify({'error': 'Invalid format type'}), 400
            
        # Create download history record
        download_record = DownloadHistory(
            url=url,
            format_type=format_type,
            quality=quality,
            status='pending'
        )
        db.session.add(download_record)
        db.session.commit()
        
        # Return download ID immediately for async processing
        download_id = download_record.id
        
        # Start download in background thread
        def background_download():
            from app import app
            with app.app_context():
                try:
                    downloader = YouTubeDownloader()
                    
                    # Download the content
                    if format_type == 'video':
                        result = downloader.download_video(url, quality)
                    else:
                        result = downloader.download_audio(url, quality)
                    
                    # Update download record
                    record = DownloadHistory.query.get(download_id)
                    if record:
                        record.title = result.get('title', 'Unknown')
                        record.file_path = result.get('file_path')
                        record.status = 'completed'
                        record.completed_at = datetime.utcnow()
                        db.session.commit()
                    
                except Exception as e:
                    # Update download record with error
                    record = DownloadHistory.query.get(download_id)
                    if record:
                        record.status = 'failed'
                        record.error_message = str(e)
                        record.completed_at = datetime.utcnow()
                        db.session.commit()
                    logger.error(f"Background download failed for URL {url}: {str(e)}")
        
        # Start background thread
        thread = threading.Thread(target=background_download)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'download_id': download_id,
            'status': 'pending',
            'status_url': f'/api/download/{download_id}/status',
            'message': 'Download started. Use status_url to check progress.'
        })
            
    except Exception as e:
        logger.error(f"API download error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/download/<int:download_id>/file')
def download_file(download_id):
    """Serve downloaded file"""
    try:
        download_record = DownloadHistory.query.get_or_404(download_id)
        
        if download_record.status != 'completed' or not download_record.file_path:
            return jsonify({'error': 'File not available'}), 404
            
        file_path = download_record.file_path
        
        # If the exact path doesn't exist, try to find the file in downloads directory
        if not os.path.exists(file_path):
            # Try to find files with similar names in downloads directory
            downloads_dir = 'downloads'
            if os.path.exists(downloads_dir):
                files = os.listdir(downloads_dir)
                # Look for files with the same title (excluding extension and quality)
                title_part = download_record.title.replace('|', '_').replace('/', '_').replace('\\', '_')
                for file in files:
                    if title_part in file or file.replace('_', ' ') in download_record.title:
                        file_path = os.path.join(downloads_dir, file)
                        # Update the database with correct path
                        download_record.file_path = file_path
                        db.session.commit()
                        break
                        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
        
    except Exception as e:
        logger.error(f"File download error: {str(e)}")
        return jsonify({'error': 'File download failed'}), 500

@app.route('/api/download/<int:download_id>/status')
def download_status(download_id):
    """Get download status"""
    try:
        download_record = DownloadHistory.query.get_or_404(download_id)
        return jsonify(download_record.to_dict())
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({'error': 'Status check failed'}), 500

@app.route('/api/info', methods=['POST'])
def get_video_info():
    """Get video information without downloading"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
            
        if not validate_youtube_url(url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400
            
        downloader = YouTubeDownloader()
        info = downloader.get_video_info(url)
        
        return jsonify({
            'success': True,
            'info': info
        })
        
    except Exception as e:
        logger.error(f"Video info error: {str(e)}")
        return jsonify({'error': f'Failed to get video info: {str(e)}'}), 500

@app.route('/api/history')
def download_history():
    """Get download history"""
    try:
        downloads = DownloadHistory.query.order_by(DownloadHistory.created_at.desc()).limit(50).all()
        return jsonify({
            'downloads': [download.to_dict() for download in downloads]
        })
    except Exception as e:
        logger.error(f"History error: {str(e)}")
        return jsonify({'error': 'Failed to get history'}), 500

@app.route('/api/upload-cookies', methods=['POST'])
def upload_cookies():
    """Upload cookies.txt file to bypass YouTube bot detection"""
    try:
        if 'cookies' not in request.files:
            return jsonify({'error': 'No cookies file provided'}), 400
        
        file = request.files['cookies']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename.endswith('.txt'):
            # Save the uploaded cookies file
            file.save('cookies.txt')
            return jsonify({
                'success': True,
                'message': 'Cookies file uploaded successfully. YouTube downloads should now work better.'
            })
        else:
            return jsonify({'error': 'Please upload a .txt file'}), 400
            
    except Exception as e:
        logger.error(f"Cookies upload error: {str(e)}")
        return jsonify({'error': 'Failed to upload cookies file'}), 500

@app.route('/api/cookies-info')
def cookies_info():
    """Get information about cookies setup"""
    try:
        cookies_exists = os.path.exists('cookies.txt')
        cookies_size = 0
        if cookies_exists:
            cookies_size = os.path.getsize('cookies.txt')
        
        return jsonify({
            'cookies_file_exists': cookies_exists,
            'cookies_file_size': cookies_size,
            'instructions': {
                'step1': 'Install browser extension "Get cookies.txt LOCALLY" or similar',
                'step2': 'Visit youtube.com and log in to your account',
                'step3': 'Use the extension to export cookies as cookies.txt',
                'step4': 'Upload the file using the upload endpoint',
                'note': 'This helps bypass YouTube bot detection for restricted videos'
            }
        })
    except Exception as e:
        logger.error(f"Cookies info error: {str(e)}")
        return jsonify({'error': 'Failed to get cookies info'}), 500

@app.route('/api/get/info')
def get_video_info_get():
    """Get video information using GET method"""
    try:
        url = request.args.get('url')
        
        if not url:
            return jsonify({'error': 'URL parameter is required'}), 400
            
        if not validate_youtube_url(url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400
            
        downloader = YouTubeDownloader()
        info = downloader.get_video_info(url)
        
        return jsonify({
            'success': True,
            'info': info
        })
        
    except Exception as e:
        logger.error(f"Video info error: {str(e)}")
        return jsonify({'error': f'Failed to get video info: {str(e)}'}), 500

@app.route('/api/get/download')
def api_download_get():
    """Download video/audio using GET method"""
    try:
        url = request.args.get('url')
        format_type = request.args.get('format', 'video')  # 'video' or 'audio'
        quality = request.args.get('quality')
        
        # Set default quality based on format
        if not quality:
            quality = '720p' if format_type == 'video' else '256kbps'
        
        # Validate inputs
        if not url:
            return jsonify({'error': 'URL parameter is required'}), 400
            
        if not validate_youtube_url(url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400
            
        if format_type not in ['video', 'audio']:
            return jsonify({'error': 'Invalid format type. Use "video" or "audio"'}), 400
            
        # Valid quality options
        video_qualities = ['3gp', '360p', '480p', '720p', '1080p']
        audio_qualities = ['128kbps', '192kbps', '256kbps', '320kbps']
        
        if format_type == 'video' and quality not in video_qualities:
            return jsonify({'error': f'Invalid video quality. Use: {", ".join(video_qualities)}'}), 400
        elif format_type == 'audio' and quality not in audio_qualities:
            return jsonify({'error': f'Invalid audio quality. Use: {", ".join(audio_qualities)}'}), 400
            
        # Create download history record
        download_record = DownloadHistory(
            url=url,
            format_type=format_type,
            quality=quality,
            status='pending'
        )
        db.session.add(download_record)
        db.session.commit()
        
        # Initialize downloader
        downloader = YouTubeDownloader()
        
        try:
            # Download the content
            if format_type == 'video':
                result = downloader.download_video(url, quality)
            else:
                result = downloader.download_audio(url, quality)
            
            # Update download record
            download_record.title = result.get('title', 'Unknown')
            download_record.file_path = result.get('file_path')
            download_record.status = 'completed'
            download_record.completed_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'download_id': download_record.id,
                'title': result.get('title'),
                'file_path': result.get('file_path'),
                'download_url': f'/api/download/{download_record.id}/file',
                'direct_download': f'/api/get/file?id={download_record.id}'
            })
            
        except Exception as e:
            # Update download record with error
            download_record.status = 'failed'
            download_record.error_message = str(e)
            download_record.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.error(f"Download failed for URL {url}: {str(e)}")
            return jsonify({'error': f'Download failed: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"API download error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/get/file')
def download_file_get():
    """Download file using GET method with ID parameter"""
    try:
        download_id = request.args.get('id')
        
        if not download_id:
            return jsonify({'error': 'ID parameter is required'}), 400
            
        try:
            download_id = int(download_id)
        except ValueError:
            return jsonify({'error': 'Invalid ID parameter'}), 400
            
        download_record = DownloadHistory.query.get_or_404(download_id)
        
        if download_record.status != 'completed' or not download_record.file_path:
            return jsonify({'error': 'File not available'}), 404
            
        file_path = download_record.file_path
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
        
    except Exception as e:
        logger.error(f"File download error: {str(e)}")
        return jsonify({'error': 'File download failed'}), 500

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """Clean up old downloaded files"""
    try:
        downloads_dir = 'downloads'
        if os.path.exists(downloads_dir):
            for filename in os.listdir(downloads_dir):
                if filename != '.gitkeep':
                    file_path = os.path.join(downloads_dir, filename)
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to remove {file_path}: {str(e)}")
        
        # Update database records
        DownloadHistory.query.update({DownloadHistory.file_path: None})
        db.session.commit()
        
        flash('Files cleaned up successfully', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        flash('Cleanup failed', 'error')
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
