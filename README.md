# Jobify – Job Portal System

A full-stack web-based recruitment platform built using Django that connects job seekers and employers through a structured, secure, and interactive hiring environment.

---

## About

Jobify is designed to streamline recruitment by replacing manual processes with a centralized, automated web system. It allows job seekers to apply for positions and employers to post vacancies, review applications, and manage hiring workflows. The system includes role-based access for **Job Seekers**, **Employers**, and **Administrators**.

Developed By: Shaikh Maryam Mohammed Farooq  
Institution: Center for Professional Courses, Gujarat University  
Program: B.Sc. IT (Software Development (Web & Mobile)  
Submission Year: 2025  

---

## Features

### Administrator
- Full control of the system
- Manage users and listings
- Moderate platform content
- View activity and maintain system health

### Employer
- Secure registration and company profile
- Create, update, and delete job postings
- Review and download applicant resumes
- Manage team access and hiring workflow

### Job Seeker
- Register and create professional profile
- Upload and manage resumes
- Search and filter suitable jobs
- Apply, track, save, and withdraw applications

### System Highlights
- Role-based authentication and authorization
- Resume upload and storage
- Advanced search and filtering
- Application tracking workflow
- Secure session and password management

---

## Technologies Used

### Frontend
- HTML5  
- Tailwind CSS  
- JavaScript  

### Backend
- Python  
- Django Framework  
- Django ORM  
- Django Authentication System  

### Database
- SQLite3 (Default Development Database)

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher  
- pip installed  
- Virtual environment recommended  

### Steps

#### 1. Clone the Repository
```bash
git clone https://github.com/your-repo-url.git
cd Jobify
```

#### 2. Create and Activate Virtual Environment
```
python -m venv env

# Windows
env\Scripts\activate

# macOS/Linux
source env/bin/activate
```

#### 3. Install Dependencies
```
pip install -r requirements.txt
```

#### 4. Run Migrations
```
python manage.py makemigrations
python manage.py migrate
```

#### 5. Create Admin User
```
python manage.py createsuperuser
```

#### 6. Start Server
```
python manage.py runserver
```

#### Application URL: http://127.0.0.1:8000/

### Usage Guide
  #### Access Points
    User Type	URL	Purpose
      Admin	http://127.0.0.1:8000/admin/
  	    Manage users, companies, listings
    Main Site	http://127.0.0.1:8000/
	    Registration, login, dashboard

#### Database Configuration

- Default configuration located in settings.py

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

Screenshots (Optional)

## License

```
This project is licensed under the MIT License.

MIT License

Copyright (c) 2025 Shaikh Maryam

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, subject to the following conditions:
```

## Acknowledgements

This project was developed as part of the B.Sc. IT Software Development curriculum under Gujarat University.

#### Special thanks to:

  Center for Professional Courses

  Django Documentation Community

#### Contact

  Developer: Shaikh Maryam
  
  Program: B.Sc. IT Software Development
  
  Institution: Center for Professional Courses, Gujarat University


Made with ❤️ for academic learning.
