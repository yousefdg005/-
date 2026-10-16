from app import app, db, User, bcrypt

with app.app_context():
    print("Connecting to Neon PostgreSQL and creating tables...")
    db.create_all()
    
    # إنشاء حساب الأدمن والقارئ الافتراضيين
    if not User.query.filter_by(username='admin').first():
        admin_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(username='admin', password=admin_pw, role='admin')
        db.session.add(admin)
        
    if not User.query.filter_by(username='reader').first():
        reader_pw = bcrypt.generate_password_hash('reader123').decode('utf-8')
        reader = User(username='reader', password=reader_pw, role='reader')
        db.session.add(reader)
        
    db.session.commit()
    print("✅ Success: Database tables and default users (admin/reader) created successfully!")