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

# جدول حفظ إعدادات الأدمن
class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

# إنشاء الجداول تلقائياً عند الإقلاع
with app.app_context():
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
    ingest_key = os.getenv('INGEST_API_KEY', 'my_secure_platform_ingest_token_2026')
    expected_token = f"Bearer {ingest_key}"
    
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
        return redirect(url_for('admin'))
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        flash('Account created successfully! You can now login as a Reader.', 'success')
        return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dictionary')
@login_required
def dictionary():
    terms = Term.query.filter_by(status='approved').order_by(Term.english_term).all()
    return render_template('dictionary.html', terms=terms)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    if request.method == 'POST':
        english_term = request.form.get('english_term')
        arabic_term = request.form.get('arabic_term')
        arabic_description = request.form.get('arabic_description')
        
        new_term = Term(
            english_term=english_term,
            arabic_term=arabic_term,
            arabic_description=arabic_description,
            status='pending'
        )
        db.session.add(new_term)
        db.session.commit()
        flash('Term added manually and is pending review.', 'success')
        return redirect(url_for('admin'))
        
    pending_terms = Term.query.filter(Term.status.in_(['pending', 'ai_suggested'])).order_by(Term.date.desc()).all()
    approved_terms = Term.query.filter_by(status='approved').all()
    new_incoming_count = Term.query.filter_by(status='pending').count()
    
    api_key, current_model = get_ai_config()
    
    return render_template('admin.html', 
                           pending_terms=pending_terms, 
                           approved_terms=approved_terms,
                           new_incoming_count=new_incoming_count,
                           openrouter_api_key=api_key,
                           current_model=current_model)

# حفظ إعدادات OpenRouter
@app.route('/admin/save_settings', methods=['POST'])
@login_required
def save_settings():
    if current_user.role != 'admin': return "Access Denied", 403
    
    api_key = request.form.get('openrouter_api_key', '').strip()
    selected_model = request.form.get('openrouter_model', 'openai/gpt-3.5-turbo')
    
    key_setting = Setting.query.filter_by(key='openrouter_api_key').first()
    if not key_setting:
        key_setting = Setting(key='openrouter_api_key', value=api_key)
        db.session.add(key_setting)
    else:
        key_setting.value = api_key
        
    model_setting = Setting.query.filter_by(key='openrouter_model').first()
    if not model_setting:
        model_setting = Setting(key='openrouter_model', value=selected_model)
        db.session.add(model_setting)
    else:
        model_setting.value = selected_model
        
    db.session.commit()
    flash('OpenRouter settings and AI Model saved successfully!', 'success')
    return redirect(url_for('admin'))

# معالجة العمليات الجماعية (اعتماد المحدد / حذف المحدد)
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
        
    for term_id in term_ids:
        term = Term.query.get(term_id)
        if term:
            if action == 'approve':
                term.status = 'approved'
            elif action == 'delete':
                db.session.delete(term)
                
    db.session.commit()
    
    if action == 'approve':
        flash('تم اعتماد المصطلحات المحددة بنجاح!', 'success')
    elif action == 'delete':
        flash('تم حذف المصطلحات المحددة بنجاح!', 'success')
        
    return redirect(url_for('admin'))

@app.route('/admin/approve/<int:term_id>')
@login_required
def approve_term(term_id):
    if current_user.role != 'admin': return "Access Denied", 403
    term = Term.query.get_or_404(term_id)
    term.status = 'approved'
    db.session.commit()
    flash('Term approved and published!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:term_id>')
@login_required
def delete_term(term_id):
    if current_user.role != 'admin': return "Access Denied", 403
    term = Term.query.get_or_404(term_id)
    db.session.delete(term)
    db.session.commit()
    flash('Term deleted.', 'warning')
    return redirect(url_for('admin'))

@app.route('/admin/edit/<int:term_id>', methods=['POST'])
@login_required
def edit_term(term_id):
    if current_user.role != 'admin': return "Access Denied", 403
    term = Term.query.get_or_404(term_id)
    term.english_term = request.form.get('english_term')
    term.arabic_term = request.form.get('arabic_term')
    term.arabic_description = request.form.get('arabic_description')
    db.session.commit()
    flash('Term updated.', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)