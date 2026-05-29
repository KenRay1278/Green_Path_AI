#!/usr/bin/env python3
"""
Conda Environment Setup Script
Jakarta Pollution-Aware Pathfinding AI
"""

import subprocess
import sys
import os
import platform

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def check_conda():
    """Check if conda is installed"""
    print("🔍 Checking for conda installation...")
    try:
        result = subprocess.run(['conda', '--version'], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            print(f"   ✅ Found: {result.stdout.strip()}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False

def create_directories():
    """Create necessary project directories"""
    print_header("Creating Project Directories")
    
    directories = [
        'data/raw',
        'data/processed',
        'scripts/cache',
        'src/__pycache__',
        'web'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ Created: {directory}")
    
    print("\n✅ All directories created!")

def create_environment():
    """Create conda environment from environment.yml"""
    print_header("Creating Conda Environment")
    
    if not os.path.exists('environment.yml'):
        print("❌ Error: environment.yml not found!")
        print("   Please ensure environment.yml is in the project root")
        return False
    
    print("📦 Creating environment 'green_path'...")
    print("   This may take 5-10 minutes...")
    
    try:
        result = subprocess.run(
            ['conda', 'env', 'create', '-f', 'environment.yml'],
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Environment created successfully!")
            return True
        else:
            print("\n⚠️  Environment might already exist or there was an error")
            return False
            
    except Exception as e:
        print(f"\n❌ Error creating environment: {e}")
        return False

def update_environment():
    """Update existing environment"""
    print_header("Updating Conda Environment")
    
    print("🔄 Updating environment 'green_path'...")
    
    try:
        result = subprocess.run(
            ['conda', 'env', 'update', '-f', 'environment.yml', '--prune'],
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Environment updated successfully!")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"\n❌ Error updating environment: {e}")
        return False

def check_environment_exists():
    """Check if green_path environment already exists"""
    try:
        result = subprocess.run(
            ['conda', 'env', 'list'],
            capture_output=True,
            text=True
        )
        
        if 'green_path' in result.stdout:
            return True
        return False
        
    except Exception:
        return False

def get_activation_command():
    """Get the correct activation command based on OS"""
    return "conda activate green_path"

def print_next_steps():
    """Print instructions for next steps"""
    activation_cmd = get_activation_command()
    
    print_header("🎉 Setup Complete!")
    
    print("Next steps:\n")
    print("1️⃣  Activate the environment:")
    print(f"   {activation_cmd}\n")
    print("2️⃣  Extract road network (first time only):")
    print("   cd scripts")
    print("   python network_extractor.py\n")
    print("3️⃣  Add pollution weights:")
    print("   python add_pollution_weights.py\n")
    print("4️⃣  Start the Flask server:")
    print("   cd ../src")
    print("   python app.py\n")
    print("5️⃣  Open web interface:")
    print("   Open http://localhost:5000/ in your browser\n")
    
    print("=" * 70)
    print("\n💡 TIP: Always activate the environment before running scripts!")
    print(f"       {activation_cmd}\n")

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║        🐍 CONDA ENVIRONMENT SETUP                            ║
    ║        Jakarta Pollution-Aware Pathfinding AI                 ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Check if conda is installed
    if not check_conda():
        print("❌ Conda is not installed or not in PATH!")
        print("\n📥 Please install Miniconda or Anaconda:")
        print("   Miniconda: https://docs.conda.io/en/latest/miniconda.html")
        print("   Anaconda: https://www.anaconda.com/download")
        return
    
    # Create project directories
    create_directories()
    
    # Check if environment already exists
    env_exists = check_environment_exists()
    
    if env_exists:
        print("⚠️  Environment 'green_path' already exists!")
        print("\nOptions:")
        print("  1. Update existing environment (recommended)")
        print("  2. Remove and recreate")
        print("  3. Cancel")
        
        choice = input("\nChoose option (1/2/3): ").strip()
        
        if choice == '1':
            success = update_environment()
        elif choice == '2':
            print("\n🗑️  Removing existing environment...")
            subprocess.run(['conda', 'env', 'remove', '-n', 'green_path', '-y'])
            print("✅ Removed!")
            success = create_environment()
        else:
            print("\n❌ Setup cancelled")
            return
    else:
        success = create_environment()
    
    if success:
        print_next_steps()
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        print("\n💡 Common issues:")
        print("   - Slow internet connection (conda downloads packages)")
        print("   - Conflicting packages (try removing existing environment)")
        print("   - Insufficient disk space")
        print("\n📧 If problems persist, check environment.yml for conflicts")

if __name__ == "__main__":
    main()