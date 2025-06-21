import qrcode
import os
from io import BytesIO
from PIL import Image
from flask import current_app, url_for

def generate_qr_code(certificate_id, base_url=None):
    """
    Generate QR code for certificate verification
    """
    try:
        # Create QR code data
        if base_url is None:
            with current_app.app_context():
                # Use the configured base URL
                verification_url = f"{current_app.config['CERT_VERIFICATION_BASE_URL']}/qr/{certificate_id}"
        else:
            verification_url = f"{base_url}/qr/{certificate_id}"

        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,  # Controls the size of the QR Code
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # About 7% or less errors can be corrected
            box_size=10,  # Controls how many pixels each "box" of the QR code is
            border=4,  # Controls how many boxes thick the border should be
        )

        # Add data to QR code
        qr.add_data(verification_url)
        qr.make(fit=True)

        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Create directory if it doesn't exist
        qr_dir = os.path.join(current_app.static_folder, 'qr_codes')
        os.makedirs(qr_dir, exist_ok=True)

        # Save QR code image
        qr_filename = f"qr_{certificate_id}.png"
        qr_path = os.path.join(qr_dir, qr_filename)
        qr_img.save(qr_path)

        return qr_path

    except Exception as e:
        current_app.logger.error(f"Error generating QR code: {str(e)}")
        return None

def generate_qr_code_with_logo(certificate_id, logo_path=None, base_url=None):
    """
    Generate QR code with embedded logo
    """
    try:
        # Create QR code data
        from flask import url_for
        if base_url is None:
            with current_app.app_context():
                verification_url = f"{current_app.config['CERT_VERIFICATION_BASE_URL']}/qr/{certificate_id}"
        else:
            verification_url = f"{base_url}/qr/{certificate_id}"

        # Create QR code instance with higher error correction for logo
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction for logo
            box_size=10,
            border=4,
        )

        # Add data to QR code
        qr.add_data(verification_url)
        qr.make(fit=True)

        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

        # Add logo if provided
        if logo_path and os.path.exists(logo_path):
            logo = Image.open(logo_path)

            # Calculate logo size (should be about 10% of QR code)
            qr_width, qr_height = qr_img.size
            logo_size = min(qr_width, qr_height) // 10

            # Resize logo
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

            # Calculate position to center logo
            logo_pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)

            # Paste logo onto QR code
            qr_img.paste(logo, logo_pos)

        # Create directory if it doesn't exist
        qr_dir = 'static/qr_codes'
        os.makedirs(qr_dir, exist_ok=True)

        # Save QR code image
        qr_filename = f"qr_{certificate_id}.png"
        qr_path = os.path.join(qr_dir, qr_filename)
        qr_img.save(qr_path)

        return qr_path

    except Exception as e:
        print(f"Error generating QR code with logo: {str(e)}")
        return generate_qr_code(certificate_id, base_url)  # Fallback to simple QR code

def get_qr_code_data(certificate_id):
    """
    Get QR code data for embedding in other applications
    """
    from flask import url_for
    verification_url = url_for('qr_verify', certificate_id=certificate_id, _external=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(verification_url)
    qr.make(fit=True)

    # Return as BytesIO for embedding
    img_buffer = BytesIO()
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    return img_buffer

def verify_qr_code_data(qr_data):
    """
    Verify if QR code data is valid certificate verification URL
    """
    try:
        if not qr_data.startswith('https://certificate-verify.com/qr/'):
            return False, "Invalid QR code format"

        certificate_id = qr_data.split('/')[-1]

        if len(certificate_id) < 5:
            return False, "Invalid certificate ID in QR code"

        return True, certificate_id

    except Exception as e:
        return False, f"Error verifying QR code: {str(e)}"
