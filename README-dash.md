
<div align="center">

# 🏛️ AI Legal Dictionary
### قاموس الذكاء الاصطناعي القانوني

**A Bilingual Arabic–English Legal Terminology Management Platform**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-008BB9?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com)
[![License](https://img.shields.io/badge/License-Academic_Use-gold?style=for-the-badge)](#)

> 🎓 **University Graduation Project** | Department of Translation Studies  
> *Developed by Youssef Nour Eldin*

---

[🌐 Live Platform](https://dictionaryly.onrender.com) • [📖 How to Use](#-how-to-use) • [🚀 Quick Start](#-quick-start)

</div>

---

## 📌 Overview | نظرة عامة

**AI Legal Dictionary** is a web-based bilingual legal terminology management system designed for legal translators, researchers, and students. It serves as the **publication and curation hub** for Arabic–English legal terms, featuring a human-supervised review pipeline that ensures only verified terminology reaches the public-facing dictionary.

**قاموس الذكاء الاصطناعي القانوني** هو نظام ويب لإدارة المصطلحات القانونية ثنائية اللغة، مُصمَّم للمترجمين القانونيين والباحثين والطلاب. يعمل كـ**مركز نشر وإشراف** للمصطلحات القانونية العربية-الإنجليزية، ويضمّ خط مراجعة بشري يكفل أن المصطلحات المنشورة في القاموس العام قد خضعت للتحقق.

---

## ✨ Features | المميزات

### 👁️ Reader Interface — القارئ
- Browse the full bilingual legal dictionary of **approved terms**.
- Each term displays: English term, Arabic equivalent, subject field, and Arabic legal definition.
- **Live client-side search** — filter instantly across all fields (no page reload).

### 🛡️ Admin Dashboard — المسؤول
- **Incoming term queue** — view all AI-suggested `pending` terms from the processing platform.
- **Bulk operations** — approve or delete multiple pending terms at once.
- **Inline editing** — edit any approved term's EN/AR text, definition, or subject field directly in the dashboard.
- **Bulk delete** approved terms when needed.
- **Manual entry** — add terms directly without going through the AI pipeline.
- **AI model settings** — configure OpenRouter API key and preferred LLM model, stored persistently in the database.

### 🤝 Platform Integration API
- A dedicated REST endpoint (`/api/receive-terms`) accepts batches of AI-extracted terms from the companion processing tool ([AI Legal Workspace](https://github.com/yousefdg005/qwqw)), enabling a seamless, automated terminology pipeline.

---

## 🔄 Term Lifecycle | دورة حياة المصطلح

```mermaid
flowchart LR
    A["🤖 AI Workspace\n(qwqw)"] -->|"POST /api/receive-terms"| B["📥 Pending Queue\nstatus = 'pending'"]
    B -->|"Admin reviews"| C{Decision}
    C -->|"✅ Approve"| D["📖 Published Dictionary\nstatus = 'approved'"]
    C -->|"✏️ Edit then Approve"| D
    C -->|"🗑️ Delete"| E["Discarded"]
    D --> F["👥 Readable by all users"]
    G["✍️ Manual Entry\nby Admin"] --> D
```

---

## 🏗️ Architecture | البنية التقنية

### Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3 / Flask |
| **Database ORM** | Flask-SQLAlchemy |
| **Database** | PostgreSQL (Neon cloud) |
| **Authentication** | Flask-Login + Flask-Bcrypt |
| **Rate Limiting** | Flask-Limiter |
| **Templating** | Jinja2 |
| **Frontend** | Bootstrap 5.3, Three.js r128, Vanilla JS |
| **Production Server** | Gunicorn |

### Database Schema

```
USER
├── id          (PK)
├── username    (unique)
├── password    (bcrypt hash)
└── role        ('admin' | 'reader')

TERM
├── id          (PK)
├── en          English term
├── ar          Arabic equivalent
├── definition  Arabic legal definition
├── subject_field  Domain (e.g., قانون عام، قانون دولي)
├── status      ('pending' | 'approved' | 'ai_suggested')
└── created_at

SETTING
├── id          (PK)
├── key         (e.g., 'openrouter_api_key', 'openrouter_model')
└── value
```

### Route Map

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| GET/POST | `/login` | Public | User login (rate-limited: 10/min) |
| GET | `/logout` | Auth | Session logout |
| GET | `/dictionary` | Reader+ | Browse approved terms |
| GET/POST | `/admin` | Admin | Dashboard: view/add terms |
| POST | `/admin/save_settings` | Admin | Save AI model config to DB |
| POST | `/admin/bulk_action` | Admin | Bulk approve/delete pending terms |
| GET | `/admin/approve/:id` | Admin | Approve single term |
| POST | `/admin/edit/:id` | Admin | Edit a term's fields |
| GET | `/admin/delete/:id` | Admin | Delete a term |
| POST | `/api/receive-terms` | Bearer Token | Ingest AI-extracted terms |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- A [Neon](https://neon.tech) PostgreSQL database (free tier available)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yousefdg005/-.git
cd -

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your values (see Configuration section)

# 4. Initialize the database
python setup_db.py

# 5. Run the application
flask run
# Or for production:
gunicorn app:app
```

### Configuration (`.env`)

```env
SECRET_KEY=your_strong_random_secret_key_here
DATABASE_URL=postgresql://user:password@host/dbname
INGEST_API_KEY=your_chosen_secure_token
```

> **After setup:** Log in with the default admin credentials created by `setup_db.py`, then immediately change the password from the admin panel.

---

## 📦 Dependencies

```
Flask                # Web framework
Flask-SQLAlchemy     # ORM for PostgreSQL
Flask-Login          # Session-based authentication
Flask-Bcrypt         # Password hashing
Flask-Limiter        # Rate limiting
psycopg2-binary      # PostgreSQL driver
python-dotenv        # .env file support
gunicorn             # Production WSGI server
```

---

## 🎨 UI Highlights

### 3D Login Page
The login page features an interactive **3D Scales of Justice** rendered with Three.js:
- Animated golden balance with spring physics
- 300 floating dust particles
- Mouse parallax camera movement
- Click each pan to open the login or registration form
- Fully responsive (mobile: bottom sheet overlay)

### Admin Dashboard
- Dark gold theme with gold-bordered tables
- Pending terms highlighted for quick review
- Inline accordion-style editing for approved terms
- Searchable approved terms table

---

## 🔗 Integration with AI Legal Workspace

This platform is the **second half** of a two-component ecosystem. It receives AI-extracted legal terms from the companion tool:

➡️ **[AI Legal Workspace (qwqw)](https://github.com/yousefdg005/qwqw)** — Processes parallel legal documents, aligns sentences, extracts terms with LLMs, and pushes them here for review.

### How the Integration Works

```
[AI Legal Workspace] ──POST /api/receive-terms──► [AI Legal Dictionary]
     (qwqw)               Bearer Token Auth            (this repo)
                          JSON: {en, ar, definition,
                                 subject field}
                                                   Terms enter as 'pending'
                                                   Admin reviews & approves
                                                   Published to /dictionary
```

---

## 🎓 Academic Context

This project was developed as part of the graduation requirements for the **Department of Translation Studies**. It addresses:

1. **Lack of centralized terminology resources** — Arabic legal translation lacks standardized, accessible reference databases.
2. **Quality control in AI-assisted translation** — Raw AI output needs human expert review before becoming a trusted reference.
3. **Accessibility** — Providing a free, web-accessible bilingual legal dictionary for students and practitioners.

The platform demonstrates the practical application of **web technologies and database design** to real translation workflow challenges, integrating AI automation with human expertise through a structured review pipeline.

---

## 📁 Project Structure

```
/
├── app.py              ← Flask application (routes, models, auth, API)
├── setup_db.py         ← Database initializer & default user creator
├── fix_db.py           ← Column migration script
├── update_schema.py    ← Schema updater (adds Setting table)
├── requirements.txt
├── .gitignore          ← Protects .env from version control
├── static/
│   ├── css/style.css   ← Dark-gold custom theme (CSS variables)
│   └── js/script.js    ← Search, alerts, confirm dialogs
└── templates/
    ├── base.html       ← Master Jinja2 layout (Bootstrap 5.3)
    ├── login.html      ← Standalone 3D WebGL login (Three.js)
    ├── dictionary.html ← Public term browser (reader view)
    └── admin.html      ← Full admin dashboard
```

---

## 👤 Developer

**Youssef Nour Eldin**  
Translation Studies Department  
📧 ywsfalmqmz@gmail.com  
📞 0928756918

---

<div align="center">

*Bridging AI and human expertise for legal translation excellence*  
*© 2026 Youssef Nour Eldin — All rights reserved*

</div>
