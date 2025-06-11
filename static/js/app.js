class YouTubeDownloader {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.currentDownloadId = null;
    }

    initializeElements() {
        this.form = document.getElementById('downloadForm');
        this.urlInput = document.getElementById('urlInput');
        this.infoBtn = document.getElementById('infoBtn');
        this.formatRadios = document.querySelectorAll('input[name="format"]');
        this.qualitySelect = document.getElementById('qualitySelect');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.videoInfoCard = document.getElementById('videoInfoCard');
        this.videoInfoContent = document.getElementById('videoInfoContent');
        this.progressCard = document.getElementById('progressCard');
        this.progressBar = document.querySelector('.progress-bar');
        this.progressText = document.getElementById('progressText');
        this.resultCard = document.getElementById('resultCard');
        this.resultContent = document.getElementById('resultContent');
        this.cookiesFile = document.getElementById('cookiesFile');
        this.cookiesStatus = document.getElementById('cookiesStatus');
    }

    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleDownload(e));
        this.infoBtn.addEventListener('click', () => this.getVideoInfo());
        
        this.formatRadios.forEach(radio => {
            radio.addEventListener('change', () => this.handleFormatChange());
        });

        this.urlInput.addEventListener('input', () => {
            this.hideCards();
        });

        // Cookies upload functionality
        if (this.cookiesFile) {
            this.cookiesFile.addEventListener('change', (e) => this.handleCookiesUpload(e));
        }

        // Load cookies status on page load
        this.loadCookiesStatus();
    }

    handleFormatChange() {
        const selectedFormat = document.querySelector('input[name="format"]:checked').value;
        
        // Clear existing options
        this.qualitySelect.innerHTML = '';
        
        if (selectedFormat === 'video') {
            // Video quality options
            const videoQualities = [
                { value: '3gp', text: '3GP (Mobile)' },
                { value: '360p', text: '360p' },
                { value: '480p', text: '480p (SD)' },
                { value: '720p', text: '720p (Recommended)' },
                { value: '1080p', text: '1080p (Full HD)' }
            ];
            
            videoQualities.forEach(quality => {
                const option = document.createElement('option');
                option.value = quality.value;
                option.textContent = quality.text;
                if (quality.value === '720p') option.selected = true;
                this.qualitySelect.appendChild(option);
            });
        } else {
            // Audio quality options
            const audioQualities = [
                { value: '128kbps', text: '128 kbps' },
                { value: '192kbps', text: '192 kbps' },
                { value: '256kbps', text: '256 kbps (Recommended)' },
                { value: '320kbps', text: '320 kbps (High Quality)' }
            ];
            
            audioQualities.forEach(quality => {
                const option = document.createElement('option');
                option.value = quality.value;
                option.textContent = quality.text;
                if (quality.value === '256kbps') option.selected = true;
                this.qualitySelect.appendChild(option);
            });
        }
    }

    async getVideoInfo() {
        const url = this.urlInput.value.trim();
        
        if (!url) {
            this.showError('Please enter a YouTube URL');
            return;
        }

        if (!this.isValidYouTubeUrl(url)) {
            this.showError('Please enter a valid YouTube URL');
            return;
        }

        this.infoBtn.disabled = true;
        this.infoBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const response = await fetch('/api/info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (data.success) {
                this.showVideoInfo(data.info);
            } else {
                this.showError(data.error || 'Failed to get video information');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.infoBtn.disabled = false;
            this.infoBtn.innerHTML = '<i class="fas fa-info-circle"></i>';
        }
    }

    showVideoInfo(info) {
        const duration = this.formatDuration(info.duration);
        const uploadDate = this.formatDate(info.upload_date);

        this.videoInfoContent.innerHTML = `
            <div class="row">
                <div class="col-md-8">
                    <h6 class="fw-bold">${this.escapeHtml(info.title)}</h6>
                    <p class="text-muted mb-2">
                        <i class="fas fa-user me-1"></i> ${this.escapeHtml(info.uploader || 'Unknown')}
                    </p>
                    <p class="text-muted mb-2">
                        <i class="fas fa-clock me-1"></i> ${duration}
                        <span class="ms-3">
                            <i class="fas fa-eye me-1"></i> ${this.formatNumber(info.view_count || 0)} views
                        </span>
                    </p>
                    <p class="text-muted mb-2">
                        <i class="fas fa-calendar me-1"></i> ${uploadDate}
                    </p>
                    ${info.description ? `<p class="small text-muted">${this.escapeHtml(info.description)}</p>` : ''}
                </div>
                <div class="col-md-4">
                    ${info.thumbnail ? `<img src="${info.thumbnail}" class="img-fluid rounded" alt="Video thumbnail">` : ''}
                </div>
            </div>
        `;

        this.videoInfoCard.style.display = 'block';
    }

    async handleDownload(e) {
        e.preventDefault();
        
        const url = this.urlInput.value.trim();
        const format = document.querySelector('input[name="format"]:checked').value;
        const quality = this.qualitySelect.value;

        if (!url) {
            this.showError('Please enter a YouTube URL');
            return;
        }

        if (!this.isValidYouTubeUrl(url)) {
            this.showError('Please enter a valid YouTube URL');
            return;
        }

        this.hideCards();
        this.showProgress('Preparing download...');
        this.setFormDisabled(true);

        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    format: format,
                    quality: quality
                })
            });

            const data = await response.json();

            if (data.success) {
                this.currentDownloadId = data.download_id;
                this.updateProgress(50, 'Downloading...');
                
                // Poll for completion
                this.pollDownloadStatus(data.download_id);
            } else {
                this.showError(data.error || 'Download failed');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.setFormDisabled(false);
        }
    }

    async pollDownloadStatus(downloadId) {
        const maxAttempts = 60; // 5 minutes max
        let attempts = 0;

        const poll = async () => {
            if (attempts >= maxAttempts) {
                this.showError('Download timeout - please try again');
                return;
            }

            try {
                const response = await fetch(`/api/download/${downloadId}/status`);
                const data = await response.json();

                if (data.status === 'completed') {
                    this.updateProgress(100, 'Download completed!');
                    setTimeout(() => {
                        this.showSuccess(data);
                    }, 1000);
                } else if (data.status === 'failed') {
                    this.showError(data.error_message || 'Download failed');
                } else {
                    // Still in progress
                    this.updateProgress(75, 'Processing...');
                    attempts++;
                    setTimeout(poll, 5000); // Poll every 5 seconds
                }
            } catch (error) {
                this.showError('Error checking download status: ' + error.message);
            }
        };

        poll();
    }

    showProgress(text) {
        this.progressText.textContent = text;
        this.progressCard.style.display = 'block';
    }

    updateProgress(percentage, text) {
        this.progressBar.style.width = percentage + '%';
        this.progressText.textContent = text;
    }

    hideProgress() {
        this.progressCard.style.display = 'none';
    }

    showSuccess(data) {
        this.hideProgress();
        
        const formatIcon = data.format_type === 'video' ? 'fa-video' : 'fa-music';
        const formatClass = data.format_type === 'video' ? 'primary' : 'success';

        this.resultContent.innerHTML = `
            <div class="text-center">
                <div class="mb-3">
                    <i class="fas fa-check-circle fa-3x text-success"></i>
                </div>
                <h5 class="text-success mb-3">Download Completed!</h5>
                <div class="mb-3">
                    <h6 class="fw-bold">${this.escapeHtml(data.title || 'Unknown Title')}</h6>
                    <span class="badge bg-${formatClass}">
                        <i class="fas ${formatIcon} me-1"></i>
                        ${data.format_type || 'video'} - ${data.quality || 'unknown'}
                    </span>
                </div>
                <div class="d-grid gap-2 col-6 mx-auto">
                    <a href="${data.download_url}" class="btn btn-success btn-lg">
                        <i class="fas fa-download me-2"></i>
                        Download File
                    </a>
                    <button type="button" class="btn btn-outline-secondary" onclick="location.reload()">
                        <i class="fas fa-redo me-2"></i>
                        Download Another
                    </button>
                </div>
            </div>
        `;

        this.resultCard.style.display = 'block';
    }

    showError(message) {
        this.hideProgress();
        
        this.resultContent.innerHTML = `
            <div class="text-center">
                <div class="mb-3">
                    <i class="fas fa-exclamation-circle fa-3x text-danger"></i>
                </div>
                <h5 class="text-danger mb-3">Download Failed</h5>
                <p class="text-muted mb-3">${this.escapeHtml(message)}</p>
                <button type="button" class="btn btn-outline-primary" onclick="location.reload()">
                    <i class="fas fa-redo me-2"></i>
                    Try Again
                </button>
            </div>
        `;

        this.resultCard.style.display = 'block';
        this.setFormDisabled(false);
    }

    hideCards() {
        this.videoInfoCard.style.display = 'none';
        this.progressCard.style.display = 'none';
        this.resultCard.style.display = 'none';
    }

    setFormDisabled(disabled) {
        this.downloadBtn.disabled = disabled;
        this.urlInput.disabled = disabled;
        this.infoBtn.disabled = disabled;
        this.qualitySelect.disabled = disabled;
        
        this.formatRadios.forEach(radio => {
            radio.disabled = disabled;
        });

        if (disabled) {
            this.downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
        } else {
            this.downloadBtn.innerHTML = '<i class="fas fa-download me-2"></i>Download';
        }
    }

    isValidYouTubeUrl(url) {
        const patterns = [
            /^https?:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/shorts\/)/i,
            /^https?:\/\/m\.youtube\.com\/watch\?v=/i
        ];
        
        return patterns.some(pattern => pattern.test(url));
    }

    formatDuration(seconds) {
        if (!seconds) return 'Unknown';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }

    formatDate(dateString) {
        if (!dateString) return 'Unknown';
        
        // dateString format: YYYYMMDD
        const year = dateString.substring(0, 4);
        const month = dateString.substring(4, 6);
        const day = dateString.substring(6, 8);
        
        const date = new Date(`${year}-${month}-${day}`);
        return date.toLocaleDateString();
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async handleCookiesUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (!file.name.endsWith('.txt')) {
            this.showCookiesStatus('Please select a .txt file', 'danger');
            return;
        }

        const formData = new FormData();
        formData.append('cookies', file);

        try {
            this.showCookiesStatus('Uploading cookies...', 'info');
            
            const response = await fetch('/api/upload-cookies', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.showCookiesStatus('Cookies uploaded successfully! YouTube downloads should work better now.', 'success');
                this.loadCookiesStatus();
            } else {
                this.showCookiesStatus(data.error || 'Upload failed', 'danger');
            }
        } catch (error) {
            this.showCookiesStatus('Upload failed: ' + error.message, 'danger');
        }

        event.target.value = '';
    }

    async loadCookiesStatus() {
        try {
            const response = await fetch('/api/cookies-info');
            const data = await response.json();

            if (data.cookies_file_exists && data.cookies_file_size > 0) {
                this.showCookiesStatus(`Cookies file active (${this.formatFileSize(data.cookies_file_size)})`, 'success');
            } else {
                this.showCookiesStatus('No cookies file uploaded', 'secondary');
            }
        } catch (error) {
            console.error('Failed to load cookies status:', error);
        }
    }

    showCookiesStatus(message, type) {
        if (!this.cookiesStatus) return;
        
        const alertClass = type === 'success' ? 'alert-success' : 
                          type === 'danger' ? 'alert-danger' : 
                          type === 'info' ? 'alert-info' : 'alert-secondary';
        
        this.cookiesStatus.innerHTML = `
            <div class="alert ${alertClass} alert-dismissible fade show mb-0" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize the downloader when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new YouTubeDownloader();
});
