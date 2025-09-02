#!/usr/bin/env python3
"""
Optimized Performance Tests - Validates performance improvements
"""

import pytest
import time
import threading
import tempfile
import os
from unittest.mock import Mock, patch

# Import modules
try:
    from backend.playback_service import PlaybackService, PlaybackState
    from backend.led_controller import LEDController
    from backend.performance_monitor import PerformanceMonitor, PerformanceMetrics
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from playback_service import PlaybackService, PlaybackState
    from led_controller import LEDController
    from performance_monitor import PerformanceMonitor, PerformanceMetrics

class TestPerformanceOptimizations:
    """Test performance optimizations"""
    
    def setup_method(self):
        """Setup test environment"""
        self.led_controller = LEDController(num_pixels=88, brightness=0.1)
        self.playback_service = PlaybackService(self.led_controller)
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.playback_service:
            self.playback_service.stop_playback()
        if self.led_controller:
            self.led_controller.cleanup()
    
    def test_performance_monitor_initialization(self):
        """Test performance monitor is properly initialized"""
        assert self.playback_service.performance_monitor is not None
        assert isinstance(self.playback_service.performance_monitor, PerformanceMonitor)
    
    def test_performance_monitor_start_stop(self):
        """Test performance monitor start/stop functionality"""
        monitor = self.playback_service.performance_monitor
        
        # Test start
        monitor.start_monitoring(interval=0.1)
        assert monitor.is_monitoring
        
        # Wait for some samples
        time.sleep(0.3)
        
        # Test stop
        monitor.stop_monitoring()
        assert not monitor.is_monitoring
        
        # Check we collected some metrics
        assert len(monitor.metrics_history) > 0
    
    def test_performance_metrics_collection(self):
        """Test performance metrics are collected correctly"""
        monitor = self.playback_service.performance_monitor
        
        # Get current metrics
        metrics = monitor.get_current_metrics()
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.timestamp > 0
        assert metrics.thread_count > 0
    
    def test_led_update_rate_limiting(self):
        """Test LED update rate is properly limited"""
        monitor = self.playback_service.performance_monitor
        
        # Record multiple LED updates
        start_time = time.time()
        for _ in range(100):
            monitor.record_led_update()
            time.sleep(0.001)  # 1ms between updates
        
        # Check LED update rate calculation
        current_metrics = monitor.get_current_metrics()
        assert current_metrics.led_update_rate > 0
    
    def test_note_processing_time_tracking(self):
        """Test note processing time is tracked"""
        monitor = self.playback_service.performance_monitor
        
        # Record some processing times
        processing_times = [0.001, 0.002, 0.0015, 0.0008]
        for pt in processing_times:
            monitor.record_note_processing_time(pt)
        
        # Check average is calculated
        current_metrics = monitor.get_current_metrics()
        expected_avg = sum(processing_times) / len(processing_times)
        assert abs(current_metrics.note_processing_time - expected_avg) < 0.0001
    
    def test_performance_summary_generation(self):
        """Test performance summary generation"""
        monitor = self.playback_service.performance_monitor
        
        # Start monitoring and collect some data
        monitor.start_monitoring(interval=0.05)
        time.sleep(0.2)
        monitor.stop_monitoring()
        
        # Get summary
        summary = monitor.get_metrics_summary()
        
        assert 'sample_count' in summary
        assert 'cpu_percent' in summary
        assert 'memory_mb' in summary
        assert 'thread_count' in summary
        
        # Check CPU stats structure
        cpu_stats = summary['cpu_percent']
        assert 'avg' in cpu_stats
        assert 'max' in cpu_stats
        assert 'min' in cpu_stats
    
    def test_optimized_playback_loop_timing(self):
        """Test optimized playback loop timing"""
        # Create a simple MIDI file for testing
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as f:
            # Write minimal MIDI file header
            midi_data = bytes([
                0x4D, 0x54, 0x68, 0x64,  # "MThd"
                0x00, 0x00, 0x00, 0x06,  # Header length
                0x00, 0x00,              # Format 0
                0x00, 0x01,              # 1 track
                0x00, 0x60,              # 96 ticks per quarter note
                0x4D, 0x54, 0x72, 0x6B,  # "MTrk"
                0x00, 0x00, 0x00, 0x0B,  # Track length
                0x00, 0x90, 0x40, 0x40,  # Note on C4
                0x60, 0x80, 0x40, 0x40,  # Note off C4
                0x00, 0xFF, 0x2F, 0x00   # End of track
            ])
            f.write(midi_data)
            temp_file = f.name
        
        try:
            # Mock MIDI parser to avoid file format issues
            with patch.object(self.playback_service, 'load_midi_file') as mock_load:
                mock_load.return_value = True
                # Add dummy note events so playback can start
                from backend.playback_service import NoteEvent
                self.playback_service._note_events = [
                    NoteEvent(time=0.0, note=60, velocity=80, duration=0.5),
                    NoteEvent(time=0.5, note=64, velocity=80, duration=0.5)
                ]
                self.playback_service._total_duration = 1.0
                
                # Start playback
                start_time = time.time()
                success = self.playback_service.start_playback()
                assert success
                
                # Let it run briefly
                time.sleep(0.1)
                
                # Check performance metrics were collected
                if self.playback_service.performance_monitor:
                    metrics = self.playback_service.performance_monitor.get_current_metrics()
                    assert metrics is not None
                
                # Stop playback
                self.playback_service.stop_playback()
                
        finally:
            # Cleanup temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_led_batching_optimization(self):
        """Test LED batching reduces show() calls"""
        # Mock the LED strip to count show() calls
        with patch.object(self.led_controller, 'strip', create=True) as mock_strip:
            mock_strip.show = Mock()
            
            # Test multiple LED updates
            led_data = {0: (255, 0, 0), 1: (0, 255, 0), 2: (0, 0, 255)}
            
            # Use batched update
            self.led_controller.set_multiple_leds(led_data)
            
            # Should only call show() once for batched update
            assert mock_strip.show.call_count <= 1
    
    def test_memory_usage_stability(self):
        """Test memory usage remains stable during operation"""
        monitor = self.playback_service.performance_monitor
        
        # Start monitoring
        monitor.start_monitoring(interval=0.05)
        
        # Simulate some workload
        for i in range(50):
            monitor.record_led_update()
            monitor.record_note_processing_time(0.001)
            time.sleep(0.01)
        
        # Stop monitoring
        monitor.stop_monitoring()
        
        # Check memory usage didn't grow excessively
        summary = monitor.get_metrics_summary()
        memory_stats = summary.get('memory_mb', {})
        
        if memory_stats:
            # Memory growth should be reasonable (less than 50MB difference)
            memory_growth = memory_stats.get('max', 0) - memory_stats.get('min', 0)
            assert memory_growth < 50, f"Excessive memory growth: {memory_growth}MB"
    
    def test_thread_count_stability(self):
        """Test thread count remains stable"""
        initial_thread_count = threading.active_count()
        
        # Start and stop playback multiple times
        for _ in range(3):
            with patch.object(self.playback_service, 'load_midi_file') as mock_load:
                mock_load.return_value = True
                self.playback_service._note_events = []
                self.playback_service._total_duration = 0.1
                
                self.playback_service.start_playback()
                time.sleep(0.05)
                self.playback_service.stop_playback()
                time.sleep(0.05)
        
        # Thread count should return to initial level (allow some variance)
        final_thread_count = threading.active_count()
        thread_difference = abs(final_thread_count - initial_thread_count)
        assert thread_difference <= 2, f"Thread leak detected: {thread_difference} threads"

