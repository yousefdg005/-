import os
from app import app, db, User, bcrypt

with app.app_context():
    print("Connecting to Neon PostgreSQL and creating tables...")
    db.create_all()
    
    # جلب كلمة المرور الأولية للأدمن من متغير البيئة مع بديل قوي افتراضي
    admin_initial_password = os.environ.get('ADMIN_INITIAL_PASSWORD', 'AdminSecureFallback#2026!')
    reader_initial_password = os.environ.get('READER_INITIAL_PASSWORD', 'ReaderSecureFallback#2026!')
    
    # إنشاء حساب الأدمن والقارئ الافتراضيين
    if not User.query.filter_by(username='admin').first():
        admin_pw = bcrypt.generate_password_hash(admin_initial_password).decode('utf-8')
        admin = User(username='admin', password=admin_pw, role='admin')
        db.session.add(admin)
        print("Initial admin user created.")
        
    if not User.query.filter_by(username='reader').first():
        reader_pw = bcrypt.generate_password_hash(reader_initial_password).decode('utf-8')
        reader = User(username='reader', password=reader_pw, role='reader')
        db.session.add(reader)
        print("Initial reader user created.")
        
    db.session.commit()
    print("✅ Success: Database tables and users initialized successfully!")
