from flask import Flask, request
import sqlite3
import datetime

app = Flask(__name__)

# تهيئة قاعدة البيانات السريعة
def init_db():
    conn = sqlite3.connect('samurai.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tokens (token TEXT PRIMARY KEY, hwid TEXT, expiry DATETIME, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# مسار للآدمن لإنشاء توكن جديد (استخدمه أنت فقط عبر المتصفح أو بوستمان)
@app.route('/admin/create_token/<token>')
def create_token(token):
    conn = sqlite3.connect('samurai.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO tokens (token, hwid, expiry, status) VALUES (?, NULL, NULL, 'NEW')", (token,))
    conn.commit()
    conn.close()
    return f"Token {token} created successfully!"

# مسار التحقق والتدمير (يتصل به البرنامج)
@app.route('/api/validate', methods=['POST'])
def validate():
    token = request.form.get('token')
    hwid = request.form.get('hwid')
    
    conn = sqlite3.connect('samurai.db')
    c = conn.cursor()
    c.execute("SELECT hwid, expiry, status FROM tokens WHERE token=?", (token,))
    row = c.fetchone()
    
    if not row:
        return "INVALID" # توكن غير موجود
        
    db_hwid, expiry_str, status = row
    
    if status == 'BURNED':
        return "BURNED" # توكن مسروق، أعطِ أمر التدمير
        
    if db_hwid is None:
        # أول تسجيل دخول! تفعيل لمدة 30 يوم وربطه ببصمة الجهاز
        new_expiry = datetime.datetime.now() + datetime.timedelta(days=30)
        c.execute("UPDATE tokens SET hwid=?, expiry=?, status='ACTIVE' WHERE token=?", (hwid, new_expiry.strftime("%Y-%m-%d %H:%M:%S"), token))
        conn.commit()
        return "VALID"
        
    if db_hwid != hwid:
        # شخص يحاول تشغيله في جهاز آخر! احرق التوكن!
        c.execute("UPDATE tokens SET status='BURNED' WHERE token=?", (token,))
        conn.commit()
        return "BURNED"
        
    if db_hwid == hwid:
        # نفس الجهاز، نتحقق من الوقت
        expiry_date = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
        if datetime.datetime.now() > expiry_date:
            return "EXPIRED" # انتهى الشهر، أعط أمر التدمير
        return "VALID"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
