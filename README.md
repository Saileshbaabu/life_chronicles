# Life Chronicles - Image-to-Article Pipeline

This Django project implements Step 1 of an image-to-article pipeline that analyzes uploaded images using AI and extracts metadata.

## Features

- **Image Upload**: Accepts image files via multipart/form-data
- **EXIF Extraction**: Extracts GPS coordinates, datetime, and camera model information
- **AI Analysis**: Uses OpenAI GPT-4o to generate:
  - Descriptive captions (1-2 sentences)
  - List of detected objects
  - OCR text extraction
- **GPS Conversion**: Converts EXIF GPS coordinates to decimal degrees
- **Temporary Storage**: Stores images in `/tmp` directory (configurable for S3 later)

## API Endpoint

### POST /api/analyze-image

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form with `image` field containing the image file

**Response:**
```json
{
  "img_caption": "A scenic mountain landscape with snow-capped peaks",
  "objects": ["mountain", "snow", "sky", "trees", "rocks"],
  "ocr_text": "Welcome to Mount Everest",
  "gps": {
    "lat": 27.9881,
    "lon": 86.9250
  },
  "datetime": "2024:01:15 10:30:45",
  "camera_model": "iPhone 15 Pro"
}
```

**Error Response:**
```json
{
  "error": "Error message here",
  "details": "Additional error details if available"
}
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `env.example` to `.env` and configure:

```bash
cp env.example .env
```

Edit `.env` with your actual values:
```bash
SECRET_KEY=your-actual-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
OPENAI_API_KEY=your-openai-api-key
```

### 3. Database Setup

```bash
python manage.py migrate
```

### 4. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/analyze-image/`

## Testing the API

### Using curl

```bash
curl -X POST \
  http://localhost:8000/api/analyze-image/ \
  -H "Content-Type: multipart/form-data" \
  -F "image=@/path/to/your/image.jpg"
```

### Using Python requests

```python
import requests

url = "http://localhost:8000/api/analyze-image/"
files = {"image": open("image.jpg", "rb")}

response = requests.post(url, files=files)
print(response.json())
```

## Project Structure

```
lifechronicles/
├── lifechronicles/          # Main Django project
│   ├── __init__.py
│   ├── settings.py          # Django settings
│   ├── urls.py             # Main URL configuration
│   ├── wsgi.py             # WSGI configuration
│   └── asgi.py             # ASGI configuration
├── image_analysis/          # Image analysis app
│   ├── __init__.py
│   ├── apps.py             # App configuration
│   ├── urls.py             # App URL configuration
│   ├── views.py            # API views
│   ├── serializers.py      # Request/response serializers
│   ├── utils.py            # EXIF extraction utilities
│   └── ai_service.py       # OpenAI AI service
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
├── env.example            # Environment variables template
└── README.md              # This file
```

## Dependencies

- **Django 4.2.7**: Web framework
- **Django REST Framework 3.14.0**: API framework
- **Pillow 10.1.0**: Image processing and EXIF extraction
- **OpenAI 1.3.7**: AI image analysis
- **python-decouple 3.8**: Environment configuration

## Error Handling

The API gracefully handles:
- Missing EXIF data (returns `null` for missing fields)
- Missing GPS coordinates (returns `null` for GPS field)
- AI analysis failures (returns error response)
- Invalid image uploads (returns validation errors)
- Missing OpenAI API key (returns configuration error)

## Future Enhancements

- S3 integration for image storage
- Image caching and optimization
- Batch image processing
- Additional AI models support
- User authentication and rate limiting
- Image metadata database storage

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**: Ensure your `.env` file contains a valid `OPENAI_API_KEY`
2. **Permission Denied**: Ensure the `/tmp` directory is writable
3. **Image Format Error**: Ensure uploaded files are valid image formats (JPEG, PNG, etc.)
4. **Memory Issues**: Large images may cause memory issues; consider image resizing

### Logs

Check Django logs for detailed error information:
```bash
python manage.py runserver --verbosity=2
```
