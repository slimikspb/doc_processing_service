# Office Document Support Enhancement

This document details the new Microsoft Office document processing capabilities added to the document processing service.

## 📊 New Supported Formats

### Microsoft Excel
- **.xlsx** - Modern Excel format (Excel 2007+)
- **.xls** - Legacy Excel format (Excel 97-2003)

### Microsoft PowerPoint  
- **.pptx** - Modern PowerPoint format (PowerPoint 2007+)
- **.ppt** - Legacy PowerPoint format (PowerPoint 97-2003) *[Limited support]*

## 🔧 Implementation Details

### Python Libraries Used

| Format | Library | Purpose | Features |
|--------|---------|---------|----------|
| .xlsx | openpyxl | Excel 2007+ processing | Full text extraction, metadata, multi-sheet support |
| .xls | xlrd | Legacy Excel processing | Text extraction, sheet information |
| .pptx | python-pptx | PowerPoint 2007+ processing | Text extraction, slide metadata, table support |
| .ppt | oletools | Legacy PowerPoint processing | Basic text extraction (limited) |

### Enhanced Features

**Excel Processing:**
- Multi-sheet text extraction
- Cell data preservation with pipe delimiters
- Sheet metadata (row/column counts, sheet names)
- Support for formulas and calculated values

**PowerPoint Processing:**
- Multi-slide text extraction
- Shape and text box content
- Table data extraction
- Slide metadata (counts, shape information)

## 📋 API Response Format

The enhanced document processing now returns additional metadata:

```json
{
  "filename": "document.xlsx",
  "text": "Sheet: Sales Data\nProduct | Quantity | Price\nWidget A | 100 | 19.99\n\nSheet: Documentation\nProduct Documentation\nThis spreadsheet contains...",
  "status": "completed",
  "extraction_method": "office",
  "metadata": {
    "sheets": ["Sales Data", "Documentation"],
    "sheet_count": 2,
    "sheet_data": {
      "Sales Data": {
        "rows": 3,
        "max_column": 3,
        "max_row": 3
      }
    }
  },
  "file_info": {
    "filename": "document.xlsx",
    "extension": ".xlsx",
    "size_bytes": 8456,
    "size_mb": 0.01,
    "processor_type": "office",
    "supported": true
  }
}
```

## 🔍 Text Extraction Details

### Excel Text Format
```
Sheet: [Sheet Name]
[Cell A1] | [Cell B1] | [Cell C1]
[Cell A2] | [Cell B2] | [Cell C2]

Sheet: [Next Sheet Name]
[Content continues...]
```

### PowerPoint Text Format
```
Slide 1:
[Title Text]
[Body Text]
[Additional Shape Text]

Slide 2:
[Title Text]
[Bullet Point 1]
[Bullet Point 2]
```

## 🌐 New API Endpoints

### `/formats` - Get Supported Formats
Returns comprehensive list of all supported document formats.

**Response:**
```json
{
  "supported_formats": {
    "office_documents": [".xlsx", ".xls", ".pptx", ".ppt"],
    "textract_documents": [".doc", ".docx", ".pdf", "..."],
    "all_supported": ["all formats combined"]
  },
  "office_documents": {
    "formats": [".xlsx", ".xls", ".pptx", ".ppt"],
    "description": "Microsoft Office documents (Excel, PowerPoint)",
    "features": ["Text extraction", "Metadata extraction", "Multi-sheet/slide support"]
  },
  "total_supported": 15
}
```

## 🧪 Testing

### Test Suite: `test_office_documents.py`

**Features:**
- Automated test file creation for Excel and PowerPoint
- Content validation testing
- Metadata extraction verification
- Format support endpoint testing

**Usage:**
```bash
# Test all Office formats
python test_office_documents.py --url http://localhost:5001 --api-key your_key

# Test specific formats
python test_office_documents.py --test excel
python test_office_documents.py --test powerpoint
python test_office_documents.py --test formats
```

### Sample Test Files Created

**Excel Test File:**
- Sheet 1: "Sales Data" with product inventory
- Sheet 2: "Documentation" with descriptive text
- Tests multi-sheet extraction and data formatting

**PowerPoint Test File:**
- Slide 1: Title slide with heading and subtitle
- Slide 2: Bullet points with key achievements
- Slide 3: Financial summary with formatted content

## ⚡ Performance Considerations

### Processing Time
- **Excel**: ~2-5 seconds for typical spreadsheets
- **PowerPoint**: ~3-7 seconds for presentations with multiple slides
- **Large Files**: May take longer, protected by circuit breaker

### Memory Usage
- Office document processing uses more memory than text-based formats
- Container memory limits set to 1GB to handle large files
- Automatic cleanup prevents memory leaks

### File Size Limits
- Default limit: **16MB** (configurable via `MAX_CONTENT_LENGTH`)
- Recommended for Office documents: Consider increasing to 32MB for large spreadsheets/presentations

## 🚨 Error Handling

### Common Error Scenarios

**Missing Dependencies:**
```json
{
  "error": "Required libraries for Office document processing are not installed"
}
```

**Corrupted Files:**
```json
{
  "error": "File appears to be corrupted or not a valid Office document"
}
```

**Unsupported Format:**
```json
{
  "error": "Unsupported file format: .xyz"
}
```

### Circuit Breaker Protection
- Office document processing is protected by the same circuit breaker as textract
- Opens after 3 consecutive failures
- Automatic recovery after 2 minutes

## 🔄 Backward Compatibility

- All existing textract-supported formats continue to work unchanged
- Existing API responses maintain same structure with additional metadata
- No breaking changes to existing endpoints

## 📈 Monitoring Integration

### New Metrics
- Office document processing success/failure rates
- Processing time breakdowns by format type
- Memory usage patterns for different Office formats

### Health Checks
Office document processors are monitored via:
- Library availability checks
- Sample file processing validation
- Memory usage tracking

## 🎯 Future Enhancements

**Potential Additions:**
- Microsoft Word (.docx) enhanced processing (beyond textract)
- CSV file structured processing
- Office 365 document format support
- Image extraction from Office documents
- Chart and graph text extraction

**Performance Optimizations:**
- Streaming processing for large files
- Parallel processing for multi-sheet/slide documents
- Caching for frequently processed templates

---

The Office document support enhancement significantly expands the service's capabilities while maintaining reliability and performance standards established by the existing architecture.