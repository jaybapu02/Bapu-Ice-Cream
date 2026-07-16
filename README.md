# 🍦 Bapu Ice Cream

A full-stack **Django-based web application** for an ice cream business, featuring product browsing, ordering system, user authentication, and catering services.

---

## 🚀 Features

* 🛒 Product listing and cart system
* 👤 User authentication (Login/Register/Profile)
* 📦 Order management system
* 💳 Payment and order confirmation
* 📞 Contact and catering enquiry forms
* 🎨 Responsive UI with static assets
* ⚙️ Admin panel for backend management

---

## 🏗️ Project Structure

```
Bapu-Ice-Cream/
│
├── manage.py
├── db.sqlite3
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
│
├── Hello/                # Main Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── home/                 # Core application
│   ├── models.py         # Database models
│   ├── views.py          # Business logic
│   ├── urls.py           # Routing
│   ├── forms.py          # Forms handling
│   ├── admin.py          # Admin configuration
│   ├── middleware.py     # Custom middleware
│   ├── exceptions.py     # Custom exceptions
│   └── migrations/       # Database migrations
│
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── products.html
│   ├── cart.html
│   ├── order.html
│   ├── payment.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── contact.html
│   ├── catering.html
│   └── ...
│
├── static/               # Static files (CSS, images)
│   ├── css/style.css
│   └── images...
│
└── .git/                 # Git version control
```

*(Structure based on your project files )*

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/Bapu-Ice-Cream.git
cd Bapu-Ice-Cream
```

### 2️⃣ Create virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run migrations

```bash
python manage.py migrate
```

### 5️⃣ Start the server

```bash
python manage.py runserver
```

Open in browser:

```
http://127.0.0.1:8000/
```

---
## 📸 Pages Included

* Home Page
* Products Page
* Cart Page
* Order & Payment
* Login / Register
* User Profile
* Contact Page
* Catering Services

---

## 🧑‍💻 Tech Stack

* **Backend:** Django (Python)
* **Frontend:** HTML, CSS
* **Database:** SQLite
* **Deployment:** Docker (optional)

---

## 📌 Future Improvements

* Online payment gateway integration
* Admin dashboard analytics
* REST API support
* Mobile responsiveness enhancement

---

## 👨‍💻 Author

**Jaychandra Das**

---

## ⭐ Contribution

Contributions are welcome! Feel free to fork the repo and submit a pull request.

---

## 📄 License

This project is for educational purposes.
