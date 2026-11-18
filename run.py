import os
import signal
import subprocess
import sys
import time
import requests
from dotenv import load_dotenv
def create_directories():
    """Create necessary data directories."""
    directories = ["data/documents", "data/vector_db"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Ensured directory exists: {directory}")
def get_python_executable():
    """Prefer .venv python if available."""
    if os.name == "nt":
        venv_py = os.path.join(os.path.dirname(__file__), ".venv", "Scripts", "python.exe")
    else:
        venv_py = os.path.join(os.path.dirname(__file__), ".venv", "bin", "python")
    if os.path.exists(venv_py):
        return venv_py
    return sys.executable
def wait_for_backend(url="http://localhost:8000/health", timeout=30):
    """Wait for the backend to become healthy."""
    print(f"Waiting for backend at {url}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Backend is up and running!")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(1)
    print("Timeout waiting for backend.")
    return False
def wait_for_frontend(url="http://localhost:8501", timeout=30):
    """Wait for the frontend to become ready."""
    print(f"Waiting for frontend at {url}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Frontend is up and running!")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(1)
    return False
def main():
    print("=" * 60)
    print("Starting Adaptive RAG Agent System")
    print("=" * 60)

    load_dotenv()

    create_directories()

    py_exe = get_python_executable()

    backend_process = None
    frontend_process = None

    def cleanup(signum=None, frame=None):
        print("\nShutting down services...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        print("Starting FastAPI Backend...")
        env = os.environ.copy()

        backend_cmd = [
            py_exe,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--reload",
        ]
        backend_process = subprocess.Popen(backend_cmd, env=env)

        wait_for_backend("http://localhost:8000/health", timeout=15)

        print("Starting Streamlit Frontend...")
        frontend_cmd = [
            py_exe,
            "-m",
            "streamlit",
            "run",
            "frontend/app.py",
            "--server.port",
            "8501",
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ]
        frontend_process = subprocess.Popen(frontend_cmd, env=env)

        wait_for_frontend("http://localhost:8501", timeout=20)

        print("=" * 60)
        print("System is running!")
        print("Backend API: http://localhost:8000")
        print("API Docs: http://localhost:8000/docs")
        print("Frontend UI: http://localhost:8501")
        print("Press Ctrl+C to stop all services")
        print("=" * 60)

        backend_process.wait()
        frontend_process.wait()

    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        print(f"Error: {e}")
        cleanup()
if __name__ == "__main__":
    main()
