import os
import time
import yaml
from datetime import datetime
from recorder import find_usb_device, record_chunk
from uploader import authenticate_drive, get_or_create_folder, upload_file_with_retry

def load_config(config_path="../config/settings.yaml"):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def main():
    print("=== Bioacoustic Edge Sync ===")
    
    # Load Configuration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "..", "config", "settings.yaml")
    config = load_config(config_path)
    
    rec_config = config['recording']
    drive_config = config['drive']
    
    chunk_duration = rec_config['chunk_duration_seconds']
    sample_rate = rec_config['sample_rate']
    channels = rec_config['channels']
    local_storage = os.path.join(script_dir, "..", rec_config['local_storage_dir'])
    
    # Ensure local directory exists
    os.makedirs(local_storage, exist_ok=True)
    
    # Auth Drive
    print("[Main] Authenticating Google Drive...")
    try:
        drive = authenticate_drive()
    except Exception as e:
        print(f"[MainError] Failed to authenticate drive: {e}")
        return

    # Create Drive Folder
    folder_name = drive_config['target_folder_name']
    parent_id = drive_config['parent_folder_id']
    print(f"[Main] Setting up Drive folder '{folder_name}'...")
    target_drive_id = get_or_create_folder(drive, folder_name, parent_id)
    
    # Continuous Recording Loop
    print("[Main] Entering continuous recording pipeline...")
    while True:
        usb_mic = find_usb_device()
        if not usb_mic:
            print("[Main] Waiting for USB microphone...")
            time.sleep(10)
            continue
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"CH01_{timestamp}.wav"
        filepath = os.path.join(local_storage, filename)
        
        # 1. Record 10-minute chunk
        success = record_chunk(filepath, duration=chunk_duration, sample_rate=sample_rate, channels=channels, device=usb_mic)
        
        if success:
            # 2. Upload to Drive (auto-reconnect redundancy handled in uploader)
            upload_success = upload_file_with_retry(drive, filepath, target_drive_id)
            if upload_success:
                print(f"[Main] {filename} fully synced. Ready for next chunk.")
            else:
                print(f"[MainWarning] {filename} sync failed. Preserved locally for later sync.")
        else:
            print("[MainError] Recording chunk failed. Retrying in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    main()
