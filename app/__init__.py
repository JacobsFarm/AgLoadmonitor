from flask import Flask

def create_app():
    # Hier start Flask. Omdat __name__ verwijst naar de map 'app',
    # vindt hij nu WEL de map 'templates' en 'static'.
    app = Flask(__name__)
    
    # Registreer de routes uit stap 2
    from app.web.routes import main
    app.register_blueprint(main)
    
    return app