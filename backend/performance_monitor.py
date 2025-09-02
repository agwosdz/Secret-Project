#!/usr/bin/env python3
"""
Performance Monitor - Tracks system performance during playback
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from collections import deque

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    thread_count: int
    led_update_rate: float = 0.0
    note_processing_time: float = 0.0

class PerformanceMonitor:
    """Monitors system performance during playback"""
    
    def __init__(self, max_samples: int = 1000):
        """
        Initialize performance monitor.
        
        Args:
            max_samples: Maximum number of samples to keep in memory
        """
        self.logger = logging.getLogger(__name__)
        self.max_samples = max_samples
        self.metrics_history: deque = deque(maxlen=max_samples)
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Performance counters
        self.led_updates = 0
        self.note_processing_times: deque = deque(maxlen=100)
        self.last_led_update_time = 0
        
        if not PSUTIL_AVAILABLE:
            self.logger.warning("psutil not available - limited performance monitoring")
    
    def start_monitoring(self, interval: float = 1.0):
        """Start performance monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info(f"Performance monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self.stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        
        self.logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self, interval: float):
        """Main monitoring loop"""
        try:
            while not self.stop_event.is_set():
                metrics = self._collect_metrics()
                if metrics:
                    self.metrics_history.append(metrics)
                
                time.sleep(interval)
        
        except Exception as e:
            self.logger.error(f"Error in monitoring loop: {e}")
    
    def _collect_metrics(self) -> Optional[PerformanceMetrics]:
        """Collect current performance metrics"""
        try:
            timestamp = time.time()
            
            if PSUTIL_AVAILABLE:
                process = psutil.Process()
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()
                memory_mb = memory_info.rss / 1024 / 1024
                thread_count = process.num_threads()
            else:
                cpu_percent = 0.0
                memory_percent = 0.0
                memory_mb = 0.0
                thread_count = threading.active_count()
            
            # Calculate LED update rate
            led_update_rate = 0.0
            if self.last_led_update_time > 0:
                time_diff = timestamp - self.last_led_update_time
                if time_diff > 0:
                    led_update_rate = self.led_updates / time_diff
            
            # Calculate average note processing time
            avg_note_processing_time = 0.0
            if self.note_processing_times:
                avg_note_processing_time = sum(self.note_processing_times) / len(self.note_processing_times)
            
            return PerformanceMetrics(
                timestamp=timestamp,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_mb=memory_mb,
                thread_count=thread_count,
                led_update_rate=led_update_rate,
                note_processing_time=avg_note_processing_time
            )
        
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return None
    
    def record_led_update(self):
        """Record an LED update event"""
        current_time = time.time()
        if self.last_led_update_time == 0:
            self.last_led_update_time = current_time
        
        self.led_updates += 1
    
    def record_note_processing_time(self, processing_time: float):
        """Record note processing time"""
        self.note_processing_times.append(processing_time)
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get current performance metrics"""
        return self._collect_metrics()
    
    def get_metrics_summary(self) -> Dict:
        """Get summary of performance metrics"""
        if not self.metrics_history:
            return {}
        
        cpu_values = [m.cpu_percent for m in self.metrics_history]
        memory_values = [m.memory_mb for m in self.metrics_history]
        led_rates = [m.led_update_rate for m in self.metrics_history if m.led_update_rate > 0]
        
        return {
            'sample_count': len(self.metrics_history),
            'cpu_percent': {
                'avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'max': max(cpu_values) if cpu_values else 0,
                'min': min(cpu_values) if cpu_values else 0
            },
            'memory_mb': {
                'avg': sum(memory_values) / len(memory_values) if memory_values else 0,
                'max': max(memory_values) if memory_values else 0,
                'min': min(memory_values) if memory_values else 0
            },
            'led_update_rate': {
                'avg': sum(led_rates) / len(led_rates) if led_rates else 0,
                'max': max(led_rates) if led_rates else 0,
                'min': min(led_rates) if led_rates else 0
            },
            'thread_count': self.metrics_history[-1].thread_count if self.metrics_history else 0
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics_history.clear()
        self.led_updates = 0
        self.note_processing_times.clear()
        self.last_led_update_time = 0
        self.logger.info("Performance metrics reset")
    
    def __enter__(self):
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_monitoring()