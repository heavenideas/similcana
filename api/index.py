import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app
from app import app

# Initialize the finder at import time
from app import initialize_finder, init_thread
if not init_thread.is_alive():
    initialize_finder()

# For Vercel serverless function handler
def handler(request):
    return app(request['env'], request['start_response'])

# Make the app directly importable for Vercel
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) 