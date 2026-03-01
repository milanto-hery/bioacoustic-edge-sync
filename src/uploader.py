from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
import time

def authenticate_drive() -> GoogleDrive:
    """Authenticates with Google Drive using PyDrive."""
    gauth = GoogleAuth()
    gauth.CommandLineAuth()
    return GoogleDrive(gauth)

def get_or_create_folder(drive: GoogleDrive, folder_name: str, parent_folder_id: str = None) -> str:
    """Gets the folder ID if it exists, otherwise creates it."""
    query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_folder_id:
        query += f" and '{parent_folder_id}' in parents"
    
    # Retry block in case of network unavailability during folder fetch
    for _ in range(3):
        try:
            folder_list = drive.ListFile({'q': query}).GetList()
            if folder_list:
                return folder_list[0]['id']
                
            folder_metadata = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
            if parent_folder_id:
                folder_metadata['parents'] = [{'id': parent_folder_id}]
                
            folder_drive = drive.CreateFile(folder_metadata)
            folder_drive.Upload()
            return folder_drive['id']
        except Exception as e:
            print(f"[DriveError] Error verifying drive folder: {e}. Retrying...")
            time.sleep(5)
    raise Exception("Could not verify or create Google Drive target folder.")

def upload_file_with_retry(drive: GoogleDrive, file_path: str, folder_id: str, max_retries: int = 5):
    """Uploads a file with auto-reconnect on network failure logic."""
    basename = os.path.basename(file_path)
    
    # Check if exists
    try:
        file_list = drive.ListFile({'q': f"'{folder_id}' in parents and title='{basename}'"}).GetList()
        if file_list:
            print(f"[Uploader] '{basename}' already exists in Drive. Skipping.")
            return True
    except Exception as e:
        print(f"[Uploader] Error checking file existence: {e}")

    # Retry loop for Auto-reconnect / Cloud Redundancy
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[Uploader] Uploading '{basename}' (Attempt {attempt}/{max_retries})...")
            file_drive = drive.CreateFile({'title': basename, 'parents': [{'id': folder_id}]})
            file_drive.SetContentFile(file_path)
            file_drive.Upload()
            print(f"[Uploader] '{basename}' uploaded successfully.")
            return True
        except Exception as e:
            print(f"[UploaderError] Upload failed: {e}")
            if attempt < max_retries:
                sleep_time = 5 * attempt
                print(f"[Uploader] Network issue detected. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print(f"[UploaderError] Max retries reached. File '{basename}' remains buffered locally.")
                return False
