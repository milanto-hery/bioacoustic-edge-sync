import os
import time
import yaml
from datetime import datetime
from recorder import find_usb_device, record_chunk
from uploader import authenticate_drive, save_files_to_drive

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
    local_storage = os.path.abspath(os.path.join(script_dir, "..", rec_config['local_storage_dir']))
    
    # Ensure local directory exists
    os.makedirs(local_storage, exist_ok=True)
    
    # Auth Drive
    print("[Main] Authenticating Google Drive...")
    try:
        drive = authenticate_drive()
    except Exception as e:
        print(f"[MainError] Failed to authenticate drive: {e}")
        return

    folder_name = drive_config['target_folder_name']
    parent_id = drive_config['parent_folder_id']
    print(f"[Main] Target Drive Folder: '{folder_name}'")
    
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
        
        # 1. Record chunk
        print(f"[Main] Starting recording for {chunk_duration} seconds...")
        success = record_chunk(filepath, duration=chunk_duration, sample_rate=sample_rate, channels=channels, device=usb_mic)
        
        if success:
            # 2. Upload to Drive (sync entire local folder)
            print("[Main] Syncing local buffer to Google Drive...")
            try:
                save_files_to_drive(drive, local_storage, folder_name, parent_id)
                print("[Main] Sync completed. Ready for next chunk.")
            except Exception as e:
                print(f"[MainWarning] Sync failed: {e}. Preserved locally for later sync.")
        else:
            print("[MainError] Recording chunk failed. Retrying in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    main()
