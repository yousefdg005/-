<div align="center">

<img src="static/img/logo.jpg" alt="LexTerm Emblem" width="160" style="border-radius: 50%; box-shadow: 0 4px 20px rgba(0,0,0,0.3); margin-bottom: 15px;" />

# 📖 LexTerm — Legal Dictionary Platform
### **المنصة السحابية المتقدمة لإدارة واعتماد ونشر القاموس القانوني ثنائي اللغة (EN ↔ AR)**

[![Flask](https://img.shields.io/badge/Framework-Flask%203.x-black.svg?logo=flask)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%20%2F%20Neon-336791.svg?logo=postgresql&logoColor=white)](https://neon.tech/)
[![Security](https://img.shields.io/badge/Security-CSRF%20%7C%20Bcrypt%20%7C%20Limiter-success.svg)](#-الأمان-وحماية-البيانات)
[![Standards](https://img.shields.io/badge/Standards-TBX%20ISO%2030042-E8C069.svg)](#-التصدير-متعدد-الصيغ)
[![Deployment](https://img.shields.io/badge/Deploy-Render%20Ready-46E3B7.svg?logo=render&logoColor=white)](#-النشر-على-السحابة-render)

<p align="center">
  <b>بوابة رقمية آمنة ومتكاملة للمعاجم والمصطلحات القانونية المعتمدة</b><br>
  تتيح للباحثين والقانونيين البحث اللحظي الدقيق، وتمكّن فرق التحرير والتدقيق من مراجعة المصطلحات الواردة، إثرائها بالذكاء الاصطناعي، وتصديرها بصيغ تخصصية موحدة.
</p>

[المميزات الرئيسية](#-المميزات-الرئيسية) •
[التشغيل المحلي](#-التثبيت-والتشغيل-المحلي) •
[واجهة الـ API](#-واجهة-استقبال-المصطلحات-api) •
[النشر السحابي](#-النشر-على-السحابة-render) •
[فريق التطوير](#-المطور-والتواصل)

---

</div>

<br>

## 🌟 المميزات الرئيسية

### 🔍 1. محرك البحث المعجمي الموجه
* **بحث حصري مركز:** يبحث فقط في عمودي **المصطلح الإنجليزي (English Term)** و**المقابل العربي (Arabic Term)** لتفادي النتائج العشوائية من الشروحات أو النصوص المصدرية.
* **تظليل بصري فوري (Live Highlight):** تمييز الكلمات المطابقة باللون الأصفر الذهبي أثناء الكتابة في شريط البحث.
* **عرض سياقي وافٍ:** عرض التعريف القانوني الدقيق، الفرع القانوني، بالإضافة إلى النصين المصدريين الأصليين باللغتين لإثبات السياق وسند الاستخدام.

### 🛡️ 2. لوحة تحكم وإدارة المصطلحات (Admin Hub)
* **دورة حياة المصطلحات:** استقبال المصطلحات في حالة انتظار (`pending`)، مراجعتها، تعديلها، ثم اعتمادها (`approved`) لتظهر فوراً في القاموس العام.
* **محرر مدمج لحظي (Inline Editor):** تعديل أي حقل للمصطلح وحفظه مباشرة دون مغادرة الصفحة.
* **إدارة دفعات المصطلحات (Bulk Actions):** اعتماد أو حذف مئات المصطلحات المحددة بضغطة واحدة.
* **محرك كشف وإزالة التكرارات الذكي (Smart Deduplication):**
  * فحص التطابق اللغوي الثنائي (EN ↔ AR).
  * توحيد قواعد الإملاء العربي (إزالة التشكيل، همزات الوصل والقطع، التاء المربوطة، وحذف "الـ" التعريف الزائدة).

### 🤖 3. إثراء المصطلحات بالذكاء الاصطناعي (AI Term Refinement)
* **تكامل سلس مع OpenRouter:** إمكانية تخصيص وحفظ مفتاح الـ API والنموذج المفضل من داخل لوحة التحكم.
* **تدقيق وتوليد التعريف:** زر بنقرة واحدة لتحليل أي مصطلح واقتراح أدق ترجمة قانونية، وصياغة تعريف مهني موجز، وتحديد فرع القانون المناسب.

### 📊 4. التصدير متعدد الصيغ المتوافقة
| الصيغة | الامتداد | المواصفات والاستخدام |
| :--- | :---: | :--- |
| **Excel Spreadsheet** | `.xlsx` | جدول منسق بألوان الهوية وخلايا عريضة مع حماية من حقن المعادلات (*Formula Injection*). |
| **Comma-Separated** | `.csv` | ملف بترميز `UTF-8-SIG` لمنع تشوه الحروف العربية عند الفتح في برامج مايكروسوفت. |
| **TermBase eXchange** | `.tbx` | معيار منظمة المقاييس الدولية **ISO 30042** الجاهز للاستيراد المباشر في منظومات Trados و SDL. |

---

## 🔒 الأمان وحماية البيانات

* **مصادقة مشفرة:** تشفير هجين لكلمات المرور باستخدام مكتبة **Bcrypt**.
* **حماية من الهجمات الخبيثة:** تفعيل حماية ضد هجمات تزوير الطلبات **CSRF (Cross-Site Request Forgery)** عبر `Flask-WTF`.
* **محدد معدل الطلبات (Rate Limiting):** تقييد محاولات تسجيل الدخول وإنشاء الحسابات لمنع هجمات التخمين والقوة العمياء (*Brute-force*).
* **حماية الترويسات (Security Headers):** إدراج ترويسات `X-Content-Type-Options`, `X-Frame-Options` لحماية كوكيز الجلسات والتكاملات الخارجية.

---

## 🏗️ البنية البرمجية وهيكل المجلدات

```text
📦 repo_audit (LexTerm Dictionary)
 ┣ 📂 static                      # الأصول الثابتة
 ┃ ┣ 📂 css                       # ملفات التنسيق الفاخر
 ┃ ┗ 📂 img                       # شعار الصقر والأيقونات الرسمية
 ┣ 📂 templates                   # قوالب Jinja2 المتجاوبة
 ┃ ┣ 📜 base.html                 # القالب العام للهيكل والتنقل
 ┃ ┣ 📜 dictionary.html           # واجهة القاموس العام والبحث اللحظي
 ┃ ┣ 📜 admin.html                # لوحة التحكم وإدارة الاعتماد
 ┃ ┣ 📜 login.html                # تسجيل الدخول وإنشاء الحسابات
 ┃ ┗ 📜 change_password.html      # إدارة أمان الحساب
 ┣ 📜 app.py                      # الخادم والمسارات ونماذج SQLAlchemy
 ┣ 📜 setup_db.py                 # سكربت تهيئة الجداول والحسابات الأولية
 ┣ 📜 update_schema.py            # تحديث حقول قاعدة البيانات
 ┣ 📜 fix_db.py                   # أدوات فحص سلامة البيانات
 ┣ 📜 .env.example                # نموذج الإعدادات البيئية
 ┣ 📜 requirements.txt            # المكتبات والاعتماديات
 ┗ 📜 README.md                   # دليل التوثيق والتشغيل
```

---

## 🚀 التثبيت والتشغيل المحلي

### 1. استنساخ المشروع وتثبيت المتطلبات
```bash
git clone https://github.com/yousefdg005/-.git
cd -
python -m venv venv
source venv/bin/activate  # على ويندوز: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. إعداد ملف البيئة (`.env`)
قم بنسخ ملف `.env.example` إلى `.env` وقم بتعديل الإعدادات:
```bash
cp .env.example .env
```

```env
# مفتاح تشفير الجلسات
SECRET_KEY=your_strong_random_secret_key_here

# رابط قاعدة البيانات (يدعم PostgreSQL أو SQLite)
DATABASE_URL=postgresql://user:password@host/dbname

# رمز المصادقة البرمجية لمنصة الاستخراج
INGEST_API_KEY=your_chosen_secure_token

# كلمات المرور الافتراضية عند أول تشغيل لـ setup_db.py
ADMIN_INITIAL_PASSWORD=StrongAdminPasswordHere
READER_INITIAL_PASSWORD=StrongReaderPasswordHere
```

### 3. تهيئة الجداول وبدء التشغيل
```bash
# إنشاء الجداول وتوليد حساب الأدمن الأولي
python setup_db.py

# بدء الخادم في وضع التطوير
python app.py
```
> 🌐 افتح المتصفح على: `http://localhost:5000`

---

## 🌐 النشر على السحابة (Render Deployment)

تم إعداد المشروع بالكامل ليعمل بشكل أصيل على خوادم **Render** عبر خادم الإنتاج **Gunicorn**:

1. أنشئ خدمة ويب جديدة (**Web Service**) واربطها بالمستودع.
2. حدد إعدادات البناء والتشغيل:
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn app:app`
3. أضف متغيرات البيئة (`Environment Variables`) المطابقة لـ `.env`.
4. اضبط المتغير `SESSION_COOKIE_SECURE=true` لضمان عمل الكوكيز عبر بروتوكول HTTPS.

---

## 🔌 واجهة استقبال المصطلحات (API)

تتيح المنصة نقطة نهاية مؤمنة تتيح لمنصة الاستخراج والمحاذاة (`qwqw`) ضخ المصطلحات المفرزة مباشرة:

* **المسار:** `POST /api/receive-terms`
* **المصادقة:** `Bearer Token` عبر ترويسة `Authorization`
* **بنية الطلب (`JSON Payload`):**

```json
{
  "terms": [
    {
      "en": "Exclusive Jurisdiction",
      "ar": "اختصاص قضائي حصري",
      "definition": "سلطة قانونية مقصورة على محكمة معينة دون غيرها لنظر نزاع محدد والفصل فيه.",
      "subject_field": "Civil Procedure",
      "source_text_en": "The courts of London shall have exclusive jurisdiction...",
      "source_text_ar": "تختص محاكم لندن اختصاصاً قضائياً حصرياً..."
    }
  ]
}
```

---

## 👨‍💻 المطور والتواصل

* **إعداد وتطوير:** **يوسف نورالدين (Youssef Nour Eldin)**
* **📱 الهاتف:** [`0928756918`](tel:0928756918)
* **✉️ البريد الإلكتروني:** [`ywsfalmqmz@gmail.com`](mailto:ywsfalmqmz@gmail.com)
* **🔗 منصة الاستخراج التوأم:** [LexTerm Workspace (`qwqw`)](https://github.com/yousefdg005/qwqw)

<div align="center">
  <sub>منصة LexTerm للقاموس القانوني • مصممة للمتخصصين في الصياغة والمصطلحات القانونية</sub>
</div>
