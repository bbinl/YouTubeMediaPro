from app import db
from datetime import datetime

class DownloadHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    format_type = db.Column(db.String(20), nullable=False)  # 'video' or 'audio'
    quality = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'failed'
    file_path = db.Column(db.String(500), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'format_type': self.format_type,
            'quality': self.quality,
            'status': self.status,
            'file_path': self.file_path,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'download_url': f'/api/download/{self.id}/file' if self.status == 'completed' else None
        }
