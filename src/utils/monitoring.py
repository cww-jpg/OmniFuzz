import time
import psutil
import logging
from typing import Dict, Any, List
import threading
from datetime import datetime

class ResourceMonitor:
    """Resource monitor"""

    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.monitor_thread = None
        self.metrics_history = []

    def start_monitoring(self):
        """Start monitoring"""
        if self.monitoring:
            self.logger.warning("Monitoring is already running")
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("Resource monitoring started")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        self.logger.info("Resource monitoring stopped")

    def _monitor_loop(self):
        """Monitoring loop"""
        while self.monitoring:
            metrics = self._collect_metrics()
            self.metrics_history.append(metrics)
            time.sleep(self.interval)

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=None),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
            'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
            'process_count': len(psutil.pids())
        }

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return self._collect_metrics()

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        if not self.metrics_history:
            return {}

        cpu_values = [m['cpu_percent'] for m in self.metrics_history]
        memory_values = [m['memory_percent'] for m in self.metrics_history]

        return {
            'duration_seconds': len(self.metrics_history) * self.interval,
            'cpu_avg': sum(cpu_values) / len(cpu_values),
            'cpu_max': max(cpu_values),
            'memory_avg': sum(memory_values) / len(memory_values),
            'memory_max': max(memory_values),
            'total_metrics': len(self.metrics_history)
        }

    def generate_report(self) -> str:
        """Generate monitoring report"""
        summary = self.get_metrics_summary()

        report = [
            "Resource Monitoring Report",
            "=" * 40,
            f"Duration: {summary.get('duration_seconds', 0):.1f} seconds",
            f"CPU usage - avg: {summary.get('cpu_avg', 0):.1f}%, max: {summary.get('cpu_max', 0):.1f}%",
            f"Memory usage - avg: {summary.get('memory_avg', 0):.1f}%, max: {summary.get('memory_max', 0):.1f}%",
            f"Total metrics collected: {summary.get('total_metrics', 0)}"
        ]

        return "\n".join(report)

class PerformanceProfiler:
    """Performance profiler"""

    def __init__(self):
        self.measurements = {}

    def start_timer(self, name: str):
        """Start timing"""
        self.measurements[name] = {
            'start': time.time(),
            'end': None,
            'duration': None
        }

    def stop_timer(self, name: str):
        """Stop timing"""
        if name in self.measurements:
            self.measurements[name]['end'] = time.time()
            self.measurements[name]['duration'] = (
                self.measurements[name]['end'] - self.measurements[name]['start']
            )

    def get_duration(self, name: str) -> float:
        """Get duration"""
        if name in self.measurements and self.measurements[name]['duration'] is not None:
            return self.measurements[name]['duration']
        return 0.0

    def print_profile_report(self):
        """Print performance profile report"""
        print("Performance Profile Report")
        print("=" * 50)

        for name, measurement in self.measurements.items():
            if measurement['duration'] is not None:
                print(f"{name}: {measurement['duration']:.4f} s")