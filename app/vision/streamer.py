import cv2
import time
import json
import os

def get_rtsp_url():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        json_path = os.path.join(root_dir, 'data', 'config.json')
        
        if not os.path.exists(json_path):
            print(f"ERROR: File not found at: {json_path}")
            return None

        with open(json_path, 'r') as f:
            config_data = json.load(f)
            return config_data.get("RTSP_URL_BAK")
            
    except Exception as e:
        print(f"ERROR fetching URL: {e}")
        return None

def generate_frames():
    RTSP_URL = get_rtsp_url()
    
    if not RTSP_URL:
        print("ERROR: Could not load RTSP_URL.")
        return

    camera = cv2.VideoCapture(RTSP_URL)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not camera.isOpened():
        print(f"ERROR: Could not open camera at: {RTSP_URL}")

    TARGET_FPS = 5             
    FRAME_INTERVAL = 1.0 / TARGET_FPS 
    last_frame_time = 0

    while True:
        success, frame = camera.read()

        if not success:
            print("Connection lost, reconnecting...")
            camera.release()
            time.sleep(2)
            
            RTSP_URL = get_rtsp_url()
            camera = cv2.VideoCapture(RTSP_URL)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            continue

        current_time = time.time()
        if (current_time - last_frame_time) < FRAME_INTERVAL:
            continue
        
        last_frame_time = current_time

        height, width = frame.shape[:2]
        if width > 640:
            new_width = 640
            new_height = int(height * (new_width / width))
            frame = cv2.resize(frame, (new_width, new_height))

        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 40])
        
        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
