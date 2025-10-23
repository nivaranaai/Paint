# 🎨 SAM Interactive Paint Studio

AI-powered paint studio using Meta's Segment Anything Model for intelligent image segmentation and coloring.

## ✨ Features

- **AI Segmentation**: Click anywhere for intelligent object segmentation
- **Fallback Mode**: OpenCV flood-fill when SAM unavailable
- **Color Palette**: Auto-extracted dominant colors
- **Blend Modes**: Normal, Overlay, Multiply
- **Opacity Control**: 10-100% transparency
- **Undo/Reset**: Full action history

## 🚀 Quick Start

### 1. Setup
```bash
python setup_sam_studio.py
python download_sam_model.py
```

### 2. Run
```bash
python manage.py runserver
```

Visit: **http://localhost:8000/sam-studio/**

## 🎯 Usage

1. **Upload**: Drag & drop image
2. **Click**: Click anywhere to segment and color
3. **Adjust**: Change colors, blend modes, opacity
4. **Save**: Download your artwork

## 🔧 API Endpoints

- `POST /api/sam-studio/create/` - Create session
- `POST /api/sam-studio/apply-color/` - Apply color

## 📋 Requirements

- Python 3.8+
- PyTorch
- OpenCV
- SAM model (2.4GB)

## 🔍 Troubleshooting

**"SAM model not found"**
- Run: `python download_sam_model.py`

**"SAM dependencies not available"**
- Run: `python setup_sam_studio.py`

## 🎨 Technical Details

- Uses Meta's SAM ViT-H model for segmentation
- Fallback to OpenCV flood-fill
- Session-based architecture
- Real-time coordinate mapping
- Memory-efficient caching

---

**Ready to create AI-powered art!** 🚀