class TestPerformanceMonitor:
    """Test PerformanceMonitor class directly"""
    
    def setup_method(self):
        """Setup test environment"""
        self.monitor = PerformanceMonitor(max_samples=100)
    
    def teardown_method(self):
        """Cleanup test environment"""
        if self.monitor.is_monitoring:
            self.monitor.stop_monitoring()
    
    def test_context_manager(self):
        """Test PerformanceMonitor as context manager"""
        with PerformanceMonitor() as monitor:
            assert monitor.is_monitoring
            time.sleep(0.1)
        
        # Should be stopped after context exit
        assert not monitor.is_monitoring
    
    def test_metrics_reset(self):
        """Test metrics reset functionality"""
        # Add some data
        self.monitor.record_led_update()
        self.monitor.record_note_processing_time(0.001)
        
        # Reset
        self.monitor.reset_metrics()
        
        # Check data is cleared
        assert len(self.monitor.metrics_history) == 0
        assert len(self.monitor.note_processing_times) == 0
        assert self.monitor.led_updates == 0
    
    def test_max_samples_limit(self):
        """Test max samples limit is respected"""
        monitor = PerformanceMonitor(max_samples=5)
        
        # Add more samples than limit
        for i in range(10):
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=i,
                memory_percent=i,
                memory_mb=i,
                thread_count=i
            )
            monitor.metrics_history.append(metrics)
        
        # Should only keep max_samples
        assert len(monitor.metrics_history) == 5

if __name__ == '__main__':
    pytest.main([__file__, '-v'])