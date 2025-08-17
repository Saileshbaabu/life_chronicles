"""
Markdown to ReportLab Paragraphs converter.
Supports basic markdown: **bold**, *italic*, and paragraphs.
"""
import re
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def convert_markdown_to_paragraphs(markdown_text, style_name='Normal', font_name='Helvetica', font_size=11):
    """
    Convert markdown text to a list of ReportLab Paragraphs.
    
    Args:
        markdown_text (str): Markdown text to convert
        style_name (str): Base style name to use
        font_name (str): Font family name
        font_size (int): Base font size
    
    Returns:
        list: List of ReportLab Paragraph objects
    """
    if not markdown_text:
        return []
    
    # Get base styles
    styles = getSampleStyleSheet()
    base_style = styles[style_name]
    
    # Create custom style for this font
    custom_style = ParagraphStyle(
        f'{style_name}_{font_name}',
        parent=base_style,
        fontName=font_name,
        fontSize=font_size,
        alignment=4,  # Justified
        spaceAfter=6,  # 6pt space after paragraphs
        leading=font_size * 1.35,  # 1.35 line height
    )
    
    # Split into paragraphs (double newlines)
    paragraphs = markdown_text.split('\n\n')
    
    result = []
    for para in paragraphs:
        if not para.strip():
            continue
            
        # Convert markdown to HTML
        html = _convert_markdown_inline(para.strip())
        
        # Create paragraph
        paragraph = Paragraph(html, custom_style)
        result.append(paragraph)
    
    return result


def _convert_markdown_inline(text):
    """
    Convert inline markdown to HTML.
    Supports: **bold**, *italic*
    """
    # Escape HTML characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # Convert **bold** to <b>bold</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # Convert *italic* to <i>italic</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    
    # Convert single newlines to <br/>
    text = text.replace('\n', '<br/>')
    
    return text


def create_tamil_style(base_style_name='Normal', font_size=11):
    """
    Create a style optimized for Tamil text rendering.
    
    Args:
        base_style_name (str): Base style name
        font_size (int): Font size
    
    Returns:
        ParagraphStyle: Custom style for Tamil text
    """
    styles = getSampleStyleSheet()
    base_style = styles[base_style_name]
    
    return ParagraphStyle(
        f'{base_style_name}_Tamil',
        parent=base_style,
        fontName='NotoSerifTamil',  # Tamil font
        fontSize=font_size,
        alignment=4,  # Justified
        spaceAfter=6,
        leading=font_size * 1.35,
    )
