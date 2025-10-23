#!/usr/bin/env python3
"""
Setup script for SAM Interactive Paint Studio
"""
import os
import sys
import subprocess

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✓ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {command}")
        return False

def main():
    print("🎨 Setting up SAM Interactive Paint Studio")
    print("=" * 50)
    
    if sys.version_info < (3, 8):
        print("✗ Python 3.8+ required")
        return False
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Install PyTorch
    print("\n📦 Installing PyTorch...")
    run_command("pip install torch torchvision")
    
    # Install Segment Anything
    print("\n📦 Installing Segment Anything...")
    run_command("pip install git+https://github.com/facebookresearch/segment-anything.git")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    deps = ["opencv-python", "pycocotools", "matplotlib", "onnxruntime", "onnx"]
    for dep in deps:
        run_command(f"pip install {dep}")
    
    print("\n🎉 Setup complete!")
    print("Next: python download_sam_model.py")
    
if __name__ == "__main__":
    main()