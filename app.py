import os
import csv
import io
import re
import json
import hmac
import secrets
import requests
import unicodedata
from datetime import datetime
from xml.sax.saxutils import escape
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from dotenv import load_dotenv
from sqlalchemy import text, func

load_dotenv()

app = Flask(__name__)

# مفتاح الجلسات السري مع قيمة احتياطية آمنة لمنع توقف خادم التشغيل في Render
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dictionary-secure-fallback-key-2026'

db_url = os.getenv('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# حد أقصى لحجم حمولة الطلبات لحماية الذاكرة ومنع هجمات حجب الخدمة (4MB)
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024

# إعدادات حوض الاتصال لدعم السيرفرليس (Neon) وتفادي قطع اتصال SSL عند الخمول
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 30,
}

# تقوية كوكيز الجلسة: HttpOnly و SameSite
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['WTF_CSRF_TIME_LIMIT'] = 3600 * 24

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

limiter = Limiter(get_remote_address, app=app, default_limits=[])
csrf = CSRFProtect(app)

# ترويسات الأمان الأساسية للحماية من Clickjacking و MIME-sniffing
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# --- الجداول (Database Models) ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='reader')

class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    en = db.Column(db.String(255), nullable=False)
    ar = db.Column(db.String(255), nullable=True)
    definition = db.Column(db.Text, nullable=True)
    subject_field = db.Column(db.String(150), nullable=True, default="قانون عام")
    source_text_en = db.Column(db.Text, nullable=True)
    source_text_ar = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, default=db.func.now())
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

