# 🧑‍💼 WorkZen HR — HR Management System

A modern, web-based HR Management System built with Flask and MySQL.
WorkZen HR helps organizations manage employees, attendance, payroll, and leave processes efficiently in one centralized platform.

---

## 🌐 Live Demo

HUMAN RESOURCES WEB APP: *(https://hr-web-app-5.onrender.com/dashboard)*
---

## 📌 Overview

WorkZen HR is designed to simplify HR operations by providing a clean interface and powerful backend for managing employee lifecycle and HR processes.

---

## 🚀 Features

### 🔐 Authentication & Roles

* Secure login system
* Role-based access (HR Manager, CHRO)
* Session management

### 👨‍💼 Employee Management

* Add new employees
* View employee profiles
* Edit employee details
* Department assignment

### 🕒 Attendance Management

* Mark attendance
* View attendance records
* Track employee presence

### 🌴 Leave Management

* Apply for leave
* Manage leave requests
* Track leave balances

### 💰 Payroll System

* Manage compensation
* Process payroll
* View salary details

### 🏢 Department Management

* Create departments
* Assign employees
* Organizational structuring

---

## 🛠️ Tech Stack

| Layer           | Technology            |
| --------------- | --------------------- |
| Backend         | Python (Flask)        |
| Database        | MySQL                 |
| Frontend        | HTML, CSS, JavaScript |
| Version Control | Git & GitHub          |

---

## 📁 Project Structure

```id="structure"
hr_web_app/
│── app.py
│── config/
│── routes/
│── templates/
│   ├── auth/
│   ├── employees/
│   ├── attendance/
│   ├── leave/
│   ├── payroll/
│── static/
│   ├── css/
│   ├── js/
│── schema.sql
│── seed_db.py
│── requirements.txt
│── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```id="clone"
git clone https://github.com/YOUR_USERNAME/hr_web_app.git
cd hr_web_app
```

---

### 2️⃣ Create Virtual Environment (Recommended)

```id="venv"
python -m venv venv
venv\Scripts\activate
```

---

### 3️⃣ Install Dependencies

```id="deps"
pip install -r requirements.txt
```

---

### 4️⃣ Setup Database

* Open MySQL
* Create database:

```sql
CREATE DATABASE hr_system;
```

* Import schema:

```id="schema"
Get-Content schema.sql | mysql -u root -p hr_system
```

---

### 5️⃣ Seed Database

```id="seed"
python seed_db.py
```

---

### 6️⃣ Run Application

```id="run"
python app.py
```

App will run at:

```
http://127.0.0.1:5000
```

---

## 🔑 Default Credentials

| Role       | Username   | Password  |
| ---------- | ---------- | --------- |
| HR Manager | hr_manager | HR@123456 |
| CHRO       | chro       | CHRO@1234 |

---

## 🔒 Environment Variables (For Deployment)

Create environment variables:

```
DB_HOST=your_host
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=hr_system
SECRET_KEY=your_secret_key
```

---

## 🚀 Deployment

This app can be deployed using:

* Render (recommended)
* Railway (for database)
* Any cloud platform supporting Flask

---

## 📈 Future Enhancements

* Multi-company (SaaS) support
* Advanced role-based dashboards
* Email notifications
* REST API integration
* Mobile responsiveness
* Analytics & reporting dashboard

---

## 🧠 Learnings

This project demonstrates:

* Full-stack web development using Flask
* Database design with MySQL
* Authentication & session handling
* Modular route structuring
* Real-world HR system workflows

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

xxxxx xxxxx xxxxx xxxxx xxxxx xxxxx xxxxx

---

## 👨‍💻 Author

Developed by *Mataruse T*
*((https://hr-web-app-5.onrender.com/dashboard))*

---

