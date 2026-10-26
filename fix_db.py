from app import app, db
from sqlalchemy import text

with app.app_context():
    print("⏳ Updating database schema in Neon (Renaming columns and adding subject_field)...")
    
    try:
        # تغيير اسم english_term إلى en
        db.session.execute(text("ALTER TABLE term RENAME COLUMN english_term TO en;"))
        # تغيير اسم arabic_term إلى ar
        db.session.execute(text("ALTER TABLE term RENAME COLUMN arabic_term TO ar;"))
        # تغيير اسم arabic_description إلى definition
        db.session.execute(text("ALTER TABLE term RENAME COLUMN arabic_description TO definition;"))
        
        db.session.commit()
        print("✅ Columns renamed successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Note on renaming columns (they might already be renamed): {e}")

    try:
        # إضافة عمود subject_field الجديد
        db.session.execute(text("ALTER TABLE term ADD COLUMN IF NOT EXISTS subject_field VARCHAR(150) DEFAULT 'قانون عام';"))
        
        # التأكد من وجود created_at
        db.session.execute(text("ALTER TABLE term ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
        
        db.session.commit()
        print("✅ New columns added successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Note on adding columns: {e}")
        
    db.create_all()
    print("✅ Schema update process complete!")
