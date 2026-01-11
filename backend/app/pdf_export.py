import logging
import io
from typing import Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import re
from html.parser import HTMLParser

logger = logging.getLogger(__name__)


class HTMLStripper(HTMLParser):
    """Simple HTML to plain text converter."""
    
    def __init__(self):
        super().__init__()
        self.text = []
    
    def handle_data(self, data):
        self.text.append(data)
    
    def get_text(self):
        return ''.join(self.text)


def strip_html(html: str) -> str:
    """Convert HTML to plain text."""
    stripper = HTMLStripper()
    stripper.feed(html)
    return stripper.get_text()


async def generate_pdf(content: str, content_type: str) -> bytes:
    """
    Generate PDF from content (backend rendering).
    Uses ReportLab for reliable PDF generation.
    """
    try:
        # Convert markdown to plain text for PDF
        # Simple markdown to text conversion (no markdown library needed)
        text_content = markdown_to_text(content)
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Build PDF content
        styles = getSampleStyleSheet()
        story = []
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#0ea5e9',
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        
        # Header style
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=16,
            textColor='#075985',
            spaceAfter=12,
            spaceBefore=20,
        )
        
        # Paragraph style
        para_style = ParagraphStyle(
            'CustomPara',
            parent=styles['BodyText'],
            fontSize=11,
            leading=14,
            spaceAfter=12,
            alignment=TA_LEFT,
        )
        
        # Parse content into sections
        lines = text_content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.2 * inch))
                continue
            
            # Detect headers (H1, H2, H3)
            if line.startswith('# '):
                # H1 - Title
                title = line[2:].strip()
                story.append(Paragraph(title, title_style))
                story.append(Spacer(1, 0.3 * inch))
            elif line.startswith('## '):
                # H2 - Section header
                header = line[3:].strip()
                story.append(Paragraph(header, header_style))
                story.append(Spacer(1, 0.2 * inch))
            elif line.startswith('### '):
                # H3 - Subsection header
                subheader = line[4:].strip()
                story.append(Paragraph(subheader, styles['Heading3']))
                story.append(Spacer(1, 0.15 * inch))
            else:
                # Regular paragraph
                # Escape HTML characters for ReportLab
                para_text = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(para_text, para_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info(f"PDF generated successfully: {len(pdf_bytes)} bytes for {content_type}")
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"PDF generation error: {e}", exc_info=True)
        raise Exception(f"Failed to generate PDF: {str(e)}")


def markdown_to_text(markdown_text: str) -> str:
    """Convert markdown to plain text suitable for PDF."""
    # Remove markdown syntax
    text = markdown_text
    
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove images
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
    
    # Keep headers (will be handled separately)
    # Remove bold/italic but keep text
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove horizontal rules
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()
