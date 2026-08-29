from flask import Flask, request, render_template_string, redirect, jsonify
from pymongo import MongoClient
import certifi
import datetime
import secrets
import os

app = Flask(__name__)

ADMIN_PASS = "samurai2026" 

MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://mimodj615_db_user:9C3rJ7Rgq05lAaSj@cluster0.5npg1u8.mongodb.net/?appName=Cluster0")

# استخدام الخيار النهائي لتخطي حظر شهادات الأمان في Render
client = MongoClient(
    MONGO_URI, 
    tls=True, 
    tlsCAFile=certifi.where(), 
    tlsAllowInvalidCertificates=True,
    serverSelectionTimeoutMS=5000
)
db = client["samurai_db"]
tokens_collection = db["tokens"]

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
        th, td { border: 1px solid #1f2833; padding: 12px 15px; text-align: left; }
        th { background-color: #c3073f; color: #ffffff; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
        tr:hover { background-color: #1a1a1d; }
        .btn { background-color: #c3073f; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 14px; transition: 0.3s; }
        .btn:hover { background-color: #95072e; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 8px; color: #66fcf1; font-weight: bold; }
        input { width: 100%; max-width: 300px; padding: 10px; background: #0b0c10; color: white; border: 1px solid #45a29e; border-radius: 5px; outline: none; }
        input:focus { border-color: #66fcf1; }
        .badge-new { color: #45a29e; font-weight: bold; }
        .badge-active { color: #2ecc71; font-weight: bold; }
        .badge-burned { color: #e74c3c; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🗡️ SAMURAI PROXIES - COMMAND CENTER</h1>
    
    <div class="panel">
        <h3 style="margin-top:0; color:white;">Create New License</h3>
        <form action="/samurai/proxies/admin/create" method="POST">
            <input type="hidden" name="password" value="{{ pwd }}">
            <div class="form-group">
                <label>Max IPs allowed for this Client:</label>
                <input type="number" name="max_ips" value="1000" min="1" required>
            </div>
            <button type="submit" class="btn">+ GENERATE SECURE TOKEN</button>
        </form>
    </div>

    <h3 style="color: white;">Client Licenses Database</h3>
    <table>
        <tr>
            <th>Token Key</th>
            <th>Status</th>
            <th>Max IPs</th>
            <th>Device HWID</th>
            <th>Activation Date</th>
            <th>Expiry Date</th>
            <th>Days Left</th>
        </tr>
        {% for row in tokens %}
        <tr>
            <td style="color: #66fcf1; font-family: monospace;">{{ row.get('token') }}</td>
            <td>
                {% if row.get('status') == 'NEW' %}<span class="badge-new">UNUSED</span>
                {% elif row.get('status') == 'ACTIVE' %}<span class="badge-active">ONLINE</span>
                {% else %}<span class="badge-burned">{{ row.get('status') }}</span>{% endif %}
            </td>
            <td style="color: #f39c12; font-weight: bold;">{{ row.get('max_ips') }}</td>
            <td style="font-size: 12px; color: #7f8c8d;">{{ (row.get('hwid')[:15] + '...') if row.get('hwid') else 'Waiting...' }}</td>
            <td>{{ row.get('start_date') or '-' }}</td>
            <td>{{ row.get('expiry') or '-' }}</td>
            <td style="font-weight: bold;">
                {% if row.get('expiry') %}
                    {% set days = (datetime.strptime(row.get('expiry'), '%Y-%m-%d %H:%M:%S') - datetime.now()).days %}
                    {% if days > 5 %}<span style="color: #2ecc71;">{{ days }} Days</span>
                    {% elif days > 0 %}<span style="color: #f1c40f;">{{ days }} Days</span>
                    {% else %}<span style="color: #e74c3c;">Expired</span>{% endif %}
                {% else %}
                    -
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route('/samurai/proxies/admin/dashboard')
def dashboard():
    pwd = request.args.get('pwd')
    if pwd != ADMIN_PASS:
        return "Access Denied. Unauthorized.", 401
    tokens = list(tokens_collection.find().sort("_id", -1))
    return render_template_string(DASHBOARD_HTML, tokens=tokens, datetime=datetime.datetime, pwd=pwd)

@app.route('/samurai/proxies/admin/create', methods=['POST'])
def create_token():
    pwd = request.form.get('password')
    if pwd != ADMIN_PASS:
        return "Unauthorized!", 401
    max_ips = int(request.form.get('max_ips', 1000))
    token = "SMR-" + secrets.token_hex(10).upper()
    new_token = {
        "token": token,
        "hwid": None,
        "start_date": None,
        "expiry": None,
        "status": "NEW",
        "max_ips": max_ips
    }
    tokens_collection.insert_one(new_token)
    return redirect(f'/samurai/proxies/admin/dashboard?pwd={ADMIN_PASS}')

@app.route('/api/validate', methods=['POST'])
def validate():
    token = request.form.get('token')
    hwid = request.form.get('hwid')
    row = tokens_collection.find_one({"token": token})
    
    if not row:
        return jsonify({"status": "INVALID"})
        
    db_hwid = row.get("hwid")
    expiry_str = row.get("expiry")
    status = row.get("status")
    max_ips = row.get("max_ips", 1000)
    
    if status == 'BURNED':
        return jsonify({"status": "BURNED"})
        
    if not db_hwid:
        now = datetime.datetime.now()
        start_date = now.strftime("%Y-%m-%d %H:%M:%S")
        expiry = (now + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        tokens_collection.update_one(
            {"token": token},
            {"$set": {"hwid": hwid, "start_date": start_date, "expiry": expiry, "status": "ACTIVE"}}
        )
        return jsonify({"status": "VALID", "max_ips": max_ips})
        
    if db_hwid != hwid:
        tokens_collection.update_one({"token": token}, {"$set": {"status": "BURNED"}})
        return jsonify({"status": "BURNED"})
        
    if db_hwid == hwid:
        if expiry_str:
            expiry_date = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() > expiry_date:
                tokens_collection.update_one({"token": token}, {"$set": {"status": "EXPIRED"}})
                return jsonify({"status": "EXPIRED"})
        return jsonify({"status": "VALID", "max_ips": max_ips})

@app.route('/')
def home():
    return "Samurai Server is Online."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
