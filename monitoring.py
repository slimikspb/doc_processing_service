"""
Comprehensive monitoring and metrics collection for the document processing service
"""
import os
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from flask import jsonify

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    memory_used_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    disk_total_gb: float
    load_average: List[float]
    process_count: int
    timestamp: str

@dataclass
class ServiceMetrics:
    """Service-specific metrics"""
    uptime_seconds: float
    active_requests: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    temp_files_count: int
    temp_files_size_mb: float

class MetricsCollector:
    """Collects and aggregates system and service metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_metrics = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'response_times': [],
            'max_response_times': 1000  # Keep last 1000 response times
        }
        self.temp_dir = '/tmp'
    
    def record_request(self, success: bool, response_time: float):
        """Record request metrics"""
        self.request_metrics['total'] += 1
        
        if success:
            self.request_metrics['successful'] += 1
        else:
            self.request_metrics['failed'] += 1
        
        # Keep rolling window of response times
        response_times = self.request_metrics['response_times']
        response_times.append(response_time)
        
        if len(response_times) > self.request_metrics['max_response_times']:
            response_times.pop(0)
    
    def get_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            memory_used_mb = memory.used / (1024 * 1024)
            
            # Disk metrics for temp directory
            disk_usage = psutil.disk_usage(self.temp_dir)
            disk_usage_percent = (disk_usage.used / disk_usage.total) * 100
            disk_free_gb = disk_usage.free / (1024 * 1024 * 1024)
            disk_total_gb = disk_usage.total / (1024 * 1024 * 1024)
            
            # Load average (Unix systems)
            try:
                load_average = list(os.getloadavg())
            except (OSError, AttributeError):
                load_average = [0.0, 0.0, 0.0]  # Windows fallback
            
            # Process count
            process_count = len(psutil.pids())
            
            return SystemMetrics(
                cpu_percent=round(cpu_percent, 2),
                memory_percent=round(memory_percent, 2),
                memory_available_mb=round(memory_available_mb, 2),
                memory_used_mb=round(memory_used_mb, 2),
                disk_usage_percent=round(disk_usage_percent, 2),
                disk_free_gb=round(disk_free_gb, 2),
                disk_total_gb=round(disk_total_gb, 2),
                load_average=[round(avg, 2) for avg in load_average],
                process_count=process_count,
                timestamp=datetime.utcnow().isoformat()
            )
        
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            # Return default metrics on error
            return SystemMetrics(
                cpu_percent=0.0, memory_percent=0.0, memory_available_mb=0.0,
                memory_used_mb=0.0, disk_usage_percent=0.0, disk_free_gb=0.0,
                disk_total_gb=0.0, load_average=[0.0, 0.0, 0.0],
                process_count=0, timestamp=datetime.utcnow().isoformat()
            )
    
    def get_temp_files_metrics(self) -> Dict[str, Any]:
        """Get temporary files metrics"""
        try:
            import glob
            pattern = os.path.join(self.temp_dir, '*_*.*')
            temp_files = glob.glob(pattern)
            
            total_size = 0
            file_details = []
            
            for file_path in temp_files:
                try:
                    stat = os.stat(file_path)
                    file_size = stat.st_size
                    total_size += file_size
                    
                    file_details.append({
                        'filename': os.path.basename(file_path),
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'age_minutes': round((time.time() - stat.st_mtime) / 60, 1)
                    })
                except OSError:
                    continue
            
            return {
                'count': len(temp_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'files': file_details
            }
        
        except Exception as e:
            logger.error(f"Error collecting temp files metrics: {e}")
            return {'count': 0, 'total_size_mb': 0.0, 'files': []}
    
    def get_service_metrics(self) -> ServiceMetrics:
        """Get service-specific metrics"""
        try:
            from graceful_shutdown import shutdown_manager
            active_requests = shutdown_manager.get_active_requests()
        except:
            active_requests = 0
        
        # Calculate average response time
        response_times = self.request_metrics['response_times']
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        # Get temp files metrics
        temp_metrics = self.get_temp_files_metrics()
        
        return ServiceMetrics(
            uptime_seconds=round(time.time() - self.start_time, 2),
            active_requests=active_requests,
            total_requests=self.request_metrics['total'],
            successful_requests=self.request_metrics['successful'],
            failed_requests=self.request_metrics['failed'],
            average_response_time=round(avg_response_time, 3),
            temp_files_count=temp_metrics['count'],
            temp_files_size_mb=temp_metrics['total_size_mb']
        )
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        system_metrics = self.get_system_metrics()
        service_metrics = self.get_service_metrics()
        
        # Determine health status based on thresholds
        warnings = []
        critical = []
        
        # Check system thresholds
        if system_metrics.cpu_percent > 90:
            critical.append(f"High CPU usage: {system_metrics.cpu_percent}%")
        elif system_metrics.cpu_percent > 70:
            warnings.append(f"Moderate CPU usage: {system_metrics.cpu_percent}%")
        
        if system_metrics.memory_percent > 90:
            critical.append(f"High memory usage: {system_metrics.memory_percent}%")
        elif system_metrics.memory_percent > 80:
            warnings.append(f"Moderate memory usage: {system_metrics.memory_percent}%")
        
        if system_metrics.disk_usage_percent > 90:
            critical.append(f"High disk usage: {system_metrics.disk_usage_percent}%")
        elif system_metrics.disk_usage_percent > 80:
            warnings.append(f"Moderate disk usage: {system_metrics.disk_usage_percent}%")
        
        # Check temp files
        if service_metrics.temp_files_size_mb > 500:
            warnings.append(f"Large temp files: {service_metrics.temp_files_size_mb}MB")
        
        # Overall health status
        if critical:
            health_status = "critical"
        elif warnings:
            health_status = "warning"
        else:
            health_status = "healthy"
        
        return {
            "status": health_status,
            "warnings": warnings,
            "critical": critical,
            "timestamp": datetime.utcnow().isoformat()
        }

# Global metrics collector
metrics_collector = MetricsCollector()

def create_monitoring_endpoints(app):
    """Add monitoring endpoints to Flask app"""
    
    @app.route('/metrics', methods=['GET'])
    def metrics():
        """Comprehensive metrics endpoint"""
        try:
            system_metrics = metrics_collector.get_system_metrics()
            service_metrics = metrics_collector.get_service_metrics()
            
            # Get Redis health
            try:
                from redis_manager import redis_manager
                redis_health = redis_manager.get_health_status()
            except:
                redis_health = {"healthy": False, "error": "Redis manager not available"}
            
            # Get circuit breaker stats
            try:
                from circuit_breaker import textract_circuit_breaker
                circuit_breaker_stats = textract_circuit_breaker.get_stats()
            except:
                circuit_breaker_stats = {"error": "Circuit breaker not available"}
            
            return jsonify({
                "timestamp": datetime.utcnow().isoformat(),
                "system": asdict(system_metrics),
                "service": asdict(service_metrics),
                "redis": redis_health,
                "circuit_breaker": circuit_breaker_stats,
                "temp_files": metrics_collector.get_temp_files_metrics()
            })
        
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/health/detailed', methods=['GET'])
    def detailed_health():
        """Detailed health check endpoint"""
        try:
            health_summary = metrics_collector.get_health_summary()
            
            # Check individual components
            components = {}
            
            # Redis health
            try:
                from health_checks import check_redis
                redis_healthy, redis_data = check_redis()
                components['redis'] = {"healthy": redis_healthy, "data": redis_data}
            except Exception as e:
                components['redis'] = {"healthy": False, "error": str(e)}
            
            # Celery worker health
            try:
                from health_checks import check_celery_worker
                celery_healthy, celery_data = check_celery_worker()
                components['celery_worker'] = {"healthy": celery_healthy, "data": celery_data}
            except Exception as e:
                components['celery_worker'] = {"healthy": False, "error": str(e)}
            
            # Disk space health
            try:
                from health_checks import check_disk_space
                disk_healthy, disk_data = check_disk_space()
                components['disk_space'] = {"healthy": disk_healthy, "data": disk_data}
            except Exception as e:
                components['disk_space'] = {"healthy": False, "error": str(e)}
            
            return jsonify({
                **health_summary,
                "components": components
            })
        
        except Exception as e:
            logger.error(f"Error in detailed health check: {e}")
            return jsonify({"error": str(e), "status": "error"}), 500
    
    @app.route('/status', methods=['GET'])
    def service_status():
        """Simple service status endpoint"""
        try:
            service_metrics = metrics_collector.get_service_metrics()
            health_summary = metrics_collector.get_health_summary()
            
            return jsonify({
                "service": "document-processing-service",
                "status": health_summary["status"],
                "uptime_seconds": service_metrics.uptime_seconds,
                "active_requests": service_metrics.active_requests,
                "total_requests": service_metrics.total_requests,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return jsonify({"error": str(e)}), 500
    
    return app