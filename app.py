from flask import Flask, request, render_template_string, redirect, jsonify
from pymongo import MongoClient
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import certifi
import datetime
import secrets
import base64
import json

app = Flask(__name__)

# 🔴 إعدادات الدخول
ADMIN_PASS = "samurai2026" 

# 🔴 رابط قاعدة البيانات المباشر
MONGO_URI = "mongodb+srv://mimodj615_db_user:9C3rJ7Rgq05lAaSj@cluster0.5npg1u8.mongodb.net"

# 🔴 مفاتيح التشفير السري للغاية (AES-256-CBC) - نفس المفاتيح ستوضع في سكربت اللينكس
AES_KEY = bytes.fromhex("e5b7e9982708bc178347e30d75a3e1452df3a9a16fbd3e1345903b12384a9e22")
AES_IV  = bytes.fromhex("84a9e22b3e1345903b12384a9e22b3e1")

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client["samurai_db"]
    tokens_collection = db["tokens"]
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print("❌ MongoDB Connection Error:", e)

# دوال التشفير العسكري
def decrypt_payload(b64_string):
    try:
        data = base64.b64decode(b64_string)
        cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV))
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(data) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
        return json.loads(decrypted.decode('utf-8'))
    except Exception:
        return None

def encrypt_payload(data_dict):
    data_json = json.dumps(data_dict).encode('utf-8')
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data_json) + padder.finalize()
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV))
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(encrypted).decode('utf-8')

