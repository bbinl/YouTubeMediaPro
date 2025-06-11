#!/usr/bin/env python3
"""
Test script to verify the YouTube Downloader works correctly before Railway deployment
"""

import requests
import time
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_health_endpoint(base_url):
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Health check passed: {data['status']}")
            return True
        else:
            logger.error(f"Health check failed: Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return False

def test_video_info(base_url):
    """Test video info extraction"""
    try:
        # Use a reliable YouTube video
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        response = requests.get(f"{base_url}/api/get/info", params={"url": test_url}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('info'):
                logger.info(f"Video info test passed: {data['info']['title'][:50]}...")
                return True
            else:
                logger.error(f"Video info test failed: {data}")
                return False
        else:
            logger.error(f"Video info test failed: Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Video info test error: {str(e)}")
        return False

def test_download_status(base_url):
    """Test download status endpoint with a sample download"""
    try:
        # Start a download
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        download_data = {
            "url": test_url,
            "format": "video",
            "quality": "3gp"  # Small format for testing
        }
        
        response = requests.post(f"{base_url}/api/download", json=download_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            download_id = data.get('download_id')
            
            if download_id:
                logger.info(f"Download started with ID: {download_id}")
                
                # Check status a few times
                for i in range(3):
                    time.sleep(2)
                    status_response = requests.get(f"{base_url}/api/status/{download_id}", timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        logger.info(f"Download status: {status_data.get('status', 'unknown')}")
                        if status_data.get('status') in ['completed', 'failed']:
                            break
                
                return True
            else:
                logger.error(f"Download test failed: No download ID returned")
                return False
        else:
            logger.error(f"Download test failed: Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Download test error: {str(e)}")
        return False

def main():
    """Run all tests"""
    base_url = "http://localhost:5000"
    
    logger.info("Starting YouTube Downloader deployment tests...")
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Video Info", test_video_info),
        ("Download Status", test_download_status),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"Running {test_name} test...")
        try:
            if test_func(base_url):
                logger.info(f"✓ {test_name} test PASSED")
                passed += 1
            else:
                logger.error(f"✗ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} test ERROR: {str(e)}")
    
    logger.info(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All tests passed! Ready for Railway deployment.")
        sys.exit(0)
    else:
        logger.error("Some tests failed. Please fix issues before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()