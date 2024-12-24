import subprocess

def compile_to_exe():
    """Compile the application to a portable executable using PyInstaller"""
    try:
        subprocess.run([
            "pyinstaller",
            "--onefile",
            "--noconsole",  # Hide console window
            "--clean",      # Clean PyInstaller cache
            "--name", "Excel to Schemas",  # Set output exe name
            "main.py"
        ], check=True)
        print("Executable compiled successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        raise

if __name__ == "__main__":
    compile_to_exe()
