import os
from app import app, db, User, bcrypt

with app.app_context():
    print("Connecting to database and creating tables...")
    db.create_all()

    # لا توجد كلمات مرور افتراضية إطلاقاً — الفشل الصريح إذا لم تُضبط المتغيرات
    admin_initial_password = os.environ.get('ADMIN_INITIAL_PASSWORD')
    reader_initial_password = os.environ.get('READER_INITIAL_PASSWORD')

    if not admin_initial_password:
        raise SystemExit(
            "❌ ADMIN_INITIAL_PASSWORD غير مضبوط — لن يتم إنشاء حساب الأدمن بكلمة مرور افتراضية.\n"
            "   اضبط المتغير في .env ثم أعد التشغيل."
        )

    if not reader_initial_password:
        raise SystemExit(
            "❌ READER_INITIAL_PASSWORD غير مضبوط — لن يتم إنشاء حساب القارئ بكلمة مرور افتراضية."
        )

    # الحسابات الموجودة لا تُمس أبداً
    if not User.query.filter_by(username='admin').first():
        admin_pw = bcrypt.generate_password_hash(admin_initial_password).decode('utf-8')
        admin = User(username='admin', password=admin_pw, role='admin')
        db.session.add(admin)
        print("Initial admin user created.")
    else:
        print("Admin user already exists — skipping (password unchanged).")

    if not User.query.filter_by(username='reader').first():
        reader_pw = bcrypt.generate_password_hash(reader_initial_password).decode('utf-8')
        reader = User(username='reader', password=reader_pw, role='reader')
        db.session.add(reader)
        print("Initial reader user created.")
    else:
        print("Reader user already exists — skipping (password unchanged).")

    db.session.commit()
    print("✅ Success: Database tables and users initialized successfully!")
