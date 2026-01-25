import cv2
import threading
import time
import app.vision.ocr as ocr_logic 
import os                   
from datetime import datetime
from app.services.weight_logic import stabilizer 

# ... (De global_state en get_video_source functies blijven hetzelfde als in) ...
global_state = {
    "latest_weight_data": {"gewicht": 0},
    "current_frame": None,
    "lock": threading.Lock()
}
latest_weight_data = global_state["latest_weight_data"]

def get_video_source(config, type_key):
    # ... (Zelfde als voorheen) ...
    if config.get('VIDEO_SOURCE_TYPE') == 'file':
        return config.get('VIDEO_SOURCE_FILE')
    return config.get('RTSP_URL_OCR') if type_key == 'OCR' else config.get('RTSP_URL_BAK')

# --- ACHTERGROND PROCES ---
# ... imports blijven hetzelfde ...

def ocr_background_worker(app_config):
    print("--- Starten van OCR Achtergrond Thread ---")
    
    # 1. SETUP: Zorg ALTIJD dat de map bestaat bij opstarten
    # Dit doen we buiten de loop om de harde schijf te sparen
    snapshot_dir = os.path.join(os.getcwd(), 'data', 'snapshots')
    if not os.path.exists(snapshot_dir):
        try:
            os.makedirs(snapshot_dir)
            print(f"Map aangemaakt: {snapshot_dir}")
        except Exception as e:
            print(f"FOUT: Kan snapshot map niet maken: {e}")

    # Variabele voor timing bijhouden
    last_snapshot_time = 0

    # Model laden
    if ocr_logic.reader is None:
        ocr_logic.init_model(app_config)
    
    src = get_video_source(app_config, 'OCR')
    cap = cv2.VideoCapture(src)
    
    while True:
        success, frame = cap.read()
        if not success:
            if app_config.get('VIDEO_SOURCE_TYPE') == 'file':
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            else:
                time.sleep(2)
                cap.open(src)
                continue

        if ocr_logic.reader is not None:
            # A. Detectie (Ogen)
            raw_weight, annotated_frame = ocr_logic.reader.detect_numbers(frame)
            
            # B. Logica (Brein)
            clean_weight = stabilizer.process_new_reading(raw_weight)
            
            # C. Update Globale Status
            with global_state["lock"]:
                latest_weight_data["gewicht"] = clean_weight
                global_state["current_frame"] = annotated_frame.copy()

            # D. SNAPSHOTS OPSLAAN (Jouw dynamische stukje)
            # We checken de config ELKE frame, zodat je live kunt wisselen
            should_save = app_config.get('SAVE_SNAPSHOTS', False)
            interval = app_config.get('SNAPSHOT_INTERVAL', 20)

            if should_save:
                current_time = time.time()
                if current_time - last_snapshot_time > interval:
                    # Bestandsnaam: snapshot_2026-01-25_14-30-05.jpg
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"snapshot_{timestamp}.jpg"
                    filepath = os.path.join(snapshot_dir, filename)
                    
                    # We slaan het ORIGINELE frame op (zonder YOLO vakjes)
                    # Dit is beter voor het hertrainen van je model later
                    cv2.imwrite(filepath, frame)
                    print(f"📸 Screenshot opgeslagen: {filename}")
                    
                    last_snapshot_time = current_time
        
        # Korte pauze (bijv. 50 FPS)
        time.sleep(0.02)

# ... (De rest van het bestand: start_ocr_thread en generate functies blijven gelijk) ...
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
    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        try:
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret: yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        except: pass
