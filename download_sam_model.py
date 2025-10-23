#!/usr/bin/env python3
"""
SAM model downloader
"""
import os
import urllib.request

def main():
    model_url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"
    model_path = "sam_vit_h_4b8939.pth"
    
    if os.path.exists(model_path):
        print(f"✓ SAM model exists: {model_path}")
        return
    
    print("📥 Downloading SAM model (2.4GB)...")
    try:
        urllib.request.urlretrieve(model_url, model_path)
        print(f"✓ Downloaded: {model_path}")
        
        size = os.path.getsize(model_path)
        print(f"✓ Size: {size/1024/1024:.1f}MB")
        
    except Exception as e:
        print(f"✗ Download failed: {e}")
        print(f"Manual download: {model_url}")

if __name__ == "__main__":
    main()