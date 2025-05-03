#!/usr/bin/env python
import argparse
import os
import subprocess
import sys
import time

def parse_args():
    parser = argparse.ArgumentParser(description="Image Processing Service CLI")
    parser.add_argument('command', choices=['start', 'stop', 'status'], help='Command to execute')
    parser.add_argument('--workers', type=int, default=2, help='Number of workers to start')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()

def start_services(args):
    print("Starting services...")
    
    # Create the uploads directory if it doesn't exist
    os.makedirs('uploads', exist_ok=True)
    
    # Start Redis if not running
    try:
        subprocess.run(['redis-cli', 'ping'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("Redis is already running")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Starting Redis...")
        subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)  # Give Redis time to start
    
    # Set environment variables
    env = os.environ.copy()
    env['DEBUG'] = 'true' if args.debug else 'false'
    
    # Start Flask app
    print("Starting Flask API...")
    flask_proc = subprocess.Popen(
        ['flask', 'run', '--host=0.0.0.0', '--port=5000'],
        env=env,
        stdout=subprocess.DEVNULL if not args.debug else None,
        stderr=subprocess.DEVNULL if not args.debug else None
    )
    
    # Start Celery workers
    print(f"Starting {args.workers} Celery workers...")
    celery_proc = subprocess.Popen(
        ['celery', '-A', 'celery_worker.celery_app', 'worker', '--loglevel=info', f'--concurrency={args.workers}'],
        env=env,
        stdout=subprocess.DEVNULL if not args.debug else None,
        stderr=subprocess.DEVNULL if not args.debug else None
    )
    
    print(f"""
Services started:
- API: http://localhost:5000
- Redis: localhost:6379
- Workers: {args.workers} instances

Use Ctrl+C to stop all services
""")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
        flask_proc.terminate()
        celery_proc.terminate()
        print("Services stopped")

def stop_services():
    print("Stopping services...")
    
    # Stop Flask (assumes default port 5000)
    try:
        subprocess.run(['pkill', '-f', 'flask run'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Flask API stopped")
    except:
        print("No Flask API process found")
    
    # Stop Celery workers
    try:
        subprocess.run(['pkill', '-f', 'celery -A celery_worker'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Celery workers stopped")
    except:
        print("No Celery workers found")
    
    # Stop Redis (optional, might be used by other services)
    try:
        result = subprocess.run(['redis-cli', 'ping'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print("Redis is still running. Use 'redis-cli shutdown' to stop it if needed.")
    except:
        print("Redis is not running")

def check_status():
    print("Checking service status...\n")
    
    # Check Redis
    try:
        result = subprocess.run(['redis-cli', 'ping'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0 and 'PONG' in result.stdout:
            print("✅ Redis: Running")
        else:
            print("❌ Redis: Not running")
    except:
        print("❌ Redis: Not running")
    
    # Check Flask API
    try:
        import requests
        response = requests.get('http://localhost:5000')
        print(f"✅ Flask API: Running (Status: {response.status_code})")
    except:
        print("❌ Flask API: Not running")
    
    # Check Celery workers
    try:
        result = subprocess.run(['celery', '-A', 'celery_worker.celery_app', 'status'], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if 'online' in result.stdout:
            print("✅ Celery Workers: Running")
        else:
            print("❌ Celery Workers: Not running")
    except:
        print("❌ Celery Workers: Not running")

def main():
    args = parse_args()
    
    if args.command == 'start':
        start_services(args)
    elif args.command == 'stop':
        stop_services()
    elif args.command == 'status':
        check_status()

if __name__ == '__main__':
    main() 