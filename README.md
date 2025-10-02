# 🎨 PaintSense - AI-Powered Paint Consultation Platform

A comprehensive Django application featuring AI paint consultation, interactive image coloring, and 3D room reconstruction.

## 🚀 Features

- **AI Paint Consultant**: OpenAI GPT-4o integration for personalized color recommendations
- **Groq API Integration**: Fast chat and vision capabilities with Llama models
- **Interactive Colorizer**: Click-to-color with SAM segmentation and OpenCV fallback
- **3D Reconstruction**: COLMAP-based room modeling from photos
- **Multi-modal Input**: Text, voice, images, and document support

## 📋 Prerequisites

- Python 3.8+
- Django 5.2+
- Required API keys (see setup below)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/nivaranaai/Paint.git
   cd Paint
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your API keys:
   OPENAI_API_KEY=your-openai-api-key-here
   GROQ_API_KEY=your-groq-api-key-here
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start the server**
   ```bash
   python manage.py runserver
   ```

## 🔑 API Keys Setup

### OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `.env` file: `OPENAI_API_KEY=sk-...`

### Groq API Key
1. Visit [Groq Console](https://console.groq.com/keys)
2. Create a new API key
3. Add to `.env` file: `GROQ_API_KEY=gsk_...`

## 🎯 Usage

### Main Features
- **Paint Consultation**: `http://localhost:8000/` - AI-powered paint recommendations
- **Interactive Colorizer**: `http://localhost:8000/colorizer/demo/` - Click-to-color images
- **Groq Demo**: `http://localhost:8000/groq/demo/` - Test Groq chat and vision
- **3D Upload**: `http://localhost:8000/upload/` - Room reconstruction

### API Endpoints

#### OpenAI Integration
- `POST /api/agent/` - Paint consultation with vision
- `POST /api/agent/confirm/` - Confirmation workflow

#### Groq Integration  
- `POST /api/groq/chat/` - Text chat with Llama models
- `POST /api/groq/vision/` - Image analysis with vision models
- `POST /api/groq/paint/` - Paint consultation via Groq
- `GET /api/groq/models/` - Available Groq models

#### Colorizer
- `POST /api/colorizer/upload/` - Upload image for coloring
- `POST /api/colorizer/color/` - Color image at point
- `POST /api/colorizer/reset/` - Reset to original
- `POST /api/colorizer/save/` - Save colored result

## 🏗️ Architecture

```
Paint/
├── colorsense/              # Main Django app
│   ├── colorizer_opencv/    # Interactive colorizer package
│   ├── groq_api_impl/       # Groq API integration
│   ├── agent.py             # OpenAI integration
│   ├── reconstruct.py       # 3D reconstruction
│   └── templates/           # Web interfaces
├── paintme/                 # Django project settings
├── media/                   # Uploaded files and outputs
└── requirements.txt         # Dependencies
```

## 🔧 Configuration

### Optional Dependencies
- **SAM Model**: Download `sam_vit_h_4b8939.pth` for advanced segmentation
- **COLMAP**: Install for 3D reconstruction features
- **Torch**: Required for SAM integration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your-openai-key
GROQ_API_KEY=your-groq-key

# Optional
PAINTSENSE_MODEL=gpt-4o  # Override default model
DEBUG=True               # Development mode
```

## 🚨 Important Notes

- **API Keys**: Never commit API keys to version control
- **Costs**: OpenAI and Groq APIs have usage costs
- **Rate Limits**: Be aware of API rate limitations
- **Security**: Use environment variables for production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure no API keys in commits
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

**"Groq client not initialized"**
- Ensure `GROQ_API_KEY` is set in environment
- Check API key validity at Groq Console

**"Template not found"**
- Restart Django server after cloning
- Check template directories in settings

**"SAM model not found"**
- Download SAM model or use OpenCV fallback
- Check `setup_colorizer.py` for setup

### Getting Help
- Check the demo pages for working examples
- Review API endpoint documentation
- Ensure all dependencies are installed..