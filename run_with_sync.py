# run_with_sync.py
import os
import sys
import subprocess
import threading
import time
from app import create_app

def run_sync_script():
    """Run the sync_spreadsheet script in a separate process."""
    print("Starting spreadsheet sync process...")
    
    # Start the sync script in a separate process
    try:
        # Use Python executable that's currently running
        python_executable = sys.executable
        subprocess.Popen([python_executable, 'sync_spreadsheet.py'])
        print("Sync process started successfully!")
    except Exception as e:
        print(f"Error starting sync process: {e}")

def run_app():
    """Run the Flask application."""
    app = create_app()
    app.run(debug=True)

if __name__ == "__main__":
    # Start the sync script in a separate thread
    sync_thread = threading.Thread(target=run_sync_script)
    sync_thread.daemon = True  # This ensures the thread will exit when the main program exits
    sync_thread.start()
    
    # Run the Flask app
    run_app()