from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

def authenticate_drive() -> GoogleDrive:
    """Authenticates with Google Drive using PyDrive."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.abspath(os.path.join(script_dir, "..", "config"))
    settings_file = os.path.join(config_dir, "settings.yaml")
    
    # Initialize GoogleAuth with the settings file
    gauth = GoogleAuth(settings_file=settings_file)
    
    # Temporarily change directory to config to correctly resolve relative paths (client_secrets.json)
    current_dir = os.getcwd()
    os.chdir(config_dir)
    try:
        gauth.CommandLineAuth() 
    finally:
        os.chdir(current_dir)
        
    return GoogleDrive(gauth)

def upload_file(drive, file_path, folder_id):
    # Check if the file already exists in the folder
    file_list = drive.ListFile({'q': "'%s' in parents and title='%s'" % (folder_id, os.path.basename(file_path))}).GetList()
    if file_list:
        print(f"File '{os.path.basename(file_path)}' already exists in the Google Drive folder. Skipping upload.")
        return

    # Upload the file if it doesn't exist
    file_drive = drive.CreateFile({'title': os.path.basename(file_path), 'parents': [{'id': folder_id}]})
    file_drive.SetContentFile(file_path)  # Set the content of the file
    file_drive.Upload()
    print(f"{file_path} uploaded successfully to Google Drive.")

def create_folder_drive(drive, folder_name, parent_folder_id=None):
    # Check if the folder already exists, if not create a new one
    folder_list = drive.ListFile({'q': "title='%s' and mimeType='application/vnd.google-apps.folder'" % folder_name}).GetList()
    if folder_list:
        return folder_list[0]['id']  # Return the existing folder ID
        
    folder_drive = drive.CreateFile({'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'})
    if parent_folder_id:
        folder_drive['parents'] = [{'id': parent_folder_id}]
    folder_drive.Upload()
    return folder_drive['id']

def save_files_to_drive(drive, local_folder, drive_folder_name, parent_folder_id):
    # Create a folder inside the folder drive to store the data
    folder_id = create_folder_drive(drive, drive_folder_name, parent_folder_id)

    # Iterate through files inside the local folder
    for filename in os.listdir(local_folder):
        file_path = os.path.join(local_folder, filename)
        
        # Check if the file exists before uploading
        if os.path.isfile(file_path) and filename.endswith(".wav"):
            upload_file(drive, file_path, folder_id)
        else:
            if not os.path.isfile(file_path):
                print(f"Error: File {file_path} not found!")
