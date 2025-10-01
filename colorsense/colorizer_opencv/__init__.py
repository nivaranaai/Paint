"""
Colorizer OpenCV Package
SAM-based image segmentation and coloring
"""
from .sam_colorizer import ImageProcessor
from .service import ColorizerService
from .views import *

try:
    from .sam_colorizer import SAMColorizer
except ImportError:
    SAMColorizer = None

__version__ = "1.0.0"
__all__ = ['SAMColorizer', 'ImageProcessor', 'ColorizerService']