from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

def generate_pdf_certificate(student_name, quiz_title, score_percentage, completion_date_str):
    """
    Generates a beautiful landscape PDF certificate using ReportLab.
    Returns the raw PDF bytes.
    """
    buffer = BytesIO()
    
    # Landscape orientation of standard Letter paper size
    width, height = landscape(letter)
    
    # Create canvas
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    
    # Draw double decorative border
    # Outer border (Purple)
    c.setStrokeColor(colors.HexColor('#7c3aed')) 
    c.setLineWidth(6)
    c.rect(25, 25, width - 50, height - 50)
    
    # Inner border (Teal)
    c.setStrokeColor(colors.HexColor('#14b8a6'))
    c.setLineWidth(1.5)
    c.rect(32, 32, width - 64, height - 64)
    
    # Background watermark / subtle accent (large light gold circle or crest)
    c.setFillColor(colors.HexColor('#faf5ff')) # Light lavender tint
    c.circle(width / 2.0, height / 2.0, 180, fill=True, stroke=False)
    
    # Draw header text
    c.setFont("Helvetica-Bold", 34)
    c.setFillColor(colors.HexColor('#1e1b4b')) # Deep Indigo
    c.drawCentredString(width / 2.0, height - 120, "CERTIFICATE OF ACHIEVEMENT")
    
    # Subheader
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor('#4b5563')) # Muted Gray
    c.drawCentredString(width / 2.0, height - 160, "This is proudly presented to")
    
    # Student Name
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(colors.HexColor('#7c3aed')) # Vibrant Purple
    c.drawCentredString(width / 2.0, height - 210, student_name)
    
    # Achievement Description
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor('#4b5563'))
    c.drawCentredString(
        width / 2.0, 
        height - 260, 
        "for successfully demonstrating expertise and passing the examination"
    )
    
    # Quiz Title
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.HexColor('#0f172a')) # Dark Slate
    c.drawCentredString(width / 2.0, height - 290, quiz_title)
    
    # Score details
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor('#6b7280'))
    c.drawCentredString(
        width / 2.0, 
        height - 330, 
        f"with a record score of {score_percentage}% on {completion_date_str}"
    )
    
    # Signature line
    c.setStrokeColor(colors.HexColor('#cbd5e1'))
    c.setLineWidth(1.5)
    c.line(width / 2.0 - 120, 100, width / 2.0 + 120, 100)
    
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(colors.HexColor('#4b5563'))
    c.drawCentredString(width / 2.0, 80, "QuizVerse Certification Authority")
    
    # Finish page
    c.showPage()
    c.save()
    
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data
