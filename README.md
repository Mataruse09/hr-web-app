# 🧑‍💼 WorkZen HR — HR Management System

A modern, web-based HR Management System built with Flask and MySQL.
WorkZen HR helps organizations manage employees, attendance, payroll, and leave processes efficiently in one centralized platform.

---

## 🌐 Live Demo

HUMAN RESOURCES WEB APP: *(https://hr-web-app-5.onrender.com/dashboard)*

---

## 📺 YouTube Channel

[![Watch on YouTube](https://img.shields.io/badge/Watch%20on-YouTube-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/@TinasheMataruse09)

For tutorials and updates, check out our YouTube channel: [Tinashe Mataruse](https://www.youtube.com/@TinasheMataruse09)

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

| Layer           | Technology                     |
| --------------- | ------------------------------ |
| Backend         | Python (Flask)                 |
| Database        | MySQL                         |
| Frontend        | HTML, CSS, JavaScript          |
| Version Control | Git & GitHub                   |

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

* Create a MySQL database.
* Set your environment variables for MySQL.

```bash
set DB_HOST=your_host
set DB_PORT=3306
set DB_USER=your_user
set DB_PASSWORD=your_password
set DB_NAME=your_database
set DATABASE_URL=mysql+pymysql://user:password@host:port/dbname
```

* Create database schema from `schema.sql`:

```bash
mysql -h %DB_HOST% -P %DB_PORT% -u %DB_USER% -p%DB_PASSWORD% %DB_NAME% < schema.sql
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
| HR Manager | hr_manager | [Set your own password] |
| CHRO       | chro       | [Set your own password] |

---

## 🔒 Environment Variables (For Deployment)

Create environment variables:

```
DB_HOST=your_host
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_database
DATABASE_URL=mysql+pymysql://user:password@host:port/dbname
SECRET_KEY=your_secret_key
```

---

## 🚀 Deployment

This app can be deployed using:

* Docker
* Heroku
* AWS Elastic Beanstalk

Refer to the deployment guide for detailed steps.

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
* Database design with PostgreSQL
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

## 📸 Application Screenshots

Below are some screenshots showcasing the features and user interface of WorkZen HR.

### 1️⃣ Login Page
![Login Page](docs/149709d2-ea6f-4b03-93fb-33d163758275.png)
- **Arrow 1**: Use the "Get Started" button to begin the login process.
- **Arrow 2**: Select your company from the dropdown menu.
- **Arrow 3**: Enter your username and password to log in.

### 2️⃣ Company Setup & Subscription
![Company Setup & Subscription](docs/image-1777013543787.png)
- **Arrow 1**: Add your first employee to the system.
- **Arrow 2**: Manage your subscription and user access.
- **Arrow 3**: View your subscription status and expiry date.

### 3️⃣ CHRO Workforce Analytics
![CHRO Workforce Analytics](docs/image-1777013800528.png)
- **Arrow 1**: View enterprise analytics, including employee count, attrition rate, and attendance rate.
- **Arrow 2**: Access premium features like AI Workforce Predictions.

### 4️⃣ Advanced Analytics
![Advanced Analytics](docs/image-1777013936163.png)
- **Arrow 1**: Explore advanced analytics such as attrition forecast, talent gap analysis, hiring forecast, and productivity insights.
- **Arrow 2**: Upgrade to premium to unlock all AI-powered analytics.

### 5️⃣ Employee Leaderboard
![Employee Leaderboard](docs/image-1777013965154.png)
- **Arrow 1**: View top performers by points, level, and achievements.
- **Arrow 2**: Access your profile and achievements.

### 6️⃣ Gamification Dashboard
![Gamification Dashboard](docs/image-1777013994858.png)
- **Arrow 1**: Learn how to earn achievements.
- **Arrow 2**: View rare achievements and their descriptions.

### 7️⃣ Dashboard Overview
![Dashboard Overview](docs/image-1777014194544.png)
- **Arrow 1**: Navigate through the core HR functionalities like Employees, Attendance, Leave, and Payroll.
- **Arrow 2**: Access performance and development features like Appraisals and Gamification.

---

