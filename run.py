from app import create_app

app = create_app()

if __name__ == '__main__':
    # Start simpelweg de Flask server
    # threaded=True zorgt dat de videostream de website niet blokkeert
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)