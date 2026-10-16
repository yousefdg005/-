import os
import requests
import json
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret_key_dictionary_2026_xyz')
db_url = os.getenv('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

# --- الجداول (Database Models) ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='reader')

class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    english_term = db.Column(db.String(255), nullable=False)
    arabic_term = db.Column(db.String(255), nullable=True)
    arabic_description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, default=db.func.now())
    status = db.Column(db.String(50), default='pending')

# تحديث هيكل قاعدة البيانات تلقائياً عند الإقلاع
with app.app_context():
    try:
        from sqlalchemy import text
        db.session.execute(text("ALTER TABLE term ADD COLUMN IF NOT EXISTS english_term VARCHAR(255);"))
        db.session.execute(text("ALTER TABLE term ADD COLUMN IF NOT EXISTS arabic_term VARCHAR(255);"))
        db.session.execute(text("ALTER TABLE term ADD COLUMN IF NOT EXISTS arabic_description TEXT;"))
        db.session.execute(text("ALTER TABLE term ADD COLUMN IF NOT EXISTS date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
        db.session.commit()
    except Exception as e:

        db.session.rollback()      
    db.create_all()
# جدول حفظ إعدادات الأدمن (مثل المفتاح والنموذج المختار)
class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
with app.app_context():
    try:
        from sqlalchemy import text
        db.session.execute(text("ALTER TABLE term ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        
    db.create_all()
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# دالة مساعدة لجلب إعدادات الذكاء الاصطناعي
def get_ai_config():
    api_key_setting = Setting.query.filter_by(key='openrouter_api_key').first()
    model_setting = Setting.query.filter_by(key='openrouter_model').first()
    
    api_key = api_key_setting.value if api_key_setting else os.getenv('OPENROUTER_API_KEY', '')
    model = model_setting.value if model_setting else 'openai/gpt-3.5-turbo'
    return api_key, model

# --- API استقبال المصطلحات من المنصة (Streamlit) ---
@app.route('/api/receive-terms', methods=['POST'])
def receive_terms():
    auth_header = request.headers.get('Authorization')
    expected_token = f"Bearer {os.getenv('INGEST_API_KEY')}"
    
    if not auth_header or auth_header != expected_token:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    terms = data.get('terms', [])
    
    for item in terms:
        eng = item.get('english_term')
        if eng:
            new_term = Term(
                english_term=eng,
                arabic_term=item.get('arabic_term'),
                arabic_description=item.get('arabic_description')
            )
            db.session.add(new_term)
            
    db.session.commit()
    return jsonify({'message': 'Terms received successfully'}), 201
# --- المسارات والصفحات ---
@app.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('dictionary'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dictionary')
@login_required
def dictionary():
    terms = Term.query.filter_by(status='approved').order_by(Term.word).all()
    return render_template('dictionary.html', terms=terms)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    if request.method == 'POST':
        word = request.form.get('word')
        definition = request.form.get('definition')
        new_term = Term(word=word, definition=definition, status='pending')
        db.session.add(new_term)
        db.session.commit()
        flash('Term added manually and is pending review.', 'success')
        return redirect(url_for('admin_dashboard'))
        
    pending_terms = Term.query.filter(Term.status.in_(['pending', 'ai_suggested'])).order_by(Term.created_at.desc()).all()
    approved_terms = Term.query.filter_by(status='approved').all()
    
    # إحصائيات وإشعارات المصطلحات
    new_incoming_count = Term.query.filter_by(status='pending').count()
    
    # جلب الإعدادات الحالية لعرضها في النموذج
    api_key, current_model = get_ai_config()
    
    return render_template('admin.html', 
                           pending_terms=pending_terms, 
                           approved_terms=approved_terms,
                           new_incoming_count=new_incoming_count,
                           openrouter_api_key=api_key,
                           current_model=current_model)

# حفظ إعدادات OpenRouter المفتاح والنموذج
@app.route('/admin/save_settings', methods=['POST'])
@login_required
def save_settings():
    if current_user.role != 'admin': return "Access Denied", 403
    
    api_key = request.form.get('openrouter_api_key', '').strip()
    selected_model = request.form.get('openrouter_model', 'openai/gpt-3.5-turbo')
    
    # حفظ أو تحديث المفتاح
    key_setting = Setting.query.filter_by(key='openrouter_api_key').first()
    if not key_setting:
        key_setting = Setting(key='openrouter_api_key', value=api_key)
        db.session.add(key_setting)
    else:
        key_setting.value = api_key
        
    # حفظ أو تحديث النموذج
    model_setting = Setting.query.filter_by(key='openrouter_model').first()
    if not model_setting:
        model_setting = Setting(key='openrouter_model', value=selected_model)
        db.session.add(model_setting)
    else:
        model_setting.value = selected_model
        
    db.session.commit()
    flash('OpenRouter settings and AI Model saved successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# معالجة فحص التكرار بـ AI باستخدام النموذج والمفتاح المختارين
@app.route('/admin/deduplicate_ai')
@login_required
def deduplicate_ai():
    if current_user.role != 'admin': return "Access Denied", 403
    
    pending_terms = Term.query.filter_by(status='pending').all()
    if not pending_terms:
        flash('No pending terms to analyze.', 'info')
        return redirect(url_for('admin_dashboard'))
        
    api_key, model = get_ai_config()
    if not api_key:
        flash('Please configure your OpenRouter API Key in the settings first.', 'danger')
        return redirect(url_for('admin_dashboard'))

    terms_data = [{"id": t.id, "word": t.word, "definition": t.definition} for t in pending_terms]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Analyze this JSON list of dictionary terms for duplicates:
    {json.dumps(terms_data, ensure_ascii=False)}
    
    Identify duplicate terms. Respond ONLY with a pure JSON array of duplicate groups to delete.
    Format:
    [
      {{"keep_id": 1, "delete_ids": [2, 3], "reason": "Duplicate"}}
    ]
    If no duplicates exist, return [].
    """
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        content = response.json()['choices'][0]['message']['content']
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '')
            
        suggestions = json.loads(content)
        deleted_count = 0
        for group in suggestions:
            delete_ids = group.get('delete_ids', [])
            for d_id in delete_ids:
                term_to_del = Term.query.get(d_id)
                if term_to_del and term_to_del.status == 'pending':
                    db.session.delete(term_to_del)
                    deleted_count += 1
                    
        db.session.commit()
        flash(f'AI Deduplication Complete using [{model}]! Removed {deleted_count} duplicates.', 'success')
    except Exception as e:
        flash('Error executing AI deduplication. Check your API Key and Model.', 'danger')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/process_ai/<int:term_id>')
@login_required
def process_ai(term_id):
    if current_user.role != 'admin': return "Access Denied", 403
    term = Term.query.get_or_404(term_id)
    
    api_key, model = get_ai_config()
    if not api_key:
        flash('Please configure your OpenRouter API Key in settings first.', 'danger')
        return redirect(url_for('admin_dashboard'))

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"Analyze term: Word: '{term.word}', Definition: '{term.definition}'. Return pure JSON only with keys: 'category' and 'refined_definition'."
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post("[https://openrouter.ai/api/v1/chat/completions](https://openrouter.ai/api/v1/chat/completions)", headers=headers, json=data)
        content = response.json()['choices'][0]['message']['content']
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '')
        ai_data = json.loads(content)
        term.category = ai_data.get('category', term.category)
        term.definition = ai_data.get('refined_definition', term.definition)
        term.status = 'ai_suggested'
        db.session.commit()
        flash(f'AI refined term "{term.word}" using [{model}].', 'info')
    except Exception as e:
        flash('AI Error. Ensure API Key and selected Model are valid.', 'danger')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve/<int:term_id>')
@login_required
def approve_term(term_id):
    if current_user.role != 'admin': return "Access Denied", 403
    term = Term.query.get_or_404(term_id)
    term.status = 'approved'
    db.session.commit()
    flash('Term approved and published!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:term_id>')
@login_required
def delete_term(term_id):
    if current_user.role != 'admin': return "Access Denied", 403
    term = Term.query.get_or_404(term_id)
    db.session.delete(term)
    db.session.commit()
    flash('Term deleted.', 'warning')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<int:term_id>', methods=['POST'])
@login_required
def edit_term(term_id):
    if current_user.role != 'admin': return "Access Denied", 403
    term = Term.query.get_or_404(term_id)
    term.word = request.form.get('word')
    term.definition = request.form.get('definition')
    term.category = request.form.get('category')
    db.session.commit()
    flash('Term updated.', 'success')
    return redirect(url_for('admin_dashboard'))
@app.route('/register', methods=['GET', 'POST'])
def register():
    # إذا كان المستخدم مسجلاً الدخول بالفعل، توجيهه للصفحة الرئيسية
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 1. التأكد من تطابق كلمتي المرور
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))
            
        # 2. التحقق من أن اسم المستخدم غير مستخدم سابقاً
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username is already taken. Please choose another.', 'danger')
            return redirect(url_for('register'))
            
        # 3. تشفير كلمة المرور وإنشاء حساب القارئ (role='reader')
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_reader = User(username=username, password=hashed_pw, role='reader')
        
        db.session.add(new_reader)
        db.session.commit()
        
        flash('Account created successfully! You can now login as a Reader.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')
if __name__ == '__main__':
    app.run(debug=True)