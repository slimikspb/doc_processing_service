"""
PDF Raster Image Detection Module

Analyzes PDF files to detect raster image content and provides detailed analysis
of image properties, coverage, and distribution across pages.
"""

import os
import logging
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

# PDF processing
try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logger = logging.getLogger(__name__)

class PDFRasterDetector:
    """
    Detects and analyzes raster images in PDF files.
    """
    
    def __init__(self):
        self.default_settings = {
            'min_image_size': (100, 100),
            'max_image_size': (5000, 5000),
            'check_image_ratio': True,
            'ratio_threshold': 0.5,
            'include_metadata': False,
            'timeout_seconds': 30
        }
        
        if not PDF_AVAILABLE:
            logger.warning("PyMuPDF not available - raster detection disabled")
    
    def detect_raster_images(self, file_path: str, settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main method to detect raster images in PDF.
        
        Args:
            file_path: Path to PDF file
            settings: Optional configuration overrides
            
        Returns:
            Dict containing detection results and analysis
        """
        if not PDF_AVAILABLE:
            raise ImportError("PyMuPDF (fitz) not available for PDF raster detection")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Merge settings with defaults
        config = {**self.default_settings, **(settings or {})}
        
        try:
            doc = fitz.open(file_path)
            
            # Initialize results
            results = {
                'has_raster_images': False,
                'image_count': 0,
                'pages_with_images': [],
                'total_pages': doc.page_count,
                'analysis': {
                    'total_images': 0,
                    'pages_dominated_by_images': 0,
                    'average_image_size': None,
                    'largest_image': None,
                    'smallest_image': None,
                    'image_formats': set(),
                    'total_image_area': 0
                },
                'detailed_images': [] if config['include_metadata'] else None,
                'settings_used': config
            }
            
            all_images = []
            total_image_area = 0
            
            # Analyze each page
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_images, page_area = self._analyze_page_images(page, page_num + 1, config)
                
                if page_images:
                    results['pages_with_images'].append(page_num + 1)
                    all_images.extend(page_images)
                    
                    # Calculate page coverage
                    if config['check_image_ratio']:
                        coverage_ratio = page_area / (page.rect.width * page.rect.height)
                        if coverage_ratio >= config['ratio_threshold']:
                            results['analysis']['pages_dominated_by_images'] += 1
                    
                    total_image_area += page_area
            
            # Update results with collected data
            if all_images:
                results['has_raster_images'] = True
                results['image_count'] = len(all_images)
                results['analysis']['total_images'] = len(all_images)
                results['analysis']['total_image_area'] = total_image_area
                
                # Calculate image statistics
                sizes = [(img['width'], img['height']) for img in all_images]
                areas = [w * h for w, h in sizes]
                
                results['analysis']['largest_image'] = f"{max(sizes, key=lambda s: s[0]*s[1])[0]}x{max(sizes, key=lambda s: s[0]*s[1])[1]}"
                results['analysis']['smallest_image'] = f"{min(sizes, key=lambda s: s[0]*s[1])[0]}x{min(sizes, key=lambda s: s[0]*s[1])[1]}"
                
                avg_width = sum(w for w, h in sizes) // len(sizes)
                avg_height = sum(h for w, h in sizes) // len(sizes)
                results['analysis']['average_image_size'] = f"{avg_width}x{avg_height}"
                
                results['analysis']['image_formats'] = list(set(img.get('format', 'unknown') for img in all_images))
                
                if config['include_metadata']:
                    results['detailed_images'] = all_images
            
            doc.close()
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing PDF {file_path}: {str(e)}")
            raise Exception(f"PDF raster detection failed: {str(e)}")
    
    def _analyze_page_images(self, page, page_num: int, config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], float]:
        """
        Analyze images on a single page.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (1-based)
            config: Configuration settings
            
        Returns:
            Tuple of (list of image info, total image area on page)
        """
        images = []
        total_area = 0
        
        try:
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Get image properties
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    # Skip if image is too small or too large
                    if (pix.width < config['min_image_size'][0] or 
                        pix.height < config['min_image_size'][1] or
                        pix.width > config['max_image_size'][0] or 
                        pix.height > config['max_image_size'][1]):
                        pix = None  # Free memory
                        continue
                    
                    # Calculate image area (in points)
                    img_rect = page.get_image_bbox(img)
                    img_area = img_rect.width * img_rect.height
                    total_area += img_area
                    
                    # Create image info
                    image_info = {
                        'page': page_num,
                        'index': img_index,
                        'width': pix.width,
                        'height': pix.height,
                        'area': img_area,
                        'dpi': self._estimate_dpi(pix, img_rect),
                        'color_space': pix.colorspace.name if pix.colorspace else 'unknown',
                        'format': self._get_image_format(pix),
                        'bbox': {
                            'x0': img_rect.x0,
                            'y0': img_rect.y0,
                            'x1': img_rect.x1,
                            'y1': img_rect.y1
                        }
                    }
                    
                    # Add additional metadata if requested
                    if config['include_metadata']:
                        image_info.update({
                            'xref': xref,
                            'size_bytes': len(pix.tobytes()) if pix.n > 0 else 0,
                            'alpha': pix.alpha,
                            'components': pix.n
                        })
                    
                    images.append(image_info)
                    pix = None  # Free memory
                    
                except Exception as img_error:
                    logger.warning(f"Error processing image {img_index} on page {page_num}: {str(img_error)}")
                    continue
                    
        except Exception as page_error:
            logger.warning(f"Error analyzing page {page_num}: {str(page_error)}")
        
        return images, total_area
    
    def _estimate_dpi(self, pixmap, bbox) -> Optional[int]:
        """
        Estimate DPI of image based on its display size vs pixel dimensions.
        """
        try:
            if bbox.width <= 0 or bbox.height <= 0:
                return None
            
            # Calculate DPI based on display dimensions
            dpi_x = pixmap.width / bbox.width * 72  # 72 points per inch
            dpi_y = pixmap.height / bbox.height * 72
            
            return int((dpi_x + dpi_y) / 2)  # Average DPI
        except:
            return None
    
    def _get_image_format(self, pixmap) -> str:
        """
        Determine image format based on color space and properties.
        """
        if pixmap.n == 1:
            return 'grayscale'
        elif pixmap.n == 3:
            return 'rgb'
        elif pixmap.n == 4:
            return 'rgba' if pixmap.alpha else 'cmyk'
        else:
            return 'unknown'
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return ['pdf'] if PDF_AVAILABLE else []

# Global instance
pdf_raster_detector = PDFRasterDetector()

def detect_pdf_raster_images(file_path: str, settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to detect raster images in PDF.
    
    Args:
        file_path: Path to PDF file
        settings: Optional configuration settings
        
    Returns:
        Dict containing raster image detection results
    """
    return pdf_raster_detector.detect_raster_images(file_path, settings)

def is_raster_detection_available() -> bool:
    """Check if raster detection is available."""
    return PDF_AVAILABLE
