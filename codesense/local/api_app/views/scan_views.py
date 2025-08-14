import os, zipfile, uuid
import tempfile
from django.http import JsonResponse
from django.conf import settings
from local.api_app.models.scan_models import ScanModel
from local.api_app.serializers.scan_serializers import ScanStartSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework import status
from scanner.rag.scanner import scan_folder
import logging
import shutil
import threading
from local.auth_app.permissions.decorators import require_permission

scan_thread = None
scan_thread_lock = threading.Lock()

MEDIA_ROOT = os.path.join(settings.BASE_DIR, "media", "scans")
os.makedirs(MEDIA_ROOT, exist_ok=True)

@method_decorator(csrf_exempt, name='dispatch')
class ScanCreateView(APIView):
    @require_permission("create_scan")
    def post(self, request):
        serializer = ScanStartSerializer(data=request.data)
        user = request.user
        triggered_by = user.get("id", "68863cf8ee93d4964a00d585")

        if serializer.is_valid():
            scan_name = serializer.validated_data['scan_name']
            project_id = serializer.validated_data['project_id']
            zip_file = serializer.validated_data['zip_file']

            # Create scan doc
            scan_data = {
                "scan_name": scan_name,
                "project_id": project_id,
                "status": "queued",
                "triggered_by": triggered_by if triggered_by else None
            }
            scan = ScanModel.create(scan_data)
            scan_id = scan["id"]

            # Create temporary directory for both ZIP file and extraction
            temp_dir = tempfile.mkdtemp()
            temp_zip_path = os.path.join(temp_dir, zip_file.name)
            extracted_folder_path = os.path.join(temp_dir, 'extracted')
    
            try:
                # Save uploaded ZIP file
                with open(temp_zip_path, 'wb+') as f:
                    for chunk in zip_file.chunks():
                        f.write(chunk)
                logging.info(f"Uploaded zipped folder saved to {temp_zip_path}")

                os.makedirs(extracted_folder_path, exist_ok=True)
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extracted_folder_path)
                logging.info(f"ZIP file extracted to {extracted_folder_path}")
                
                # List contents for debugging
                extracted_contents = []
                for root, dirs, files in os.walk(extracted_folder_path):
                    for file in files:
                        extracted_contents.append(os.path.join(root, file))
                logging.info(f"Extracted {len(extracted_contents)} files: {extracted_contents[:10]}...")  # Show first 10 files

            except zipfile.BadZipFile:
                logging.error("Uploaded file is not a valid ZIP file")
                shutil.rmtree(temp_dir)
                return JsonResponse({"error": "Invalid zip file"}, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                logging.error(f"Failed to process uploaded file: {e}")
                shutil.rmtree(temp_dir)
                return JsonResponse({"detail": "Failed to process uploaded file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Start scan in background thread
            def run_scan():
                try:
                    # Get kb_path - assuming it's in the scanner directory
                    kb_path = os.path.join(os.getcwd(), 'scanner')
                    logging.info(f"Starting scan with scan_name={scan_name}, kb_path={kb_path}")
                    
                    # Call scan_folder with extracted folder path
                    findings = scan_folder(folder_path=extracted_folder_path, scan_id=scan_id, triggered_by=triggered_by, kb_path=kb_path, scan_name=scan_name)
                    logging.info(f"Scan completed successfully. Found {len(findings) if findings else 0} vulnerabilities.")
                    
                except Exception as e:
                    logging.error(f"Error during scan: {e}")
                    import traceback
                    logging.error(traceback.format_exc())
                finally:
                    # Cleanup temp files and directory
                    try:
                        shutil.rmtree(temp_dir)
                        logging.info(f"Cleaned up temporary directory: {temp_dir}")
                    except Exception as e:
                        logging.error(f"Error cleaning up temporary files: {e}")

            global scan_thread
            with scan_thread_lock:
                if scan_thread and scan_thread.is_alive():
                    return JsonResponse({"detail": "Scan already in progress."}, status=status.HTTP_409_CONFLICT)
                scan_thread = threading.Thread(target=run_scan, daemon=True)
                scan_thread.start()

            return JsonResponse({"detail": "Scan started successfully.", "scan": scan}, status=status.HTTP_202_ACCEPTED)
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
   
class ScanDetailView(APIView):
    @require_permission("view_scans")
    def get(self, request, scan_id):
        scan = ScanModel.find_by_id(scan_id=scan_id)
        if not scan:
            return JsonResponse({"error": "Scan not found"}, status=status.HTTP_404_NOT_FOUND)

        return JsonResponse(scan, status=status.HTTP_200_OK)
    
    @require_permission("delete_scan")
    def delete(self, request, scan_id):
        res = ScanModel.delete_scan(scan_id=scan_id)
        if not res:
            return JsonResponse({"error": "Scan not found"}, status=status.HTTP_404_NOT_FOUND)
        return JsonResponse({"detail": "Scan deleted permenantly"}, status=status.HTTP_204_NO_CONTENT)
    
       
class ScanListView(APIView):
    @require_permission("view_scans")
    def get(self, request, project_id):
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))

        scans = ScanModel.find_by_project(project_id=project_id, page=page, limit=limit)
        if not scans:
            return JsonResponse({"error": "Scan not found"}, status=status.HTTP_404_NOT_FOUND)

        return JsonResponse(scans, status=status.HTTP_200_OK)
 