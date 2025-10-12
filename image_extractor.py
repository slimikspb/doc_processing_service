"""
Image extraction module for PDFs.
Extracts images from PDF files with metadata (page number, position, dimensions).
"""

import os
import uuid
import logging
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from PIL import Image

logger = logging.getLogger(__name__)

class ImageExtractor:
    """
    Extracts images from PDF files and saves them temporarily with metadata.
    """
    
    def __init__(self, temp_dir: str = "/tmp"):
        self.temp_dir = temp_dir
        if not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not available - image extraction disabled")
    
    def extract_images_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract all images from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of dicts containing image metadata and file paths
        """
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF (fitz) not available for image extraction")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        extracted_images = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_images = self._extract_page_images(page, page_num + 1, pdf_path)
                extracted_images.extend(page_images)
            
            doc.close()
            
            logger.info(f"Extracted {len(extracted_images)} images from {pdf_path}")
            return extracted_images
            
        except Exception as e:
            logger.error(f"Error extracting images from {pdf_path}: {str(e)}")
            raise Exception(f"Image extraction failed: {str(e)}")
    
    def _extract_page_images(self, page, page_num: int, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract images from a single page.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (1-based)
            pdf_path: Path to source PDF file
            
        Returns:
            List of image metadata dicts
        """
        images = []
        
        try:
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Get image xref
                    xref = img[0]
                    
                    # Extract image data
                    base_image = page.parent.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Get pixmap for dimensions
                    pix = fitz.Pixmap(page.parent, xref)
                    width = pix.width
                    height = pix.height
                    
                    # Get image position on page
                    img_rect = page.get_image_bbox(img)
                    
                    # Generate unique filename
                    file_id = str(uuid.uuid4())
                    filename = f"img_{page_num}_{img_index}_{file_id}.{image_ext}"
                    file_path = os.path.join(self.temp_dir, filename)
                    
                    # Save image to disk
                    with open(file_path, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    # Create metadata
                    image_info = {
                        'file_path': file_path,
                        'page_number': page_num,
                        'image_index': img_index,
                        'width': width,
                        'height': height,
                        'format': image_ext,
                        'position': {
                            'x0': img_rect.x0,
                            'y0': img_rect.y0,
                            'x1': img_rect.x1,
                            'y1': img_rect.y1
                        },
                        'size_bytes': len(image_bytes)
                    }
                    
                    images.append(image_info)
                    
                    # Free memory
                    pix = None
                    
                except Exception as img_error:
                    logger.warning(f"Error extracting image {img_index} from page {page_num}: {str(img_error)}")
                    continue
            
        except Exception as page_error:
            logger.warning(f"Error processing page {page_num}: {str(page_error)}")
        
        return images
    
    def cleanup_images(self, image_list: List[Dict[str, Any]]) -> None:
        """
        Clean up extracted image files.
        
        Args:
            image_list: List of image metadata dicts containing file paths
        """
        for image_info in image_list:
            file_path = image_info.get('file_path')
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Cleaned up image: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup image {file_path}: {str(e)}")

# Global instance
image_extractor = ImageExtractor()

def extract_images_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Convenience function to extract images from PDF.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of image metadata dicts
    """
    return image_extractor.extract_images_from_pdf(pdf_path)

def cleanup_images(image_list: List[Dict[str, Any]]) -> None:
    """
    Convenience function to cleanup extracted images.
    
    Args:
        image_list: List of image metadata dicts
    """
    return image_extractor.cleanup_images(image_list)

def is_image_extraction_available() -> bool:
    """Check if image extraction is available."""
    return PYMUPDF_AVAILABLE

