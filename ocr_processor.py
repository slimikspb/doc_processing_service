"""
OCR processing module using Tesseract.
Performs optical character recognition on images with multi-language support.
"""

import os
import logging
from typing import Dict, Any, List, Optional

try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)

class OCRProcessor:
    """
    Wrapper for Tesseract OCR processing with multi-language support.
    """
    
    def __init__(self, languages: str = "eng+rus"):
        """
        Initialize OCR processor.
        
        Args:
            languages: Tesseract language codes separated by + (e.g., "eng+rus")
        """
        self.languages = languages
        self.available = self._check_availability()
        
        if self.available:
            logger.info(f"OCR processor initialized with languages: {self.languages}")
        else:
            logger.warning("Tesseract not available - OCR disabled")
    
    def _check_availability(self) -> bool:
        """
        Check if Tesseract is installed and available.
        
        Returns:
            True if Tesseract is available, False otherwise
        """
        if not PYTESSERACT_AVAILABLE:
            return False
        
        try:
            # Try to get Tesseract version
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
            return True
        except Exception as e:
            logger.warning(f"Tesseract not available: {str(e)}")
            return False
    
    def process_image(self, image_path: str) -> str:
        """
        Perform OCR on a single image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text from image
        """
        if not self.available:
            raise Exception("Tesseract not available - cannot perform OCR")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # Open image
            image = Image.open(image_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(
                image,
                lang=self.languages,
                config='--psm 3'  # Fully automatic page segmentation
            )
            
            # Close image
            image.close()
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {str(e)}")
            return f"[OCR Error: {str(e)}]"
    
    def process_images(self, image_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform OCR on multiple images.
        
        Args:
            image_list: List of image metadata dicts with file_path keys
            
        Returns:
            Updated list with 'ocr_text' added to each dict
        """
        if not self.available:
            raise Exception("Tesseract not available - cannot perform OCR")
        
        results = []
        
        for image_info in image_list:
            file_path = image_info.get('file_path')
            
            if not file_path:
                logger.warning("Image info missing file_path, skipping")
                continue
            
            try:
                # Perform OCR
                ocr_text = self.process_image(file_path)
                
                # Add OCR text to metadata
                image_info['ocr_text'] = ocr_text
                image_info['ocr_success'] = True
                
                logger.debug(f"OCR extracted {len(ocr_text)} characters from {file_path}")
                
            except Exception as e:
                logger.error(f"OCR failed for {file_path}: {str(e)}")
                image_info['ocr_text'] = ""
                image_info['ocr_success'] = False
                image_info['ocr_error'] = str(e)
            
            results.append(image_info)
        
        return results
    
    def is_available(self) -> bool:
        """Check if OCR is available."""
        return self.available

# Global instance - will be initialized with languages from ENV in app.py
ocr_processor = None

def initialize_ocr_processor(languages: str = "eng+rus") -> None:
    """
    Initialize global OCR processor instance.
    
    Args:
        languages: Tesseract language codes
    """
    global ocr_processor
    ocr_processor = OCRProcessor(languages)

def process_image(image_path: str) -> str:
    """
    Convenience function to process a single image.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Extracted OCR text
    """
    if ocr_processor is None:
        initialize_ocr_processor()
    return ocr_processor.process_image(image_path)

def process_images(image_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function to process multiple images.
    
    Args:
        image_list: List of image metadata dicts
        
    Returns:
        Updated list with OCR results
    """
    if ocr_processor is None:
        initialize_ocr_processor()
    return ocr_processor.process_images(image_list)

def is_ocr_available() -> bool:
    """Check if OCR is available."""
    if ocr_processor is None:
        initialize_ocr_processor()
    return ocr_processor.is_available() if ocr_processor else False

