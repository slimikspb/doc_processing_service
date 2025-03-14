# Document Converter Service

A microservice that converts DOC, DOCX, and other document formats to plain text JSON.
This service is designed to work alongside n8n for document processing workflows.

## Features

- Converts various document formats to plain text
- Exposes a simple REST API
- Returns extracted text in JSON format
- Containerized for easy deployment
- Includes n8n integration

## Supported Document Formats

- Microsoft Word (.doc, .docx)
- OpenDocument Text (.odt)
- Rich Text Format (.rtf)

## Requirements

- Docker
- Docker Compose

## Setup and Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/document-converter-service.git
   cd document-converter-service
   ```

2. Start the services:
   ```
   docker-compose up -d
   ```

3. The services will be available at:
   - Document Converter API: http://localhost:5000
   - n8n: http://localhost:5678

## API Usage

### Convert a document to text

**Endpoint:** `POST /convert`

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `document`: The document file to convert

**Response:**
```json
{
  "filename": "example.docx",
  "text": "Extracted text content from the document..."
}
```

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok"
}
```

## Integration with n8n

To use this service with n8n:

1. In n8n, add an HTTP Request node
2. Configure it with the following settings:
   - Method: POST
   - URL: http://doc-converter:5000/convert
   - Binary Data: true
   - Set the document file as the binary input

## Building and Customizing

To customize the service:

1. Modify `app.py` as needed
2. Update the Docker image:
   ```
   docker-compose build
   ```

3. Restart the services:
   ```
   docker-compose down
   docker-compose up -d
   ```

## Troubleshooting

- If you encounter issues with specific document formats, make sure all necessary system dependencies are installed in the Dockerfile.
- For large documents, you may need to increase the `MAX_CONTENT_LENGTH` environment variable in the docker-compose.yml file.

## License

MIT