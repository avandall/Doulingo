"""
Cron Service for Scheduled Background Tasks.
Provides maintenance functions such as cleanup of temporary audio cache files.
"""

import logging
import os
import time
from typing import Any

logger = logging.getLogger("haku_hakus.cron")


def cleanup_audio_cache(
    cache_dir: str | None = None, max_age_hours: float = 24.0
) -> dict[str, Any]:
    """
    Scans and removes temporary audio cache files older than max_age_hours.

    Args:
        cache_dir: Path to audio cache directory. Defaults to AUDIO_CACHE_DIR env or 'data/audio_cache'.
        max_age_hours: Age threshold in hours for deleting audio files (default 24.0 hours).

    Returns:
        Dict containing cache_dir, deleted_count, freed_bytes, and freed_mb.
    """
    if cache_dir is None:
        cache_dir = os.getenv("AUDIO_CACHE_DIR", "data/audio_cache")

    deleted_count = 0
    freed_bytes = 0

    if not os.path.exists(cache_dir) or not os.path.isdir(cache_dir):
        logger.info(
            "Audio cache directory '%s' does not exist or is not a directory. Cleanup skipped.",
            cache_dir,
        )
        return {
            "cache_dir": cache_dir,
            "deleted_count": 0,
            "freed_bytes": 0,
            "freed_mb": 0.0,
        }

    now = time.time()
    cutoff_seconds = max_age_hours * 3600.0

    try:
        entries = os.listdir(cache_dir)
    except Exception as e:
        logger.error("Error reading audio cache directory '%s': %s", cache_dir, e)
        return {
            "cache_dir": cache_dir,
            "deleted_count": 0,
            "freed_bytes": 0,
            "freed_mb": 0.0,
            "error": str(e),
        }

    if not entries:
        logger.info("Audio cache directory '%s' is empty.", cache_dir)
        return {
            "cache_dir": cache_dir,
            "deleted_count": 0,
            "freed_bytes": 0,
            "freed_mb": 0.0,
        }

    for file_name in entries:
        file_path = os.path.join(cache_dir, file_name)
        if not os.path.isfile(file_path):
            continue

        try:
            mtime = os.path.getmtime(file_path)
            file_age = now - mtime
            if file_age > cutoff_seconds:
                size = os.path.getsize(file_path)
                os.remove(file_path)
                deleted_count += 1
                freed_bytes += size
                logger.debug(
                    "Deleted old audio cache file '%s' (age: %.1f hrs, size: %d bytes)",
                    file_name,
                    file_age / 3600.0,
                    size,
                )
        except OSError as exc:
            logger.warning("Failed to inspect/delete file '%s': %s", file_path, exc)

    freed_mb = round(freed_bytes / (1024.0 * 1024.0), 2)
    logger.info(
        "Audio cache cleanup completed for '%s': %d files deleted, %d bytes (%.2f MB) freed.",
        cache_dir,
        deleted_count,
        freed_bytes,
        freed_mb,
    )

    return {
        "cache_dir": cache_dir,
        "deleted_count": deleted_count,
        "freed_bytes": freed_bytes,
        "freed_mb": freed_mb,
    }
