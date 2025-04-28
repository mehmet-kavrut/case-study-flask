import os
import time

def cleanup_old_files(folder, days=20):
    now = time.time()
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.stat(file_path).st_mtime < now - days * 86400:
            os.remove(file_path)