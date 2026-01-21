import os

class Config:
    # --- Basis Instellingen ---
    # Bepaalt de map waar dit bestand staat, handig voor absolute paden.
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'een-heel-geheim-sleutelwoord-voor-flask'

    # --- Camera URL's (PAS DIT AAN!) ---
    # Voorbeeld: "rtsp://gebruiker:wachtwoord@192.168.1.50:554/stream1"
    # Zet hier de URL van de camera in de bak
    RTSP_URL_BAK = "rtsp://admin:77778888Camera89.@192.168.178.46:554/h264Preview_02_sub"
    
    # Zet hier later de URL van de camera op de monitor
    RTSP_URL_OCR = "" 

    # --- Paden naar data ---
    PLANS_FOLDER = os.path.join(BASE_DIR, 'data', 'plans')
    LOGS_FOLDER = os.path.join(BASE_DIR, 'data', 'logs')
    MODEL_PATH = os.path.join(BASE_DIR, 'models', 'yolo_digits_v1.pt')

    # --- Applicatie Logica ---
    # Hoeveel seconden moet gewicht stabiel zijn voor auto-volgende-stap?
    AUTO_NEXT_STEP_DELAY = 5 