# ==========================================
# تصميم لوحة التحكم (نفس التصميم السابق)
# ==========================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Samurai - Admin Dashboard</title>
    <style>
        body { background-color: #0b0c10; color: #c5c6c7; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 30px; }
        h1 { color: #66fcf1; border-bottom: 2px solid #1f2833; padding-bottom: 10px; }
        .panel { background: #1f2833; padding: 25px; border-radius: 10px; margin-bottom: 30px; border-left: 5px solid #c3073f; box-shadow: 0 4px 8px rgba(0,0,0,0.5); }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; background: #0b0c10; border-radius: 8px; overflow: hidden; }
        th, td { border: 1px solid #1f2833; padding: 12px; text-align: left; vertical-align: middle; }
        th { background-color: #c3073f; color: #ffffff; font-weight: bold; text-transform: uppercase; font-size: 13px; }
        tr:hover { background-color: #1a1a1d; }
        .btn { background-color: #c3073f; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; transition: 0.3s; }
        .btn:hover { background-color: #95072e; }
        .btn-small { padding: 6px 12px; font-size: 12px; margin-top: 4px; }
        .btn-edit { background-color: #f39c12; } .btn-edit:hover { background-color: #d68910; }
        .btn-delete { background-color: #e74c3c; } .btn-delete:hover { background-color: #c0392b; }
        .form-row { display: flex; gap: 15px; align-items: flex-end; margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #66fcf1; font-weight: bold; font-size: 14px; }
        input { padding: 8px; background: #0b0c10; color: white; border: 1px solid #45a29e; border-radius: 4px; outline: none; }
        input:focus { border-color: #66fcf1; }
        .badge-new { color: #45a29e; font-weight: bold; }
        .badge-active { color: #2ecc71; font-weight: bold; }
        .badge-burned { color: #e74c3c; font-weight: bold; }
        .manage-box { display: flex; gap: 5px; flex-wrap: wrap; }
    </style>
</head>
<body>
    <h1>🗡️ SAMURAI PROXIES - COMMAND CENTER</h1>
    
    <div class="panel">
        <h3 style="margin-top:0; color:white;">Create New License</h3>
        <form action="/samurai/proxies/admin/create" method="POST">
            <input type="hidden" name="password" value="{{ pwd }}">
            <div class="form-row">
                <div>
                    <label>Max IPs:</label>
                    <input type="number" name="max_ips" value="1000" min="1" style="width: 120px;" required>
                </div>
                <div>
                    <label>Duration (Days):</label>
                    <input type="number" name="duration_days" value="30" min="1" style="width: 120px;" required>
                </div>
                <button type="submit" class="btn">+ GENERATE TOKEN</button>
            </div>
        </form>
    </div>

    <h3 style="color: white;">Client Licenses Database</h3>
    <table>
        <tr>
            <th>Token Key</th>
            <th>Status</th>
            <th>Max IPs</th>
            <th>Base Days</th>
            <th>Expiry Date</th>
            <th>Days Left</th>
            <th>Manage (Edit / Delete)</th>
        </tr>
        {% for row in tokens %}
        <tr>
            <td style="color: #66fcf1; font-family: monospace; font-size: 13px;">{{ row.get('token') }}</td>
            <td>
                {% if row.get('status') == 'NEW' %}<span class="badge-new">UNUSED</span>
                {% elif row.get('status') == 'ACTIVE' %}<span class="badge-active">ONLINE</span>
                {% else %}<span class="badge-burned">{{ row.get('status') }}</span>{% endif %}
            </td>
            <td style="color: #f39c12; font-weight: bold;">{{ row.get('max_ips') }}</td>
            <td>{{ row.get('duration_days', 30) }}</td>
            <td style="font-size: 13px;">{{ row.get('expiry') or 'Waiting Activation' }}</td>
            <td style="font-weight: bold; font-size: 14px;">
                {% if row.get('expiry') %}
                    {% set days = (datetime.strptime(row.get('expiry'), '%Y-%m-%d %H:%M:%S') - datetime.now()).days %}
                    {% if days > 5 %}<span style="color: #2ecc71;">{{ days }} Days</span>
                    {% elif days >= 0 %}<span style="color: #f1c40f;">{{ days }} Days</span>
                    {% else %}<span style="color: #e74c3c;">Expired</span>{% endif %}
                {% else %}
                    -
                {% endif %}
            </td>
            <td>
                <div class="manage-box">
                    <form action="/samurai/proxies/admin/update" method="POST" style="display:inline;">
                        <input type="hidden" name="password" value="{{ pwd }}">
                        <input type="hidden" name="token" value="{{ row.get('token') }}">
                        <input type="number" name="new_max_ips" value="{{ row.get('max_ips') }}" title="Change Max IPs" style="width:60px; padding:4px;" required>
                        <input type="number" name="add_days" placeholder="+Days" title="Add or Subtract Days (e.g. 10 or -5)" style="width:60px; padding:4px;">
                        <button type="submit" class="btn btn-small btn-edit">Save</button>
                    </form>
                    <form action="/samurai/proxies/admin/delete" method="POST" style="display:inline;" onsubmit="return confirm('WARNING: Are you sure you want to permanently DELETE this token?');">
                        <input type="hidden" name="password" value="{{ pwd }}">
                        <input type="hidden" name="token" value="{{ row.get('token') }}">
                        <button type="submit" class="btn btn-small btn-delete">Delete</button>
                    </form>
                </div>
            </td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# ==========================================
# مسارات السيرفر (Routes)
# ==========================================
@app.route('/samurai/proxies/admin/dashboard')
def dashboard():
    pwd = request.args.get('pwd')
    if pwd != ADMIN_PASS: return "Access Denied. Unauthorized.", 401
    tokens = list(tokens_collection.find().sort("_id", -1))
    return render_template_string(DASHBOARD_HTML, tokens=tokens, datetime=datetime.datetime, pwd=pwd)

@app.route('/samurai/proxies/admin/create', methods=['POST'])
def create_token():
    pwd = request.form.get('password')
    if pwd != ADMIN_PASS: return "Unauthorized!", 401
        
    max_ips = int(request.form.get('max_ips', 1000))
    duration_days = int(request.form.get('duration_days', 30))
    token = "SMR-" + secrets.token_hex(10).upper()
    
    new_token = {
        "token": token,
        "hwid": None,
        "start_date": None,
        "expiry": None,
        "status": "NEW",
        "max_ips": max_ips,
        "duration_days": duration_days
    }
    tokens_collection.insert_one(new_token)
    return redirect(f'/samurai/proxies/admin/dashboard?pwd={ADMIN_PASS}')

@app.route('/samurai/proxies/admin/update', methods=['POST'])
def update_token():
    pwd = request.form.get('password')
    if pwd != ADMIN_PASS: return "Unauthorized!", 401
    
    token = request.form.get('token')
    new_max_ips = int(request.form.get('new_max_ips', 1000))
    add_days_str = request.form.get('add_days', '')
    
    row = tokens_collection.find_one({"token": token})
    if not row: return "Token not found", 404
    
    update_fields = {"max_ips": new_max_ips}
    
    if add_days_str:
        add_days = int(add_days_str)
        if row.get("status") == "NEW":
            current_duration = row.get("duration_days", 30)
            update_fields["duration_days"] = current_duration + add_days
        elif row.get("expiry"):
            current_expiry = datetime.datetime.strptime(row.get("expiry"), "%Y-%m-%d %H:%M:%S")
            new_expiry = current_expiry + datetime.timedelta(days=add_days)
            update_fields["expiry"] = new_expiry.strftime("%Y-%m-%d %H:%M:%S")
            if row.get("status") == "EXPIRED" and datetime.datetime.now() < new_expiry:
                update_fields["status"] = "ACTIVE"
                
    tokens_collection.update_one({"token": token}, {"$set": update_fields})
    return redirect(f'/samurai/proxies/admin/dashboard?pwd={ADMIN_PASS}')

@app.route('/samurai/proxies/admin/delete', methods=['POST'])
def delete_token():
    pwd = request.form.get('password')
    if pwd != ADMIN_PASS: return "Unauthorized!", 401
    token = request.form.get('token')
    tokens_collection.delete_one({"token": token})
    return redirect(f'/samurai/proxies/admin/dashboard?pwd={ADMIN_PASS}')

# مسار الـ API المشفر (لا يتلقى إلا حزم مشفرة)
@app.route('/api/validate', methods=['POST'])
def validate():
    encrypted_req = request.form.get('payload')
    if not encrypted_req: return jsonify({"payload": encrypt_payload({"status": "ERROR"})})
    
    data = decrypt_payload(encrypted_req)
    if not data: return jsonify({"payload": encrypt_payload({"status": "ERROR"})})
    
    token = data.get('token')
    hwid = data.get('hwid')
    
    try: row = tokens_collection.find_one({"token": token})
    except: return jsonify({"payload": encrypt_payload({"status": "ERROR"})})
    
    if not row: return jsonify({"payload": encrypt_payload({"status": "INVALID"})})
        
    db_hwid = row.get("hwid")
    expiry_str = row.get("expiry")
    status = row.get("status")
    max_ips = row.get("max_ips", 1000)
    duration_days = row.get("duration_days", 30)
    
    if status == 'BURNED': 
        return jsonify({"payload": encrypt_payload({"status": "BURNED"})})
        
    if not db_hwid:
        now = datetime.datetime.now()
        start_date = now.strftime("%Y-%m-%d %H:%M:%S")
        expiry = (now + datetime.timedelta(days=duration_days)).strftime("%Y-%m-%d %H:%M:%S")
        tokens_collection.update_one(
            {"token": token},
            {"$set": {"hwid": hwid, "start_date": start_date, "expiry": expiry, "status": "ACTIVE"}}
        )
        return jsonify({"payload": encrypt_payload({"status": "VALID", "max_ips": max_ips})})
        
    if db_hwid != hwid:
        tokens_collection.update_one({"token": token}, {"$set": {"status": "BURNED"}})
        return jsonify({"payload": encrypt_payload({"status": "BURNED"})})
        
    if db_hwid == hwid:
        if expiry_str:
            expiry_date = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() > expiry_date:
                tokens_collection.update_one({"token": token}, {"$set": {"status": "EXPIRED"}})
                return jsonify({"payload": encrypt_payload({"status": "EXPIRED"})})
        return jsonify({"payload": encrypt_payload({"status": "VALID", "max_ips": max_ips})})

@app.route('/')
def home():
    return "Samurai System is ONLINE and SECURED."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
