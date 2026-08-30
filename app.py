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

# 🔴 مفاتيح التشفير السري للغاية (AES-256-CBC)
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
# تصميم لوحة التحكم الاحترافية (Samurai UI)
# ==========================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Samurai Master - Command Center</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --bg: #050505; --surface: #111111; --primary: #e22828; --primary-hover: #b91c1c; --accent: #00f0ff; --text: #e0e0e0; --border: #222; }
        body { background-color: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; margin: 0; padding: 0; }
        header { background: var(--surface); border-bottom: 2px solid var(--primary); padding: 20px 40px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 15px rgba(226, 40, 40, 0.15); }
        h1 { font-family: 'Orbitron', sans-serif; color: var(--primary); margin: 0; font-size: 26px; text-transform: uppercase; letter-spacing: 2px; }
        h1 i { color: var(--text); margin-right: 12px; }
        .container { padding: 40px; max-width: 1400px; margin: 0 auto; }
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 25px; margin-bottom: 30px; box-shadow: 0 8px 30px rgba(0,0,0,0.5); position: relative; overflow: hidden; }
        .card::before { content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: var(--primary); }
        .card h3 { font-family: 'Orbitron', sans-serif; color: var(--text); margin-top: 0; margin-bottom: 25px; font-size: 18px; border-bottom: 1px solid var(--border); padding-bottom: 15px; }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; align-items: end; }
        .input-group { display: flex; flex-direction: column; }
        .input-group label { font-size: 12px; color: var(--accent); font-weight: 600; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
        .input-group input { background: rgba(0,0,0,0.5); border: 1px solid var(--border); color: #fff; padding: 12px 15px; border-radius: 6px; font-family: 'Inter', sans-serif; outline: none; transition: 0.3s; }
        .input-group input:focus { border-color: var(--accent); box-shadow: 0 0 10px rgba(0, 240, 255, 0.15); }
        .btn { background: var(--primary); color: #fff; border: none; padding: 12px 25px; font-family: 'Orbitron', sans-serif; font-size: 13px; font-weight: 700; border-radius: 6px; cursor: pointer; transition: 0.3s; text-transform: uppercase; letter-spacing: 1px; display: flex; justify-content: center; align-items: center; gap: 8px; }
        .btn:hover { background: var(--primary-hover); transform: translateY(-2px); box-shadow: 0 5px 15px rgba(226, 40, 40, 0.3); }
        .btn-edit { background: #f39c12; color: #fff; padding: 8px 15px; } .btn-edit:hover { background: #d68910; }
        .btn-delete { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 8px 15px; } .btn-delete:hover { background: var(--primary); color: #fff; }
        .table-container { overflow-x: auto; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; }
        table { width: 100%; border-collapse: separate; border-spacing: 0; }
        th { background: rgba(226, 40, 40, 0.05); color: var(--primary); font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; padding: 18px 15px; text-align: left; border-bottom: 1px solid var(--border); }
        td { padding: 15px; border-bottom: 1px solid var(--border); font-size: 13px; vertical-align: middle; }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background: rgba(255,255,255,0.02); }
        .token-cell { font-family: monospace; color: var(--accent); font-size: 14px; font-weight: 600; letter-spacing: 1px; background: rgba(0, 240, 255, 0.05); padding: 6px 10px; border-radius: 4px; display: inline-block; }
        .badge { padding: 5px 10px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; display: inline-block; }
        .bg-new { background: rgba(0, 240, 255, 0.1); color: var(--accent); border: 1px solid var(--accent); }
        .bg-active { background: rgba(46, 204, 113, 0.1); color: #2ecc71; border: 1px solid #2ecc71; }
        .bg-burned { background: rgba(226, 40, 40, 0.1); color: var(--primary); border: 1px solid var(--primary); }
        .manage-controls { display: flex; gap: 10px; align-items: center; }
        .manage-controls input { background: rgba(0,0,0,0.5); border: 1px solid var(--border); color: #fff; padding: 8px; border-radius: 4px; width: 60px; text-align: center; font-family: monospace; }
        .info-box { display: flex; align-items: center; gap: 8px; color: #aaa; font-size: 12px; margin-top: 5px; }
        .info-box i { color: #f39c12; }
    </style>
</head>
<body>

    <header>
        <h1><i class="fa-solid fa-khanda"></i> Samurai Command Center</h1>
    </header>

    <div class="container">
        <!-- Create License Card -->
        <div class="card">
            <h3><i class="fa-solid fa-key" style="color: var(--accent); margin-right: 10px;"></i> Generate New License</h3>
            <form action="/samurai/proxies/admin/create" method="POST">
                <input type="hidden" name="password" value="{{ pwd }}">
                <div class="form-grid">
                    <div class="input-group">
                        <label>Max Proxies (IPs)</label>
                        <input type="number" name="max_ips" value="1000" min="1" required>
                    </div>
                    <div class="input-group">
                        <label>Duration (Days)</label>
                        <input type="number" name="duration_days" value="30" min="1" required>
                    </div>
                    <div class="input-group">
                        <label>Client Panel Username</label>
                        <input type="text" name="panel_user" placeholder="e.g. client_name" required>
                    </div>
                    <div class="input-group">
                        <label>Client Panel Password</label>
                        <input type="text" name="panel_pass" placeholder="e.g. secret123" required>
                    </div>
                    <button type="submit" class="btn"><i class="fa-solid fa-bolt"></i> Generate Token</button>
                </div>
            </form>
        </div>

        <!-- Database Table -->
        <div class="card">
            <h3><i class="fa-solid fa-database" style="color: var(--primary); margin-right: 10px;"></i> Active Network Licenses</h3>
            <div class="table-container">
                <table>
                    <tr>
                        <th>Access Token</th>
                        <th>Status</th>
                        <th>Capacity</th>
                        <th>Client Credentials</th>
                        <th>Lifecycle</th>
                        <th>Operations</th>
                    </tr>
                    {% for row in tokens %}
                    <tr>
                        <td><span class="token-cell">{{ row.get('token') }}</span></td>
                        <td>
                            {% if row.get('status') == 'NEW' %}<span class="badge bg-new">Awaiting Boot</span>
                            {% elif row.get('status') == 'ACTIVE' %}<span class="badge bg-active">Online</span>
                            {% else %}<span class="badge bg-burned">{{ row.get('status') }}</span>{% endif %}
                        </td>
                        <td><strong style="color: #f39c12; font-size: 15px;">{{ row.get('max_ips') }}</strong> IPs</td>
                        <td>
                            <div style="color: #ccc;">User: <span style="color:#fff;">{{ row.get('panel_user', 'admin') }}</span></div>
                            <div style="color: #ccc;">Pass: <span style="color:#fff;">{{ row.get('panel_pass', 'admin') }}</span></div>
                        </td>
                        <td>
                            {% if row.get('expiry') %}
                                {% set days = (datetime.strptime(row.get('expiry'), '%Y-%m-%d %H:%M:%S') - datetime.now()).days %}
                                {% if days > 5 %}<span style="color: #2ecc71; font-weight:bold;">{{ days }} Days Left</span>
                                {% elif days >= 0 %}<span style="color: #f39c12; font-weight:bold;">{{ days }} Days Left</span>
                                {% else %}<span style="color: var(--primary); font-weight:bold;">Expired</span>{% endif %}
                                <div class="info-box"><i class="fa-regular fa-clock"></i> {{ row.get('expiry') }}</div>
                            {% else %}
                                <span style="color: #777;">{{ row.get('duration_days', 30) }} Days (Pending)</span>
                            {% endif %}
                        </td>
                        <td>
                            <div class="manage-controls">
                                <form action="/samurai/proxies/admin/update" method="POST" style="display:flex; gap:5px; align-items:center; margin:0;">
                                    <input type="hidden" name="password" value="{{ pwd }}">
                                    <input type="hidden" name="token" value="{{ row.get('token') }}">
                                    <input type="number" name="new_max_ips" value="{{ row.get('max_ips') }}" title="Change Max IPs" required>
                                    <input type="number" name="add_days" placeholder="+Days" title="Add/Subtract Days">
                                    <button type="submit" class="btn btn-edit"><i class="fa-solid fa-pen"></i></button>
                                </form>
                                <form action="/samurai/proxies/admin/delete" method="POST" style="margin:0;" onsubmit="return confirm('WARNING: Destroying this token will immediately disconnect the client network. Proceed?');">
                                    <input type="hidden" name="password" value="{{ pwd }}">
                                    <input type="hidden" name="token" value="{{ row.get('token') }}">
                                    <button type="submit" class="btn btn-delete"><i class="fa-solid fa-trash"></i></button>
                                </form>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>
    </div>
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
    panel_user = request.form.get('panel_user', 'admin').strip()
    panel_pass = request.form.get('panel_pass', 'admin').strip()
    token = "SMR-" + secrets.token_hex(10).upper()
    
    new_token = {
        "token": token,
        "hwid": None,
        "start_date": None,
        "expiry": None,
        "status": "NEW",
        "max_ips": max_ips,
        "duration_days": duration_days,
        "panel_user": panel_user,
        "panel_pass": panel_pass
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
    
    # 🔴 البيانات التي سيتم إرسالها للعميل داخل الحزمة المشفرة
    payload_data = {
        "status": "VALID", 
        "max_ips": row.get("max_ips", 1000),
        "panel_user": row.get("panel_user", "admin"),
        "panel_pass": row.get("panel_pass", "admin")
    }
    
    if status == 'BURNED': 
        return jsonify({"payload": encrypt_payload({"status": "BURNED"})})
        
    if not db_hwid:
        now = datetime.datetime.now()
        start_date = now.strftime("%Y-%m-%d %H:%M:%S")
        expiry = (now + datetime.timedelta(days=row.get("duration_days", 30))).strftime("%Y-%m-%d %H:%M:%S")
        tokens_collection.update_one(
            {"token": token},
            {"$set": {"hwid": hwid, "start_date": start_date, "expiry": expiry, "status": "ACTIVE"}}
        )
        return jsonify({"payload": encrypt_payload(payload_data)})
        
    if db_hwid != hwid:
        tokens_collection.update_one({"token": token}, {"$set": {"status": "BURNED"}})
        return jsonify({"payload": encrypt_payload({"status": "BURNED"})})
        
    if db_hwid == hwid:
        if expiry_str:
            expiry_date = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() > expiry_date:
                tokens_collection.update_one({"token": token}, {"$set": {"status": "EXPIRED"}})
                return jsonify({"payload": encrypt_payload({"status": "EXPIRED"})})
        return jsonify({"payload": encrypt_payload(payload_data)})

@app.route('/')
def home():
    return "Samurai System is ONLINE and SECURED."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
