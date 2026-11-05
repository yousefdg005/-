<div align="center">

# 🦉 LexTerm — Legal Dictionary
### *قاموس المصطلحات القانونية*
#### Platform B — الواجهة الخلفية للمنظومة المتكاملة

<img src="static/img/logo.jpg" alt="LexTerm Logo" width="180">

---

**المطوّر:** يوسف نورالدين المقعمز  
**الإطار الأكاديمي:** مشروع تخرج — قسم الترجمة  
**الإصدار:** 3.0  
**الرابط المباشر:** [dictionaryly.onrender.com](https://dictionaryly.onrender.com)

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech)
[![Hosted on Render](https://img.shields.io/badge/Hosted%20on-Render.com-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)

</div>

---

## 📋 جدول المحتويات

1. [نظرة عامة](#1-نظرة-عامة)
2. [موقع المنصة في المنظومة الكاملة](#2-موقع-المنصة-في-المنظومة-الكاملة)
3. [المميزات الأساسية — البوابة الثالثة HITL](#3-المميزات-الأساسية--البوابة-الثالثة-hitl)
4. [الدوال البرمجية المبتكرة](#4-الدوال-البرمجية-المبتكرة)
5. [البدء والتشغيل](#5-البدء-والتشغيل)
6. [الاستضافة على Render.com](#6-الاستضافة-على-rendercom)
7. [سير العمل خطوة بخطوة](#7-سير-العمل-خطوة-بخطوة)
8. [نموذج البيانات](#8-نموذج-البيانات)
9. [المسارات (API Routes)](#9-المسارات-api-routes)
10. [بنية الأمان](#10-بنية-الأمان)
11. [التقنيات المستخدمة](#11-التقنيات-المستخدمة)
12. [صيغ التصدير](#12-صيغ-التصدير)

---

## 1. نظرة عامة

**LexTerm** هو تطبيق ويب مبني بـ **Python + Flask**، يعمل كقاعدة بيانات ونظام إدارة ثنائي اللغة (إنجليزي ↔ عربي) لقواعد المصطلحات القانونية. يستقبل هذا التطبيق المصطلحات المستخرجة آلياً من [منصة LexTerm](https://github.com/yousefdg005/qwqw) عبر REST API مؤمّن، ويضعها في قائمة انتظار للمراجعة البشرية، ثم يتيح تصدير المصطلحات المعتمدة بصيغ متعددة متوافقة مع أدوات الترجمة بمساعدة الحاسوب (CAT Tools).

**منظومة الأدوار:**
- **Admin (مدير قاعدة المصطلحات):** يستعرض المصطلحات الواردة، يعتمدها أو يرفضها أو يعدّلها، ويُصدّر القاموس المكتمل
- **Reader (قارئ):** يتصفح القاموس المعتمد فقط (للاطلاع والمرجعية)

> **المبدأ التصميمي:** لا يظهر أي مصطلح في القاموس العام ما لم يوافق عليه مدير بشري صراحةً — هذا هو جوهر نظرية HITL المطبّقة.

---

## 2. موقع المنصة في المنظومة الكاملة

```mermaid
flowchart LR
    A["⚡ LexTerm\nPlatform A — qwqw"] -->|"POST /api/receive-terms\nBearer Token Auth\n10 مصطلحات / دُفعة"| B

    subgraph P2["🦉 هذه المنصة — LexTerm"]
        B["receive_terms() API\nتحقق من Bearer Token\nكشف التكرار الفوري\nstatus = 'pending'"]
        B --> C["📋 لوحة Admin\nعرض المصطلحات المعلّقة\nمع نص المصدر"]
        C --> D{"👤 قرار المدير"}
        D -- "✅ اعتماد" --> E["status = 'approved'\nيظهر في القاموس"]
        D -- "✏️ تعديل" --> F["تصحيح الترجمة\nأو التعريف أو الحقل"]
        D -- "🗑️ حذف" --> G["حذف نهائي من قاعدة البيانات"]
        F --> E
        E --> H["📤 تصدير متعدد الصيغ"]
    end

    H --> I["TBX ISO 30042\nSDL Trados / memoQ"]
    H --> J["CSV UTF-8 BOM\nExcel / LibreOffice"]
    H --> K["Excel XLSX\nمنسّق احترافياً"]

    style D fill:#EAB308,color:#000,font-weight:bold
    style P2 fill:#1E293B,color:#EEF2F8
```

---

## 3. المميزات الأساسية — البوابة الثالثة HITL

هذه المنصة تُمثّل **البوابة البشرية الثالثة والأخيرة** في سلسلة المنظومة. كل مصطلح يصل من Platform A يُسجَّل بحالة `pending` ويظهر في لوحة Admin للمراجعة.

### 3.1 عرض السياق الكامل لكل مصطلح

عند مراجعة كل مصطلح، يرى المدير:
- **المصطلح الإنجليزي** والمقابل العربي
- **التعريف** المُولَّد بالعربية (جنس + فصل)
- **حقل التخصص** (مثال: Contract Law, Property Law)
- **الجملة المصدر الإنجليزية** التي استُخرج منها المصطلح
- **الجملة المصدر العربية** الموازية

هذا السياق يمنح المدير كل المعلومات اللازمة للحكم على صحة المصطلح ودقة ترجمته **داخل سياقه الفعلي** في النص القانوني الأصلي.

### 3.2 الإجراءات المتاحة للمدير

| الإجراء | الوصف | الأثر في قاعدة البيانات |
|---------|-------|------------------------|
| **اعتماد فردي** | نقرة واحدة على "Approve" | `status → 'approved'` |
| **اعتماد جماعي** | تحديد عدة مصطلحات + Approve All | `status → 'approved'` لكل المحدد |
| **تعديل** | تصحيح أي حقل (en, ar, definition, subject_field) | تحديث فوري في PostgreSQL |
| **حذف فردي** | نقرة على "Delete" | حذف نهائي من الجدول |
| **حذف جماعي** | تحديد + Delete Selected | حذف نهائي لكل المحدد |
| **إزالة التكرار** | زر "Deduplicate" | حذف النسخ المكررة بالاحتفاظ بالأقدم |

### 3.3 المصطلحات المعتمدة — القاموس العام

عند الاعتماد، يصبح المصطلح مرئياً في مسار `/dictionary` المتاح لجميع المستخدمين المسجّلين. القاموس يعرض المصطلحات مرتبةً أبجدياً باللغة الإنجليزية مع إمكانية البحث.

---

## 4. الدوال البرمجية المبتكرة

### 4.1 `receive_terms()` — نقطة نهاية API الاستقبال

**الموقع:** `app.py` السطور 120–184  
**المسار:** `POST /api/receive-terms`

```python
@csrf.exempt          # مُعفى من CSRF — المصادقة بـ Bearer Token
@app.route('/api/receive-terms', methods=['POST'])
@limiter.limit("60 per hour")
def receive_terms():
    # 1. التحقق من Bearer Token
    auth_header = request.headers.get('Authorization')
    expected_token = f"Bearer {os.environ.get('INGEST_API_KEY')}"
    if not auth_header or auth_header != expected_token:
        return jsonify({'error': 'Unauthorized'}), 401

    terms = request.get_json().get('terms', [])

    # 2. كشف التكرار الفوري قبل الإدراج
    existing_rows = db.session.query(Term.en).all()
    existing_keys = {_term_key(r[0]) for r in existing_rows if r[0]}
    seen_in_batch = set()
    added_count = skipped_count = 0

    for item in terms:
        norm_key = _term_key(item.get('en', ''))
        if not norm_key or norm_key in existing_keys or norm_key in seen_in_batch:
            skipped_count += 1; continue

        seen_in_batch.add(norm_key)
        existing_keys.add(norm_key)

        new_term = Term(
            en=item.get('en'), ar=item.get('ar'),
            definition=item.get('definition'),
            subject_field=item.get('subject field', 'قانون عام'),
            source_text_en=item.get('source_text_en') or item.get('source text en'),
            source_text_ar=item.get('source_text_ar') or item.get('source text ar'),
            status='pending'      # ← كل وارد يبدأ بالانتظار
        )
        db.session.add(new_term); added_count += 1

    db.session.commit()
    return jsonify({'added_count': added_count,
                    'skipped_duplicate_count': skipped_count}), 201
```

**نقاط التصميم:**
- **`@csrf.exempt`** مع **Bearer Token** بدلاً من كوكيز الجلسة — المسار يتلقى طلبات من تطبيق خارجي (Streamlit) لا من متصفح مستخدم، لذا CSRF غير ذي صلة والمصادقة بالرمز أنسب
- **كشف التكرار الفوري** ثنائي المستوى: داخل الدُّفعة الواحدة (`seen_in_batch`) وعبر كل قاعدة البيانات (`existing_keys`)
- **الإدراج الآمن من العمليات المتكررة (idempotent):** إعادة إرسال نفس الدُّفعة لا تُضيف نسخاً مكررة

---

### 4.2 `deduplicate_terms()` — إزالة التكرار الحتمية ثلاثية المراحل

**الموقع:** `app.py` السطور 430–465  
**المسار:** `POST /admin/deduplicate`

```python
def deduplicate_terms():
    # المرحلة 1: المصطلحات المعتمدة — احتفاظ بالأقدم (أصغر id)
    approved = Term.query.filter_by(status='approved').order_by(Term.id).all()
    kept_keys = set()
    dup_approved = []
    for term in approved:
        key = _term_key(term.en)
        if not key or key in kept_keys:
            dup_approved.append(term)   # مكرر — مُعلَّم للحذف
        else:
            kept_keys.add(key)

    # المرحلة 2: المصطلحات المعلّقة المطابِقة لمعتمدة موجودة → حذف
    # المرحلة 3: التكرارات بين المعلّقين أنفسهم → حذف
    pending = Term.query.filter(Term.status.in_(['pending', 'ai_suggested'])) \
                        .order_by(Term.id).all()
    dup_pending = []; seen_pending = set()
    for term in pending:
        key = _term_key(term.en)
        if key in kept_keys or key in seen_pending:
            dup_pending.append(term)
        else:
            seen_pending.add(key)

    for term in dup_approved + dup_pending:
        db.session.delete(term)
    db.session.commit()
```

الترتيب بـ `Term.id` (تصاعدي) يضمن **الاحتفاظ دائماً بأول إصدار أُدرج** — ثابت حيوي لقاعدة مصطلحات يخضع فيها الاعتماد الأول لوزن تحريري.

---

### 4.3 `_term_key()` — معيار التطبيع العالمي

**الموقع:** `app.py` السطور 113–116

```python
def _term_key(value):
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    value = re.sub(r"[\W_]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()
```

نفس الدالة الموجودة في Platform A بالضبط — يضمن ذلك **اتساق منطق كشف التكرار** عبر المنظومة كاملة. NFKC ضروري للعربية لتطبيع متغيرات التشكيل وأشكال الهمزة.

---

### 4.4 `export_tbx()` — تصدير ISO 30042 (TBX) لأدوات الترجمة

**الموقع:** `app.py` السطور 597–650  
**المسار:** `GET /admin/export/tbx`

```python
def export_tbx():
    terms = Term.query.filter_by(status='approved').order_by(Term.en).all()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE martif PUBLIC "ISO 12200:1999A//DTD Martif plain//EN" "TBXcdv02.dtd">',
        '<martif type="TBX" xml:lang="en">',
        '  <martifHeader>...',
        # رأس ملف TBX كاملاً
    ]
    for term in terms:
        lines.append(f'      <termEntry id="c{term.id:06d}">')
        if term.subject_field:
            lines.append(f'        <descripGrp>'
                         f'<descrip type="subjectField">{escape(term.subject_field)}</descrip>'
                         f'</descripGrp>')
        lines.append('        <langSet xml:lang="en">')
        lines.append(f'          <tig><term>{escape(term.en)}</term></tig>')
        lines.append('        </langSet>')
        if term.ar:
            lines.append('        <langSet xml:lang="ar">')
            if term.definition:
                lines.append(f'          <descripGrp>'
                             f'<descrip type="definition">{escape(term.definition)}</descrip>'
                             f'</descripGrp>')
            lines.append(f'          <tig><term>{escape(term.ar)}</term></tig>')
            lines.append('        </langSet>')
        lines.append('      </termEntry>')
```

**الإخراج:** ملف TBX متوافق مع **SDL MultiTerm** (مكوّن قاعدة المصطلحات في SDL Trados Studio) و**memoQ** و**Phrase TMS**، يحمل:
- المصطلح الإنجليزي والعربي
- التعريف العربي
- حقل التخصص (subjectField)
- معرّف فريد منسّق: `c000001`, `c000002`...

---

### 4.5 `export_csv()` — تصدير CSV مع BOM للعربية

**الموقع:** `app.py` السطور 484–514

```python
def export_csv():
    terms = Term.query.filter_by(status='approved').order_by(Term.en).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['#','ID','English Term (en)','Arabic Term (ar)',
                     'Subject Field','Definition','Source Text EN',
                     'Source Text AR','Date Added'])
    for idx, term in enumerate(terms, start=1):
        writer.writerow([idx, term.id, term.en, term.ar or '',
                         term.subject_field or '', term.definition or '',
                         term.source_text_en or '', term.source_text_ar or '',
                         term.date.strftime('%Y-%m-%d') if term.date else ''])

    # BOM (\\ufeff) يضمن عرض العربية صحيحاً في Excel
    data = '\ufeff' + output.getvalue()
    return send_file(io.BytesIO(data.encode('utf-8-sig')),
                     mimetype='text/csv; charset=utf-8',
                     as_attachment=True,
                     download_name=f'legal_dictionary_{datetime.now().strftime("%Y-%m-%d")}.csv')
```

> [!TIP]
> `utf-8-sig` هو ترميز Python الذي يُدرج BOM تلقائياً. بدونه يُعرض النص العربي في Excel كرموز غير مقروءة. هذا قرار تقني مقصود يوفّر على المستخدم خطوة "اختيار الترميز عند الاستيراد".

---

### 4.6 `export_excel()` — تصدير Excel منسّق احترافياً

**الموقع:** `app.py` السطور 517–594

```python
def export_excel():
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Legal Dictionary"

    # تنسيق رأس الجدول بخلفية داكنة ونص أبيض عريض
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1E293B', end_color='1E293B', fill_type='solid')

    # محاذاة ثنائية الاتجاه: LTR للإنجليزية، RTL للعربية
    align_left  = Alignment(horizontal='left',   vertical='top', wrap_text=True)
    align_right = Alignment(horizontal='right',  vertical='top', wrap_text=True)

    # عروض أعمدة مُحسَّنة
    col_widths = {1:8, 2:8, 3:25, 4:25, 5:22, 6:40, 7:40, 8:40, 9:14}
```

الملف الناتج يتضمن:
- رأس جدول بتصميم بصري مميز (خلفية `#1E293B`، نص أبيض)
- محاذاة يمينية للحقول العربية
- التفاف النص (Wrap text) للتعريفات ونصوص المصدر
- عروض أعمدة محسوبة لكل حقل

---

### 4.7 ترحيل المخطط الآمن — إضافة أعمدة لقواعد بيانات قائمة

**الموقع:** `app.py` السطور 80–97

```python
# يُنفَّذ عند كل إقلاع — آمن للتكرار (idempotent)
try:
    if db.engine.name == 'sqlite':
        cols = [row[1] for row in db.session.execute(
            text("PRAGMA table_info(term)")).fetchall()]
        if 'source_text_en' not in cols:
            db.session.execute(text("ALTER TABLE term ADD COLUMN source_text_en TEXT;"))

    else:  # PostgreSQL — Neon/Render
        db.session.execute(text(
            "ALTER TABLE term ADD COLUMN IF NOT EXISTS subject_field VARCHAR(150) DEFAULT 'قانون عام';"))
        db.session.execute(text(
            "ALTER TABLE term ADD COLUMN IF NOT EXISTS source_text_en TEXT;"))
        db.session.execute(text(
            "ALTER TABLE term ADD COLUMN IF NOT EXISTS source_text_ar TEXT;"))
    db.session.commit()
except Exception:
    db.session.rollback()
```

`db.create_all()` لا يُضيف أعمدة للجداول الموجودة مسبقاً. هذا الكود يُنفّذ `ALTER TABLE` عند كل إقلاع بأمان تام (`IF NOT EXISTS`) ليضمن توافق قواعد البيانات القديمة مع المخطط الجديد.

---

## 5. البدء والتشغيل

### المتطلبات

| المتطلب | التفصيل |
|---------|---------|
| Python | 3.10 أو أحدث |
| PostgreSQL | Neon (مُوصى به) أو SQLite للتطوير المحلي |
| `INGEST_API_KEY` | رمز مشترك مع Platform A — يُولَّد عشوائياً |
| `SECRET_KEY` | مفتاح جلسات Flask — يُولَّد عشوائياً |

### التشغيل المحلي

```bash
# 1. استنساخ المستودع
git clone https://github.com/yousefdg005/-
cd "-"

# 2. تثبيت الاعتماديات
pip install -r requirements.txt

# 3. إعداد ملف البيئة
cp .env.example .env
# عدّل القيم التالية في .env:
```

**محتوى `.env` الكامل:**

```bash
# مفتاح جلسات Flask — ولّد بـ: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_strong_random_secret_key_here

# رابط قاعدة بيانات PostgreSQL (Neon)
# للتطوير المحلي يمكن استخدام SQLite: sqlite:///local.db
DATABASE_URL=postgresql://user:password@host/dbname

# مفتاح المصادقة بين قwqw وهذه المنصة (Bearer Token)
INGEST_API_KEY=your_chosen_secure_token

# كلمات المرور الأولية لأول تشغيل لـ setup_db.py
ADMIN_INITIAL_PASSWORD=choose_a_strong_admin_password
READER_INITIAL_PASSWORD=choose_a_strong_reader_password

# (اختياري) مفتاح OpenRouter الاحتياطي
OPENROUTER_API_KEY=

# true في الإنتاج (Render + HTTPS) ، false للتطوير المحلي
SESSION_COOKIE_SECURE=false
```

```bash
# 4. إنشاء الجداول والمستخدمين الأوليين
python setup_db.py

# 5. تشغيل التطبيق
# للتطوير المحلي:
python app.py
# للإنتاج:
gunicorn app:app
```

> [!IMPORTANT]
> `setup_db.py` يرفض صراحةً العمل بدون `ADMIN_INITIAL_PASSWORD` و`READER_INITIAL_PASSWORD` — لا توجد كلمات مرور افتراضية مُضمَّنة في الكود أبداً. الحسابات الموجودة لا تُمس عند إعادة التشغيل.

---

## 6. الاستضافة على Render.com

هذه المنصة مُستضافة على **[Render.com](https://render.com)** — منصة سحابية مُدارة، باستخدام **Gunicorn** كـ WSGI server.

### إعداد قاعدة البيانات (Neon PostgreSQL)

```
1. أنشئ حساباً مجانياً على neon.tech
2. أنشئ مشروعاً جديداً → احصل على DATABASE_URL
3. أضفه في متغيرات بيئة Render
```

> [!NOTE]
> الكود يُحوّل تلقائياً `postgres://` إلى `postgresql://` (السطر 25–27 في app.py) للتوافق مع SQLAlchemy، حيث أن Neon يُصدر الرابط بالصيغة القديمة أحياناً.

### إعداد النشر على Render

```
1. سجّل في render.com
2. أنشئ خدمة "Web Service" جديدة
3. اربطها بمستودع GitHub: yousefdg005/-
4. إعدادات البناء:
   - Build Command:  pip install -r requirements.txt
   - Start Command:  gunicorn app:app
5. أضف متغيرات البيئة في "Environment":
   - SECRET_KEY
   - DATABASE_URL
   - INGEST_API_KEY
   - ADMIN_INITIAL_PASSWORD   (يُحذف بعد أول تشغيل)
   - READER_INITIAL_PASSWORD  (يُحذف بعد أول تشغيل)
   - SESSION_COOKIE_SECURE=true
6. بعد النشر، شغّل في "Shell":
   python setup_db.py
```

### إعدادات الاتصال مع قاعدة البيانات اللامركزية

```python
# app.py — السطور 31–35
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,   # اختبار الاتصال قبل كل استعلام (يتعامل مع قطع SSL)
    'pool_recycle': 300,     # تجديد الاتصالات كل 5 دقائق (يمنع انتهاء صلاحية Neon)
    'pool_timeout': 30,      # حد انتظار الاتصال
}
```

هذه الإعدادات مُحسَّنة خصيصاً لـ Neon الذي يتسم بالاتصالات اللامركزية (serverless) التي تخمد عند الخمول.

---

## 7. سير العمل خطوة بخطوة

```
الخطوة 1 │ تصل دُفعات المصطلحات من Platform A
          │ → POST /api/receive-terms + Bearer Token
          │ → كشف التكرار فوري + إدراج بـ status='pending'

الخطوة 2 │ [المدير] يفتح /admin
          │ → يرى قائمة المصطلحات المعلّقة مرتبةً بالأحدث
          │ → يرى نص المصدر الكامل (EN + AR) لكل مصطلح

الخطوة 3 │ [المدير] يتخذ قراره لكل مصطلح:
          │ → اعتماد / تعديل ثم اعتماد / حذف

الخطوة 4 │ المصطلحات المعتمدة تظهر في /dictionary
          │ → مرتبة أبجدياً، مع حقل التخصص والتعريف

الخطوة 5 │ [المدير] يُصدّر القاموس بالصيغة المطلوبة:
          │ → TBX لـ SDL Trados / memoQ / Phrase TMS
          │ → Excel للمرجعية الورقية
          │ → CSV لمعالجة البيانات الإضافية
```

---

## 8. نموذج البيانات

### جدول `term`

| العمود | النوع | الوصف |
|--------|-------|-------|
| `id` | Integer PK | معرّف تلقائي |
| `en` | String(255) | المصطلح الإنجليزي |
| `ar` | String(255) | المقابل العربي |
| `definition` | Text | التعريف العربي (جنس + فصل) |
| `subject_field` | String(150) | حقل التخصص (مثال: Contract Law) |
| `source_text_en` | Text | الجملة الإنجليزية التي استُخرج منها |
| `source_text_ar` | Text | الجملة العربية الموازية |
| `status` | String(50) | `pending` / `approved` / `ai_suggested` |
| `date` | DateTime | تاريخ الإضافة |
| `created_at` | DateTime | طابع زمني للتدقيق (Audit Trail) |

### جدول `user`

| العمود | النوع | الوصف |
|--------|-------|-------|
| `id` | Integer PK | معرّف تلقائي |
| `username` | String(50) UNIQUE | اسم المستخدم |
| `password` | String(255) | كلمة مرور مُجزَّأة بـ bcrypt |
| `role` | String(20) | `admin` أو `reader` |

### جدول `setting`

| العمود | النوع | الوصف |
|--------|-------|-------|
| `id` | Integer PK | معرّف تلقائي |
| `key` | String(50) UNIQUE | اسم الإعداد |
| `value` | Text | قيمة الإعداد (مشفّرة في الذاكرة فقط) |

---

## 9. المسارات (API Routes)

### المسارات العامة

| المسار | الطريقة | الوصف | المصادقة |
|--------|---------|-------|---------|
| `/login` | GET, POST | تسجيل الدخول | — |
| `/register` | GET, POST | إنشاء حساب جديد (reader) | — |
| `/logout` | GET | تسجيل الخروج | مُسجَّل |
| `/dictionary` | GET | القاموس العام (معتمد فقط) | مُسجَّل |
| `/account/password` | GET, POST | تغيير كلمة المرور | مُسجَّل |

### مسارات المدير

| المسار | الطريقة | الوصف |
|--------|---------|-------|
| `/admin` | GET, POST | لوحة الإدارة + إضافة يدوية |
| `/admin/approve/<id>` | POST | اعتماد مصطلح فردي |
| `/admin/delete/<id>` | POST | حذف مصطلح فردي |
| `/admin/edit/<id>` | POST | تعديل مصطلح |
| `/admin/bulk_action` | POST | اعتماد/حذف جماعي (pending) |
| `/admin/approved_bulk_delete` | POST | حذف جماعي من المعتمد |
| `/admin/deduplicate` | POST | إزالة التكرارات |
| `/admin/save_settings` | POST | حفظ إعدادات OpenRouter |
| `/admin/export/tbx` | GET | تصدير TBX |
| `/admin/export/csv` | GET | تصدير CSV |
| `/admin/export/excel` | GET | تصدير Excel |

### مسار API الاستقبال (من Platform A)

| المسار | الطريقة | المصادقة | الوصف |
|--------|---------|---------|-------|
| `/api/receive-terms` | POST | Bearer Token | استقبال دُفعات المصطلحات |

---

## 10. بنية الأمان

```mermaid
flowchart TD
    A["طلب خارجي"] --> B["Flask-Limiter\nحد المعدّل\n10/دقيقة على تسجيل الدخول\n5/ساعة على التسجيل\n60/ساعة على API"]
    B --> C{"نوع المسار؟"}
    C -- "HTML (كوكيز الجلسة)" --> D["Flask-WTF\nحماية CSRF\nرمز في كل نموذج"]
    C -- "API /api/receive-terms" --> E["Bearer Token\nINGEST_API_KEY\nمن متغيرات البيئة"]
    D --> F["Flask-Login\nالتحقق من الجلسة"]
    E --> F
    F --> G{"دور المستخدم؟"}
    G -- "admin" --> H["كامل الصلاحيات:\nاعتماد · تعديل · حذف · تصدير"]
    G -- "reader" --> I["قراءة فقط:\nتصفح القاموس المعتمد"]
    G -- "مجهول" --> J["إعادة توجيه لصفحة الدخول\n401 / 403"]

    style G fill:#EAB308,color:#000,font-weight:bold
```

| الطبقة | التقنية | التفصيل |
|--------|---------|---------|
| **تجزئة كلمات المرور** | Flask-Bcrypt | bcrypt مع salt تلقائي |
| **حماية CSRF** | Flask-WTF | رمز في كل نموذج HTML |
| **مصادقة API** | Bearer Token | `INGEST_API_KEY` من متغيرات البيئة فقط |
| **تحديد معدّل الطلبات** | Flask-Limiter | حدود مختلفة لكل مسار |
| **كوكيز الجلسة** | SameSite + Secure | `Lax` + `Secure=true` في الإنتاج |
| **حقن SQL** | SQLAlchemy ORM | استعلامات مُعامَلة بالمعاملات |
| **الاتصال بقاعدة البيانات** | pool_pre_ping | اختبار قبل كل استعلام |

> [!CAUTION]
> لا تُضمِّن `INGEST_API_KEY` أو `SECRET_KEY` في الكود أو في commits. استخدم دائماً متغيرات البيئة على Render أو ملف `.env` المُدرَج في `.gitignore`.

---

## 11. التقنيات المستخدمة

| الطبقة | التقنية | الإصدار | الغرض |
|--------|---------|---------|-------|
| **لغة البرمجة** | Python | 3.10+ | اللغة الأساسية |
| **إطار الويب** | Flask | 3.x | خادم الويب |
| **ORM** | Flask-SQLAlchemy | — | التجريد عن قاعدة البيانات |
| **قاعدة البيانات** | PostgreSQL (Neon) | 16+ | التخزين الدائم |
| **قاعدة البيانات (محلي)** | SQLite | — | للتطوير والاختبار |
| **المصادقة** | Flask-Login | — | إدارة الجلسات |
| **التجزئة** | Flask-Bcrypt | — | حماية كلمات المرور |
| **حماية CSRF** | Flask-WTF | — | أمان النماذج |
| **تحديد المعدّل** | Flask-Limiter | — | الحماية من Brute-Force |
| **قراءة البيئة** | python-dotenv | — | متغيرات `.env` |
| **تصدير Excel** | openpyxl | — | توليد `.xlsx` مُنسَّق |
| **تصدير XML** | xml.sax.saxutils | stdlib | توليد TBX آمن من الحقن |
| **WSGI Server** | Gunicorn | — | خادم الإنتاج على Render |
| **برنامج تشغيل PostgreSQL** | psycopg2-binary + psycopg[binary] | — | الاتصال بـ PostgreSQL |

---

## 12. صيغ التصدير

| الصيغة | المعيار | يتوافق مع | يحتوي |
|--------|---------|----------|-------|
| **TBX** | ISO 30042 | SDL Trados MultiTerm, memoQ, Phrase TMS | المصطلح + التعريف + حقل التخصص |
| **Excel (XLSX)** | ECMA-376 | MS Excel, LibreOffice, Google Sheets | كل البيانات مع تنسيق احترافي |
| **CSV (UTF-8 BOM)** | RFC 4180 | أي معالج نصوص / Excel | كل البيانات، عربية آمنة |

**الحقول المُصدَّرة في جميع الصيغ:**

```
#  │  ID  │  English Term  │  Arabic Term  │  Subject Field
   │  Definition  │  Source Text EN  │  Source Text AR  │  Date Added
```

> [!NOTE]
> حقلا `Source Text EN` و`Source Text AR` يحفظان الجمل الأصلية التي استُخرج منها كل مصطلح — وهو ما يُميّز هذا النظام عن قواميس المصطلحات التقليدية التي تفتقر للاستشهاد بالمصدر.

---

<div align="center">

---

**إعداد وتطوير: يوسف نورالدين المقعمز**  
📱 [0928756918](tel:0928756918) · ✉️ [ywsfalmqmz@gmail.com](mailto:ywsfalmqmz@gmail.com)

*"المصطلح المعتمد هو الذي اجتاز عيون المترجم والآلة معاً."*

© 2026 — جميع الحقوق محفوظة

</div>
