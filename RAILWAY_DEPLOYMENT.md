# Railway Deployment Guide for YouTube Downloader

## Fixed Issues ✅

- **HTTP 403 Errors**: Enhanced anti-detection with multiple fallback methods
- **Cookie Support**: Improved cookie handling system for YouTube authentication
- **Health Checks**: Added `/health` endpoint for Railway deployment monitoring
- **Error Handling**: Better error messages guide users to solutions

## Quick Deploy to Railway

1. **Fork/Clone Repository**: Get the code to your GitHub account
2. **Connect to Railway**: 
   - Go to railway.app and sign in
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
3. **Add PostgreSQL**: Click "Add Service" → "Database" → "PostgreSQL"
4. **Environment Variables**: Set in Railway dashboard:
   - `SESSION_SECRET`: Generate a random 32-character string
   - Database variables are auto-configured by Railway

## Fixing YouTube 403 Errors

The HTTP 403 Forbidden errors occur because YouTube detects automated requests. Here's how to fix it:

### Method 1: Upload Cookies (Recommended)

1. **Get YouTube Cookies**:
   - Install browser extension like "Get cookies.txt LOCALLY"
   - Go to YouTube.com while logged in
   - Export cookies as `cookies.txt`

2. **Upload Cookies**:
   - Use the "Upload cookies.txt" button in the app
   - Or manually place `cookies.txt` in the project root

### Method 2: Use VPN/Proxy (Alternative)

If cookies don't work, the app will automatically try:
- Android client fallback
- Different user agents
- Retry mechanisms

## Railway-Specific Features

- **Auto-scaling**: Railway handles traffic spikes
- **Health checks**: App monitors itself
- **File cleanup**: Old downloads are automatically removed
- **Database**: PostgreSQL for download history

## Troubleshooting

### Common Issues:

1. **Build Failures**: Check nixpacks.toml configuration
2. **Memory Issues**: Railway provides sufficient resources
3. **Timeout Errors**: App configured with 120s timeout
4. **Cookie Expiry**: Re-upload cookies if downloads start failing

### Logs:
- View logs in Railway dashboard
- Look for "Successfully extracted/downloaded" messages
- HTTP 403 errors indicate need for fresh cookies

## API Usage on Railway

Once deployed, use your Railway URL:
```
https://your-app.railway.app/api/get/download?url=VIDEO_URL&format=video&quality=720p
```

## Performance Optimizations

- Concurrent download limit: 2 workers
- File cleanup: Every 15 minutes
- Database connection pooling enabled
- Optimized for Railway's infrastructure