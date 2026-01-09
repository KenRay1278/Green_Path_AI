#!/usr/bin/env python3
"""
Flask Server Runner
Checks environment and starts the Flask app
"""

import os
import sys
import subprocess
import webbrowser
import time

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def check_conda_environment():
    """Check if running in correct conda environment"""
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', '')
    
    if conda_env == 'green_path':
        print(f"✅ Running in conda environment: {conda_env}")
        return True
    elif conda_env:
        print(f"⚠️  Running in environment: {conda_env}")
        print(f"   Recommended: conda activate green_path")
        return True
    else:
        print("❌ Not running in a conda environment!")
        print("   Please activate: conda activate green_path")
        return False

def check_processed_data():
    """Check if processed network data exists"""
    data_path = os.path.join('data', 'processed', 'jakarta_network_processed.pkl')
    
    if os.path.exists(data_path):
        size_mb = os.path.getsize(data_path) / (1024 * 1024)
        print(f"✅ Network data found: {size_mb:.2f} MB")
        return True
    else:
        print("⚠️  Network data not found!")
        print("   Please run:")
        print("   1. cd scripts")
        print("   2. python network_extractor.py")
        print("   3. python add_pollution_weights.py")
        return False

def check_files():
    """Check if required files exist"""
    required_files = {
        'src/app.py': 'Flask server',
        'src/pathfinding_algo.py': 'Pathfinding algorithm',
        'web/index.html': 'Web interface'
    }
    
    all_exist = True
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            print(f"✅ {description}: {file_path}")
        else:
            print(f"❌ Missing {description}: {file_path}")
            all_exist = False
    
    return all_exist

def open_browser():
    """Open web interface in browser"""
    time.sleep(2)  # Wait for server to start
    
    web_path = os.path.abspath('web/index.html')
    
    if os.path.exists(web_path):
        print(f"\n🌐 Opening web interface...")
        webbrowser.open(f'file:///{web_path}')
    else:
        print(f"\n⚠️  Web interface not found at: {web_path}")

def start_server():
    """Start Flask server"""
    print_header("Starting Flask Server")
    
    os.chdir('src')
    
    print("🚀 Starting Flask on http://localhost:5000")
    print("📡 API endpoint: http://localhost:5000/get_route")
    print("\n⌨️  Press Ctrl+C to stop the server\n")
    
    try:
        # Start Flask
        subprocess.run([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
        print("=" * 70)

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║        🚀 FLASK SERVER RUNNER                                ║
    ║        Jakarta Pollution-Aware Pathfinding AI                 ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print_header("Pre-flight Checks")
    
    # Check environment
    env_ok = check_conda_environment()
    print()
    
    # Check files
    files_ok = check_files()
    print()
    
    # Check data
    data_ok = check_processed_data()
    
    if not files_ok:
        print("\n❌ Missing required files! Cannot start server.")
        return
    
    if not data_ok:
        print("\n⚠️  Network data not ready!")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Open browser in background
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start server
    start_server()

if __name__ == "__main__":
    # Change to project root if running from src/
    if os.path.basename(os.getcwd()) == 'src':
        os.chdir('..')
    
    main()