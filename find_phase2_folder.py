import os

def find_phase2_frontend():
    # Starting from current directory
    for root, dirs, files in os.walk('.'):
        if 'index.html' in files and 'about.html' in files:
            print(f"Found Phase 2 frontend files in: {os.path.abspath(root)}")
            return os.path.relpath(root)
    print("Phase 2 frontend files not found.")

folder = find_phase2_frontend()
print(f"Use this folder path in deploy_to_github.py for FOLDER_TO_DEPLOY:\n'{folder}'")
