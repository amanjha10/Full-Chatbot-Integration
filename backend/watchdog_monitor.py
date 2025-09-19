#!/usr/bin/env python3
"""
Watchdog system for monitoring FAQ file changes and auto-refreshing vector database
"""

import os
import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from django.conf import settings

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
import django
django.setup()


class FAQFileHandler(FileSystemEventHandler):
    """Handler for FAQ file changes"""
    
    def __init__(self):
        self.faq_file_path = os.path.join(settings.BASE_DIR, 'refrence', 'data', 'documents', 'education_faq.json')
        self.refresh_script_path = os.path.join(settings.BASE_DIR, 'refresh_vectors.py')
        self.last_refresh = 0
        self.debounce_time = 2  # Wait 2 seconds between refreshes
        
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
            
        # Check if the modified file is our FAQ file
        if os.path.abspath(event.src_path) == os.path.abspath(self.faq_file_path):
            current_time = time.time()
            
            # Debounce: only refresh if enough time has passed
            if current_time - self.last_refresh > self.debounce_time:
                print(f"📝 FAQ file changed: {event.src_path}")
                self.refresh_vector_database()
                self.last_refresh = current_time
    
    def refresh_vector_database(self):
        """Refresh the vector database"""
        try:
            if os.path.exists(self.refresh_script_path):
                print("🔄 Auto-refreshing vector database...")
                result = subprocess.run([
                    sys.executable, self.refresh_script_path
                ], capture_output=True, text=True, cwd=settings.BASE_DIR)
                
                if result.returncode == 0:
                    print("✅ Vector database auto-refreshed successfully")
                else:
                    print(f"⚠️ Vector refresh failed: {result.stderr}")
            else:
                print("⚠️ Vector refresh script not found")
        except Exception as e:
            print(f"❌ Error refreshing vector database: {e}")


def start_watchdog():
    """Start the watchdog monitoring system"""
    handler = FAQFileHandler()
    observer = Observer()
    
    # Monitor the directory containing the FAQ file
    watch_directory = os.path.dirname(handler.faq_file_path)
    
    if not os.path.exists(watch_directory):
        print(f"❌ Watch directory does not exist: {watch_directory}")
        return
    
    observer.schedule(handler, watch_directory, recursive=False)
    observer.start()
    
    print(f"👁️ Watchdog started monitoring: {watch_directory}")
    print(f"📁 FAQ file: {handler.faq_file_path}")
    print("🔄 Auto-refresh enabled for vector database")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Watchdog stopped")
    
    observer.join()


if __name__ == "__main__":
    start_watchdog()
