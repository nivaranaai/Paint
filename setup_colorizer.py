"""
Setup script for SAM colorizer
Downloads SAM model and installs dependencies
"""
import os
import urllib.request
import sys

def download_sam_model():
    """Download SAM model checkpoint"""
    model_url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"
    model_path = "sam_vit_h_4b8939.pth"
    
    if os.path.exists(model_path):
        print(f"SAM model already exists at {model_path}")
        return model_path
    
    print("Downloading SAM model (2.4GB)...")
    try:
        urllib.request.urlretrieve(model_url, model_path)
        print(f"SAM model downloaded to {model_path}")
        return model_path
    except Exception as e:
        print(f"Error downloading SAM model: {e}")
        return None

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    os.system("pip install -r requirments.txt")

if __name__ == "__main__":
    print("Setting up SAM Colorizer...")
    
    # Install dependencies
    install_dependencies()
    
    # Download SAM model
    model_path = download_sam_model()
    
    if model_path:
        print("\nSetup complete!")
        print("You can now run:")
        print("python manage.py runserver")
        print("Then visit: http://localhost:8000/colorizer/demo/")
    else:
        print("\nSetup completed with warnings.")
        print("Please manually download the SAM model.")