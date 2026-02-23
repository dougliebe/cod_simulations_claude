"""Script to restart Flask by killing old instances and starting fresh."""
import os
import subprocess
import time
import sys

print("Stopping all Flask/Python processes...")
# Kill all python processes (except this one)
current_pid = os.getpid()
try:
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                          capture_output=True, text=True)
    for line in result.stdout.split('\n')[1:]:  # Skip header
        if line.strip():
            parts = line.replace('"', '').split(',')
            if len(parts) >= 2:
                pid = int(parts[1])
                if pid != current_pid:
                    print(f"Killing PID {pid}...")
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)],
                                 capture_output=True)
except Exception as e:
    print(f"Error killing processes: {e}")

print("Waiting 2 seconds...")
time.sleep(2)

print("Starting Flask...")
os.system('py app.py')
