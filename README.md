# 🏦 PromptPay QR Code Generator

เครื่องมือสร้าง QR Code สำหรับรับเงินผ่านระบบ PromptPay ของประเทศไทย

![Python](https://img.shields.io/badge/Python-3.11+-green)
![Flask](https://img.shields.io/badge/Flask-2.3+-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- 📱 รองรับเบอร์โทรศัพท์ (06, 08, 09) และเลขบัตรประชาชน 13 หลัก
- 💰 กำหนดจำนวนเงินที่ต้องการรับ
- 👤 เพิ่มชื่อผู้รับเงิน (ไม่บังคับ)
- ⬇️ ดาวน์โหลด QR Code เป็นไฟล์ PNG
- 📱 ใช้งานได้ทั้งมือถือและคอมพิวเตอร์

## 🚀 การติดตั้ง

```bash
# Clone repository
git clone https://github.com/yourusername/promptpay-qr-generator.git
cd promptpay-qr-generator

# สร้าง virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# หรือ source venv/bin/activate  # Mac/Linux

# ติดตั้ง dependencies
pip install -r requirements.txt

# รันแอป
python generate_qr.py
```

เปิดเบราว์เซอร์ไปที่: `http://localhost:5000`

## 📋 รูปแบบที่รองรับ

**เบอร์โทรศัพท์:**
- 06XXXXXXXX, 08XXXXXXXX, 09XXXXXXXX

**เลขบัตรประชาชน:**
- 13 หลัก (ต้องลงทะเบียน PromptPay แล้ว)

**จำนวนเงิน:**
- 0.01 - 999,999.99 บาท

## 🔧 API Usage

```bash
# สร้าง QR Code
curl -X POST http://localhost:5000/generate \
  -F "mobile=0812345678" \
  -F "amount=100.00" \
  -F "name=ทดสอบ" \
  --output qr_code.png

# ตรวจสอบเบอร์โทร
curl http://localhost:5000/validate/0812345678

# ทดสอบระบบ
curl http://localhost:5000/test
```

## ⚠️ ข้อควรระวัง

- เลขบัตรประชาชนต้องลงทะเบียน PromptPay ผ่านแอปธนาคารก่อน
- QR Code ใช้ได้กับแอปธนาคารไทยทุกธนาคาร
- ไม่เก็บข้อมูลส่วนบุคคลบนเซิร์ฟเวอร์

## 📄 License

MIT License - ดู [LICENSE](LICENSE) สำหรับรายละเอียด

---

Made with ❤️ for Thai FinTech Community
