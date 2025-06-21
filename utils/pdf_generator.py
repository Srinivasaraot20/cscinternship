import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import qrcode

# Register Arial font
pdfmetrics.registerFont(TTFont('Arial', 'assets/fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', 'assets/fonts/arialbd.ttf'))

def draw_text(c, text, x, y, font_name, font_size, alignment, max_width=None):
    c.setFont(font_name, font_size)
    text_width = c.stringWidth(text, font_name, font_size)
    if alignment == 'center':
        x = x - text_width / 2
    elif alignment == 'right':
        x = x - text_width
    if max_width and text_width > max_width:
        # Optionally shrink font size to fit
        font_size = font_size * max_width / text_width
        c.setFont(font_name, font_size)
        text_width = c.stringWidth(text, font_name, font_size)
        if alignment == 'center':
            x = x - text_width / 2
        elif alignment == 'right':
            x = x - text_width
    c.drawString(x, y, text)

def generate_certificate(student):
    """
    Generate certificate PDF using template's natural dimensions
    """
    try:
        # Create certificates directory if it doesn't exist
        os.makedirs('certificates', exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"certificate_{student.certificate_id}_{timestamp}.pdf"
        filepath = os.path.join('certificates', filename)
        
        # Load the template image
        template_path = os.path.join('attached_assets', 'temp_1749797940108.jpg')
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Certificate template not found at {template_path}")
        
        # Get template dimensions
        img = Image.open(template_path)
        img_width, img_height = img.size
        
        # Create PDF with template's natural dimensions
        c = canvas.Canvas(filepath, pagesize=(img_width, img_height))
        
        # Draw the background image at full size
        c.drawImage(template_path, 0, 0, width=img_width, height=img_height)
        
        # Set default font and color
        c.setFont("Arial", 25)
        c.setFillColor(colors.black)
        
        # Name field: X: 490px, Y: 410px (from top-left) - Centered
        c.setFont("Arial-Bold", 25)
        draw_text(c, student.student_name, 580, img_height - 410, "Arial-Bold", 25, 'center')

        # Location field (College Name): X: 230px, Y: 450px (from top-left)
        c.setFont("Arial", 25)
        c.drawString(230, img_height - 450, student.college_name)

        # Institution field (using College Name): X: 308px, Y: 498px (from top-left)
        c.drawString(308, img_height - 498, student.college_name)

        # Roll number field: X: 916px, Y: 498px (from top-left)
        if hasattr(student, 'roll_number') and student.roll_number:
            c.drawString(926, img_height - 498, student.roll_number)

        # Program field (Internship Name): X: 734px, Y: 548px (from top-left) - Centered
        draw_text(c, student.internship_name, 880, img_height - 548, "Arial", 25, 'center')

        # Start date field: X: 596px, Y: 630px (from top-left)
        c.drawString(596, img_height - 630, student.start_date.strftime('%B %d, %Y'))

        # End date field: X: 819px, Y: 630px (from top-left)
        c.drawString(819, img_height - 630, student.end_date.strftime('%B %d, %Y'))

        # Certificate ID field: X: 260px, Y: 160px (from bottom-left grid)
        c.setFont("Arial", 20)
        c.setFillColor(colors.red)
        c.drawString(305, 180, student.certificate_id)

        # Issue Date field: X: 200px, Y: 130px (from bottom-left grid)
        c.drawString(230, 140, datetime.now().strftime('%d-%m-%Y'))

        # Generate QR code (X:500, Y:120 from bottom-left grid)
        try:
            from flask import current_app
            with current_app.app_context():
                qr_data = f"{current_app.config['CERT_VERIFICATION_BASE_URL']}/qr/{student.certificate_id}"
        except Exception as e:
            current_app.logger.error(f"Error getting app context for QR URL in pdf_generator: {str(e)}. Falling back to default URL.")
            qr_data = f"https://certificate-verify.com/qr/{student.certificate_id}"

        qr = qrcode.QRCode(version=1, box_size=3, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code temporarily
        qr_temp_path = f"temp_qr_{student.certificate_id}.png"
        qr_img.save(qr_temp_path)

        # Add QR code to certificate
        c.drawInlineImage(qr_temp_path, 720, 120, width=80, height=80)

        # Clean up QR temp file
        try:
            os.remove(qr_temp_path)
        except:
            pass

        # Save the PDF
        c.save()
        
        # Verify the PDF was created successfully
        if not os.path.exists(filepath):
            raise Exception("Failed to create PDF file")
            
        return filepath

    except Exception as e:
        print(f"Error generating certificate: {str(e)}")
        # Clean up any temporary files
        try:
            if 'qr_temp_path' in locals():
                os.remove(qr_temp_path)
        except:
            pass
        raise e