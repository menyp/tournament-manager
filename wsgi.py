"""
WSGI entry point for the Tournament Manager application.
This file is used by Gunicorn to serve the application in production.
"""

from app import app

if __name__ == "__main__":
    app.run()
