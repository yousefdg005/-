import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
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

# تحديث هيكل جدول المصطلحات
class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    en = db.Column(db.String(255), nullable=False)
    ar = db.Column(db.String(255), nullable=True)
    definition = db.Column(db.Text, nullable=True)
    subject_field = db.Column(db.String(150), nullable=True, default="قانون عام") # إضافة عمود المجال
    date = db.Column(db.DateTime, default=db.func.now())
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())

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
    ingest_key = os.environ.get('INGEST_API_KEY')
    if not ingest_key:
        return jsonify({'error': 'Server configuration error: INGEST_API_KEY is not configured'}), 500

    expected_token = f"Bearer {ingest_key}"
    if not auth_header or auth_header != expected_token:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON payload'}), 400

    terms = data.get('terms', [])
    if not isinstance(terms, list):
        return jsonify({'error': 'Terms payload must be a list'}), 400
    
    try:
        added_count = 0
        for item in terms:
            eng = item.get('en')
            if eng:
                new_term = Term(
                    en=eng,
                    ar=item.get('ar'),
                    definition=item.get('definition'),
                    subject_field=item.get('subject field', 'قانون عام'),
                    status='pending'
                )
                db.session.add(new_term)
                added_count += 1
                
        db.session.commit()
        return jsonify({'message': 'Terms received successfully', 'count': added_count}), 201
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
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not password:
            flash('يرجى ملء جميع الحقول المطلوبة.', 'danger')
            return render_template('login.html')
            
        if confirm_password and password != confirm_password:
            flash('كلمة المرور وتأكيد كلمة المرور غير متطابقتين.', 'danger')
            return render_template('login.html')
            
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم مسجل مسبقاً، يرجى اختيار اسم آخر.', 'warning')
            return render_template('login.html')
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password, role='reader')
        db.session.add(new_user)
        db.session.commit()
        
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
    # تحديث جلب البيانات لترتيبها حسب الحقل الجديد
    terms = Term.query.filter_by(status='approved').order_by(Term.en).all()
    return render_template('dictionary.html', terms=terms)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.role != 'admin':
        return "Access Denied", 403
    
    if request.method == 'POST':
        # تحديث الإدخال اليدوي للأدمن ليطابق الأعمدة الجديدة
        en_term = request.form.get('en')
        ar_term = request.form.get('ar')
        definition = request.form.get('definition')
        subject_field = request.form.get('subject_field', 'قانون عام')
        
        new_term = Term(
            en=en_term,
            ar=ar_term,
            definition=definition,
            subject_field=subject_field,
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
        # تحويل المعرفات إلى أعداد صحيحة
        term_ids_int = [int(t) for t in term_ids]
        terms = Term.query.filter(Term.id.in_(term_ids_int)).all()
        
        for term in terms:
            if action == 'approve':
                term.status = 'approved'
            elif action == 'delete':
                db.session.delete(term)
                
        db.session.commit()
        
        if action == 'approve':
            flash('تم اعتماد المصطلحات المحددة بنجاح!', 'success')
        elif action == 'delete':
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
        # تحويل المعرفات إلى أعداد صحيحة لتتوافق مع نوع العمود في PostgreSQL
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

@app.route('/admin/deduplicate_ai')
@login_required
def deduplicate_ai():
    if current_user.role != 'admin': 
        return "Access Denied", 403
    flash('AI Deduplication feature is ready.', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/edit/<int:term_id>', methods=['POST'])
@login_required
def edit_term(term_id):
    if current_user.role != 'admin': return "Access Denied", 403
    term = Term.query.get_or_404(term_id)
    # تحديث حقول التعديل للمصطلحات
    term.en = request.form.get('en')
    term.ar = request.form.get('ar')
    term.definition = request.form.get('definition')
    term.subject_field = request.form.get('subject_field')
    db.session.commit()
    flash('Term updated.', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
