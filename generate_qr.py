from flask import Flask, request, send_file, render_template_string, jsonify
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)

def crc16_ccitt(data):
    """Calculate CRC16-CCITT checksum for PromptPay"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

def format_mobile(mobile):
    """Format mobile number for PromptPay"""
    mobile = ''.join(filter(str.isdigit, mobile))
    
    # รองรับเบอร์โทรศัพท์ไทยทุกรูปแบบ
    if len(mobile) == 10 and mobile[0] == '0':
        # เบอร์ที่ขึ้นต้นด้วย 0 (06, 08, 09, etc.)
        return '0066' + mobile[1:]
    elif len(mobile) == 9 and mobile[0] in ['6', '8', '9']:
        # เบอร์ที่ไม่มี 0 นำหน้า
        return '0066' + mobile
    elif len(mobile) == 13:
        # เลขบัตรประชาชน 13 หลัก - ใช้รูปแบบพิเศษสำหรับ PromptPay
        return mobile
    else:
        raise ValueError('รูปแบบเบอร์โทรศัพท์ไม่ถูกต้อง (ต้องเป็นเบอร์โทรศัพท์ 10 หลัก หรือเลขบัตรประชาชน 13 หลัก)')

def generate_promptpay_payload(mobile, amount, name=""):
    """Generate PromptPay QR payload"""
    mobile_clean = ''.join(filter(str.isdigit, mobile))
    amount = float(amount)
    amount_str = f"{amount:.2f}"
    
    # Build EMVCo payload according to PromptPay standard
    payload = ""
    
    # Payload Format Indicator
    payload += "000201"
    
    # Point of Initiation Method
    payload += "010212"
    
    # Merchant Account Information (Tag 29)
    if len(mobile_clean) == 13:
        # เลขบัตรประชาชน - ใช้ Tag 02 แทน Tag 01
        merchant_info = "0016A000000677010111"  # PromptPay AID
        merchant_info += f"02{len(mobile_clean):02d}{mobile_clean}"  # National ID
    else:
        # เบอร์โทรศัพท์ - ใช้ Tag 01
        formatted_mobile = format_mobile(mobile_clean)
        merchant_info = "0016A000000677010111"  # PromptPay AID
        merchant_info += f"01{len(formatted_mobile):02d}{formatted_mobile}"  # Mobile number
    
    payload += f"29{len(merchant_info):02d}{merchant_info}"
    
    # Country Code
    payload += "5802TH"
    
    # Transaction Currency
    payload += "5303764"  # THB
    
    # Transaction Amount
    payload += f"54{len(amount_str):02d}{amount_str}"
    
    # Merchant Name (if provided)
    if name:
        name = name[:25]  # Limit to 25 characters
        payload += f"59{len(name):02d}{name}"
    
    # Additional Data Field (Tag 62)
    additional_data = ""
    if additional_data:
        payload += f"62{len(additional_data):02d}{additional_data}"
    
    # CRC (Tag 63)
    payload += "6304"
    
    # Calculate CRC16
    crc = crc16_ccitt(payload.encode('ascii'))
    payload += f"{crc:04X}"
    
    return payload

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromptPay QR Code Generator</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            max-width: 500px;
            width: 100%;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
            font-size: 1.1em;
        }
        
        .input-wrapper {
            position: relative;
        }
        
        .input-wrapper i {
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: #667eea;
            font-size: 1.2em;
        }
        
        .form-control {
            width: 100%;
            padding: 15px 15px 15px 50px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1.1em;
            transition: all 0.3s ease;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .btn-generate {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.2em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 10px;
        }
        
        .btn-generate:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .qr-result {
            text-align: center;
            margin-top: 30px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 15px;
            display: none;
        }
        
        .qr-code {
            max-width: 300px;
            width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        
        .download-btn {
            margin-top: 20px;
            padding: 12px 30px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            display: inline-block;
            transition: all 0.3s ease;
        }
        
        .download-btn:hover {
            background: #218838;
            transform: translateY(-2px);
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            display: none;
        }
        
        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 5px;
        }
        
        .info-box h4 {
            color: #1976d2;
            margin-bottom: 8px;
        }
        
        .info-box ul {
            color: #424242;
            margin-left: 20px;
        }
        
        .phone-examples {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 5px;
        }
        
        .phone-examples h4 {
            color: #856404;
            margin-bottom: 8px;
        }
        
        .phone-examples ul {
            color: #856404;
            margin-left: 20px;
        }
        
        .warning-box {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 5px;
        }
        
        .warning-box h4 {
            color: #721c24;
            margin-bottom: 8px;
        }
        
        .warning-box p {
            color: #721c24;
            margin: 0;
        }
        
        @media (max-width: 600px) {
            .container {
                padding: 25px;
                margin: 10px;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-qrcode"></i> PromptPay QR</h1>
            <p>สร้าง QR Code สำหรับรับเงินผ่าน PromptPay</p>
        </div>
        
        <div class="info-box">
            <h4><i class="fas fa-info-circle"></i> วิธีใช้งาน</h4>
            <ul>
                <li>กรอกเบอร์โทรศัพท์ที่ลงทะเบียน PromptPay</li>
                <li>กรอกจำนวนเงินที่ต้องการรับ</li>
                <li>กรอกชื่อผู้รับเงิน (ไม่บังคับ)</li>
                <li>กด "สร้าง QR Code" เพื่อสร้างบาร์โค้ด</li>
            </ul>
        </div>
        
        <div class="phone-examples">
            <h4><i class="fas fa-phone"></i> รูปแบบที่รองรับ</h4>
            <ul>
                <li><strong>เบอร์โทรศัพท์:</strong> 06XXXXXXXX, 08XXXXXXXX, 09XXXXXXXX</li>
                <li><strong>เลขบัตรประชาชน:</strong> 13 หลัก (ต้องลงทะเบียน PromptPay แล้ว)</li>
            </ul>
        </div>
        
        <div class="warning-box">
            <h4><i class="fas fa-exclamation-triangle"></i> ข้อควรระวัง</h4>
            <p>เลขบัตรประชาชนต้องลงทะเบียนกับ PromptPay ผ่านแอปธนาคารก่อนใช้งาน</p>
        </div>
        
        <form id="qrForm">
            <div class="form-group">
                <label for="mobile">เบอร์โทรศัพท์ หรือ เลขบัตรประชาชน</label>
                <div class="input-wrapper">
                    <i class="fas fa-mobile-alt"></i>
                    <input type="text" id="mobile" name="mobile" class="form-control" 
                           placeholder="เบอร์โทรศัพท์ 10 หลัก หรือ เลขบัตรประชาชน 13 หลัก" required>
                </div>
            </div>
            
            <div class="form-group">
                <label for="amount">จำนวนเงิน (บาท)</label>
                <div class="input-wrapper">
                    <i class="fas fa-money-bill-wave"></i>
                    <input type="number" id="amount" name="amount" class="form-control" 
                           placeholder="100.00" step="0.01" min="0.01" required>
                </div>
            </div>
            
            <div class="form-group">
                <label for="name">ชื่อผู้รับเงิน (ไม่บังคับ)</label>
                <div class="input-wrapper">
                    <i class="fas fa-user"></i>
                    <input type="text" id="name" name="name" class="form-control" 
                           placeholder="ชื่อ-นามสกุล" maxlength="25">
                </div>
            </div>
            
            <button type="submit" class="btn-generate">
                <i class="fas fa-magic"></i> สร้าง QR Code
            </button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>กำลังสร้าง QR Code...</p>
        </div>
        
        <div class="error" id="error"></div>
        
        <div class="qr-result" id="qrResult">
            <h3><i class="fas fa-check-circle" style="color: #28a745;"></i> QR Code สำเร็จ!</h3>
            <p style="margin: 15px 0;">สแกนด้วยแอปธนาคารเพื่อจ่ายเงิน</p>
            <img id="qrImage" class="qr-code" alt="PromptPay QR Code">
            <br>
            <a id="downloadBtn" class="download-btn" download="promptpay-qr.png">
                <i class="fas fa-download"></i> ดาวน์โหลด QR Code
            </a>
        </div>
    </div>

    <script>
        document.getElementById('qrForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const mobile = document.getElementById('mobile').value;
            const amount = document.getElementById('amount').value;
            const name = document.getElementById('name').value;
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');
            const qrResult = document.getElementById('qrResult');
            
            // Hide previous results
            error.style.display = 'none';
            qrResult.style.display = 'none';
            loading.style.display = 'block';
            
            try {
                const formData = new FormData();
                formData.append('mobile', mobile);
                formData.append('amount', amount);
                formData.append('name', name);
                
                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const imageUrl = URL.createObjectURL(blob);
                    
                    document.getElementById('qrImage').src = imageUrl;
                    document.getElementById('downloadBtn').href = imageUrl;
                    
                    loading.style.display = 'none';
                    qrResult.style.display = 'block';
                } else {
                    const errorText = await response.text();
                    throw new Error(errorText);
                }
            } catch (err) {
                loading.style.display = 'none';
                error.textContent = 'เกิดข้อผิดพลาด: ' + err.message;
                error.style.display = 'block';
            }
        });
        
        // Format input - รองรับทั้งเบอร์โทรและบัตรประชาชน
        document.getElementById('mobile').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            // จำกัดความยาวตามประเภท
            if (value.length <= 10) {
                // เบอร์โทรศัพท์ 10 หลัก
                e.target.value = value;
            } else if (value.length <= 13) {
                // เลขบัตรประชาชน 13 หลัก
                e.target.value = value;
            } else {
                // ตัดให้เหลือ 13 หลัก
                e.target.value = value.slice(0, 13);
            }
        });
        
        // Validate input format
        document.getElementById('mobile').addEventListener('blur', function(e) {
            const value = e.target.value;
            const errorDiv = document.getElementById('error');
            
            if (value) {
                const isValidPhone = /^(06|08|09)\d{8}$/.test(value);
                const isValidID = /^\d{13}$/.test(value);
                
                if (!isValidPhone && !isValidID) {
                    errorDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i> รูปแบบไม่ถูกต้อง<br>• เบอร์โทรศัพท์: ต้องขึ้นต้นด้วย 06, 08, 09 และมี 10 หลัก<br>• เลขบัตรประชาชน: ต้องมี 13 หลัก';
                    errorDiv.style.display = 'block';
                } else {
                    errorDiv.style.display = 'none';
                }
            }
        });
    </script>
</body>
</html>
    ''')

@app.route('/generate', methods=['POST'])
def generate_qr():
    try:
        mobile = request.form['mobile']
        amount = request.form['amount']
        name = request.form.get('name', '')
        
        # Validate inputs
        if not mobile or not amount:
            return 'กรุณากรอกข้อมูลให้ครบถ้วน', 400
            
        # Validate mobile number/national ID
        mobile_clean = ''.join(filter(str.isdigit, mobile))
        
        if len(mobile_clean) == 10:
            # เบอร์โทรศัพท์ 10 หลัก
            if not mobile_clean.startswith(('06', '08', '09')):
                return 'เบอร์โทรศัพท์ต้องขึ้นต้นด้วย 06, 08, หรือ 09', 400
        elif len(mobile_clean) == 13:
            # เลขบัตรประชาชน 13 หลัก
            # ตรวจสอบ checksum ของเลขบัตรประชาชน (ไม่บังคับ แต่แนะนำ)
            if not is_valid_national_id(mobile_clean):
                return 'เลขบัตรประชาชนไม่ถูกต้อง', 400
        else:
            return 'ต้องเป็นเบอร์โทรศัพท์ 10 หลัก หรือเลขบัตรประชาชน 13 หลัก', 400
            
        # Validate amount
        try:
            amount_float = float(amount)
            if amount_float <= 0:
                return 'จำนวนเงินต้องมากกว่า 0', 400
            if amount_float > 999999.99:
                return 'จำนวนเงินต้องไม่เกิน 999,999.99 บาท', 400
        except ValueError:
            return 'จำนวนเงินไม่ถูกต้อง', 400
            
        # Generate payload
        payload = generate_promptpay_payload(mobile_clean, amount, name)
        
        # Create QR Code with optimal settings
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        
        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', as_attachment=False)
        
    except Exception as e:
        return f'เกิดข้อผิดพลาด: {str(e)}', 400

def is_valid_national_id(national_id):
    """Validate Thai National ID checksum"""
    if len(national_id) != 13:
        return False
    
    try:
        # คำนวณ checksum ของเลขบัตรประชาชนไทย
        sum_digits = 0
        for i in range(12):
            sum_digits += int(national_id[i]) * (13 - i)
        
        remainder = sum_digits % 11
        check_digit = (11 - remainder) % 10
        
        return int(national_id[12]) == check_digit
    except:
        return False

@app.route('/test')
def test():
    """Test endpoint to verify payload generation"""
    try:
        # Test with different formats
        test_cases = [
            {"mobile": "0812345678", "amount": "100.00", "name": "ทดสอบ 08", "type": "mobile"},
            {"mobile": "0612345678", "amount": "50.00", "name": "ทดสอบ 06", "type": "mobile"},
            {"mobile": "0912345678", "amount": "200.00", "name": "ทดสอบ 09", "type": "mobile"},
            {"mobile": "1234567890128", "amount": "75.50", "name": "ทดสอบ ID", "type": "national_id"}  # Valid checksum
        ]
        
        results = []
        for test_case in test_cases:
            try:
                payload = generate_promptpay_payload(
                    test_case["mobile"], 
                    test_case["amount"], 
                    test_case["name"]
                )
                
                # Analyze payload structure
                payload_info = analyze_payload(payload)
                
                results.append({
                    **test_case,
                    'payload': payload,
                    'payload_length': len(payload),
                    'payload_info': payload_info,
                    'status': 'success'
                })
            except Exception as e:
                results.append({
                    **test_case,
                    'error': str(e),
                    'status': 'error'
                })
        
        return jsonify({
            'test_results': results,
            'total_tests': len(test_cases),
            'successful_tests': len([r for r in results if r['status'] == 'success'])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def analyze_payload(payload):
    """Analyze PromptPay payload structure"""
    try:
        info = {}
        pos = 0
        
        while pos < len(payload) - 4:  # -4 for CRC
            if pos + 4 > len(payload):
                break
                
            tag = payload[pos:pos+2]
            length = int(payload[pos+2:pos+4])
            value = payload[pos+4:pos+4+length]
            
            tag_names = {
                '00': 'Payload Format Indicator',
                '01': 'Point of Initiation Method',
                '29': 'Merchant Account Information',
                '52': 'Merchant Category Code',
                '53': 'Transaction Currency',
                '54': 'Transaction Amount',
                '58': 'Country Code',
                '59': 'Merchant Name',
                '62': 'Additional Data Field',
                '63': 'CRC'
            }
            
            info[tag] = {
                'name': tag_names.get(tag, f'Tag {tag}'),
                'length': length,
                'value': value
            }
            
            pos += 4 + length
        
        # Add CRC
        if len(payload) >= 4:
            info['63'] = {
                'name': 'CRC',
                'length': 4,
                'value': payload[-4:]
            }
        
        return info
    except:
        return {'error': 'Cannot analyze payload'}

@app.route('/validate/<mobile>')
def validate_mobile(mobile):
    """Validate mobile number or national ID format"""
    try:
        mobile_clean = ''.join(filter(str.isdigit, mobile))
        
        if len(mobile_clean) == 10:
            if mobile_clean.startswith(('06', '08', '09')):
                formatted = format_mobile(mobile_clean)
                return jsonify({
                    'original': mobile,
                    'cleaned': mobile_clean,
                    'formatted': formatted,
                    'valid': True,
                    'type': 'mobile_phone',
                    'operator': get_operator(mobile_clean[:2])
                })
            else:
                return jsonify({
                    'original': mobile,
                    'cleaned': mobile_clean,
                    'valid': False,
                    'error': 'เบอร์โทรศัพท์ต้องขึ้นต้นด้วย 06, 08, หรือ 09'
                }), 400
        elif len(mobile_clean) == 13:
            is_valid = is_valid_national_id(mobile_clean)
            return jsonify({
                'original': mobile,
                'cleaned': mobile_clean,
                'formatted': mobile_clean,
                'valid': is_valid,
                'type': 'national_id',
                'checksum_valid': is_valid
            })
        else:
            return jsonify({
                'original': mobile,
                'cleaned': mobile_clean,
                'valid': False,
                'error': 'ต้องเป็นเบอร์โทรศัพท์ 10 หลัก หรือเลขบัตรประชาชน 13 หลัก'
            }), 400
            
    except Exception as e:
        return jsonify({
            'original': mobile,
            'valid': False,
            'error': str(e)
        }), 400

def get_operator(prefix):
    """Get mobile operator from prefix"""
    operators = {
        '06': 'AIS/True',
        '08': 'AIS/True/dtac',
        '09': 'AIS/True/dtac'
    }
    return operators.get(prefix, 'Unknown')

if __name__ == '__main__':
    print("🚀 Starting PromptPay QR Code Generator...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🧪 Test payload generation at: http://localhost:5000/test")
    print("✅ Validate number at: http://localhost:5000/validate/0812345678")
    print("\n📋 Supported formats:")
    print("   📞 Mobile: 06XXXXXXXX, 08XXXXXXXX, 09XXXXXXXX")
    print("   🆔 National ID: 13 digits (with checksum validation)")
    print("\n⚠️  Note: National ID must be registered with PromptPay first!")
    app.run(debug=True, host='0.0.0.0', port=5000)
