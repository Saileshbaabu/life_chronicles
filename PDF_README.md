# 🚀 **PDF Generation System for LifeChronicles**

## **Overview**
A comprehensive server-side PDF generator for single-photo articles with support for English and Tamil languages, multiple page sizes, and professional layout.

## **✨ Features**

### **📱 Layout & Design**
- **Portrait orientation** with professional typography
- **Header**: Brand, date, section label with accent line
- **Title & Subtitle**: Bold title, italic subtitle with proper spacing
- **Body**: Single column, justified text with markdown support
- **Tags**: Horizontal chip-style tags with rounded backgrounds
- **Image**: Full-width image at bottom with caption
- **Footer**: Share URL/QR code + page number

### **🌍 Multilingual Support**
- **English**: Playfair Display fonts (with fallbacks)
- **Tamil**: Noto Serif Tamil font (with fallbacks)
- **Automatic language detection** and font selection
- **Proper text rendering** for both scripts

### **📄 Page Sizes**
- **Letter**: 612 × 792 points (default)
- **A4**: 595 × 842 points
- **Query parameter**: `?size=a4|letter`

### **🎨 Visual Design**
- **Colors**: Professional color scheme with accent red
- **Typography**: Serif fonts for readability
- **Spacing**: Consistent spacing system (6pt, 10pt, 16pt, 24pt)
- **Margins**: 0.75" on all sides

## **🏗️ Architecture**

### **Core Components**
1. **`PDFBuilder`**: Main PDF generation service
2. **`ArticlePDFView`**: Django REST API endpoint
3. **`md_to_paragraphs`**: Markdown to ReportLab converter
4. **Font management**: Custom font registration with fallbacks

### **File Structure**
```
image_analysis/
├── services/
│   └── pdf_builder.py          # Main PDF generation logic
├── utils/
│   └── md_to_paragraphs.py     # Markdown conversion utility
├── views_pdf.py                 # Django API views
├── static/
│   └── fonts/                   # Custom fonts (TTF files)
└── urls.py                      # URL routing
```

## **🚀 API Endpoints**

### **Generate PDF**
```
GET /api/stories/{id}/pdf/
GET /api/stories/{id}/pdf/?size=a4
GET /api/stories/{id}/pdf/?size=letter
GET /api/stories/{id}/pdf/?inline=1
```

### **Query Parameters**
- `size`: `a4` or `letter` (default: `letter`)
- `inline`: `1` to view in browser, otherwise download

### **Response**
- **Success**: PDF file with proper headers
- **Error**: JSON error response with details

## **📊 Input Data Schema**

```json
{
  "brand": "YourBrand",
  "dateline": "Thursday, 14 August 2025",
  "section": "Photo Feature",
  "title": "Article Title",
  "subtitle": "Article Subtitle",
  "body": "Article body with **bold** and *italic* text",
  "image_url": "https://example.com/image.jpg",
  "image_alt": "Image description",
  "image_caption": "Image caption text",
  "tags": ["tag1", "tag2", "tag3"],
  "lang": "en",
  "share_url": "https://yourapp.com/share/abc123"
}
```

## **🔧 Technical Implementation**

### **Dependencies**
```python
reportlab>=4.0.0      # PDF generation
requests>=2.31.0      # Image downloading
qrcode[pil]>=7.4.0    # QR code generation
Pillow>=10.4.0        # Image processing
```

### **Font System**
- **Custom fonts**: TTF files in `static/fonts/`
- **Fallback fonts**: System fonts (Helvetica, Times)
- **Automatic detection**: Font availability checking
- **Language-specific**: Tamil vs English font selection

### **Image Handling**
- **Download**: HTTP requests with timeout
- **Processing**: Aspect ratio preservation
- **Fallback**: Placeholder for failed downloads
- **Optimization**: Memory-efficient streaming

### **Markdown Support**
- **Bold**: `**text**` → `<b>text</b>`
- **Italic**: `*text*` → `<i>text</i>`
- **Paragraphs**: Double newlines
- **HTML escaping**: Security-first approach

## **🎯 Usage Examples**

### **1. Generate English PDF (Letter)**
```bash
curl -X GET "http://127.0.0.1:8000/api/stories/123/pdf/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o article.pdf
```

### **2. Generate Tamil PDF (A4)**
```bash
curl -X GET "http://127.0.0.1:8000/api/stories/123/pdf/?size=a4" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o article_tamil.pdf
```

### **3. View PDF in Browser**
```bash
curl -X GET "http://127.0.0.1:8000/api/stories/123/pdf/?inline=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **4. Test PDF Generation**
```bash
python test_pdf_generation.py
```

## **🔍 Testing**

### **Unit Tests**
- **Font registration**: Custom font availability
- **Language support**: English vs Tamil rendering
- **Page sizes**: Letter vs A4 dimensions
- **Error handling**: Missing data, failed images

### **Integration Tests**
- **API endpoints**: Django view functionality
- **PDF generation**: Complete workflow testing
- **Image handling**: Download and processing
- **Markdown conversion**: Text formatting

## **🚨 Error Handling**

### **Common Issues**
1. **Missing fonts**: Automatic fallback to system fonts
2. **Image failures**: Placeholder with error message
3. **Invalid data**: JSON validation with clear errors
4. **Network timeouts**: Configurable timeout settings

### **Fallback Strategy**
- **Fonts**: System fonts when custom fonts unavailable
- **Images**: Placeholder boxes for failed downloads
- **Languages**: Default to English if language unclear
- **Page sizes**: Default to Letter if size invalid

## **🔒 Security & Performance**

### **Security Features**
- **Authentication**: Required for all PDF endpoints
- **Input validation**: Strict data validation
- **HTML escaping**: XSS prevention in markdown
- **File size limits**: Configurable image size limits

### **Performance Optimizations**
- **Font caching**: Registered fonts cached in memory
- **Image streaming**: Efficient image processing
- **Memory management**: Proper cleanup of resources
- **Async support**: Non-blocking PDF generation

## **📈 Future Enhancements**

### **Planned Features**
- **Multiple layouts**: Magazine, blog, social media styles
- **Custom themes**: User-defined color schemes
- **Batch processing**: Multiple articles at once
- **Watermarking**: Brand protection features
- **Compression**: Optimized file sizes

### **Integration Opportunities**
- **Email**: PDF attachments in notifications
- **Social media**: Optimized sharing formats
- **Print services**: Print-ready PDFs
- **Analytics**: PDF generation metrics

## **🛠️ Development Setup**

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Add Custom Fonts**
```bash
# Download fonts to static/fonts/
# - PlayfairDisplay-Regular.ttf
# - PlayfairDisplay-Bold.ttf
# - NotoSerifTamil-Regular.ttf
```

### **3. Test Generation**
```bash
python test_pdf_generation.py
```

### **4. Start Server**
```bash
python manage.py runserver
```

### **5. Test API**
```bash
curl "http://127.0.0.1:8000/api/stories/test123/pdf/"
```

## **🎉 Success Metrics**

- ✅ **PDF Generation**: Working for both languages
- ✅ **Page Sizes**: Letter and A4 support
- ✅ **Font Fallbacks**: Graceful degradation
- ✅ **Image Handling**: Download and processing
- ✅ **Markdown Support**: Bold, italic, paragraphs
- ✅ **API Integration**: Django REST endpoints
- ✅ **Error Handling**: Comprehensive fallbacks

---

**Built with ❤️ for LifeChronicles - Transform your images into compelling stories!**
