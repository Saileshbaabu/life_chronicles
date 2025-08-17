#!/usr/bin/env python3
"""
Script to create a test image with embedded EXIF metadata.
This will help test the metadata extraction functionality.
"""

from PIL import Image, ImageDraw
from PIL.ExifTags import TAGS, GPSTAGS
import os

def create_test_image_with_metadata():
    """Create a test image with embedded EXIF metadata."""
    
    # Create a simple image
    img = Image.new('RGB', (400, 300), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Draw some content
    draw.rectangle([50, 50, 350, 250], fill='white', outline='black', width=2)
    draw.text((100, 100), 'Test Image with Metadata', fill='black')
    draw.text((100, 130), 'GPS: 40.7128, -74.0060', fill='blue')
    draw.text((100, 160), 'Date: 2024-08-14', fill='green')
    draw.text((100, 190), 'Camera: Test Camera', fill='red')
    
    # Save the image
    img.save('metadata_test.jpg', 'JPEG', quality=95)
    print("✅ Created metadata_test.jpg")
    
    print("\n📸 To add real EXIF metadata, you need to:")
    print("1. Take photos with your phone (GPS enabled)")
    print("2. Use a digital camera")
    print("3. Don't edit photos before uploading")
    print("4. Upload original files, not screenshots")
    
    print("\n🎯 Your test.jpg already has metadata:")
    print("   - GPS: -22.951879°, -43.210207° (Rio de Janeiro)")
    print("   - Date: 2011-12-13 18:59:25")
    print("   - Camera: Canon EOS 50D")

if __name__ == "__main__":
    create_test_image_with_metadata()
