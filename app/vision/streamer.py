import cv2
import threading
import time
import os
import numpy as np # Nodig voor de berekening van het midden (mediaan)
from datetime import datetime
import app.vision.ocr as ocr_logic
from app.services.weight_logic import stabilizer

# ================= CONFIGURATION =================

# --- Performance Settings ---
FRAME_SKIP_INTERVAL = 4       # Process 1 out of X frames
BUFFER_SIZE = 1               # Low latency buffer

# --- Auto-Zoom Settings ---
AUTO_ZOOM_ENABLED = True      
AUTO_ZOOM_TARGETS = ['monitor']  #['lcd-screen', 'monitor']

# Stability: Collects multiple samples to find the perfect static position
AUTO_ZOOM_SAMPLES = 20        # Number of frames to analyze before locking
AUTO_ZOOM_PADDING = 15        # Extra pixels around the box

# --- Snapshot Settings ---
ENABLE_SNAPSHOTS = False     
SNAPSHOT_INTERVAL = 20        

# =================================================

global_state = {
    "latest_weight_data": {"gewicht": 0},
    "current_frame": None,
    "lock": threading.Lock()
}
latest_weight_data = global_state["latest_weight_data"]

zoom_state = {
    "locked": False,
    "coords": None,
    "candidates": [], # List to store the 20 samples
    "attempts": 0
}

def get_video_source(config, type_key):
    if config.get('VIDEO_SOURCE_TYPE') == 'file':
        return config.get('VIDEO_SOURCE_FILE')
    return config.get('RTSP_URL_OCR') if type_key == 'OCR' else config.get('RTSP_URL_BAK')

def ocr_background_worker(app_config):
    print(f"--- OCR Service Started | Interval: {FRAME_SKIP_INTERVAL} | Sampling: {AUTO_ZOOM_SAMPLES} frames ---")
    
    snapshot_dir = os.path.join(os.getcwd(), 'data', 'snapshots')
    os.makedirs(snapshot_dir, exist_ok=True)
    last_snapshot_time = 0

    if ocr_logic.reader is None:
        ocr_logic.init_model(app_config)
    
    src = get_video_source(app_config, 'OCR')
    cap = cv2.VideoCapture(src)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, BUFFER_SIZE)

    frame_count = 0

    while True:
        success, full_frame = cap.read()
        
        if not success:
            if app_config.get('VIDEO_SOURCE_TYPE') != 'file':
                time.sleep(2)
                cap.open(src)
            else:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame_count += 1
        
        # Scan faster during search phase, slower when locked
        current_interval = 2 if (AUTO_ZOOM_ENABLED and not zoom_state["locked"]) else FRAME_SKIP_INTERVAL
        
        if frame_count % current_interval != 0:
            continue

        if ocr_logic.reader is not None:
            processing_frame = full_frame
            
            # --- Auto-Zoom Logic ---
            if AUTO_ZOOM_ENABLED:
                
                # Phase 1: Collecting Samples (The Stabilization Phase)
                if not zoom_state["locked"]:
                    try:
                        # 1. Find the screen box
                        box = ocr_logic.reader.find_screen_box(full_frame, AUTO_ZOOM_TARGETS)
                        
                        if box:
                            # 2. Add to candidates list
                            zoom_state["candidates"].append(box)
                            print(f"Sampling position... {len(zoom_state['candidates'])}/{AUTO_ZOOM_SAMPLES}")
                            
                            # 3. Check if we have enough samples
                            if len(zoom_state["candidates"]) >= AUTO_ZOOM_SAMPLES:
                                print("Calculating optimal stable crop...")
                                
                                # 4. Calculate the MEDIAN (This removes jitter/shaking)
                                median_box = np.median(zoom_state["candidates"], axis=0).astype(int)
                                
                                h, w, _ = full_frame.shape
                                
                                # 5. Apply Padding (No manual offsets anymore)
                                x1 = max(0, median_box[0] - AUTO_ZOOM_PADDING)
                                y1 = max(0, median_box[1] - AUTO_ZOOM_PADDING)
                                x2 = min(w, median_box[2] + AUTO_ZOOM_PADDING)
                                y2 = min(h, median_box[3] + AUTO_ZOOM_PADDING)
                                
                                # 6. Final Validation
                                if (x2 - x1) > 50 and (y2 - y1) > 50:
                                    zoom_state["coords"] = (x1, y1, x2, y2)
                                    zoom_state["locked"] = True
                                    print(f"✅ STABLE LOCK ACQUIRED at: {zoom_state['coords']}")
                                else:
                                    # Reset if invalid
                                    zoom_state["candidates"] = []
                                    
                    except AttributeError:
                        print("⚠️ Error: Function 'find_screen_box' missing in ocr.py")

                # Phase 2: Apply Crop
                elif zoom_state["locked"] and zoom_state["coords"]:
                    x1, y1, x2, y2 = zoom_state["coords"]
                    processing_frame = full_frame[y1:y2, x1:x2]

            # --- Detection ---
            raw_weight, annotated_img = ocr_logic.reader.detect_numbers(processing_frame)
            clean_weight = stabilizer.process_new_reading(raw_weight)
            
            # --- Update State ---
            with global_state["lock"]:
                latest_weight_data["gewicht"] = clean_weight
                global_state["current_frame"] = annotated_img.copy()

            # --- Snapshots ---
            if ENABLE_SNAPSHOTS:
                current_time = time.time()
                if current_time - last_snapshot_time > SNAPSHOT_INTERVAL:
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"snapshot_{timestamp}.jpg"
                    cv2.imwrite(os.path.join(snapshot_dir, filename), full_frame)
                    last_snapshot_time = current_time

def start_ocr_thread(app_config):
    t = threading.Thread(target=ocr_background_worker, args=(app_config,))
    t.daemon = True
    t.start()

def generate_ocr_frames(app_config):
    while True:
        frame = None
        with global_state["lock"]:
            if global_state["current_frame"] is not None:
                frame = global_state["current_frame"]
        
        if frame is not None:
            try:
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret: yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            except: pass
        time.sleep(0.1)

def generate_bak_frames(app_config):
    src = get_video_source(app_config, 'BAK')
    cap = cv2.VideoCapture(src)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, BUFFER_SIZE)
    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        try:
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret: yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        except: pass
