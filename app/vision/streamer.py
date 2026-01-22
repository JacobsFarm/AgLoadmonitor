import cv2
import time

# Je RTSP URL
RTSP_URL = "rtsp://admin:YourPassword123@192.168.100.22:554/h264Preview_01_sub"

def generate_frames():
    camera = cv2.VideoCapture(RTSP_URL)
    
    # Buffer op 1 zetten is cruciaal voor 'live' gevoel
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not camera.isOpened():
        print("FOUT: Kan camera niet openen.")

    # --- INSTELLINGEN ---
    TARGET_FPS = 5             # We willen max 5 beelden per seconde sturen
    FRAME_INTERVAL = 1.0 / TARGET_FPS 
    last_frame_time = 0

    while True:
        # We lezen ALTIJD de camera uit om de buffer leeg te houden
        success, frame = camera.read()

        if not success:
            # Verbinding verbroken? Probeer opnieuw.
            print("Verbinding weg, herstarten...")
            camera.release()
            time.sleep(2)
            camera = cv2.VideoCapture(RTSP_URL)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            continue

        # --- TIJD CHECK ---
        # Is het al tijd voor het volgende plaatje?
        current_time = time.time()
        if (current_time - last_frame_time) < FRAME_INTERVAL:
            # Nee, het is nog te vroeg. Sla dit frame over.
            continue
        
        last_frame_time = current_time

        # --- VERWERKING (Alleen als het tijd is) ---
        
        # 1. Verkleinen (alleen als de bron groter is dan 640px)
        # Dit spaart de CPU van de Raspberry Pi
        height, width = frame.shape[:2]
        if width > 640:
            new_width = 640
            new_height = int(height * (new_width / width))
            frame = cv2.resize(frame, (new_width, new_height))

        # 2. Comprimeren naar JPG
        # Kwaliteit 40 is vaak goed genoeg voor op een telefoon
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 40])
        
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'

               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
