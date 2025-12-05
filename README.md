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

## Screenshots
<img width="1920" height="1080" alt="Screenshot (131)" src="https://github.com/user-attachments/assets/95058896-7aca-47cd-97a1-5dba572fb245" />

<img width="1920" height="1080" alt="Screenshot (134)" src="https://github.com/user-attachments/assets/89194860-f4af-4ef2-8f9c-42a39a244647" />

<img width="1920" height="1080" alt="Screenshot (137)" src="https://github.com/user-attachments/assets/ad762d12-bf7e-44c9-af6f-00b7f85e6273" />

<img width="1920" height="1080" alt="Screenshot (138)" src="https://github.com/user-attachments/assets/67d869cf-f552-460c-95ca-c3bdf82a74f8" />

<img width="1920" height="1080" alt="Screenshot (144)" src="https://github.com/user-attachments/assets/5d9cadd2-31b2-443e-b1e1-e7205a0cfaa6" />

<img width="1920" height="1080" alt="Screenshot (146)" src="https://github.com/user-attachments/assets/b2caa818-e1b8-43a0-bfcf-bc2fd47464fe" />

<img width="1920" height="1080" alt="Screenshot (150)" src="https://github.com/user-attachments/assets/0dfba0a4-1e45-4858-8c25-c92ec416df6f" />

<img width="1920" height="1080" alt="Screenshot (152)" src="https://github.com/user-attachments/assets/e36493c0-088c-4594-8eed-88b2a2202a26" />

<img width="1920" height="1080" alt="Screenshot (153)" src="https://github.com/user-attachments/assets/43765828-c05e-428f-9896-4fa9d3523326" />

<img width="1920" height="1080" alt="Screenshot (155)" src="https://github.com/user-attachments/assets/a866032d-3a79-4fd7-bf9c-fd12f7519472" />

<img width="1920" height="1080" alt="Screenshot (234)" src="https://github.com/user-attachments/assets/1e2f0e62-56df-4cb4-84e5-0db7d9f030e3" />

<img width="1920" height="1080" alt="Screenshot (241)" src="https://github.com/user-attachments/assets/afcf0896-2035-4ac7-9d2d-331af01c293d" />

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
