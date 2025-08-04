from .config import SCAN_PROGRESS, PROGRESS_LOCK

def update_progress(scanned=None, total=None, status=None):
    """Update scan progress."""
    with PROGRESS_LOCK:
        if scanned is not None:
            SCAN_PROGRESS["scanned"] = scanned
        if total is not None:
            SCAN_PROGRESS["total"] = total
        if status is not None:
            SCAN_PROGRESS["status"] = status

def get_scan_progress():
    with PROGRESS_LOCK:
        return SCAN_PROGRESS.copy()

def display_progress():
    """Print a formatted view of scan progress."""
    scanned = SCAN_PROGRESS.get("scanned", 0)
    total = SCAN_PROGRESS.get("total", 0)
    remaining = total - scanned
    percentage = SCAN_PROGRESS.get("percentage", 0)
    status = SCAN_PROGRESS.get("status", "unknown")
    start_time = SCAN_PROGRESS.get("start_time", "N/A")
    end_time = SCAN_PROGRESS.get("end_time", "N/A")
    project_name = SCAN_PROGRESS.get("project_name", "Unknown Project")

    print("\n" + "=" * 50)
    print("SCAN PROGRESS")
    print("=" * 50)
    print(f"Project          : {project_name}")
    print(f"Status           : {status.upper()}")
    print(f"Start Time       : {start_time}")
    if status == "completed":
        print(f"End Time         : {end_time}")
    print(f"Total Files      : {total}")
    print(f"Files Scanned    : {scanned}")
    print(f"Files Remaining  : {remaining}")
    print(f"Completed        : {percentage}%")
    print("=" * 50 + "\n")
