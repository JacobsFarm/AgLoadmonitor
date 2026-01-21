from flask import Blueprint, render_template, Response
from app.vision.streamer import generate_frames

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html', 
                           gewicht=4500, 
                           stap="Mais Laden", 
                           doel=1000)

@main.route('/video_feed')
def video_feed():
    # Dit vertelt de browser: "Hier komt een oneindige stroom plaatjes aan"
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')