# إنشاء الجداول والتحقق من الأعمدة بأمان
with app.app_context():
    try:
        db.create_all()
        if db.engine.name == 'sqlite':
            cols = [row[1] for row in db.session.execute(text("PRAGMA table_info(term)")).fetchall()]
            sqlite_columns = [
                ('subject_field', "VARCHAR(150) DEFAULT 'قانون عام'"),
                ('source_text_en', "TEXT"),
                ('source_text_ar', "TEXT"),
                ('date', "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ('created_at', "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            ]
            for col_name, col_def in sqlite_columns:
                if col_name not in cols:
                    db.session.execute(text(f"ALTER TABLE term ADD COLUMN {col_name} {col_def};"))
        else:  # PostgreSQL (Neon/Render)
            db.session.execute(text("ALTER TABLE term ADD COLUMN IF NOT EXISTS subject_field VARCHAR(150) DEFAULT 'قانون عام';"))
            db.session.execute(text("ALTER TABLE term ADD COLUMN IF NOT EXISTS source_text_en TEXT;"))
            db.session.execute(text("ALTER TABLE term ADD COLUMN IF NOT EXISTS source_text_ar TEXT;"))
            db.session.execute(text("ALTER TABLE term ADD COLUMN IF NOT EXISTS date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
            db.session.execute(text("ALTER TABLE term ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
        db.session.commit()
    except Exception:
        db.session.rollback()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_ai_config():
    api_key_setting = Setting.query.filter_by(key='openrouter_api_key').first()
    model_setting = Setting.query.filter_by(key='openrouter_model').first()
    api_key = api_key_setting.value if api_key_setting else os.getenv('OPENROUTER_API_KEY', '')
    model = model_setting.value if model_setting else 'openai/gpt-3.5-turbo'
    return api_key, model

_INVISIBLE_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]")
_AR_DIACRITICS_RE = re.compile(r"[\u0640\u064b-\u065f\u0670\u06d6-\u06ed]")

def normalize_text(text):
    text = unicodedata.normalize("NFKC", str(text or ""))
    text = _INVISIBLE_RE.sub("", text)
    return text.replace("\u00a0", " ")

def _strip_ar_diacritics(text):
    return _AR_DIACRITICS_RE.sub("", str(text or ""))

def _term_key(value):
    value = normalize_text(str(value or "")).casefold()
    # إزالة التشكيل والمد (التطويل) قبل استبدال غير الحروف بمسافات حتى لا تنقسم الكلمات العربية
    value = _strip_ar_diacritics(value)
    # توحيد المتغيرات الإملائية العربية الشائعة لمنع التكرار
    value = re.sub(r"[أإآٱ]", "ا", value)
    value = re.sub(r"ى(?=\s|$|\W)", "ي", value)
    value = re.sub(r"ة(?=\s|$|\W)", "ه", value)
    value = re.sub(r"[\W_]+", " ", value, flags=re.UNICODE)
    words = value.split()
    norm_words = [w[2:] if re.match(r"^ال[\u0600-\u06ff]{2,}", w) else w for w in words]
    return " ".join(norm_words).strip()

def _pair_key(en_val, ar_val=""):
    en_k = _term_key(en_val)
    ar_k = _term_key(ar_val)
    if not en_k:
        return ""
    return f"{en_k}|{ar_k}" if ar_k else en_k

def sanitize_excel_cell(value):
    """حماية ملفات Excel و CSV من ثغرة Formula Injection (CWE-1236)"""
    if value is None:
        return ""
    val_str = str(value)
    if val_str and val_str[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + val_str
    return val_str

def clean_xml_text(value):
    """تنظيف النصوص من المحارف غير الصالحة في مواصفة XML 1.0"""
    if not value:
        return ""
    return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str(value))

# --- API استقبال المصطلحات من المنصة (qwqw) ---
@csrf.exempt
@app.route('/api/receive-terms', methods=['POST'])
@limiter.limit("60 per hour")
def receive_terms():
    auth_header = request.headers.get('Authorization')
    ingest_key = os.environ.get('INGEST_API_KEY')
    if not ingest_key:
        return jsonify({'error': 'Server configuration error: INGEST_API_KEY is not configured'}), 500

    expected_token = f"Bearer {ingest_key}"
    # مقارنة آمنة ذات وقت ثابت لمنع هجمات التوقيت
    if not auth_header or not hmac.compare_digest(auth_header, expected_token):
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON payload'}), 400

    terms = data.get('terms', [])
    if not isinstance(terms, list):
        return jsonify({'error': 'Terms payload must be a list'}), 400

    if len(terms) > 300:
        return jsonify({'error': 'Batch size exceeds limit of 300 terms'}), 400
    
    try:
        # فحص استباقي للمصطلحات الواردة بالدفعة فقط بدلاً من جلب كامل الجدول لتوفير الذاكرة
        incoming_words = [str(item.get('en') or '').strip() for item in terms if item.get('en')]
        matched_rows = Term.query.filter(Term.en.in_(incoming_words)).all() if incoming_words else []
        existing_map = {_pair_key(r.en, r.ar): r for r in matched_rows if _pair_key(r.en, r.ar)}
        existing_keys = set(existing_map.keys())

        seen_in_batch = set()
        added_count = 0
        skipped_count = 0

        for item in terms:
            eng = str(item.get('en') or '').strip()
            if not eng:
                continue
            ara = str(item.get('ar') or '').strip()

            norm_key = _pair_key(eng, ara)
            if not norm_key or norm_key in seen_in_batch:
                skipped_count += 1
                continue

            if norm_key in existing_keys:
                existing_term = existing_map.get(norm_key)
                if existing_term and existing_term.status == 'pending':
                    new_def = str(item.get('definition') or '').strip()
                    new_subj = str(item.get('subject field') or item.get('subject_field') or '').strip()
                    new_src_en = str(item.get('source_text_en') or item.get('source text en') or '').strip()
                    new_src_ar = str(item.get('source_text_ar') or item.get('source text ar') or '').strip()
                    if new_def:
                        existing_term.definition = new_def
                    if new_subj:
                        existing_term.subject_field = new_subj
                    if new_src_en:
                        existing_term.source_text_en = new_src_en
                    if new_src_ar:
                        existing_term.source_text_ar = new_src_ar
                skipped_count += 1
                seen_in_batch.add(norm_key)
                continue

            seen_in_batch.add(norm_key)
            existing_keys.add(norm_key)

            new_term = Term(
                en=eng,
                ar=ara,
                definition=str(item.get('definition') or '').strip(),
                subject_field=str(item.get('subject field') or item.get('subject_field') or 'قانون عام').strip(),
                source_text_en=str(item.get('source_text_en') or item.get('source text en') or '').strip(),
                source_text_ar=str(item.get('source_text_ar') or item.get('source text ar') or '').strip(),
                status='pending'
            )
            db.session.add(new_term)
            added_count += 1

        db.session.commit()
        return jsonify({
            'message': 'Terms processed successfully',
            'added_count': added_count,
            'skipped_duplicate_count': skipped_count
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- المسارات والصفحات ---
@app.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        return redirect(url_for('admin'))
    return redirect(url_for('dictionary'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter(func.lower(User.username) == username.lower()).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('بيانات الدخول غير صحيحة، يرجى المحاولة مجدداً.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour", methods=['POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not password:
            flash('يرجى ملء جميع الحقول المطلوبة.', 'danger')
            return render_template('login.html')
            
        if len(username) < 3 or len(username) > 50:
            flash('اسم المستخدم يجب أن يكون بين 3 و 50 حرفاً.', 'danger')
            return render_template('login.html')

        if len(password) < 8:
            flash('كلمة المرور يجب أن تتكون من 8 أحرف على الأقل.', 'danger')
            return render_template('login.html')

        if password != confirm_password:
            flash('كلمة المرور وتأكيد كلمة المرور غير متطابقتين.', 'danger')
            return render_template('login.html')
            
        if User.query.filter(func.lower(User.username) == username.lower()).first():
            flash('اسم المستخدم مسجل مسبقاً، يرجى اختيار اسم آخر.', 'warning')
            return render_template('login.html')
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password, role='reader')
        db.session.add(new_user)
        db.session.commit()
        
        flash('تم إنشاء حساب القارئ بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
        return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/account/password', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=['POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not bcrypt.check_password_hash(current_user.password, current_password):
            flash('كلمة المرور الحالية غير صحيحة.', 'danger')
        elif len(new_password) < 8:
            flash('كلمة المرور الجديدة يجب أن تتكون من 8 أحرف على الأقل.', 'danger')
        elif new_password != confirm_password:
            flash('كلمة المرور الجديدة وتأكيدها غير متطابقين.', 'danger')
        else:
            current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
            flash('تم تغيير كلمة المرور بنجاح!', 'success')
            return redirect(url_for('index'))

    return render_template('change_password.html')

@app.route('/dictionary')
@login_required
def dictionary():
    terms = Term.query.filter_by(status='approved').order_by(Term.en).all()
    return render_template('dictionary.html', terms=terms)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    if request.method == 'POST':
        en_term = request.form.get('en', '').strip()
        ar_term = request.form.get('ar', '').strip()
        definition = request.form.get('definition', '').strip()
        subject_field = request.form.get('subject_field', 'قانون عام').strip()
        source_text_en = request.form.get('source_text_en', '').strip()
        source_text_ar = request.form.get('source_text_ar', '').strip()

        if not en_term:
            flash('المصطلح الإنجليزي حقل إلزامي.', 'warning')
            return redirect(url_for('admin'))

        new_term = Term(
            en=en_term,
            ar=ar_term,
            definition=definition,
            subject_field=subject_field or 'قانون عام',
            source_text_en=source_text_en,
            source_text_ar=source_text_ar,
            status='pending'
        )
        db.session.add(new_term)
        db.session.commit()
        flash('تمت إضافة المصطلح يدوياً وهو بانتظار المراجعة والاعتماد.', 'success')
        return redirect(url_for('admin'))
        
    pending_terms = Term.query.filter(Term.status.in_(['pending', 'ai_suggested'])).order_by(Term.date.desc()).all()
    approved_terms = Term.query.filter_by(status='approved').order_by(Term.en).all()
    new_incoming_count = Term.query.filter_by(status='pending').count()
    
    api_key, current_model = get_ai_config()
    
    return render_template('admin.html', 
                           pending_terms=pending_terms, 
                           approved_terms=approved_terms,
                           new_incoming_count=new_incoming_count,
                           has_api_key=bool(api_key),
                           current_model=current_model)

@app.route('/admin/save_settings', methods=['POST'])
@login_required
def save_settings():
    if current_user.role != 'admin': return "Access Denied", 403
    
    api_key = request.form.get('openrouter_api_key', '').strip()
    selected_model = request.form.get('openrouter_model', 'openai/gpt-3.5-turbo')
    
    if api_key:
        key_setting = Setting.query.filter_by(key='openrouter_api_key').first()
        if not key_setting:
            db.session.add(Setting(key='openrouter_api_key', value=api_key))
        else:
            key_setting.value = api_key
        
    model_setting = Setting.query.filter_by(key='openrouter_model').first()
    if not model_setting:
        model_setting = Setting(key='openrouter_model', value=selected_model)
        db.session.add(model_setting)
    else:
        model_setting.value = selected_model
        
    db.session.commit()
    flash('تم حفظ إعدادات OpenRouter ونموذج الذكاء الاصطناعي بنجاح!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/process_ai/<int:term_id>', methods=['POST'])
@login_required
def process_ai(term_id):
    if current_user.role != 'admin':
        return "Access Denied", 403
        
    term = Term.query.get_or_404(term_id)
    api_key, model = get_ai_config()
    if not api_key:
        flash('يرجى ضبط مفتاح OpenRouter في إعدادات الذكاء الاصطناعي أولاً.', 'danger')
        return redirect(url_for('admin'))

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://lexterm.legal",
        "X-Title": "LexTerm Legal Dictionary"
    }
    
    prompt = (
        f"أنت خبير في المصطلحات والترجمة القانونية. حلل المصطلح التالي:\n"
        f"المصطلح الإنجليزي: '{term.en}'\n"
        f"المقابل العربي الحالي: '{term.ar or ''}'\n"
        f"التعريف الحالي: '{term.definition or ''}'\n"
        f"المجال الحالي: '{term.subject_field or ''}'\n\n"
        f"أعد الرد بصيغة JSON نقية فقط (بدون أي نصوص إضافية أو markdown خارج JSON) تحتوي المفاتيح التالية باللغة العربية:\n"
        f'{{"ar": "أدق مقابل قانوني عربي", "definition": "شرح قانوني موجز ومحدد", "subject_field": "الفرع القانوني الدقيق مثل قانون جنائي، تجاري، مدني..."}}'
    )
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=25)
        if res.status_code != 200:
            flash(f'فشل الاتصال بـ OpenRouter (رمز الخطأ: {res.status_code})', 'danger')
            return redirect(url_for('admin'))
            
        raw_content = res.json()['choices'][0]['message']['content'].strip()
        if raw_content.startswith('```'):
            raw_content = re.sub(r'^```(?:json)?\s*', '', raw_content)
            raw_content = re.sub(r'\s*```$', '', raw_content)
            
        ai_data = json.loads(raw_content)
        if ai_data.get('ar'):
            term.ar = str(ai_data['ar']).strip()
        if ai_data.get('definition'):
            term.definition = str(ai_data['definition']).strip()
        if ai_data.get('subject_field'):
            term.subject_field = str(ai_data['subject_field']).strip()
            
        term.status = 'ai_suggested'
        db.session.commit()
        flash(f'تم تحسين المصطلح "{term.en}" بنجاح بواسطة الذكاء الاصطناعي [{model}].', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء معالجة الذكاء الاصطناعي: {str(e)}', 'danger')
        
    return redirect(url_for('admin'))

@app.route('/admin/bulk_action', methods=['POST'])
@login_required
def bulk_action():
    if current_user.role != 'admin':
        flash('غير مصرح لك بالدخول.', 'danger')
        return redirect(url_for('index'))
        
    action = request.form.get('action')
    term_ids = request.form.getlist('term_ids')
    
    if not term_ids:
        flash('لم يتم تحديد أي مصطلحات للقيام بهذه العملية!', 'warning')
        return redirect(url_for('admin'))
        
    try:
        term_ids_int = [int(t) for t in term_ids]
        if action == 'approve':
            Term.query.filter(Term.id.in_(term_ids_int)).update({Term.status: 'approved'}, synchronize_session=False)
            db.session.commit()
            flash('تم اعتماد المصطلحات المحددة بنجاح!', 'success')
        elif action == 'delete':
            Term.query.filter(Term.id.in_(term_ids_int)).delete(synchronize_session=False)
            db.session.commit()
            flash('تم حذف المصطلحات المحددة بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
        
    return redirect(url_for('admin'))

@app.route('/admin/approved_bulk_delete', methods=['POST'])
@login_required
def approved_bulk_delete():
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    term_ids = request.form.getlist('approved_term_ids')
    if not term_ids:
        flash('لم يتم تحديد أي مصطلحات من القاموس المحفوظ.', 'warning')
        return redirect(url_for('admin'))
        
    try:
        term_ids_int = [int(t) for t in term_ids]
        deleted_count = Term.query.filter(
            Term.id.in_(term_ids_int), 
            Term.status == 'approved'
        ).delete(synchronize_session=False)
        
        db.session.commit()
        flash(f'تم حذف {deleted_count} مصطلحاً محدداً من القاموس المحفوظ.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء محاولة الحذف: {str(e)}', 'danger')
        
    return redirect(url_for('admin'))

@app.route('/admin/approve/<int:term_id>', methods=['POST'])
@login_required
def approve_term(term_id):
    if current_user.role != 'admin': return "Access Denied", 403
    term = Term.query.get_or_404(term_id)
    term.status = 'approved'
    db.session.commit()
    flash(f'تم اعتماد ونشر المصطلح "{term.en}" بنجاح!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:term_id>', methods=['POST'])
@login_required
def delete_term(term_id):
    if current_user.role != 'admin': return "Access Denied", 403
    term = Term.query.get_or_404(term_id)
    db.session.delete(term)
    db.session.commit()
    flash('تم حذف المصطلح بنجاح.', 'warning')
    return redirect(url_for('admin'))

@app.route('/admin/deduplicate', methods=['POST'])
@login_required
def deduplicate_terms():
    if current_user.role != 'admin':
        return "Access Denied", 403

    approved = Term.query.filter_by(status='approved').order_by(Term.id).all()
    kept_keys = set()
    dup_approved = []
    for term in approved:
        key = _pair_key(term.en, term.ar)
        if not key or key in kept_keys:
            dup_approved.append(term)
        else:
            kept_keys.add(key)

    pending = Term.query.filter(Term.status.in_(['pending', 'ai_suggested'])).order_by(Term.id).all()
    dup_pending = []
    seen_pending = set()
    for term in pending:
        key = _pair_key(term.en, term.ar)
        if not key or key in kept_keys or key in seen_pending:
            dup_pending.append(term)
        else:
            seen_pending.add(key)

    for term in dup_approved + dup_pending:
        db.session.delete(term)
    db.session.commit()

    total = len(dup_approved) + len(dup_pending)
    category = 'success' if total else 'info'
    flash(f'اكتملت مراجعة التكرارات: حُذف {len(dup_approved)} من المعتمد و{len(dup_pending)} من المعلق.', category)
    return redirect(url_for('admin'))

@app.route('/admin/edit/<int:term_id>', methods=['POST'])
@login_required
def edit_term(term_id):
    if current_user.role != 'admin': return "Access Denied", 403
    term = Term.query.get_or_404(term_id)
    term.en = request.form.get('en', '').strip()
    term.ar = request.form.get('ar', '').strip()
    term.definition = request.form.get('definition', '').strip()
    term.subject_field = request.form.get('subject_field', '').strip() or 'قانون عام'
    term.source_text_en = request.form.get('source_text_en', '').strip()
    term.source_text_ar = request.form.get('source_text_ar', '').strip()
    db.session.commit()
    flash('تم حفظ تعديلات المصطلح بنجاح.', 'success')
    return redirect(url_for('admin'))

# --- تصدير القاموس المعتمد بصيغة CSV (محمي من Formula Injection وبدون Double BOM) ---
@app.route('/admin/export/csv')
@login_required
def export_csv():
    if current_user.role != 'admin': return "Access Denied", 403

    terms = Term.query.filter_by(status='approved').order_by(Term.en).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['#', 'ID', 'English Term (en)', 'Arabic Term (ar)', 'Subject Field', 'Definition', 'Source Text EN', 'Source Text AR', 'Date Added'])
    for idx, term in enumerate(terms, start=1):
        writer.writerow([
            idx,
            term.id,
            sanitize_excel_cell(term.en),
            sanitize_excel_cell(term.ar or ''),
            sanitize_excel_cell(term.subject_field or ''),
            sanitize_excel_cell(term.definition or ''),
            sanitize_excel_cell(term.source_text_en or ''),
            sanitize_excel_cell(term.source_text_ar or ''),
            term.date.strftime('%Y-%m-%d') if term.date else ''
        ])

    data = output.getvalue()
    return send_file(
        io.BytesIO(data.encode('utf-8-sig')),
        mimetype='text/csv; charset=utf-8',
        as_attachment=True,
        download_name=f'legal_dictionary_{datetime.now().strftime("%Y-%m-%d")}.csv'
    )

# --- تصدير القاموس المعتمد بصيغة Excel (محمي من Formula Injection) ---
@app.route('/admin/export/excel')
@app.route('/admin/export/xls')
@login_required
def export_excel():
    if current_user.role != 'admin': return "Access Denied", 403

    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    terms = Term.query.filter_by(status='approved').order_by(Term.en).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Legal Dictionary"

    headers = [
        '#', 'ID', 'English Term (en)', 'Arabic Term (ar)',
        'Subject Field', 'Definition', 'Source Text EN', 'Source Text AR', 'Date Added'
    ]
    ws.append(headers)

    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1E293B', end_color='1E293B', fill_type='solid')
    header_align = Alignment(horizontal='center', vertical='center', wrap_text=True)

    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align

    for idx, term in enumerate(terms, start=1):
        ws.append([
            idx,
            term.id,
            sanitize_excel_cell(term.en),
            sanitize_excel_cell(term.ar or ''),
            sanitize_excel_cell(term.subject_field or ''),
            sanitize_excel_cell(term.definition or ''),
            sanitize_excel_cell(term.source_text_en or ''),
            sanitize_excel_cell(term.source_text_ar or ''),
            term.date.strftime('%Y-%m-%d') if term.date else ''
        ])

    align_left = Alignment(horizontal='left', vertical='top', wrap_text=True)
    align_right = Alignment(horizontal='right', vertical='top', wrap_text=True)
    align_center = Alignment(horizontal='center', vertical='top')

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(headers)):
        row[0].alignment = align_center # #
        row[1].alignment = align_center # ID
        row[2].alignment = align_left   # en
        row[3].alignment = align_right  # ar
        row[4].alignment = align_center # subject_field
        row[5].alignment = align_right  # definition
        row[6].alignment = align_left   # source_text_en
        row[7].alignment = align_right  # source_text_ar
        row[8].alignment = align_center # date

    col_widths = {1: 8, 2: 8, 3: 25, 4: 25, 5: 22, 6: 40, 7: 40, 8: 40, 9: 14}
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    excel_output = io.BytesIO()
    wb.save(excel_output)
    excel_output.seek(0)

    return send_file(
        excel_output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'legal_dictionary_{datetime.now().strftime("%Y-%m-%d")}.xlsx'
    )

# --- تصدير القاموس المعتمد بصيغة TBX (ISO 30042) ---
@app.route('/admin/export/tbx')
@login_required
def export_tbx():
    if current_user.role != 'admin': return "Access Denied", 403

    terms = Term.query.filter_by(status='approved').order_by(Term.en).all()
    today = datetime.now().strftime('%Y-%m-%d')

    xml_entities = {'"': '&quot;', "'": '&apos;'}

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE martif PUBLIC "ISO 12200:1999A//DTD Martif plain//EN" "TBXcdv02.dtd">',
        '<martif type="TBX" xml:lang="en">',
        '  <martifHeader>',
        '    <fileDesc>',
        '      <titleStmt>',
        '        <title>LexTerm Legal Dictionary - Bilingual Legal Terms (EN-AR)</title>',
        '      </titleStmt>',
        '      <sourceDesc>',
        f'        <p>Exported from LexTerm Legal Dictionary platform on {today}</p>',
        '      </sourceDesc>',
        '    </fileDesc>',
        '    <encodingDesc>',
        '      <p type="XCSURI">TBXcdv02.xcs</p>',
        '    </encodingDesc>',
        '  </martifHeader>',
        '  <text>',
        '    <body>',
    ]
    for term in terms:
        lines.append(f'      <termEntry id="c{term.id:06d}">')
        if term.subject_field:
            clean_sub = escape(clean_xml_text(term.subject_field), xml_entities)
            lines.append(f'        <descripGrp><descrip type="subjectField">{clean_sub}</descrip></descripGrp>')
        clean_en = escape(clean_xml_text(term.en), xml_entities)
        lines.append('        <langSet xml:lang="en">')
        lines.append(f'          <tig><term>{clean_en}</term></tig>')
        lines.append('        </langSet>')
        if term.ar:
            clean_ar = escape(clean_xml_text(term.ar), xml_entities)
            lines.append('        <langSet xml:lang="ar">')
            if term.definition:
                clean_def = escape(clean_xml_text(term.definition), xml_entities)
                lines.append(f'          <descripGrp><descrip type="definition">{clean_def}</descrip></descripGrp>')
            lines.append(f'          <tig><term>{clean_ar}</term></tig>')
            lines.append('        </langSet>')
        lines.append('      </termEntry>')
    lines += [
        '    </body>',
        '  </text>',
        '</martif>',
    ]

    return send_file(
        io.BytesIO('\n'.join(lines).encode('utf-8')),
        mimetype='application/xml',
        as_attachment=True,
        download_name=f'legal_dictionary_{today}.tbx'
    )

if __name__ == '__main__':
    app.run(debug=True)
