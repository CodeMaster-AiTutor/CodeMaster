from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))  # Changed to 5001 to avoid conflicts
    debug = os.getenv('FLASK_ENV') == 'development'
    host = os.getenv('HOST', '127.0.0.1')  # Use localhost instead of 0.0.0.0 to avoid permission issues
    print(f"Starting CodeMaster Backend on http://{host}:{port}")
    print(f"Health check: http://{host}:{port}/api/health")
    app.run(host=host, port=port, debug=debug, use_reloader=False)
