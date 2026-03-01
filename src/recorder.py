import numpy as np
import pyaudio
import sounddevice as sd
import soundfile as sf
import time

def find_usb_device():
    """Finds and returns the name of the first available USB microphone."""
    input_devices = sd.query_devices()
    usb_devices = [device for device in input_devices if 'USB' in device['name']]
    if usb_devices:
        return usb_devices[0]['name']
    print("No USB mic device found!")
    return None

def record_chunk(filename: str, duration: int, sample_rate: int, channels: int = 1, device: str = None):
    """
    Records audio for a specified duration using the provided device.
    Saves the data directly as a WAV file.
    """
    if device is None:
        print("Please insert a USB device.")
        return False

    print(f"[Recorder] Recording {duration}s from {device} to {filename}...")
    p = pyaudio.PyAudio()

    input_device_index = None
    for i in range(p.get_device_count()):
        if p.get_device_info_by_index(i)["name"] == device:
            input_device_index = i
            break

    if input_device_index is None:
        print(f"[Recorder] Device '{device}' is not found.")
        p.terminate()
        return False

    try:
        stream = p.open(format=pyaudio.paFloat32,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        input_device_index=input_device_index,
                        frames_per_buffer=4096)
        
        frames = []
        total_frames = int(sample_rate * duration)
        read_frames = 0
        
        while read_frames < total_frames:
            chunk_size = min(4096, total_frames - read_frames)
            data = stream.read(chunk_size, exception_on_overflow=False)
            frames.append(data)
            read_frames += chunk_size

        stream.stop_stream()
        stream.close()
        p.terminate()

        audio_data = np.frombuffer(b''.join(frames), dtype=np.float32)
        
        # Save as WAV directly
        sf.write(filename, audio_data, sample_rate)
        print(f"[Recorder] Chunk saved to {filename}.")
        return True

    except Exception as e:
        print(f"[RecorderError] Failed to record chunk: {e}")
        p.terminate()
        return False
