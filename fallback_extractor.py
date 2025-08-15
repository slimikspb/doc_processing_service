"""
Fallback document extractor when Office processing libraries are not available
"""
import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any
import textract

logger = logging.getLogger(__name__)

class FallbackDocumentExtractor:
    """Fallback extractor using only textract for when Office libraries are unavailable"""
    
    def __init__(self):
        # Only textract formats when Office processing is not available
        self.textract_formats = {
            '.doc', '.docx', '.odt', '.rtf', '.pdf', '.txt', 
            '.png', '.jpg', '.jpeg', '.tiff', '.gif'
        }
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information with fallback processing"""
        file_ext = Path(file_path).suffix.lower()
        file_size = os.path.getsize(file_path)
        
        # Office formats not supported in fallback mode
        office_formats = {'.xlsx', '.xls', '.pptx', '.ppt'}
        
        if file_ext in office_formats:
            processor_type = 'unsupported_office'
            supported = False
        elif file_ext in self.textract_formats:
            processor_type = 'textract'
            supported = True
        else:
            processor_type = 'unsupported'
            supported = False
        
        return {
            'filename': Path(file_path).name,
            'extension': file_ext,
            'size_bytes': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'processor_type': processor_type,
            'supported': supported
        }
    
    def extract_text(self, file_path: str, timeout: int = 60) -> Dict[str, Any]:
        """Extract text using only textract (fallback mode)"""
        file_info = self.get_file_info(file_path)
        
        if not file_info['supported']:
            if file_info['processor_type'] == 'unsupported_office':
                raise ValueError(f"Office document processing not available. Install required libraries: openpyxl, xlrd, python-pptx, oletools")
            else:
                raise ValueError(f"Unsupported file format: {file_info['extension']}")
        
        try:
            # Use textract for supported formats
            result = self._extract_textract_document(file_path, timeout)
            
            return {
                **result,
                'file_info': file_info,
                'extraction_method': 'textract_fallback'
            }
            
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {str(e)}")
            raise Exception(f"Failed to extract text: {str(e)}")
    
    def _extract_textract_document(self, file_path: str, timeout: int = 60) -> Dict[str, Any]:
        """Extract text using textract with timeout"""
        try:
            # Simple textract approach without circuit breaker in fallback mode
            text = textract.process(file_path).decode('utf-8', errors='replace')
            
            return {
                'text': text,
                'metadata': {
                    'extraction_method': 'textract_fallback',
                    'office_support': False
                },
                'processor': 'textract_fallback'
            }
            
        except Exception as e:
            logger.error(f'Textract extraction failed: {str(e)}')
            raise Exception(f"Text extraction failed: {str(e)}")
    
    def get_supported_formats(self) -> Dict[str, list]:
        """Get list of supported formats in fallback mode"""
        return {
            'office_documents': [],  # Not supported in fallback
            'textract_documents': list(self.textract_formats),
            'all_supported': list(self.textract_formats)
        }

# Create fallback instance
fallback_document_extractor = FallbackDocumentExtractor()