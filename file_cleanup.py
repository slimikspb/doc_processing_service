import os
import glob
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Configure temp file directory and max age
TEMP_DIR = '/tmp'
TEMP_FILE_MAX_AGE_HOURS = 24  # Files older than this will be deleted
MAX_TEMP_DIR_SIZE_MB = 500  # Maximum size of temp directory in MB

def get_temp_file_size_mb():
    """Get the total size of all temporary files in MB"""
    pattern = os.path.join(TEMP_DIR, '*_*.*')  # Match our UUID-prefixed temp files
    total_size = 0
    for file_path in glob.glob(pattern):
        try:
            total_size += os.path.getsize(file_path)
        except (OSError, FileNotFoundError):
            pass  # Skip files that can't be accessed
    return total_size / (1024 * 1024)  # Convert bytes to MB

def cleanup_temp_files():
    """Clean up old temporary files"""
    logger.info('Running temporary file cleanup task')
    
    # Calculate cutoff time for old files
    cutoff_time = datetime.now() - timedelta(hours=TEMP_FILE_MAX_AGE_HOURS)
    cutoff_timestamp = cutoff_time.timestamp()
    
    # Get all temp files created by our application (UUID_filename pattern)
    pattern = os.path.join(TEMP_DIR, '*_*.*')  # Match our UUID-prefixed temp files
    deleted_count = 0
    deleted_size = 0
    
    # First pass: delete old files
    for file_path in glob.glob(pattern):
        try:
            file_stat = os.stat(file_path)
            # Check if file is older than cutoff time
            if file_stat.st_mtime < cutoff_timestamp:
                file_size = file_stat.st_size
                os.remove(file_path)
                deleted_count += 1
                deleted_size += file_size
                logger.debug(f'Deleted old temp file: {file_path}')
        except (OSError, FileNotFoundError):
            pass  # Skip files that can't be accessed
    
    # Second pass: check total size and delete oldest files if over limit
    current_size_mb = get_temp_file_size_mb()
    if current_size_mb > MAX_TEMP_DIR_SIZE_MB:
        logger.warning(f'Temp directory size ({current_size_mb:.2f} MB) exceeds limit ({MAX_TEMP_DIR_SIZE_MB} MB)')
        
        # Get all remaining files with creation time
        files_with_time = []
        for file_path in glob.glob(pattern):
            try:
                mtime = os.path.getmtime(file_path)
                size = os.path.getsize(file_path)
                files_with_time.append((file_path, mtime, size))
            except (OSError, FileNotFoundError):
                pass
        
        # Sort by modification time (oldest first)
        files_with_time.sort(key=lambda x: x[1])
        
        # Delete oldest files until under size limit
        for file_path, _, file_size in files_with_time:
            if current_size_mb <= MAX_TEMP_DIR_SIZE_MB * 0.9:  # Stop at 90% of limit
                break
                
            try:
                os.remove(file_path)
                deleted_count += 1
                deleted_size += file_size
                current_size_mb -= file_size / (1024 * 1024)
                logger.debug(f'Deleted temp file due to size limit: {file_path}')
            except (OSError, FileNotFoundError):
                pass
    
    deleted_size_mb = deleted_size / (1024 * 1024)
    logger.info(f'Cleanup complete: deleted {deleted_count} files ({deleted_size_mb:.2f} MB)')
    return {
        'deleted_count': deleted_count,
        'deleted_size_mb': deleted_size_mb,
        'current_size_mb': get_temp_file_size_mb()
    }
