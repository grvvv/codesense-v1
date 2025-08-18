from datetime import datetime, timezone
from bson import ObjectId
from common.db import MongoDBClient

SCAN_COLLECTION = MongoDBClient.get_database()["scans"]

def update_progress(scan_id, scanned=None, total=None, status=None, end_time=None, findings=None, error=None):
    """Update scan progress in MongoDB scan document."""
    update_fields = {"last_updated": datetime.now(timezone.utc)}

    if scanned is not None:
        update_fields["files_scanned"] = scanned
    if total is not None:
        update_fields["total_files"] = total
    if status is not None:
        update_fields["status"] = status
    if end_time is not None:
        update_fields["end_time"] = end_time
    if findings is not None:
        update_fields["findings"] = findings
    if error is not None:
        update_fields["error"] = error

    SCAN_COLLECTION.update_one(
        {"_id": ObjectId(scan_id)},
        {"$set": update_fields}
    )

def get_scan_progress(scan_id):
    """Fetch scan progress from MongoDB."""
    scan = SCAN_COLLECTION.find_one({"_id": ObjectId(scan_id)}, {
        "scan_name": 1,
        "status": 1,
        "total_files": 1,
        "files_scanned": 1,
        "total_findings": 1,
        "created_at": 1,
        "last_updated": 1,
        "end_time": 1,
        "error": 1
    })

    if not scan:
        return None

    progress = {
        "project_name": scan.get("scan_name", "Unknown"),
        "status": scan.get("status", "unknown"),
        "start_time": scan.get("created_at"),
        "end_time": scan.get("end_time"),
        "total": scan.get("total_files", 0),
        "scanned": scan.get("files_scanned", 0),
        "findings": scan.get("total_findings", 0),
        "error": scan.get("error"),
    }

    progress["percentage"] = (
        int((progress["scanned"] / progress["total"]) * 100)
        if progress["total"] else 0
    )
    return progress

def display_progress(scan_id):
    """Pretty-print scan progress from MongoDB."""
    progress = get_scan_progress(scan_id)
    if not progress:
        print("No progress found for given scan ID.")
        return

    print("\n" + "=" * 50)
    print("SCAN PROGRESS")
    print("=" * 50)
    print(f"Project          : {progress['project_name']}")
    print(f"Status           : {progress['status'].upper()}")
    print(f"Start Time       : {progress['start_time']}")
    if progress["status"] == "completed":
        print(f"End Time         : {progress['end_time']}")
    print(f"Total Files      : {progress['total']}")
    print(f"Files Scanned    : {progress['scanned']}")
    print(f"Files Remaining  : {progress['total'] - progress['scanned']}")
    print(f"Completed        : {progress['percentage']}%")
    if progress.get("error"):
        print(f"⚠️ Error         : {progress['error']}")
    print("=" * 50 + "\n")
