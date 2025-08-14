"""
Enhanced document text extraction supporting multiple formats including Office documents
"""
import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any
import textract
from office_processor import office_processor
from circuit_breaker import with_textract_circuit_breaker

logger = logging.getLogger(__name__)

class DocumentExtractor:
    """Enhanced document extractor supporting multiple formats"""
    
    def __init__(self):
        # Office formats supported by our office processor
        self.office_formats = {'.xlsx', '.xls', '.pptx', '.ppt'}
        
        # Formats supported by textract
        self.textract_formats = {
            '.doc', '.docx', '.odt', '.rtf', '.pdf', '.txt', 
            '.png', '.jpg', '.jpeg', '.tiff', '.gif'
        }
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information and determine processing method"""
        file_ext = Path(file_path).suffix.lower()
        file_size = os.path.getsize(file_path)
        
        processor_type = None
        if file_ext in self.office_formats:
            processor_type = 'office'
        elif file_ext in self.textract_formats:
            processor_type = 'textract'
        else:
            processor_type = 'unsupported'
        
        return {
            'filename': Path(file_path).name,
            'extension': file_ext,
            'size_bytes': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'processor_type': processor_type,
            'supported': processor_type != 'unsupported'
        }
    
    def extract_text(self, file_path: str, timeout: int = 60) -> Dict[str, Any]:
        """Extract text from document using appropriate processor"""
        file_info = self.get_file_info(file_path)
        
        if not file_info['supported']:
            raise ValueError(f"Unsupported file format: {file_info['extension']}")
        
        try:
            if file_info['processor_type'] == 'office':
                result = self._extract_office_document(file_path)
            else:
                result = self._extract_textract_document(file_path, timeout)
            
            # Combine file info with extraction result
            return {
                **result,
                'file_info': file_info,
                'extraction_method': file_info['processor_type']
            }
            
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {str(e)}")
            raise Exception(f"Failed to extract text: {str(e)}")
    
    def _extract_office_document(self, file_path: str) -> Dict[str, Any]:
        """Extract text from Office documents (Excel, PowerPoint)"""
        try:
            result = office_processor.extract_text(file_path)
            
            return {
                'text': result['text'],
                'metadata': result.get('metadata', {}),
                'format_details': result.get('format', 'unknown'),
                'processor': 'office_processor'
            }
            
        except Exception as e:
            # Log the specific error but provide a user-friendly message
            logger.error(f"Office document extraction error: {str(e)}")
            
            # Try to provide more specific error messages
            if "library not available" in str(e):
                raise Exception("Required libraries for Office document processing are not installed")
            elif "Invalid" in str(e):
                raise Exception("File appears to be corrupted or not a valid Office document")
            else:
                raise Exception(f"Office document processing failed: {str(e)}")
    
    @with_textract_circuit_breaker
    def _extract_textract_document(self, file_path: str, timeout: int = 60) -> Dict[str, Any]:
        """Extract text using textract with circuit breaker protection"""
        try:
            # First try subprocess approach with timeout
            result = subprocess.run(
                ['python', '-c', f"import textract; print(textract.process('{file_path}').decode('utf-8', errors='replace'))"],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                text = result.stdout.strip()
            else:
                # Fallback to direct textract
                logger.warning("Subprocess textract failed, trying direct approach")
                text = textract.process(file_path).decode('utf-8', errors='replace')
            
            return {
                'text': text,
                'metadata': {
                    'extraction_method': 'textract',
                    'subprocess_used': result.returncode == 0 if 'result' in locals() else False
                },
                'processor': 'textract'
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f'Textract extraction timed out for {file_path}')
            raise Exception('Document processing timed out')
        except Exception as e:
            logger.error(f'Textract extraction failed: {str(e)}')
            
            # Try to provide more specific error messages
            if "textract" in str(e).lower():
                raise Exception("Textract processing failed - file may be corrupted or unsupported")
            else:
                raise Exception(f"Text extraction failed: {str(e)}")
    
    def get_supported_formats(self) -> Dict[str, list]:
        """Get list of all supported formats"""
        return {
            'office_documents': list(self.office_formats),
            'textract_documents': list(self.textract_formats),
            'all_supported': list(self.office_formats | self.textract_formats)
        }

# Global instance
document_extractor = DocumentExtractor()