#!/usr/bin/env python3
"""
Backend Health Monitor for Piano LED Visualizer
Monitors the backend service and restarts if unhealthy
"""

import requests
import subprocess
import time
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/piano-led-monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

HEALTH_URL = "http://localhost:5001/health"
SERVICE_NAME = "piano-led-visualizer.service"
CHECK_INTERVAL = 30  # seconds
MAX_FAILURES = 3
TIMEOUT = 10  # seconds

class BackendMonitor:
    def __init__(self):
        self.failure_count = 0
        self.last_restart = None
        
    def check_health(self):
        """Check if the backend is responding to health checks"""
        try:
            response = requests.get(HEALTH_URL, timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    return True
            return False
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def restart_service(self):
        """Restart the backend service"""
        try:
            logger.info(f"Restarting {SERVICE_NAME}...")
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', SERVICE_NAME],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully restarted {SERVICE_NAME}")
                self.last_restart = datetime.now()
                self.failure_count = 0
                return True
            else:
                logger.error(f"Failed to restart service: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restarting service: {e}")
            return False
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Starting backend health monitor...")
        
        while True:
            try:
                if self.check_health():
                    if self.failure_count > 0:
                        logger.info("Backend is healthy again")
                        self.failure_count = 0
                else:
                    self.failure_count += 1
                    logger.warning(f"Health check failed ({self.failure_count}/{MAX_FAILURES})")
                    
                    if self.failure_count >= MAX_FAILURES:
                        # Avoid restarting too frequently
                        if (self.last_restart is None or 
                            (datetime.now() - self.last_restart).seconds > 300):
                            self.restart_service()
                        else:
                            logger.warning("Skipping restart - too recent")
                            self.failure_count = MAX_FAILURES - 1  # Reset but keep elevated
                
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitor: {e}")
                time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    monitor = BackendMonitor()
    monitor.run()