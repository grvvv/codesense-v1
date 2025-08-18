from concurrent.futures import ThreadPoolExecutor, as_completed
from .kb import load_knowledge_base
from .files import get_source_files
from .analysis import scan_single_file
from .database import save_findings_to_db
from .progress import update_progress, display_progress
from .config import (set_kb_path)
from datetime import datetime, timezone
import traceback
import logging
logger = logging.getLogger(__name__)

def scan_folder(folder_path, kb_path, scan_id, triggered_by, scan_name):
    set_kb_path(kb_path)
    _, _ = load_knowledge_base(kb_path)
    source_files = get_source_files(folder_path)
    total_files = len(source_files)
    if not source_files:
        logging.warning(f"No source code files found in {folder_path}")
        update_progress(scan_id=scan_id, total=0, scanned=0, status="completed", end_time=datetime.now(timezone.utc))
        return []

    
    update_progress(scan_id=scan_id, total=total_files, scanned=0, status="in_progress")

    logging.info(f"Starting parallel scan of {total_files} files for project: {scan_name or 'Unknown'}")

    all_findings = []
    failed_files = []
    completed_files = 0


    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(scan_single_file, path, scan_id, triggered_by): path
            for path in source_files
        }

        for index, future in enumerate(as_completed(futures)):
            file_path = futures[future]
            try:
                findings = future.result()
                if findings:
                    save_findings_to_db(findings)
                    all_findings.extend(findings)
            except Exception as e:
                failed_files.append(file_path)
                logging.error(f"Error processing file {file_path}: {e}\n{traceback.format_exc()}")
            finally:
                completed_files += 1
                update_progress(scan_id=scan_id, findings=len(all_findings), scanned=completed_files)
                display_progress(scan_id=scan_id)

    finding_count = len(all_findings)
    update_progress(scan_id, findings=finding_count, status="completed", end_time=datetime.now(timezone.utc))
    logging.info(f"Scan completed! Found {finding_count} total vulnerabilities across {total_files} files")
    if failed_files:
        logging.warning(f"{len(failed_files)} files failed during scan.")

    return all_findings
