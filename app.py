from flask import Flask, request, send_file, render_template_string, jsonify
import qrcode
from io import BytesIO
import base64
import os

app = Flask(__name__)

# เนื้อหาเดิมของคุณ (คัดลอกทั้งหมดจาก generate_qr.py)
# ... (ใส่โค้ดทั้งหมดจากไฟล์เดิม) ...

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)