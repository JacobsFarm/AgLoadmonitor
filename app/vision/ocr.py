import cv2
import numpy as np
from ultralytics import YOLO
import os

class DigitalReadout:
    def __init__(self, model_path):
        print(f"Laden van YOLO model: {model_path}")
        self.model = YOLO(model_path)

    def find_screen_box(self, frame, target_labels=['lcd', 'monitor']):
        """
        Zoekt naar een specifiek object (bijv. lcd of monitor) om op in te zoomen.
        Geeft terug: (x1, y1, x2, y2) of None
        """
        # Scan het hele plaatje
        results = self.model.predict(frame, conf=0.4, verbose=False)
        
        best_box = None
        highest_conf = 0.0

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                conf = box.conf[0].item()

                # Als dit label in onze zoeklijst staat (bijv. 'lcd')
                if label in target_labels:
                    # We pakken de box met de hoogste zekerheid
                    if conf > highest_conf:
                        highest_conf = conf
                        # Coördinaten ophalen en omzetten naar integers
                        coords = box.xyxy[0].tolist() # [x1, y1, x2, y2]
                        best_box = [int(c) for c in coords]

        return best_box

    def detect_numbers(self, frame):
        """
        Voert detectie uit op het (eventueel uitgeknipte) frame.
        """
        results = self.model.predict(frame, conf=0.5, verbose=False)
        
        detections = []

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                
                # Alleen cijfers (of de punt/komma als je die getraind hebt)
                if label.isdigit() or label in ['.', ',']:
                    x1 = box.xyxy[0][0].item() 
                    detections.append((x1, label))

        # Sorteer van Links naar Rechts
        detections.sort(key=lambda x: x[0])
        number_str = "".join([d[1] for d in detections])
        
        raw_number = None
        if number_str:
            # Filter eventuele niet-cijfers eruit als int() faalt
            clean_str = ''.join(filter(str.isdigit, number_str))
            if clean_str:
                raw_number = int(clean_str)

        # Plot de resultaten op het frame (voor debug)
        return raw_number, results[0].plot()

# Global setup
reader = None

def init_model(app_config):
    global reader
    path = os.path.join(os.getcwd(), app_config['YOLO_MODEL_PATH'])
    reader = DigitalReadout(path)
