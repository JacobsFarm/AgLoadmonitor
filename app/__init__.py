import os
import json
from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # 1. Config Laden
    base_dir = os.getcwd()
    config_path = os.path.join(base_dir, 'data', 'config.json')
    try:
        with open(config_path, 'r') as f:
            app.config.update(json.load(f))
    except FileNotFoundError:
        print("Config niet gevonden!")

    # 2. Blueprints
    from app.web.routes import main
    app.register_blueprint(main)
    
    from app.api.endpoints import api
    app.register_blueprint(api, url_prefix='/api')

    # 3. START DE ACHTERGROND OCR THREAD (NIEUW)
    from app.vision.streamer import start_ocr_thread
    # We doen dit alleen als we niet in 'debug reloader' modus zitten
    # (anders start hij 2x op in development), of gewoon simpel checken:
    if os.environ.get('WERKZEUG_RUN_MAIN') or __name__ == 'app': 
         # Let op: bij simpele run.py werkt dit soms direct, 
         # anders gewoon: start_ocr_thread(app.config)
         print("Starten van OCR services...")
         start_ocr_thread(app.config)

    return app
