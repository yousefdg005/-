from app import app, db
from sqlalchemy import text

with app.app_context():
    print("⏳ Updating database schema in Neon...")
    
    # 1. إضافة عمود created_at لجدول term إذا لم يكن موجوداً
    try:
        db.session.execute(text("ALTER TABLE term ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
        db.session.commit()
        print("✅ Column 'created_at' added successfully to 'term' table!")
    except Exception as e:
        db.session.rollback()
        print(f"Note on created_at: {e}")
        
    # 2. إنشاء الجداول الجديدة مثل جدول Setting إذا لم تكن موجودة
    db.create_all()
    print("✅ All tables (including Setting) are now fully up to date!")