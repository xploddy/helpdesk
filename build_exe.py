import PyInstaller.__main__
import os
import shutil

def build():
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "icon-192.ico")
    
    # Check for icon
    if not os.path.exists(icon_path):
        icon_path = os.path.join(base_dir, "app", "static", "icons", "icon-192.ico")
    
    # Arguments for PyInstaller
    args = [
        'run.py',                    # Entry point
        '--name=HelpDeskApp',        # Name of the executable
        '--onedir',                  # Create a single folder (easier to debug/smaller individual files)
        '--noconsole',               # Don't show the command prompt
        '--clean',                   # Clean cache before build
        # Exclude heavy unnecessary modules
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=tkinter',
        '--exclude-module=PIL',
        '--exclude-module=scipy',
        '--exclude-module=unittest',
    ]

    
    # Add icon if it exists
    if os.path.exists(icon_path):
        print(f"Using icon: {icon_path}")
        args.append(f'--icon={icon_path}')
    else:
        print("Warning: Icon not found. Building without icon.")
    
    # Add data folders (templates and static)
    # The format is 'source;destination' for Windows
    templates_rel = os.path.join('app', 'templates')
    static_rel = os.path.join('app', 'static')
    
    args.append(f'--add-data={templates_rel};app/templates')
    args.append(f'--add-data={static_rel};app/static')
    
    # Run PyInstaller
    print("Starting build process...")
    PyInstaller.__main__.run(args)
    print("Build finished! Check the 'dist' folder.")

if __name__ == "__main__":
    # Ensure pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        os.system("pip install pyinstaller")
        
    build()
