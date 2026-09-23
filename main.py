"""Local dev entrypoint: `python main.py` or `flask --app main run`."""
from app.factory import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config.get('DEBUG', False))
