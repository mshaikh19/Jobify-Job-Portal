import io
import json
import logging
import os
import random
import string
import urllib.parse
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from io import BytesIO
from dotenv import load_dotenv

import pandas as pd
import paypalrestsdk
import plotly.express as px
import plotly.graph_objects as go
import requests
from cashfree_pg import ApiClient, Configuration
from cashfree_pg.models import CreateOrderRequest, CustomerDetails
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (authenticate, get_backends, get_user, login,
                                 logout, update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.messages import get_messages
from django.core.cache import cache
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, F, IntegerField, Q, Sum
from django.db.models.functions import Cast, TruncDate, TruncMonth
from django.forms import modelformset_factory
from django.http import (FileResponse, Http404, HttpResponse,
                         HttpResponseBadRequest, JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
# from google.auth.transport import requests
from google.oauth2 import id_token
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)
from sms import send_sms

from job_portal.find_jobs import (build_job_dict_list,
                                  enhanced_job_recommendation,
                                  get_ai_recommendations,
                                  get_jobs_by_search_term)
from job_portal.forms.AdditionalDetails import (Step1BasicInfoForm,
                                                Step2SkillsForm,
                                                Step3EducationForm)
from job_portal.forms.AddTeamMemberForm import (AddTeamMemberForm,
                                                CustomUserFormForTeamMember)
from job_portal.forms.CompanyEditForm import (CompanyEditForm,
                                              CustomUserFormForCompany)
from job_portal.forms.CompanyRegistration import (CompanyFormStep1,
                                                  CompanyFormStep2,
                                                  LocationForm)
from job_portal.forms.JobApplicationForm import JobApplicationForm
from job_portal.forms.JobForm import JobForm, LocationFormForJob
from job_portal.forms.JobSeekerEditFormss import (AddressForm,
                                                  CertificationForm,
                                                  CustomUserFormForJobSeeker,
                                                  EducationForm,
                                                  JobSeekerProfileForm,
                                                  SchoolAddressForm,
                                                  WorkExperienceForm)
from job_portal.forms.PhoneVerification import PhoneVerificationForm
from job_portal.models import (Address, Application, Company, Education, Job,
                               JobPayment, Location)
from job_portal.models.Experience import Experience
from job_portal.models.JobSeeker import JobSeekerProfile
from job_portal.models.SavedJobs import SavedJob
from job_portal.preference import ai_score_jobs

from .forms.CompanyPersonEditForm import (CompanyPersonEditForm,
                                          CustomUserFormForCompanyPerson)
from .forms.HeadQuartersAddressForm import HeadQuartersAddressForm
from .forms.LocationForm import LocationFormSet
from .forms.UserLogin import UserLoginForm
from .forms.UserRegistration import (UserRegistrationForm,
                                     UserRegistrationFormForCompany)
from .models.Certifications import Certification
from .models.CompanyPerson import CompanyPerson
from .models.CustomUserModel import CustomUser
from .models.HeadQuartersAddress import HeadQuartersAddress
from .models.PhoneVerification import PhoneVerification
from .models.SchoolAddres import SchoolAddress
from .paypal import configure_paypal
from .utils import send_otp_to_phone

# from twilio.rest import Client




# Create your views here.
def index(request):
    return render(request, 'index.html')

# def home(request):
#     return render(request, 'home.html')

from django.contrib.auth.decorators import login_required


@login_required(login_url='login')  # Redirect to login page if not authenticated
def home(request):
    user = request.user
    print("[DEBUG] The User is : " , user)
    jobs_data = Job.objects.all()

    if request.user.is_authenticated and user.user_type == "job_seeker":
    
        seeker_profile = JobSeekerProfile.objects.get(user=request.user)

        job_seeker_application_form = JobApplicationForm(request.POST , instance = seeker_profile)

        matched_jobs = ai_score_jobs(jobs_data, seeker_profile)

        print("[DEBUG] The Jobs generated are : " , matched_jobs)
        # Convert matched_jobs to a serializable format
        job_list = []
        for job in matched_jobs:
            company = job.company
            job_dict = {
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "job_type": job.get_job_type_display(),
                "expected_start_date": job.expected_start_date,
                "experience_required": job.experience_required,
                "job_language": job.get_job_language_display(),
                "number_of_people": job.number_of_people,
                "work_location_type": job.get_work_location_type_display(),
                "job_location": {
                    "address": job.job_location.address,
                    "city": job.job_location.city,
                    "state": job.job_location.state,
                    "country": job.job_location.country,
                } if job.job_location else None,

                "company_goal": job.company_goal,
                "work_environment": job.work_environment,
                "additional_questions": job.get_additional_questions(),
                "salary": job.salary,
                "requirements": job.get_requirements(),
                "application_deadline": job.application_deadline.strftime('%Y-%m-%d') if job.application_deadline else '',
                "created_at": job.created_at.strftime('%Y-%m-%d'),
                "custom_questions": [
                    {"question": question.strip()}
                    for question in job.additional_questions.split(",")
                ] if job.additional_questions else [],

                "company": {
                    "name": company.name,
                    "description": company.description,
                    "website": company.website,
                    "industry": company.industry,
                    "tagline": company.tagline,
                    "linkedin_profile": company.linkedin_profile,
                    "registration_number": company.registration_number,
                    "business_license": company.business_license.url if company.business_license else '',
                    "company_policy_link": company.company_policy_link,
                    "founded": company.founded,
                    "company_size": company.company_size,
                    "headquarters_address": {
                        "address": company.headquarters_address.street_address,
                        "city": company.headquarters_address.city,
                        "state": company.headquarters_address.state,
                        "country": company.headquarters_address.country
                    } if company.headquarters_address else None,
                    "locations": [
                        {
                            "address": loc.address,
                            "city": loc.city,
                            "state": loc.state,
                            "country": loc.country
                        }
                        for loc in company.company_locations.all()
                    ]
                }
            
            }
            job_list.append(job_dict)
            if job.additional_questions:
                custom_questions = job.additional_questions.split('\n')
            

        
    return render(request, 'home.html', {'jobs': json.dumps(job_list, cls=DjangoJSONEncoder) , 'job_seeker' : seeker_profile , 'application_form' : job_seeker_application_form , 'custom_questions' : custom_questions})

def toggle_save_job(request):
    user = request.user
    print("[DEBUG] Toggle Save Job Function Called")
    if request.method == "POST":
        job_id = request.POST.get("job_id")
        print("[DEBUG] Job ID : " , job_id)
        try:
            job = Job.objects.get(id=job_id)
            print("[DEBUG] JOB Found : " , job)
            job_seeker = JobSeekerProfile.objects.get(user=user)
            saved_job, created = SavedJob.objects.get_or_create(job_seeker=job_seeker, job=job)
            print("[DEBUG] Saved Job Created  : " , saved_job)
            if not created:
                saved_job.delete()
                return JsonResponse({'status': 'unsaved'})
            return JsonResponse({'status': 'saved'})
        except Job.DoesNotExist:
            return JsonResponse({'error': 'Job not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def saved_jobs_view(request):
    user = request.user
    print("[DEBUG] The User is : " , user)

    if request.user.is_authenticated and user.user_type == "job_seeker":
        job_seeker = JobSeekerProfile.objects.get(user = user)
        applied_jobs = Application.objects.filter(job_seeker=job_seeker)
        saved_jobs = SavedJob.objects.filter(job_seeker=job_seeker)

        # Get job IDs for applied jobs
        applied_job_ids = set(app.job.id for app in applied_jobs)

        # Create a list of saved jobs with applied status
        jobs_with_status = []
        for saved in saved_jobs:
            job = saved.job
            is_applied = job.id in applied_job_ids
            jobs_with_status.append({
                'job': job,
                'applied': is_applied,
            })
        print("[DEBUG] Jobs with Status  : " , jobs_with_status)
        return render(request, 'saved_jobs.html', {'saved_jobs': saved_jobs , 'jobs_status'  : jobs_with_status})
    else:
        return redirect('login')

def delete_saved_job(request, saved_job_id):
    user = request.user
    print("[DEBUG] The User is : " , user)

    if user.is_authenticated and user.user_type == "job_seeker":
        job_seeker = JobSeekerProfile.objects.get(user = user)
        saved_job = get_object_or_404(SavedJob, id=saved_job_id, job_seeker=job_seeker)
        saved_job.delete()
        messages.success(request, f"Saved Job '{saved_job.job.title}' deleted.", extra_tags="saved_job_delete_success")
        return redirect('saved-jobs')
    else:
        return redirect('login')


def apply_for_job(request, job_id):
    if request.method == "POST":
        # Create the application form with POST data
        form = JobApplicationForm(request.POST, request.FILES)

        job = get_object_or_404(Job, id=job_id)
        user_profile = JobSeekerProfile.objects.get(user=request.user)

        # ✅ Check if user already applied
        if Application.objects.filter(job=job, job_seeker=user_profile).exists():
            return JsonResponse({'success': False, 'errors': 'You have already applied for this job.'})
        # Check if the job is already closed (if the number of applicants is full)
        if job.is_full():
            return JsonResponse({'success': False, 'errors': 'This job is closed as the maximum number of applicants has been reached.'})

        if form.is_valid():
            # Create application instance but don't save yet
            application = form.save(commit=False)
            application.job_seeker = user_profile
            application.job = job  # Set the job ID

            # Check which resume option was selected
            resume_option = request.POST.get('resume_option')

            if resume_option == 'profile':
                # If 'Use resume from profile' is selected, get the resume from the user's profile
                if user_profile.resume:
                    application.resume = user_profile.resume  # Attach profile resume to application
                else:
                    return JsonResponse({'success': False, 'errors': 'No resume found in profile.'})

            elif resume_option == 'upload':
                # If 'Upload new resume' is selected, use the uploaded resume
                if 'resume' in request.FILES:
                    application.resume = request.FILES['resume']
                else:
                    return JsonResponse({'success': False, 'errors': 'Please upload a resume.'})

            # Save the application
            application.save()

            # Increment the current applicant count for the job
            job.current_applicants += 1
            job.save()
            return JsonResponse({'success': True, 'message': 'Application submitted successfully.'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

    return JsonResponse({'success': False, 'errors': 'Invalid request method.'})

def applied_jobs_view(request):
    user = request.user
    print("[DEBUG] The User is : " , user)

    if request.user.is_authenticated and user.user_type == "job_seeker":
        job_seeker = JobSeekerProfile.objects.get(user = user)
        applied_jobs = Application.objects.filter(job_seeker=job_seeker)
        return render(request, 'applied_jobs.html', {'applied_jobs': applied_jobs , 'job_seeker' : job_seeker})
    else:
        return redirect('login')


def delete_application(request, job_id):
    user = request.user
    print("[DEBUG] The User is : " , user)

    if user.is_authenticated and user.user_type == "job_seeker":
        # Get the logged-in JobSeeker instance
        job_seeker = JobSeekerProfile.objects.get(user=request.user)
        # Get the application instance for the job and the job seeker
        application = get_object_or_404(Application, job_id=job_id, job_seeker=job_seeker)
        # Delete the application
        application.delete()
        # Add a success message
        messages.success(request, f"Your application for '{application.job.title}' has been successfully deleted.")
        # Redirect to the job seeker dashboard or job listing page
        return redirect('applied-jobs')
    else:
        return redirect('login')


from django.db.models import Q


def find_jobs(request):
    user = request.user
    print("[DEBUG] The User is : ", user)
    
    if user.is_authenticated and user.user_type == "job_seeker":
        print("[DEBUG] User is Authenticated")
        seeker_profile = JobSeekerProfile.objects.get(user=user)
        
        # Step 1: Get search terms and filters from the request (form submission)
        encoded_query = request.GET.get('query', '').strip()
        category = request.GET.get('category', 'All categories')
        query = urllib.parse.unquote(encoded_query)
        # Filters
        pay_filter = request.GET.get('pay', False)
        remote_filter = request.GET.get('remote', False)
        date_posted_filter = request.GET.get('datePosted', False)
        radius_filter = request.GET.get('radius', False)
        company_filter = request.GET.get('company', False)
        job_type_filter = request.GET.get('jobType', '').strip()
        language_filter = request.GET.get('language', '').strip()
        location_filter = request.GET.get('location', '').strip()

        # Step 2: Get recommendations based on search term + filters
        jobs = Job.objects.all()

        # Apply category filter if provided and if it's not "All categories"
        if category and category != "All categories":
            jobs = jobs.filter(company__industry__icontains=category)
            print("[DEBUG] Found category match")

        # Apply search query filter if provided
        if query:
            jobs = jobs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(company__name__icontains=query) |
                Q(job_type__icontains=query) |
                Q(job_language__icontains=query) |
                Q(requirements__icontains=query)
            )
            print("[DEBUG] Found search match")

        # Apply other filters (salary, remote, etc.)
        if pay_filter:
            jobs = jobs.filter(salary__gte=1)
            print("[DEBUG] Found pay match")

        if remote_filter:
            jobs = jobs.filter(job_location="Remote")
            print("[DEBUG] Found remote match")

        if date_posted_filter:
            jobs = jobs.filter(posted_date__gte="2025-01-01")
            print("[DEBUG] Found date match")

        if radius_filter:
            # Apply radius filter logic here (custom logic based on location)
            pass

        if company_filter:
            jobs = jobs.filter(company__isnull=False)
            print("[DEBUG] Found company match")

        if job_type_filter:
            jobs = jobs.filter(job_type__icontains=job_type_filter)
            print("[DEBUG] Found job_type match")

        if language_filter:
            jobs = jobs.filter(job_language__icontains=language_filter)
            print("[DEBUG] Found language match")

        if location_filter:
            jobs = jobs.filter(job_location__icontains=location_filter)
            print("[DEBUG] Found location match")

        # Step 3: If no jobs match, get profile-based recommendations
        filtered_jobs_data = build_job_dict_list(jobs)
        print("[DEBUG] Found Filtered Data  : ", filtered_jobs_data)

        if not filtered_jobs_data:
            seeker_query_text = " ".join([seeker_profile.skills or '', seeker_profile.desired_position or '', seeker_profile.about or '']).strip()
            profile_matches = enhanced_job_recommendation(seeker_query_text, seeker_profile.expected_salary or 0, filtered_jobs_data)
            
            if not profile_matches:
                # Step 4: If no profile matches, show all jobs
                all_jobs = Job.objects.all()
                all_jobs_data = build_job_dict_list(all_jobs)
                recommended_jobs = all_jobs_data
            else:
                recommended_jobs = profile_matches
        else:
            recommended_jobs = filtered_jobs_data

        # Step 5: Render the data into the HTML page
        return render(request, 'find_jobs.html', {
            'jobs': recommended_jobs,  # Make sure to send as JSON string
            'search_term': query,
            'filters': {
                'pay': pay_filter,
                'remote': remote_filter,
                'datePosted': date_posted_filter,
                'radius': radius_filter,
                'company': company_filter,
                'jobType': job_type_filter,
                'language': language_filter,
                'location': location_filter,
                'category': category
            },
        })
    else:
        return redirect('login')


def pre_register(request):
    if request.method == "POST":
        email = request.POST.get('email')
        user_type = request.POST.get('user_type')
        
        # Check for empty fields and show error messages
        if not email:
            messages.error(request, "Please enter your email.")
        if not user_type:
            messages.error(request, "Please select your user type.")

        # If there are any errors, re-render the form
        if not email or not user_type:
            return render(request, 'user_type.html')
        
        # Save the info in the session
        request.session['email'] = email
        request.session['user_type'] = user_type

        # Redirect to static HTML page (template)
        if user_type == 'job_seeker':
            return redirect('job-seeker-register')  # This should be a URL that maps to the HTML
        elif user_type == 'employer':
            return redirect('employer-register')
    else:
        return render(request, 'user_type.html')

def job_seeker_register(request):
    email = request.session['email']
    user_type = request.session['user_type']
    print("✉️ Email " , email , "User Type " , user_type)
    if email and user_type == "job_seeker" and request.method == "POST":
        password = request.POST.get('password')
        resume = request.FILES.get('resume_file')
        build_resume = request.POST.get('build_resume')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        street_address = request.POST.get('street_address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        level_of_education = request.POST.get('level_of_education')
        field = request.POST.get('field')
        school_name = request.POST.get('school_name')
        school_city = request.POST.get('school_city')
        school_state = request.POST.get('school_state')
        school_country = request.POST.get('school_country')
        currently_enrolled = request.POST.get('enroll')
        school_start = request.POST.get('school_from')
        school_end = request.POST.get('school_to')
        work_experience = request.POST.get('work_exp')
        min_wage_expectation = request.POST.get('min_wage')
        skills = request.POST.getlist('skills[]')

        certifications = []
        i = 1  # Start with the first certification
        
        while True:
            cert_name = request.POST.get(f'certifications[{i}][name]')
            cert_file = request.FILES.get(f'certifications[{i}][file]') 

            print("Certificate : " , cert_name)
            if not cert_name:  # If there's no cert_name, break the loop (no more certifications)
                break
            
            cert_info = {
                'name': cert_name,
                'file': cert_file
            }
            
            print(cert_info)
            certifications.append(cert_info)
            i += 1  # Increment the counter to check for the next certification
        certifications_objs = []
        if certifications:
            for cert in certifications:
                certifications_obj  = Certification.objects.create(
                    name=cert['name'],
                    certificate_file=cert['file']
                )
                certifications_objs.append(certifications_obj)

        experiences = []
        i = 1  # Start with the first experience

        while True:
            position = request.POST.get(f'experiences[{i}][position]')
            company = request.POST.get(f'experiences[{i}][company]')
            start_year = request.POST.get(f'experiences[{i}][start_year]')
            end_year = request.POST.get(f'experiences[{i}][end_year]')
            description = request.POST.get(f'experiences[{i}][description]')

            # Break the loop if no position is provided (indicating no more experiences)
            if not position:
                break

            experience_info = {
                'position': position,
                'company': company,
                'start_date': start_year,
                'end_date': end_year,
                'description': description
            }

            experiences.append(experience_info)
            i += 1  # Increment the counter to check for the next experience

        experience_objs = []
        if experiences:
            for exp in experiences:
                experience = Experience.objects.create(
                    position=exp['position'],
                    company=exp['company'],
                    start_date=exp['start_date'],
                    end_date=exp['end_date'] or None,  # Handle optional end date
                    description=exp['description']
                )
                experience_objs.append(experience)

        desired_job_title = request.POST.get('job_title')
        relocation = request.POST.get('relocation')
        job_type = request.POST.get('job_type[]')
        profile_type = request.POST.get('visibility')


        print("Details : " , email , user_type , password , resume , build_resume , first_name , last_name , age , gender , street_address , city , state , country , level_of_education , field , school_name , school_city , school_state , school_country , currently_enrolled , school_start , school_end , work_experience , min_wage_expectation , skills , certifications , desired_job_title , relocation , job_type , profile_type)
        # 1. Check if user already exists
        user = CustomUser.objects.filter(email=email).first()

        if not user:
            # 1. Create CustomUser
            user = CustomUser.objects.create(
                username = email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type,
                password=make_password(password)  # Hash the password
            )

            # 2. Create Address
            address = Address.objects.create(
                street_address=street_address,
                city=city,
                state=state,
                country=country
            )

            # 3. Create School Address
            school_address = SchoolAddress.objects.create(
                school_name=school_name,
                school_city=school_city,
                school_state=school_state,
                school_country=school_country
            )

            # 4. Create Education
            education = Education.objects.create(
                level=level_of_education,
                field=field,
                start_year=school_start,
                end_year=school_end,
                currently_enrolled=(currently_enrolled == "yes")
            )

            # 5. Create JobSeekerProfile
            profile = JobSeekerProfile.objects.create(
                user=user,
                gender=gender,
                age=int(age) if age else None,
                address=address,
                school_address=school_address,
                location_preference='hybrid',  # Can be made dynamic
                onsite_location='',  # If you have onsite address
                skills=",".join(skills),
                work_experience=int(work_experience) if work_experience else 0,
                education=education,
                expected_salary=min_wage_expectation if min_wage_expectation else None,
                desired_position=desired_job_title,
                relocation=relocation,
                job_type=job_type,
                profile_visibility=profile_type
            )
            if certifications_objs:
                profile.certificates.set([certifications_objs])
            else:
                print("No certificates found")
            if experience_objs:
                profile.certificates.set([experience_objs])
            else:
                print("No Experience found")
            if(resume):
                profile.resume.set(resume)  
            elif(build_resume == "Yes"):
                # Generate the PDF from the function
                pdf_buffer = generate_resume_pdf(user, profile)
                
                # Convert the buffer to a Django File
                pdf_file = File(pdf_buffer, name="resume.pdf")
                
                # Save the file to the profile's resume field
                profile.resume.save(f"resume_{user.get_full_name()}.pdf", pdf_file, save=True)
            else:
                print("Resume not Build / Found")
            profile.save()
            print("The user is : " , user)
            request.session['registering_user_id'] = user.id
            print("ID  :  " , request.session['registering_user_id'])
            print("Job Seeker created : " , profile)

        else:
            print(f"User with email {email} already exists. Using existing user.")


        return redirect('phone_verification')
        
    years = list(range(1990, datetime.now().year + 1))
    print(years)
    return render(request, 'register.html', {'years' : years, 'email': email})

def company_register(request):
    email = request.session['email']
    user_type = request.session['user_type']
    print("✉️ Email", email, "User Type", user_type)

    if email and user_type == "employer" and request.method == "POST":
        password = request.POST.get('password')

        company_name = request.POST.get('company_name')
        company_email = request.POST.get('company_email')

        employees = request.POST.get('employees')
        company_website = request.POST.get('website')
        company_industry = request.POST.get('industry')
        foundation_year = request.POST.get('foundation_year')

        company_headquarters_address = request.POST.get('hq_street')
        company_headquarters_city = request.POST.get('hq_city')
        company_headquarters_state = request.POST.get('hq_state')
        company_headquarters_country = request.POST.get('hq_country')

        locations_data = []
            
        # Collect all location data from the POST request
        for key, value in request.POST.items():
            if key.startswith('locations['):
                # Extract the index and field name from keys like "locations[0][street]"
                parts = key.split('[')[1].split(']')
                if len(parts) == 2:
                    index = parts[0]
                    field = parts[1].strip('[]')  # Handles both formats: locations[0][street] and locations[0][street]
                    
                    # Ensure we have a list entry for this index
                    while len(locations_data) <= int(index):
                        locations_data.append({})
                    
                    locations_data[int(index)][field] = value

        company_logo = request.FILES.get('company_logo') 
        company_tagline = request.POST.get('tagline')
        company_description = request.POST.get('description')
        company_registration_number = request.POST.get('tax_id')
        business_license = request.FILES.get('business_license') 
        company_policy_link = request.POST.get('policies_link')
        company_linkedin_profile = request.POST.get('company_linkedin')


        # Company Person Info
        person_linkedin_profile = request.POST.get('linkedin_profile')
        person_position = request.POST.get('sposition')
        person_first_name = request.POST.get('first_name')
        person_last_name = request.POST.get('last_name')

        # 1. Check if company exists
        company = CustomUser.objects.filter(email=email, user_type='company').first()

        if not company:
            # 1. Create Company CustomUser
            company = CustomUser.objects.create(
                username=company_email,
                email=company_email,
                user_type='company',
                password=make_password(password)  # Hash the password
            )
            if company_logo:
                company.profile_picture = company_logo
                company.save()

            locations = []
            # Create Location objects for each valid location
            for loc_data in locations_data:
                if loc_data.get('street') and loc_data.get('city'):
                    location = Location.objects.create(
                        street=loc_data.get('street'),
                        city=loc_data.get('city'),
                        state=loc_data.get('state', ''),
                        country=loc_data.get('country', '')
                    )
                    locations.append(location) 

            headquarters_address = HeadQuartersAddress.objects.create(
                street_address=company_headquarters_address,
                city=company_headquarters_city,
                state=company_headquarters_state,
                country=company_headquarters_country
            )
            # 2. Create Company Profile
            company_profile = Company.objects.create(
                user=company,
                name=company_name,
                description=company_description,
                website=company_website,
                industry=company_industry,
                headquarters_address=headquarters_address,
                founded = foundation_year,
                company_size = employees,
                linkedin_profile = company_linkedin_profile,
                tagline=company_tagline,
                registration_number=company_registration_number,
                business_license = business_license,
                company_policy_link=company_policy_link
            )
            company_profile.company_locations.set(locations)
            
            # 3. Add the first company person (CEO or primary contact)
            company_person = CustomUser.objects.create(
                username=email,
                email=email,
                user_type='company_person',
                first_name=person_first_name,
                last_name=person_last_name,
                password=make_password(password)
            )
            CompanyPerson.objects.create(
                company=company_profile,
                user=company_person,
                position=person_position,
                linkedin_profile=person_linkedin_profile,
                is_superuser = True
            )


            print("The user is : " , company_person)
            request.session['registering_user_id'] = company_person.id
            print("ID  :  " , request.session['registering_user_id'])

            # 4. Redirect to Profile or Dashboard
            return redirect('phone_verification')
        else:
            print(f"Company with email {email} already exists.")

    return render(request, 'company_register.html')



def user_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = CustomUser(
                username = form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                user_type = "Job Seeker",
                is_active=False
            )
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Store user ID in session for multi-step registration
            request.session['registering_user_id'] = user.id

            return redirect('phone_verification')
        else:
            print("Form is invalid")  # Debugging line
            print(form.errors.as_json())
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})


# def phone_verification(request):
#     user_id = request.session.get('registering_user_id')
#     print(user_id)
#     if not user_id:
#         return redirect('user_register')
    
#     try:
#         user = CustomUser.objects.get(id=user_id)
#         print(type(user))
#     except CustomUser.DoesNotExist:
#         return redirect('user_register')
    
#     if request.method == 'POST':
#         form = PhoneVerificationForm(request.POST)
#         form.request = request

#         if 'send_otp' in request.POST: 
#             if form.is_valid():
#                 cache_key = f'otp_attempts_{user_id}'
#                 attempts = cache.get(cache_key, 0)
                
#                 if attempts >= 3:  # Limit to 3 attempts
#                     form.add_error(None, 'Too many attempts. Please try again later.')
#                     return render(request, 'phone_verification.html', {'form': form})
            
#                 full_phone = form.cleaned_data['full_phone']
                
#                 # if CustomUser.objects.exclude(id=user_id).filter(phone_number=full_phone).exists():
#                 #     form.add_error('phone_number', 'This phone number is already registered.')
#                 #     return render(request, 'phone_verification.html', {'form': form})
                
#                 # Generate and save OTP
#                 otp = str(random.randint(100000, 999999))
#                 PhoneVerification.objects.filter(user=user).delete()  # Clear previous attempts
#                 PhoneVerification.objects.create(
#                     user=user, 
#                     phone_number = full_phone,
#                     otp=otp)
                
#                 # Send OTP via Twilio
#                 client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#                 try:
#                     message = client.messages.create(
#                         body=f'Your verification code is: {otp}',
#                         from_=settings.TWILIO_PHONE_NUMBER,
#                         to=full_phone
#                     )
#                     print(message.sid)
#                     # Store phone number in session
#                     request.session['verification_phone'] = full_phone
#                     return render(request, 'phone_verification.html', {
#                         'form': form,
#                         'otp_sent': True,
#                         'phone_number': full_phone
#                     })
#                 except Exception as e:
#                     print(f"Failed to send OTP: {str(e)}")
#                     form.add_error(None, 'Failed to send OTP. Please try again.')
        
#         elif 'verify_otp' in request.POST:  # Verify OTP button clicked
#             if form.is_valid():
#                 otp = form.cleaned_data['otp']
#                 full_phone = request.session.get('verification_phone')
                
#                 try:
#                     verification = PhoneVerification.objects.get(
#                         user=user,
#                         otp=otp,
#                         is_verified=False
#                     )
#                     # Mark as verified
#                     verification.is_verified = True
#                     verification.phone_number = full_phone
#                     verification.save()
                    
#                     # Update user's phone number and verification status
#                     user.phone_number = full_phone
#                     user.is_phone_verified = True
#                     user.save()
                    
#                     # Clean up session
#                     if 'verification_phone' in request.session:
#                         del request.session['verification_phone']
#                     cache.delete(f'otp_attempts_{user_id}')
                    
#                     return redirect('job_seeker_details_1')
#                 except PhoneVerification.DoesNotExist:
#                     form.add_error('otp', 'Invalid OTP code')
#                     return render(request, 'phone_verification.html', {
#                         'form': form,
#                         'otp_sent': True,
#                         'phone_number': full_phone
#                     })
#             else:
#                 return render(request, 'phone_verification.html', {
#                     'form': form,
#                     'otp_sent': True,
#                     'phone_number': request.session.get('verification_phone')
#                 })
#         elif 'resend_otp' in request.POST:  # Resend OTP button clicked
#             full_phone = request.session.get('verification_phone')
#             if form.is_valid() and full_phone:

#                 # Rate limiting check for resend
#                 cache_key = f'otp_attempts_{user_id}'
#                 attempts = cache.get(cache_key, 0)
                
#                 if attempts >= 3:
#                     form.add_error(None, 'Too many attempts. Please try again later.')
#                     return render(request, 'phone_verification.html', {
#                         'form': form,
#                         'otp_sent': True,
#                         'phone_number': full_phone
#                     })
                
#                 # Generate new OTP
#                 otp = str(random.randint(100000, 999999))
#                 PhoneVerification.objects.filter(user=user).delete()
#                 PhoneVerification.objects.create(user=user, otp=otp)
                
#                 # Update rate limiting counter
#                 cache.set(cache_key, attempts + 1, timeout=300)

#                 # Resend OTP
#                 client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#                 try:
#                     message = client.messages.create(
#                         body=f'Your new verification code is: {otp}',
#                         from_=settings.TWILIO_PHONE_NUMBER,
#                         to=full_phone
#                     )
#                     return render(request, 'phone_verification.html', {
#                         'form': form,
#                         'otp_sent': True,
#                         'phone_number': full_phone,
#                         'resend_success': True
#                     })
#                 except Exception as e:
#                     form.add_error(None, 'Failed to resend OTP. Please try again.')
#             else:
#                 if not full_phone:
#                     form.add_error('phone_number', 'Phone number is required')
#                 if not form.is_valid():  # Will contain existing validation errors
#                     return render(request, 'phone_verification.html', {
#                         'form': form,
#                         'otp_sent': True
#                     })
#     else:
#         form = PhoneVerificationForm()
#         form.request = request
#     return render(request, 'phone_verification.html', {'form': form})
logger = logging.getLogger(__name__)

# def phone_verification(request):
#     user_id = request.session.get('registering_user_id')
#     print("The user ID is  : " , user_id)
#     if not user_id:
#         return redirect('user_type')
    
#     try:
#         user = CustomUser.objects.get(id=user_id)
#         print("The user in phone verification is : " , user)
#     except CustomUser.DoesNotExist:
#         return redirect('user_register')
    
#     if request.method == 'POST':
#         form = PhoneVerificationForm(request.POST)
#         form.request = request

#         if 'send_otp' in request.POST: 
#             if form.is_valid():
#                 cache_key = f'otp_attempts_{user_id}'
#                 attempts = cache.get(cache_key, 0)
                
#                 if attempts >= 3:
#                     form.add_error(None, 'Too many attempts. Please try again later.')
#                     return render(request, 'phone_verification.html', {'form': form})
            
#                 full_phone = form.cleaned_data['full_phone']
                
#                 # Generate and save OTP
#                 otp = str(random.randint(100000, 999999))
#                 PhoneVerification.objects.filter(user=user).delete()
#                 PhoneVerification.objects.create(
#                     user=user, 
#                     phone_number=full_phone,
#                     otp=otp
#                 )
                
#                 # Send OTP using django-sms (development)
#                 try:
#                     send_sms(
#                         f'Your verification code is: {otp}',
#                         None,  # Fake number for development
#                         [full_phone],
#                         fail_silently=False
#                     )
                    
#                     # In development, print to console and continue
#                     print(f"DEV: OTP for {full_phone} is {otp}")
                    
#                     request.session['verification_phone'] = full_phone
#                     return render(request, 'phone_verification.html', {
#                         'form': form,
#                         'otp_sent': True,
#                         'phone_number': full_phone
#                     })
#                 except Exception as e:
#                     print(f"Failed to send OTP: {str(e)}")
#                     form.add_error(None, 'Failed to send OTP. Please try again.')
        
#         elif 'verify_otp' in request.POST:
#             full_phone = request.session.get('verification_phone')
#             if not full_phone:
#                 form.add_error(None, 'Phone number not found. Please request a new OTP.')
#                 return render(request, 'phone_verification.html', {'form': form})
            
#             otp = request.POST.get('otp')
#             if not otp:
#                 form.add_error('otp', 'OTP is required')
#                 return render(request, 'phone_verification.html', {
#                     'form': form,
#                     'otp_sent': True,
#                     'phone_number': full_phone
#                 })
            
#             try:
#                 verification = PhoneVerification.objects.get(
#                     user=user,
#                     otp=otp,
#                     is_verified=False
#                 )
                
#                 # Mark as verified
#                 verification.is_verified = True
#                 verification.save()
                
#                 # Update user
#                 user.phone_number = full_phone
#                 user.is_phone_verified = True
#                 user.is_active = True
#                 user.save()
                

#                 # ✅ Clear old OTP session and cache
#                 if 'verification_phone' in request.session:
#                     del request.session['verification_phone']
#                 cache.delete(f'otp_attempts_{user_id}')
                
#                 # Log the user in after successful phone verification
#                 user.backend = 'django.contrib.auth.backends.ModelBackend'
#                 logger.info(f"Logging in user: {user.username} with backend: {user.backend}")
                
#                 request.session.flush()
#                 login(request, user)

#                 # Save session and clear OTP-related data
#                 request.session.save()

#                 # Log session info
#                 logger.info(f"User authenticated: {request.user.is_authenticated}")
#                 logger.info(f"Session Key: {request.session.session_key}")
#                 logger.info(f"Session Data: {dict(request.session.items())}")
                
#                 return redirect('job_seeker_details_1')
                
                
#             except PhoneVerification.DoesNotExist:
#                 form.add_error('otp', 'Invalid OTP code')
#                 logger.error(f"Invalid OTP attempt for user: {user.username}")
#                 return render(request, 'phone_verification.html', {
#                     'form': form,
#                     'otp_sent': True,
#                     'phone_number': full_phone
#                 })
    
#         elif 'resend_otp' in request.POST:
#             full_phone = request.session.get('verification_phone')
#             if form.is_valid() and full_phone:
#                 cache_key = f'otp_attempts_{user_id}'
#                 attempts = cache.get(cache_key, 0)
                
#                 if attempts >= 3:
#                     form.add_error(None, 'Too many attempts. Please try again later.')
#                     return render(request, 'phone_verification.html', {
#                         'form': form,
#                         'otp_sent': True,
#                         'phone_number': full_phone
#                     })
                
#                 # Generate new OTP
#                 otp = str(random.randint(100000, 999999))
#                 PhoneVerification.objects.filter(user=user).delete()
#                 PhoneVerification.objects.create(
#                     user=user, 
#                     phone_number=full_phone,
#                     otp=otp
#                 )
                
#                 cache.set(cache_key, attempts + 1, timeout=300)

#                 # Resend OTP (development)
#                 try:
#                     send_sms(
#                         f'Your new verification code is: {otp}',
#                         None,
#                         [full_phone],
#                         fail_silently=False
#                     )
#                     print(f"DEV: Resent OTP for {full_phone} is {otp}")
                    
#                     return render(request, 'phone_verification.html', {
#                         'form': form,
#                         'otp_sent': True,
#                         'phone_number': full_phone,
#                         'resend_success': True
#                     })
#                 except Exception as e:
#                     form.add_error(None, 'Failed to resend OTP. Please try again.')
    
#     else:
#         form = PhoneVerificationForm()
    
#     return render(request, 'phone_verification.html', {'form': form})

def phone_verification(request):
    user_id = request.session.get('registering_user_id')
    print("The user ID is:", user_id)

    if not user_id:
        return redirect('pre-signup')
    
    try:
        user = CustomUser.objects.get(id=user_id)
        print("The user in phone verification is:", user)
    except CustomUser.DoesNotExist:
        return redirect('user_register')

    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)
        form.request = request

        if 'send_otp' in request.POST:
            if form.is_valid():
                cache_key = f'otp_attempts_{user_id}'
                attempts = cache.get(cache_key, 0)
                
                if attempts >= 3:
                    form.add_error(None, 'Too many attempts. Please try again later.')
                    return render(request, 'phone_verification.html', {'form': form})

                full_phone = form.cleaned_data['full_phone']
                
                # Generate and save OTP
                otp = str(random.randint(100000, 999999))
                PhoneVerification.objects.filter(user=user).delete()
                PhoneVerification.objects.create(
                    user=user,
                    phone_number=full_phone,
                    otp=otp
                )

                try:
                    send_sms(
                        f'Your verification code is: {otp}',
                        None,
                        [full_phone],
                        fail_silently=False
                    )
                    print(f"DEV: OTP for {full_phone} is {otp}")

                    request.session['verification_phone'] = full_phone
                    return render(request, 'phone_verification.html', {
                        'form': form,
                        'otp_sent': True,
                        'phone_number': full_phone
                    })
                except Exception as e:
                    print(f"Failed to send OTP: {str(e)}")
                    form.add_error(None, 'Failed to send OTP. Please try again.')

        elif 'verify_otp' in request.POST:
            full_phone = request.session.get('verification_phone')
            if not full_phone:
                form.add_error(None, 'Phone number not found. Please request a new OTP.')
                return render(request, 'phone_verification.html', {'form': form})

            # ✅ Collect OTP from 6 separate fields
            otp_digits = [
                request.POST.get(f'otp_{i}', '') for i in '123456'
            ]
            otp = ''.join(otp_digits).strip()

            if not otp or len(otp) != 6:
                form.add_error('otp', 'Complete 6-digit OTP is required.')
                return render(request, 'phone_verification.html', {
                    'form': form,
                    'otp_sent': True,
                    'phone_number': full_phone
                })

            try:
                verification = PhoneVerification.objects.get(
                    user=user,
                    otp=otp,
                    is_verified=False
                )

                verification.is_verified = True
                verification.save()

                # Update user
                user.phone_number = full_phone
                user.is_phone_verified = True
                user.is_active = True
                user.save()

                # Clear old session and cache
                if 'verification_phone' in request.session:
                    del request.session['verification_phone']
                cache.delete(f'otp_attempts_{user_id}')

                # Log in user
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                logger.info(f"Logging in user: {user.username} with backend: {user.backend}")

                login(request, user)

                logger.info(f"User authenticated: {request.user.is_authenticated}")
                logger.info(f"Session Key: {request.session.session_key}")
                logger.info(f"Session Data: {dict(request.session.items())}")

                # ✅ Now Redirect based on role
                if user.user_type == "job_seeker":
                    try:
                        return redirect('home')

                    except JobSeekerProfile.DoesNotExist:
                        return redirect('error_page')
                
                elif user.user_type == "company_person":
                    try:
                        company_person = CompanyPerson.objects.get(user=user)
                        if company_person.is_superuser:
                            return redirect('company_admin_dashboard')
                        else:
                            return redirect('company_person_dashboard')
                    except CompanyPerson.DoesNotExist:
                        return redirect('error_page')

                else:
                    return redirect('pre-signup')

            except PhoneVerification.DoesNotExist:
                form.add_error('otp', 'Invalid OTP code.')
                logger.error(f"Invalid OTP attempt for user: {user.username}")
                return render(request, 'phone_verification.html', {
                    'form': form,
                    'otp_sent': True,
                    'phone_number': full_phone
                })

        elif 'resend_otp' in request.POST:
            full_phone = request.POST.get('full_phone')
            if form.is_valid() and full_phone:
                cache_key = f'otp_attempts_{user_id}'
                attempts = cache.get(cache_key, 0)

                if attempts >= 3:
                    form.add_error(None, 'Too many attempts. Please try again later.')
                    return render(request, 'phone_verification.html', {
                        'form': form,
                        'otp_sent': True,
                        'phone_number': full_phone
                    })

                otp = str(random.randint(100000, 999999))
                PhoneVerification.objects.filter(user=user).delete()
                PhoneVerification.objects.create(
                    user=user,
                    phone_number=full_phone,
                    otp=otp
                )

                cache.set(cache_key, attempts + 1, timeout=300)

                try:
                    send_sms(
                        f'Your new verification code is: {otp}',
                        None,
                        [full_phone],
                        fail_silently=False
                    )
                    print(f"DEV: Resent OTP for {full_phone} is {otp}")

                    return render(request, 'phone_verification.html', {
                        'form': form,
                        'otp_sent': True,
                        'phone_number': full_phone,
                        'resend_success': True
                    })
                except Exception as e:
                    form.add_error(None, 'Failed to resend OTP. Please try again.')

    else:
        form = PhoneVerificationForm()

    return render(request, 'phone_verification.html', {'form': form})


def company_person_edit_view(request, company_name, company_person_name):
    user = request.user

    if user.is_authenticated and user.user_type == "company_person":
        try:
            company = Company.objects.get(name=company_name)
            company_person = CompanyPerson.objects.get(user=user, company=company)
            company_person_full_name = company_person.user.get_full_name()

            if company_person_full_name != company_person_name:
                return redirect('login')

            otp_form = PhoneVerificationForm(request.POST or None, request=request)

            if request.method == "POST":
                if "send_otp" in request.POST:
                    # Handle OTP sending
                    if otp_form.is_valid():
                        full_phone = otp_form.cleaned_data['full_phone']
                        otp = str(random.randint(100000, 999999))

                        # Store OTP in the PhoneVerification model
                        PhoneVerification.objects.filter(user=user).delete()
                        PhoneVerification.objects.create(
                            user=user,
                            phone_number=full_phone,
                            otp=otp
                        )

                        # Track attempts
                        cache_key = f'otp_attempts_{user.id}'
                        attempts = cache.get(cache_key, 0)
                        if attempts >= 3:
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Too many attempts. Please try again later.'
                            })

                        cache.set(cache_key, attempts + 1, timeout=300)

                        try:
                            # Send OTP via SMS
                            send_sms(
                                f'Your verification code is: {otp}',
                                None,
                                [full_phone],
                                fail_silently=False
                            )
                            request.session['verification_phone'] = full_phone
                            return JsonResponse({
                                'status': 'success',
                                'otp_sent': True,
                                'phone_number': full_phone
                            })

                        except Exception as e:
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Failed to send OTP. Please try again.'
                            })

                elif "verify_otp" in request.POST:
                    # Handle OTP verification
                    full_phone = request.session.get('verification_phone')
                    if not full_phone:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Phone number not found. Please request a new OTP.'
                        })

                    otp_digits = [request.POST.get(f'otp_{i}', '') for i in '123456']
                    otp = ''.join(otp_digits).strip()

                    if not otp or len(otp) != 6:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Complete 6-digit OTP is required.'
                        })

                    try:
                        # Validate OTP
                        verification = PhoneVerification.objects.get(
                            user=user,
                            otp=otp,
                            is_verified=False
                        )
                        verification.is_verified = True
                        verification.save()

                        # Update user
                        user.phone_number = full_phone
                        user.is_phone_verified = True
                        user.is_active = True
                        user.save()

                        # Clear old session and cache
                        if 'verification_phone' in request.session:
                            del request.session['verification_phone']
                        cache.delete(f'otp_attempts_{user.id}')

                        # Log in user
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                        login(request, user)

                        return JsonResponse({
                            'status': 'success',
                            'message': 'OTP verified successfully. Profile updated!'
                        })

                    except PhoneVerification.DoesNotExist:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Invalid OTP code.'
                        })

                elif "resend_otp" in request.POST:
                    # Handle OTP resend
                    full_phone = request.POST.get('full_phone')
                    if otp_form.is_valid() and full_phone:
                        cache_key = f'otp_attempts_{user.id}'
                        attempts = cache.get(cache_key, 0)

                        if attempts >= 3:
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Too many attempts. Please try again later.'
                            })

                        otp = str(random.randint(100000, 999999))
                        PhoneVerification.objects.filter(user=user).delete()
                        PhoneVerification.objects.create(
                            user=user,
                            phone_number=full_phone,
                            otp=otp
                        )

                        cache.set(cache_key, attempts + 1, timeout=300)

                        try:
                            # Send OTP via SMS
                            send_sms(
                                f'Your new verification code is: {otp}',
                                None,
                                [full_phone],
                                fail_silently=False
                            )

                            return JsonResponse({
                                'status': 'success',
                                'message': 'OTP resent successfully.'
                            })

                        except Exception as e:
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Failed to resend OTP. Please try again.'
                            })

            else:
                return render(request, 'company/edit_company_person.html', {
                    'otp_form': otp_form,
                    'company_person_form': CompanyPersonEditForm(instance=company_person),
                    'company': company,
                    'company_person': company_person,
                    'company_person_full_name': company_person_full_name
                })

        except Company.DoesNotExist:
            return redirect('pre-signup')
        except CompanyPerson.DoesNotExist:
            return redirect('login')

    else:
        return redirect('login')

def job_seeker_details_1(request):
    """View for the first step of job seeker profile creation (Basic Info)"""
    logger.info(f"User authenticated: {request.user.is_authenticated}")
    logger.info(f"Session Key: {request.session.session_key}")
    logger.info(f"Session Data: {dict(request.session.items())}")

    if not request.user.is_authenticated and '_auth_user_id' in request.session:
        user_id = request.session['_auth_user_id']
        
        try:
            user = CustomUser.objects.get(pk=user_id)
            request.user = user  # ✅ Manually assign user
            logger.info(f"✅ User manually loaded from session: {user.username}")
        except CustomUser.DoesNotExist:
            logger.warning(f"⚠️ User ID {user_id} not found in database.")

    # 🔍 Final authentication check
    logger.info(f"🔍 Final Authentication Check: {request.user.is_authenticated}")

    # Check if the user already has a profile
    if request.user.is_authenticated:

        try:
            profile = JobSeekerProfile.objects.get(user=request.user)
        except JobSeekerProfile.DoesNotExist:
            # Create a new profile if one doesn't exist
            profile = JobSeekerProfile(user=request.user)
            profile.save()
        
        if request.method == 'POST':
            # Check if the user wants to skip this step
            if 'skip' in request.POST:
                return redirect('job_seeker_details_2')
            
            form = Step1BasicInfoForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Basic information saved successfully!')
                return redirect('job_seeker_details_2')
        else:
            form = Step1BasicInfoForm(instance=profile)
        
        return render(request, 'basic_info.html', {'form': form})
    messages.error(request, 'You must verify your phone number first.')
    return redirect('phone_verification')

def job_seeker_details_2(request):
    """View for the second step of job seeker profile creation (Skills & Experience)"""
    logger.info(f"User authenticated: {request.user.is_authenticated}")
    logger.info(f"Session Key: {request.session.session_key}")
    logger.info(f"Session Data: {dict(request.session.items())}")
    
    if not request.user.is_authenticated and '_auth_user_id' in request.session:
        user_id = request.session['_auth_user_id']
        
        try:
            user = CustomUser.objects.get(pk=user_id)
            request.user = user  # ✅ Manually assign user
            logger.info(f"✅ User manually loaded from session: {user.username}")
        except CustomUser.DoesNotExist:
            logger.warning(f"⚠️ User ID {user_id} not found in database.")

    # 🔍 Final authentication check
    logger.info(f"🔍 Final Authentication Check: {request.user.is_authenticated}")

    # Check if the user already has a profile
    if request.user.is_authenticated:

        try:
            profile = JobSeekerProfile.objects.get(user=request.user)
        except JobSeekerProfile.DoesNotExist:
            # Create a profile if it doesn't exist (in case they skipped step 1)
            profile = JobSeekerProfile(user=request.user)
            profile.save()
        
        if request.method == 'POST':
            # Check if the user wants to skip this step
            if 'skip' in request.POST:
                return redirect('job_seeker_details_3')
            
            form = Step2SkillsForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Skills and experience saved successfully!')
                return redirect('job_seeker_details_3')
        else:
            form = Step2SkillsForm(instance=profile)
        
        return render(request, 'skills.html', {'form': form})

    messages.error(request, 'You must verify your phone number first.')
    return redirect('phone_verification')

def job_seeker_details_3(request):
    """View for the third step of job seeker profile creation (Education & Documents)"""
    logger.info(f"User authenticated: {request.user.is_authenticated}")
    logger.info(f"Session Key: {request.session.session_key}")
    logger.info(f"Session Data: {dict(request.session.items())}")
    
    if not request.user.is_authenticated and '_auth_user_id' in request.session:
        user_id = request.session['_auth_user_id']
        
        try:
            user = CustomUser.objects.get(pk=user_id)
            request.user = user  # ✅ Manually assign user
            logger.info(f"✅ User manually loaded from session: {user.username}")
        except CustomUser.DoesNotExist:
            logger.warning(f"⚠️ User ID {user_id} not found in database.")

    # 🔍 Final authentication check
    logger.info(f"🔍 Final Authentication Check: {request.user.is_authenticated}")

    # Check if the user already has a profile
    if request.user.is_authenticated:

        try:
            profile = JobSeekerProfile.objects.get(user=request.user)
        except JobSeekerProfile.DoesNotExist:
            # Create a profile if it doesn't exist (in case they skipped steps 1 and 2)
            profile = JobSeekerProfile(user=request.user)
            profile.save()
        
        if request.method == 'POST':
            # Check if the user wants to skip this step
            if 'skip' in request.POST:
                profile.is_complete = True
                profile.save()
                messages.success(request, 'Your profile has been completed successfully!')
                return redirect('home')
            
            form = Step3EducationForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                profile = form.save(commit=False)
                profile.is_complete = True
                profile.save()
                messages.success(request, 'Your profile has been completed successfully!')
                return redirect('home')
        else:
            form = Step3EducationForm(instance=profile)
        
        return render(request, 'education.html', {'form': form})
    messages.error(request, 'You must verify your phone number first.')
    return redirect('phone_verification')


@login_required(login_url='login')
def profile_view(request):
    print("🔍 Request user:", request.user)
    print("🔐 Is authenticated?", request.user.is_authenticated)
    if not request.user.is_authenticated:
        messages.warning(request, "Please Log In first!.")
    is_external = False
    profile_picture = request.user.profile_picture
    profile_picture_url = str(profile_picture) if profile_picture else ""
    if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
        print(profile_picture_url)
        is_external = True
    else:
        is_external = False
    job_seeker = JobSeekerProfile.objects.get(user=request.user)
    saved_jobs_count = SavedJob.objects.filter(job_seeker=job_seeker).count()
    applied_jobs_count = Application.objects.filter(job_seeker=job_seeker).count()
    if job_seeker.skills:
        skills = [skill.strip() for skill in job_seeker.skills.split(',')]
    else:
        skills = []

            
        return redirect('login')  # Redirect to login if not authenticated

    return render(request, 'profile.html', {'job_seeker': job_seeker, 'applied_jobs_count' : applied_jobs_count ,
        'saved_jobs_count': saved_jobs_count, 'is_external' : is_external , 'skills' : skills})


# def edit_profile_view(request):
#     try:
#         user = request.user
#         job_seeker_profile = JobSeekerProfile.objects.get(user=user)
#     except JobSeekerProfile.DoesNotExist:
#         job_seeker_profile = None
    
#     if not job_seeker_profile:
#         print("Job Seeker Profile does not exist for this user")
#         return redirect('pre-signup')  # Or any other suitable URL for creating a profile

#     # Debug: Check the certificates and experiences attributes
#     print("Certificates:", job_seeker_profile.certificates.all())  # Should not throw an error
#     print("Experiences:", job_seeker_profile.experiences.all())  # Should not throw an error

#     # Initial form instance with current data from job_seeker_profile
#     profile_form = JobSeekerProfileForm(instance=job_seeker_profile)
#     user_form = CustomUserFormForJobSeeker(instance=job_seeker_profile.user)
#     address_form = AddressForm(instance=job_seeker_profile.address)
#     # Formsets for certifications, work experience, and education
#     CertificationFormSet = modelformset_factory(Certification, form=CertificationForm, extra=1, can_delete=True)
#     WorkExperienceFormSet = modelformset_factory(Experience, form=WorkExperienceForm, extra=1, can_delete=True)
#     EducationFormSet = modelformset_factory(Education, form=EducationForm, extra=1, can_delete=True)

#     # Handling formset creation or updates
#     certification_formset = CertificationFormSet(queryset=job_seeker_profile.certificates.all())
#     work_experience_formset = WorkExperienceFormSet(queryset=job_seeker_profile.experiences.all())
#     education_formset = EducationFormSet(queryset=job_seeker_profile.education.all())
#     school_address_form = SchoolAddressForm(prefix='school', instance=job_seeker_profile.education.school_address if job_seeker_profile.education.school_address else None)
#     print("[DEBUG] The School Address Form is : " , school_address_form)
#     if request.method == 'POST':
#         # Bind profile form
#         profile_form = JobSeekerProfileForm(request.POST, request.FILES, instance=job_seeker_profile)
#         user_form = CustomUserFormForJobSeeker(request.POST, request.FILES, instance=job_seeker_profile.user)
#         address_form = AddressForm(request.POST, instance=job_seeker_profile.address)
#         # Bind Education formset (which includes school_address)
#         education_formset = EducationFormSet(request.POST)
#         # Bind formsets for certifications and work experience
#         certification_formset = CertificationFormSet(request.POST, request.FILES)
#         work_experience_formset = WorkExperienceFormSet(request.POST)

#         if profile_form.is_valid() and certification_formset.is_valid() and work_experience_formset.is_valid() and address_form.is_valid() and education_formset.is_valid():
#             user = user_form.save()  # Save the user form first
#             address = address_form.save()  # Save the address form
            
#             # Save the profile form
#             job_seeker = profile_form.save(commit=False)
#             job_seeker.user = user
#             job_seeker.address = address

#             # Save the formsets for certifications and work experience
#             certifications = certification_formset.save(commit=False)
#             experiences = work_experience_formset.save(commit=False)
            
#             for cert in certifications:
#                 cert.save()
#                 job_seeker.certificates.add(cert)

#             for exp in experiences:
#                 exp.save()
#                 job_seeker.experiences.add(exp)


#             for edu_form in education_formset.forms:
#                 if edu_form.cleaned_data and not edu_form.cleaned_data.get('DELETE', False):
#                     # Save education form
#                     education_instance = edu_form.save(commit=False)
                    
#                     # Process associated school form
#                     school_address_form = SchoolAddressForm(request.POST, prefix=f'school-{edu_form.prefix}')
#                     if school_address_form.is_valid():
#                         school_instance = school_address_form.save()

#                         # Link the school to education
#                         education_instance.school_address = school_instance
#                         education_instance.save()
#                 elif edu_form.cleaned_data.get('DELETE', False) and edu_form.instance.pk:
#                     edu_form.instance.delete()

#             for cert_form in certification_formset.forms:
#                 if cert_form.cleaned_data and not cert_form.cleaned_data.get('DELETE', False):
#                     cert_form.save()
#                 elif cert_form.cleaned_data.get('DELETE', False) and cert_form.instance.pk:
#                     cert_form.instance.delete()

#             job_seeker.save()  # Save the profile instance

#             return redirect('profile')  # Redirect to the profile view page after saving

#     return render(request, 'edit_profile.html', {
#         'profile_form': profile_form,
#         'certification_formset': certification_formset,
#         'work_experience_formset': work_experience_formset,
#         'user_form': user_form,
#         'address_form': address_form,
#         'education_formset': education_formset,
#         'school_address_form' : school_address_form # Pass formset to template
#     })

def edit_profile_view(request):
    print("[DEBUG] Profile EDIT View")
    user = request.user

    try:
        job_seeker_profile = JobSeekerProfile.objects.get(user=user)
    except JobSeekerProfile.DoesNotExist:
        return redirect('pre-signup')

    CertificationFormSet = modelformset_factory(Certification, form=CertificationForm, extra=1, can_delete=True)
    WorkExperienceFormSet = modelformset_factory(Experience, form=WorkExperienceForm, extra=1, can_delete=True)
    EducationFormSet = modelformset_factory(Education, form=EducationForm, extra=1, can_delete=True)

    if request.method == 'POST':
        print("[DEBUG] Request POST " , request.POST)
        profile_form = JobSeekerProfileForm(request.POST, request.FILES, instance=job_seeker_profile)
        user_form = CustomUserFormForJobSeeker(request.POST, instance=user)
        address_form = AddressForm(request.POST, instance=job_seeker_profile.address)

        certification_formset = CertificationFormSet(
            request.POST or None,
            request.FILES or None,
            queryset=job_seeker_profile.certificates.all(),
            prefix="certification"
        )

        work_experience_formset = WorkExperienceFormSet(
            request.POST or None,
            request.FILES or None,
            queryset=job_seeker_profile.experiences.all(),
            prefix="experience"
        )

        education_formset = EducationFormSet(
            request.POST or None,
            request.FILES or None,
            queryset=job_seeker_profile.education.all(),
            prefix="education"
        )
        # certification_formset = CertificationFormSet(request.POST, request.FILES, queryset=job_seeker_profile.certifications.all() , prefix="certification")
        # work_experience_formset = WorkExperienceFormSet(request.POST, request.FILES, queryset=job_seeker_profile.experiences.all() , prefix="experience")
        # education_formset = EducationFormSet(request.POST, request.FILES, queryset=job_seeker_profile.education.all() , prefix="education")

        # Bind nested SchoolAddressForms
        # for edu_form in education_formset:
        #     edu_form.school_address_form = SchoolAddressForm(
        #         request.POST, prefix=f'sa-{edu_form.prefix}',
        #         instance=edu_form.instance.school_address if edu_form.instance.pk else None
        #     )

        # Validate all
        if all([
            profile_form.is_valid(),
            user_form.is_valid(),
            address_form.is_valid(),
            certification_formset.is_valid(),
            work_experience_formset.is_valid(),
            all(f.is_valid() and f.school_address_form.is_valid() for f in education_formset)
        ]):
            print("[DEBUG] All forms are valid ")
            user = user_form.save()
            address = address_form.save()

            job_seeker = profile_form.save(commit=False)
            job_seeker.user = user
            job_seeker.address = address

            job_seeker.certificates.clear()
            job_seeker.experiences.clear()
            job_seeker.education.clear()

            for cert_form in certification_formset:
                if cert_form.cleaned_data and not cert_form.cleaned_data.get('DELETE', False):
                    cert = cert_form.save()
                    job_seeker.certificates.add(cert)

            for exp_form in work_experience_formset:
                if exp_form.cleaned_data and not exp_form.cleaned_data.get('DELETE', False):
                    exp = exp_form.save()
                    job_seeker.experiences.add(exp)

            for edu_form in education_formset:
                if edu_form.cleaned_data and not edu_form.cleaned_data.get('DELETE', False):
                    school_address = edu_form.school_address_form.save()
                    edu = edu_form.save(commit=False)
                    edu.school_address = school_address
                    edu.save()
                    job_seeker.education.add(edu)
            if 'resume' in request.FILES:
                resume_file = request.FILES['resume']
                job_seeker.resume = resume_file  # Save the uploaded resume
            else:
                # No file uploaded, generate PDF
                resume_pdf = generate_resume_pdf(user, job_seeker)
                # Convert PDF to file-like object and save to database
                job_seeker.resume.save(
                    f"{job_seeker.user.get_full_name()}_resume.pdf",
                    ContentFile(resume_pdf.getvalue()),
                    save=True
                )

            job_seeker.save()

            return redirect('profile')
        if not profile_form.is_valid():
            print("[DEBUG] Profile Form Errors:", profile_form.errors)
        if not user_form.is_valid():
            print("[DEBUG] User Form Errors:", user_form.errors)
        if not address_form.is_valid():
            print("[DEBUG] Address Form Errors:", address_form.errors)
        if not certification_formset.is_valid():
            print("[DEBUG] Certification FormSet Errors:", certification_formset.errors)
        if not work_experience_formset.is_valid():
            print("[DEBUG] Work Experience FormSet Errors:", work_experience_formset.errors)
        if not education_formset.is_valid():
            print("[DEBUG] Education FormSet Errors:", education_formset.errors)
    else:
        profile_form = JobSeekerProfileForm(instance=job_seeker_profile)
        user_form = CustomUserFormForJobSeeker(instance=user)
        address_form = AddressForm(instance=job_seeker_profile.address)

        certification_formset = CertificationFormSet(
            request.POST or None,
            request.FILES or None,
            queryset=job_seeker_profile.certificates.all(),
            prefix="certification"
        )

        work_experience_formset = WorkExperienceFormSet(
            request.POST or None,
            request.FILES or None,
            queryset=job_seeker_profile.experiences.all(),
            prefix="experience"
        )

        education_formset = EducationFormSet(
            request.POST or None,
            request.FILES or None,
            queryset=job_seeker_profile.education.all(),
            prefix="education"
        )
        
        print("[DEBUG] Profile Form VALID: " ,profile_form.is_valid())
        print("[DEBUG] ERROR Profile Form: " ,profile_form.errors)
        print("[DEBUG] User Form VALID: " ,user_form.is_valid())
        print("[DEBUG] ERROR User Form: " ,user_form.errors)
        print("[DEBUG] Address Form VALID: " ,address_form.is_valid())
        print("[DEBUG] ERROR Address Form: " ,address_form.errors)
        print("[DEBUG] ERROR : " ,certification_formset.errors)
        print("[DEBUG] ERROR : " ,certification_formset.errors)
        print("[DEBUG] ERROR : " ,work_experience_formset.errors)
        print("[DEBUG] ERROR : " ,education_formset.errors)

    return render(request, 'edit_profile.html', {
        'profile_form': profile_form,
        'user_form': user_form,
        'address_form': address_form,
        'certification_formset': certification_formset,
        'work_experience_formset': work_experience_formset,
        'education_formset': education_formset,
    })

def settings_view(request):
    print("🔍 Request user:", request.user)
    print("🔐 Is authenticated?", request.user.is_authenticated)

    if not request.user.is_authenticated:
        messages.warning(request, "Please Log In first!.")
            
        return redirect('login')
    
    return render(request, 'settings.html')

def download_resume(request):
    try:
        job_seeker = JobSeekerProfile.objects.get(user=request.user)
        
        if not job_seeker.resume:
            raise Http404("Resume not found.")
        
        # Return the resume file for download
        return FileResponse(job_seeker.resume.open('rb'), as_attachment=True, filename='Resume.pdf')
    
    except JobSeekerProfile.DoesNotExist:
        raise Http404("Job seeker profile not found.")


def download_resume_application(request, application_id):
    # Get the application
    application = get_object_or_404(Application, id=application_id)

    # Get the company person making the request
    company_person = get_object_or_404(CompanyPerson, user=request.user)

    # Check if the job belongs to this company
    if application.job.company != company_person.company:
        raise Http404("You are not authorized to download this resume.")

    # Check if resume exists
    if not application.resume:
        raise Http404("Resume not found.")

    # Return the resume file
    return FileResponse(application.resume.open('rb'), as_attachment=True, filename=application.resume.name)

# def user_login(request):
#     user = request.user
#     storage = get_messages(request)
#     for message in storage:
#         print("Consumed Message:", message)
#     list(storage)
#     if user.is_authenticated:
#         messages.info(request, 'You are already logged in.')
#         if user.user_type == "Job Seeker":
#             job_seeker = JobSeeker.objects.get(user=user)
#             print("Job Seeker : " , job_seeker)
#             jobs = get_matching_jobs_for_user(job_seeker)
#             return redirect('home', jobs = jobs)
#         elif user.user_type == "Company":
#             return redirect('company_dashboard')
        
#     if request.method == 'POST':
#         print("🔹 Received POST request for login.")
#         form = UserLoginForm(data=request.POST)
#         print(form.data)
        
#         if form.is_valid():
#             print("✅ Form is valid.")
#             # Authenticate the user
#             # username = form.cleaned_data.get('username')
#             # password = form.cleaned_data.get('password')
#             # print(username , password)
#             # print(f"🔍 Attempting to authenticate user with email: {username}")
#             try:
#                 user = form.get_user()
#                 print(user)
#                 # user = CustomUser.objects.get(username=username)  # Fetch user by email
#                 # print(f"✅ User found: {user.username}")

#                 # user = authenticate(request, username=username, password=password)  # ✅ Authenticate properly

#                 if user is not None:
                    
#                     login(request, user)
#                     print("✅ Login successful")
#                     if user.user_type == "Job Seeker":
#                         job_seeker = JobSeekerProfile.objects.get(user=user)
#                         jobs = get_matching_jobs_for_user(job_seeker)
#                         return render(request, 'home.html', {'jobs': jobs})
#                     elif user.user_type == "Company":
#                         company = Company.objects.get(user=request.user)
#                         return redirect('company_dashboard', company_name = company.name)
                            
#             except CustomUser.DoesNotExist:
#                 print("❌ User with this email does not exist.")
#         else:
#             print("❌ Form is invalid. Errors:")
#             for field, errors in form.errors.items():
#                 for error in errors:
#                     print(f"   🔴 Field '{field}': {error}")
#             messages.error(request, 'Please correct the errors below.')
#     else:
#         form = UserLoginForm()
#     return render(request, 'login.html', {'form': form})



def user_login(request):
    user = request.user
    print("The user for login : " , user)


    if user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        if user.is_superuser:
            return redirect('admin_dashboard')
        elif user.user_type == "job_seeker":
            return redirect('home')

        elif user.user_type == "company_person":
            return redirect('company_dashboard')
        
        else:
            return redirect('pre-signup')

    if request.method == 'POST':
        print("🔹 Received POST request for login.")
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            print("✅ Form is valid.")
            user = form.get_user()
            print(f"✅ Authenticated user: {user}")
            try:
                if user is not None:
                    login(request, user)
                    print("✅ Login successful")
                    if user.is_superuser:
                        return redirect('admin_dashboard')
                    elif user.user_type == "job_seeker":
                        return redirect('home')
                    elif user.user_type == "company_person":                       
                        return redirect('company_dashboard')


            except CustomUser.DoesNotExist:
                print("❌ User with this email does not exist.")
        else:
            print("❌ Form is invalid. Errors:")
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"   🔴 Field '{field}': {error}")
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'form': form})

# @csrf_exempt
# def auth_receiver(request):
#     """
#     Google calls this URL after the user has signed in with their Google account.
#     """
#     print('Inside')
#     token = request.POST['credential']

#     try:
#         user_data = id_token.verify_oauth2_token(
#             token, requests.Request(), os.environ['GOOGLE_OAUTH_CLIENT_ID']
#         )
#     except ValueError:
#         return HttpResponse(status=403)

#     # In a real app, I'd also save any new user here to the database.
#     # You could also authenticate the user here using the details from Google (https://docs.djangoproject.com/en/4.2/topics/auth/default/#how-to-log-a-user-in)
#     request.session['user_data'] = user_data

#     return redirect('log_in')

@csrf_exempt
def auth_receiver_for_jobseeker(request):
    """
    Google calls this URL after the user has signed in with their Google account.
    """
    print('Inside auth_receiver')
    print(f"Request method: {request.method}")
    print('POST data:', request.POST)

    token = request.POST.get('credential')
    print('Token received:', bool(token))

    if not token:
        return HttpResponse("No credential token received", status=400)
    
    try:
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        if not client_id:
            return HttpResponse("Server configuration error: No client ID", status=500)

        # Verify the token using Google's library
        user_data = id_token.verify_oauth2_token(
            token, requests.Request(), os.environ['GOOGLE_OAUTH_CLIENT_ID']
        )
        print("User Data:", user_data)
        
    except ValueError:
        print("Token verification error:", str(ValueError))
        return HttpResponse("Invalid token", status=403)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
    

    # Extract email, first name, and last name from user_data
    email = user_data.get('email')
    first_name = user_data.get('given_name', '')
    last_name = user_data.get('family_name', '')
    user_type = "Job Seeker"

    if not email:
        return HttpResponse("No email found in token", status=400)

    # Check if the user exists in Django's User model
    user = CustomUser.objects.filter(email=email).first()

    if not user:
        try:
            # User doesn't exist — create a new one
            user = CustomUser.objects.create_user(
                username=email,  # Using email as username (unique)
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=None,  # No password since it's Google login
                user_type = user_type
            )
            print(f"New user created: {user}")
        except Exception as e:
            return HttpResponse(f"Error creating user: {str(e)}", status=500)
    try:
        # Explicitly set the authentication backend
        backend = get_backends()[0]  # Choose the first backend
        user.backend = f'{backend.__module__}.{backend.__class__.__name__}'

        # Log the user in with the specified backend
        login(request, user, backend=user.backend)

        return redirect('home')  # Redirect to home page after login
    except Exception as e:
        import traceback
        print(f"Error during user creation or login: {str(e)}")
        print(traceback.format_exc())  # Print the full traceback
        return HttpResponse(f"Error during login process: {str(e)}", status=500)


def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect('index')



# Company Views
def register_company_step1(request):
    """Step 1: Register User (Only Email & Password) and Redirect to Company Registration"""

    if request.method == "POST":
        user_form = UserRegistrationFormForCompany(request.POST)
        
        if user_form.is_valid():
            user = CustomUser(
                username = user_form.cleaned_data['email'],
                email=user_form.cleaned_data['email'],
                user_type = "Company",
                is_active=False
            )
            user.set_password(user_form.cleaned_data['password1'])
            user.save()
            
            request.session["user_id"] = user.id  # Store user ID for next step
            
            return redirect("company_register_2")  # Redirect to company registration
    else:
        user_form = UserRegistrationFormForCompany()

    return render(request, "company/company_register_step1.html", {"user_form": user_form})

def register_company_step2(request):
    """Step 2: Register Company and Link to the User"""

    user_id = request.session.get("user_id")  # Retrieve user ID from session
    if not user_id:
        return redirect("register_user_step1")  # Redirect back if no user ID found

    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        company_form = CompanyFormStep1(request.POST, request.FILES)

        if company_form.is_valid():
            company = company_form.save(commit=False)
            company.user = user  # Assign company to user
            company.save()

            return redirect("company_register_3", company_id=company.id)  # Redirect to phone verification
    else:
        company_form = CompanyFormStep1()

    return render(request, "company/company_register_step2.html", {"company_form": company_form})

def register_company_step3(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    company_form = CompanyFormStep2(instance=company)
    location_form = LocationForm()

    if request.method == "POST":
        if "add_location" in request.POST:
            location_form = LocationForm(request.POST)
            if location_form.is_valid():
                location = location_form.save(commit=False)
                location.company = company  # Assign company to location
                location.save()
                return redirect("company_register_3", company_id=company.id)

        elif "remove_location" in request.POST:
            location_id = request.POST.get("location_id")
            location = get_object_or_404(Location, id=location_id)
            location.delete()  # Delete location
            return redirect("company_register_3", company_id=company.id)

        else:
            company_form = CompanyFormStep2(request.POST, instance=company)
            if company_form.is_valid():
                company_form.save()
                request.session["user_id"] = company.user.id
                print("Session data before redirect:", request.session.items())
                return redirect("phone_verification_for_company")

    return render(request, "company/company_register_step3.html", {
        "company_form": company_form,
        "location_form": location_form,
        "company": company,
    })

def phone_verification_for_company(request):
    user_id = request.session.get("user_id")
    company = get_object_or_404(Company, user_id=user_id)
    print("Company : " , company)
    if not user_id:
        return redirect('company_register_1')
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return redirect('company_register_1')
    
    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)
        form.request = request

        if 'send_otp' in request.POST: 
            if form.is_valid():
                cache_key = f'otp_attempts_{user_id}'
                attempts = cache.get(cache_key, 0)
                
                if attempts >= 3:
                    form.add_error(None, 'Too many attempts. Please try again later.')
                    return render(request, 'phone_verification.html', {'form': form})
            
                full_phone = form.cleaned_data['full_phone']
                
                # Generate and save OTP
                otp = str(random.randint(100000, 999999))
                PhoneVerification.objects.filter(user=user).delete()
                PhoneVerification.objects.create(
                    user=user, 
                    phone_number=full_phone,
                    otp=otp
                )
                
                # Send OTP using django-sms (development)
                try:
                    send_sms(
                        f'Your verification code is: {otp}',
                        None,  # Fake number for development
                        [full_phone],
                        fail_silently=False
                    )
                    
                    # In development, print to console and continue
                    print(f"DEV: OTP for {full_phone} is {otp}")
                    
                    request.session['verification_phone'] = full_phone
                    return render(request, 'phone_verification.html', {
                        'form': form,
                        'otp_sent': True,
                        'phone_number': full_phone
                    })
                except Exception as e:
                    print(f"Failed to send OTP: {str(e)}")
                    form.add_error(None, 'Failed to send OTP. Please try again.')
        
        elif 'verify_otp' in request.POST:
            full_phone = request.session.get('verification_phone')
            if not full_phone:
                form.add_error(None, 'Phone number not found. Please request a new OTP.')
                return render(request, 'phone_verification.html', {'form': form})
            
            otp = request.POST.get('otp')
            if not otp:
                form.add_error('otp', 'OTP is required')
                return render(request, 'phone_verification.html', {
                    'form': form,
                    'otp_sent': True,
                    'phone_number': full_phone
                })
            
            try:
                verification = PhoneVerification.objects.get(
                    user=user,
                    otp=otp,
                    is_verified=False
                )
                
                # Mark as verified
                verification.is_verified = True
                verification.save()
                
                # Update user
                user.phone_number = full_phone
                user.is_phone_verified = True
                user.is_active = True
                user.save()
                

                # ✅ Clear old OTP session and cache
                if 'verification_phone' in request.session:
                    del request.session['verification_phone']
                cache.delete(f'otp_attempts_{user_id}')
                
                # Log the user in after successful phone verification
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                logger.info(f"Logging in user: {user.username} with backend: {user.backend}")
                
                request.session.flush()
                login(request, user)

                # Save session and clear OTP-related data
                request.session.save()

                # Log session info
                logger.info(f"User authenticated: {request.user.is_authenticated}")
                logger.info(f"Session Key: {request.session.session_key}")
                logger.info(f"Session Data: {dict(request.session.items())}")
                
                return redirect('company_dashboard', company_name = company.name)
                
                
            except PhoneVerification.DoesNotExist:
                form.add_error('otp', 'Invalid OTP code')
                logger.error(f"Invalid OTP attempt for user: {user.username}")
                return render(request, 'phone_verification.html', {
                    'form': form,
                    'otp_sent': True,
                    'phone_number': full_phone
                })
    
        elif 'resend_otp' in request.POST:
            full_phone = request.session.get('verification_phone')
            if form.is_valid() and full_phone:
                cache_key = f'otp_attempts_{user_id}'
                attempts = cache.get(cache_key, 0)
                
                if attempts >= 3:
                    form.add_error(None, 'Too many attempts. Please try again later.')
                    return render(request, 'phone_verification.html', {
                        'form': form,
                        'otp_sent': True,
                        'phone_number': full_phone
                    })
                
                # Generate new OTP
                otp = str(random.randint(100000, 999999))
                PhoneVerification.objects.filter(user=user).delete()
                PhoneVerification.objects.create(
                    user=user, 
                    phone_number=full_phone,
                    otp=otp
                )
                
                cache.set(cache_key, attempts + 1, timeout=300)

                # Resend OTP (development)
                try:
                    send_sms(
                        f'Your new verification code is: {otp}',
                        None,
                        [full_phone],
                        fail_silently=False
                    )
                    print(f"DEV: Resent OTP for {full_phone} is {otp}")
                    
                    return render(request, 'phone_verification.html', {
                        'form': form,
                        'otp_sent': True,
                        'phone_number': full_phone,
                        'resend_success': True
                    })
                except Exception as e:
                    form.add_error(None, 'Failed to resend OTP. Please try again.')
    
    else:
        form = PhoneVerificationForm()
    
    return render(request, 'phone_verification.html', {'form': form})



def company_dashboard(request):
    user = request.user
    print("User : " , user)
    if user.is_authenticated and user.user_type == "company_person":
        try:
            company_person = CompanyPerson.objects.get(user=user)
            company = company_person.company
            company_person_full_name = company_person.user.get_full_name()

            if company_person.is_admin:
                return redirect('company_admin_dashboard' , company.name , company_person_full_name)
            else:
                return redirect('company_person_dashboard' , company.name , company_person_full_name)

        except CompanyPerson.DoesNotExist:
            return redirect('pre-signup') 
    else:
        return redirect('login')

def company_admin_dashboard(request, company_name, company_person_name):
    user = request.user
    print("User: ", user)

    if not user.is_authenticated or user.user_type != "company_person":
        return redirect('login')

    try:
        # Match the company and person
        company = Company.objects.get(name=company_name)
        company_person = CompanyPerson.objects.get(user=user, company=company)
        company_person_full_name = company_person.user.get_full_name()
        if company_person.user.get_full_name() != company_person_name:
            return redirect('login')
        
        if not company_person.is_admin:
            return redirect('company_dashboard')  # non-admin redirect

        is_external = False
        profile_picture = request.user.profile_picture
        profile_picture_url = str(profile_picture) if profile_picture else ""
        if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
            print(profile_picture_url)
            is_external = True
        else:
            is_external = False
        # Get the latest 4 jobs posted by this company
        jobs = Job.objects.filter(company=company)
        job_count = jobs.count()
        recent_jobs = Job.objects.filter(company=company).order_by('-created_at')[:4]
       
        print("Recent Jobs: ", recent_jobs)

        return render(request, 'company/admin_dashboard.html', {
            'is_external' : is_external,
            'job_count' : job_count,
            'company': company,
            'company_person': company_person,
            'recent_jobs': recent_jobs,
            'company_person_full_name' : company_person_full_name,
        })

    except (Company.DoesNotExist, CompanyPerson.DoesNotExist):
        return redirect('employer-register')

def company_person_dashboard(request, company_name, company_person_name):
    user = request.user
    print("User: ", user)

    if not user.is_authenticated or user.user_type != "company_person":
        return redirect('login')

    try:
        # Match the company and person
        company = Company.objects.get(name=company_name)
        company_person = CompanyPerson.objects.get(user=user, company=company)
        company_person_full_name = company_person.user.get_full_name()
        if company_person.user.get_full_name() != company_person_name:
            return redirect('login')
        
        if company_person.is_admin:
            return redirect('company_dashboard')  # non-admin redirect

        is_external = False
        profile_picture = request.user.profile_picture
        profile_picture_url = str(profile_picture) if profile_picture else ""
        if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
            print(profile_picture_url)
            is_external = True
        else:
            is_external = False
        # Get the latest 4 jobs posted by this company
        jobs = Job.objects.filter(company=company)
        job_count = jobs.count()
        recent_jobs = Job.objects.filter(company=company).order_by('-created_at')[:4]
       
        print("Recent Jobs: ", recent_jobs)

        return render(request, 'company/person_dashboard.html', {
            'is_external' : is_external,
            'job_count' : job_count,
            'company': company,
            'company_person': company_person,
            'recent_jobs': recent_jobs,
            'company_person_full_name' : company_person_full_name,
        })

    except (Company.DoesNotExist, CompanyPerson.DoesNotExist):
        return redirect('employer-register')



def company_profile_view(request, company_name):
    user = request.user
    print("User : " , user)
    if user.is_authenticated and user.user_type == "company_person":
        try:
            # Match the company and person
            company = Company.objects.get(name=company_name)
            company_person = CompanyPerson.objects.get(user=user, company=company)
            company_person_full_name = company_person.user.get_full_name()

            if not company_person.is_admin:
                return redirect('company_person_dashboard')  # non-admin redirect
            is_external = False
            profile_picture = company.user.profile_picture
            profile_picture_url = str(profile_picture) if profile_picture else ""
            if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
                print(profile_picture_url)
                is_external = True
            else:
                is_external = False
            return render(request, 'company/company_profile.html', {'company': company , 'company_person' : company_person , 'company_person_full_name' : company_person_full_name , 'is_external' : is_external})
        except Company.DoesNotExist:
            return redirect('pre-signup')  # If no company, force registration
    else:
        return redirect('login')


# def company_person_profile_view(request, company_name, company_person_name):
#     user = request.user

#     if user.is_authenticated and user.user_type == "company_person":
#         try:
#             company = Company.objects.get(name=company_name)
#             company_person = CompanyPerson.objects.get(user=user, company=company)
#             company_person_full_name = company_person.user.get_full_name()

#             # Ensure name in URL matches the logged-in person
#             if company_person_full_name != company_person_name:
#                 return redirect('login')

#             # Use the provided profile picture logic
#             is_external = False
#             profile_picture = company_person.user.profile_picture
#             profile_picture_url = str(profile_picture) if profile_picture else ""
#             if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
#                 print(profile_picture_url)
#                 is_external = True
#             else:
#                 is_external = False

#             return render(
#                 request,
#                 'company/company_person_profile.html',
#                 {
#                     'company': company,
#                     'company_person': company_person,
#                     'company_person_full_name': company_person_full_name,
#                     'is_external': is_external
#                 }
#             )
#         except Company.DoesNotExist:
#             return redirect('pre-signup')
#         except CompanyPerson.DoesNotExist:
#             return redirect('login')
#     else:
#         return redirect('login')

def company_person_profile_view(request, company_name, company_person_name):
    user = request.user

    if user.is_authenticated and user.user_type == "company_person":
        try:
            company = Company.objects.get(name=company_name)
            company_person = CompanyPerson.objects.get(user=user, company=company)
            company_person_full_name = company_person.user.get_full_name()

            if company_person_full_name != company_person_name:
                return redirect('login')

            # Profile picture handling
            profile_picture = company_person.user.profile_picture
            profile_picture_url = str(profile_picture) if profile_picture else ""
            is_external = profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')

            # ✅ Choose template based on admin status
            template_name = 'company/company_admin_profile.html' if company_person.is_admin else 'company/company_person_profile.html'

            return render(
                request,
                template_name,
                {
                    'company': company,
                    'company_person': company_person,
                    'company_person_full_name': company_person_full_name,
                    'is_external': is_external
                }
            )
        except Company.DoesNotExist:
            return redirect('pre-signup')
        except CompanyPerson.DoesNotExist:
            return redirect('login')
    else:
        return redirect('login')
    
def company_edit_view(request, company_name):
    user = request.user

    # Check if the user is authenticated and of type 'company_person'
    if not user.is_authenticated or user.user_type != "company_person":
        return redirect('company_register_1')

    # Get the company and company person details
    company_person = CompanyPerson.objects.get(user=user)
    company = Company.objects.get(name=company_name)
    company_person_full_name = user.get_full_name()
    company_user = company.user
    company_headquarters_address = company.headquarters_address
    company_locations = company.company_locations.all()
    

    

    print("The Company Locations : " , company_locations)
    if request.method == "POST":
        company_form = CompanyEditForm(request.POST, request.FILES, instance=company)
        user_form = CustomUserFormForCompany(request.POST, request.FILES, instance=company_user)
        headquarters_form = HeadQuartersAddressForm(request.POST , instance=company_headquarters_address)
        location_form = LocationFormSet(request.POST, queryset=company_locations)

        print("Location Formset Errors before validation:", location_form.errors)
        if company_form.is_valid() and user_form.is_valid() and headquarters_form.is_valid() and location_form.is_valid():
            # Handle dynamic locations here, check for empty data before adding
            # Handle dynamic locations here
            # if 'locations' in request.POST:
            #     locations_data = defaultdict(dict)
            #     for key, value in request.POST.items():
            #         if key.startswith("locations-"):
            #             parts = key.split("-")
            #             if len(parts) == 3:
            #                 index, field = parts[1], parts[2]
            #                 locations_data[index][field] = value

            #     # Clear old locations
            #     if locations_data:
            #         company.company_locations.clear()
            #         for loc in locations_data.values():
            #             if any(loc.values()):  # Skip empty inputs
            #                 location = Location.objects.create(
            #                     address=loc.get("address", ""),
            #                     city=loc.get("city", ""),
            #                     state=loc.get("state", ""),
            #                     country=loc.get("country", "")
            #                 )
            #                 company.company_locations.add(location)
            # Save locations

            for form in location_form:
                if form.cleaned_data.get('DELETE'):  # Check if the form has a DELETE flag
                    loc_to_delete = form.instance
                    if loc_to_delete.id:  # Only delete if the object has a valid ID
                        loc_to_delete.delete()  # Delete the corresponding location instance
                        print(f"[DEBUG] Location with ID {loc_to_delete.id} Deleted")
                    else:
                        # Log that we are attempting to delete an unsaved location (if needed)
                        print(f"[DEBUG] Attempted to delete an unsaved location without an ID")
            instances = location_form.save(commit=False)
            for loc in instances:
                # If the location form is new and doesn't have an ID, set the ID to None (for new records)
                if not loc.pk:  # If no ID (new form)
                    print("[DEBUG] PK not found")
                    loc.pk = None
                loc.save()
                company.company_locations.add(loc)
                print(f"[DEBUG] Location Saved with ID {loc.id}")
                
            headquarters = headquarters_form.save()
            # locations = location_form.save()
            user_form.save()
            company_form.save()
            # company.company_locations.set(locations)
            company.headquarters_address = headquarters
            company.save()
            messages.success(request, "✅ Company Profile updated successfully!")
            return redirect('company_admin_dashboard', company_name=company.name, company_person_name=company_person_full_name)

        else:
            print("Invalid form submission")
            print("Company form Valid:", company_form.is_valid())
            print("Company form errors:", company_form.errors)
            print("User form Valis:", user_form.is_valid())
            print("User form errors:", user_form.errors)
            print("HQ form Valid:", headquarters_form.is_valid())
            print("HQ form errors:", headquarters_form.errors)
            print("Location Formset Valid:", location_form.is_valid())
            print("Location formset errors:", location_form.errors)
            print("POST Data for Location Formset:", request.POST)
            
            errors = {
                'company_form_errors': company_form.errors,
                'user_form_errors': user_form.errors,
                'headquarters_form_errors': headquarters_form.errors,
                'location_form_errors': location_form.errors,
            }
            context = {**errors, 
                        'company_form': company_form,
                        'user_form': user_form,
                        'headquarters_form': headquarters_form,
                        'location_form': location_form,
                        'company': company,
                        'company_person': company_person,
                        'company_person_full_name': company_person_full_name,
                        'company_locations': company_locations}
            return render(request, 'company/edit_company.html', context)

    else:
        # Initialize the forms with existing data
        company_form = CompanyEditForm(instance=company)
        user_form = CustomUserFormForCompany(instance=company_user)
        headquarters_form = HeadQuartersAddressForm(instance=company_headquarters_address)
        location_form = LocationFormSet(queryset=company_locations)


        # Pass both forms and other context to the template
        context = {
            'company_form': company_form,
            'user_form': user_form,
            'headquarters_form': headquarters_form,
            'location_form': location_form,
            'company': company,
            'company_person': company_person,
            'company_person_full_name': company_person_full_name,
            'company_locations' : company_locations,
        }
        return render(request, 'company/edit_company.html', context)

logger = logging.getLogger(__name__)

# def company_person_edit_view(request, company_name, company_person_name):
#     user = request.user

#     if not user.is_authenticated or user.user_type != "company_person":
#         return redirect("login")

#     try:
#         company = Company.objects.get(name=company_name)
#         company_person = CompanyPerson.objects.get(user=user, company=company)

#         if user.get_full_name() != company_person_name:
#             return redirect("login")

#         otp_form = PhoneVerificationForm(request.POST or None, request=request)
#         user_form = CustomUserFormForCompanyPerson(request.POST or None, request.FILES or None, instance=user)
#         company_person_form = CompanyPersonEditForm(request.POST or None, instance=company_person)

#         phone_changed = False
#         current_phone = company_person.user.phone_number  # adjust based on your model field

#         if request.method == "POST":

#             # OTP Sending Flow
#             if "send_otp" in request.POST and otp_form.is_valid():
#                 full_phone = otp_form.cleaned_data['full_phone']
#                 if full_phone != current_phone:
#                     otp = str(random.randint(100000, 999999))
#                     cache.set(full_phone, otp, timeout=300)
#                     cache.set(f'otp_attempts_{user.id}', 1, timeout=300)

#                     try:
#                         send_sms(f"Your verification code is: {otp}", None, [full_phone], fail_silently=False)
#                         request.session['pending_phone'] = full_phone
#                         request.session['otp_verified'] = False
#                         if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                             return JsonResponse({'status': 'success', 'message': f'OTP sent to {full_phone}'})
#                     except Exception:
#                         if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                             return JsonResponse({'status': 'error', 'message': 'Failed to send OTP. Try again.'})
#                 else:
#                     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                         return JsonResponse({'status': 'error', 'message': 'Phone number has not changed.'})


#                 return render(request, 'company/edit_company_person.html', {
#                     "user_form": user_form,
#                     "company_person_form": company_person_form,
#                     "otp_form": otp_form,
#                     "company": company,
#                     "otp_modal_open": True,
#                     "company_person": company_person,
#                     "company_person_full_name": company_person_name,
#                     "otp_sent": True,
#                     "phone_number": full_phone,
#                     "resend_success" : False
#                 })

#             # OTP Resend Flow
#             elif "resend_otp" in request.POST:
#                 full_phone = request.session.get('pending_phone')
#                 attempts = cache.get(f'otp_attempts_{user.id}', 0)

#                 if full_phone and attempts < 3:
#                     otp = str(random.randint(100000, 999999))
#                     cache.set(full_phone, otp, timeout=300)
#                     cache.set(f'otp_attempts_{user.id}', attempts + 1, timeout=300)

#                     try:
#                         send_sms(f"Your new OTP is: {otp}", None, [full_phone], fail_silently=False)
#                         if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                             return JsonResponse({'status': 'success', 'message': f'OTP resent to {full_phone}'})
#                     except Exception:
#                         if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                             return JsonResponse({'status': 'error', 'message': 'Failed to resend OTP.'})
#                 else:
#                     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                         return JsonResponse({'status': 'error', 'message': 'Too many attempts or missing phone number.'})

#                 return render(request, 'company/edit_company_person.html', {
#                     "user_form": user_form,
#                     "company_person_form": company_person_form,
#                     "otp_form": otp_form,
#                     "company": company,
#                     "otp_modal_open": True,
#                     "company_person": company_person,
#                     "company_person_full_name": company_person_name,
#                     "otp_sent": True,
#                     "phone_number": full_phone,
#                     "resend_success" : True
#                 })

#             # OTP Verification Flow
#             elif "verify_otp" in request.POST:
#                 full_phone = request.session.get("pending_phone")
#                 entered_otp = ''.join([request.POST.get(f"otp_{i}", '') for i in '123456']).strip()
#                 real_otp = cache.get(full_phone)

#                 if entered_otp == real_otp:
#                     request.session["otp_verified"] = True
#                     messages.success(request, "OTP verified successfully.")
#                 else:
#                     request.session["otp_verified"] = False
#                     messages.error(request, "Invalid OTP.")

#                 return render(request, 'company/edit_company_person.html', {
#                     "user_form": user_form,
#                     "company_person_form": company_person_form,
#                     "otp_form": otp_form,
#                     "company": company,
#                     "otp_modal_open": True,
#                     "company_person": company_person,
#                     "company_person_full_name": company_person_name,
#                     "otp_sent": True,
#                     "phone_number": full_phone,
#                     "resend_success" : False
#                 })

#             # Form Submit Flow
#             else:
#                 if user_form.is_valid() and company_person_form.is_valid():
#                     new_phone = user_form.cleaned_data.get("phone_number")
#                     phone_changed = new_phone != current_phone

#                     # If phone changed, OTP must be verified
#                     if phone_changed and not request.session.get("otp_verified"):
#                         messages.error(request, "Please verify your new phone number before saving.")
#                         return render(request, 'company/edit_company_person.html', {
#                             "user_form": user_form,
#                             "company_person_form": company_person_form,
#                             "otp_form": otp_form,
#                             "company": company,
#                             "company_person": company_person,
#                             "company_person_full_name": company_person_name,
#                             "otp_required": True,
#                             "otp_modal_open": True,
#                         })

#                     # Save changes
#                     user_form.save()
#                     company_person_form.save()
#                     messages.success(request, "Profile updated successfully.")

#                     # Clean up OTP session state
#                     request.session.pop("otp_verified", None)
#                     request.session.pop("pending_phone", None)

#                     return redirect("company_admin_dashboard", company_name=company.name, company_person_name=user.get_full_name())

#         # GET or fallback render
#         return render(request, 'company/edit_company_person.html', {
#             "user_form": user_form,
#             "company_person_form": company_person_form,
#             "otp_form": otp_form,
#             "company": company,
#             "company_person": company_person,
#             "company_person_full_name": company_person_name,
#         })

#     except (Company.DoesNotExist, CompanyPerson.DoesNotExist):
#         return redirect("login")

from django.http import JsonResponse
from django.shortcuts import render

# def generate_otp():
#     return str(random.randint(100000, 999999))

# @csrf_exempt
# def send_otp_view(request):
#     if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
#         try:
#             data = json.loads(request.body)
#             full_phone = data.get("full_phone")
#             if not full_phone:
#                 return JsonResponse({"status": "error", "message": "Phone number missing"}, status=400)

#             otp = generate_otp()
#             cache.set(f"otp_{full_phone}", otp, timeout=300)
#             request.session["pending_phone"] = full_phone
#             request.session.modified = True  # Important!

#             print(f"[DEBUG] Sent OTP {otp} to {full_phone}")  # Replace with actual SMS logic

#             return JsonResponse({"status": "success", "message": "OTP sent successfully!"})
#         except json.JSONDecodeError:
#             return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

#     return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


# @csrf_exempt
# def verify_otp_view(request):
#     if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
#         try:
#             data = json.loads(request.body)
#             full_phone = data.get("full_phone")
#             entered_otp = data.get("otp")
#             real_otp = cache.get(f"otp_{full_phone}")

#             if real_otp == entered_otp:
#                 request.session["verified_phone"] = full_phone
#                 request.session.modified = True
#                 return JsonResponse({"status": "success", "message": "Phone verified!"})
#             return JsonResponse({"status": "error", "message": "Invalid OTP"}, status=400)
#         except json.JSONDecodeError:
#             return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

#     return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


# def company_person_edit_view(request, company_name, company_person_name):
#     user = request.user

#     if not user.is_authenticated or user.user_type != "company_person":
#         return redirect("login")

#     try:
#         company = Company.objects.get(name=company_name)
#         company_person = CompanyPerson.objects.get(user=user, company=company)
#         company_person_full_name = company_person.user.get_full_name()

#         if company_person_full_name != company_person_name:
#             return redirect("login")


#         if request.method == "POST":
#             user_form = CustomUserFormForCompanyPerson(request.POST or None, request.FILES or None, instance=user)
#             company_person_form = CompanyPersonEditForm(request.POST or None, instance=company_person)
            
#             if user_form.is_valid() and company_person_form.is_valid():
#                 user_form.save()
#                 company_person.user = user
#                 company_person_form.save()

#                 messages.success(request, "✅ Company and user profile updated successfully!")
#                 return redirect('company_admin_dashboard', company_name=company.name, company_person_name=company_person_full_name)

#             else:
#                 print("Invalid form submission")
#                 print("Company Person form Valid:", company_person_form.is_valid())
#                 print("Company Person form errors:", company_person_form.errors)
#                 print("User form Valis:", user_form.is_valid())
#                 print("User form errors:", user_form.errors)
                
#                 errors = {
#                     'company_person_form_errors': company_person_form.errors,
#                     'user_form_errors': user_form.errors,
#                 }
#                 context = {**errors, 
#                             'company_person_form': company_person_form,
#                             'user_form': user_form,
#                             'company': company,
#                             'company_person': company_person,
#                             'company_person_full_name': company_person_full_name}
#                 return render(request, 'company/edit_company_person.html', context)
#         else:
#             # Initialize the forms with existing data
#             company_person_form = CompanyEditForm(instance=company_person)
#             user_form = CustomUserFormForCompany(instance=company_person)


#             # Pass both forms and other context to the template
#             context = {
#                 'company_person_form': company_person_form,
#                 'user_form': user_form,
#                 'company': company,
#                 'company_person': company_person,
#                 'company_person_full_name': company_person_full_name,
#             }
#             return render(request, 'company/edit_company_person.html', context)
#     except (Company.DoesNotExist, CompanyPerson.DoesNotExist):
#         return redirect("login")

# def company_person_edit_view(request, company_name , company_person_name):
#     user = request.user

#     if not user.is_authenticated or user.user_type != "company_person":
#         return redirect("login")

    
#     company = Company.objects.get(name=company_name)
#     company_person = CompanyPerson.objects.get(user=user, company=company)
#     company_person_full_name = company_person.user.get_full_name()

#     if company_person_full_name != company_person_name:
#         return redirect("login")

#     is_external = False
#     profile_picture = company.user.profile_picture
#     profile_picture_url = str(profile_picture) if profile_picture else ""
#     if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
#         print(profile_picture_url)
#         is_external = True
#     else:
#         is_external = False
#     user_form = CustomUserFormForCompanyPerson(request.POST or None, request.FILES or None, instance=user)
#     company_person_form = CompanyPersonEditForm(request.POST or None, instance=company_person)

#     # Check if the form is a POST request
#     if request.method == 'POST':

#         # If all forms are valid, save the data and redirect
#         if user_form.is_valid() and company_person_form.is_valid():

#             user_form.save()
#             company_person.user = user
#             company_person_form.save()
#             messages.success(request, "Profile updated successfully.")
#             return redirect('company_dashboard')
#         else:
#             errors = {
#                 'company_person_form_errors': company_person_form.errors,
#                 'user_form_errors': user_form.errors
#             }
#             context = {**errors, 
#                     'company_person_form': company_person_form,
#                     'user_form': user_form,
#                     'company': company,
#                     'company_person': company_person,
#                     'company_person_full_name': company_person_full_name,
#                     'is_external' : is_external
#                 }
#             print("Form is not valid")
#             print(errors)
#             return render(request, 'company/edit_company_person.html', context)

#     else:
#         # Initialize the forms with existing data
#         user_form = CustomUserFormForCompanyPerson(instance=user)
#         company_person_form = CompanyPersonEditForm(instance=company_person)


#     # Render the page with forms
#     return render(request, 'company/edit_company_person.html', {
#         'user_form': user_form,
#         'company_person_form': company_person_form,
#         'company_person_full_name' : company_person_full_name,
#         'company' : company,
#         'company_person' : company_person,
#         'is_external' : is_external
#     })


def company_person_edit_view(request, company_name, company_person_name):
    user = request.user

    if not user.is_authenticated or user.user_type != "company_person":
        return redirect("login")

    company = Company.objects.get(name=company_name)
    company_person = CompanyPerson.objects.get(user=user, company=company)
    company_person_full_name = company_person.user.get_full_name()

    if company_person_full_name != company_person_name:
        return redirect("login")

    is_external = False
    profile_picture = company.user.profile_picture
    profile_picture_url = str(profile_picture) if profile_picture else ""
    if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
        is_external = True

    user_form = CustomUserFormForCompanyPerson(request.POST or None, request.FILES or None, instance=user)
    company_person_form = CompanyPersonEditForm(request.POST or None, instance=company_person)

    template_name = 'company/edit_company_admin.html' if company_person.is_admin else 'company/edit_company_person.html'

    if request.method == 'POST':
        if user_form.is_valid() and company_person_form.is_valid():
            user_form.save()
            company_person.user = user
            company_person_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('company_dashboard')
        else:
            errors = {
                'company_person_form_errors': company_person_form.errors,
                'user_form_errors': user_form.errors
            }
            context = {
                **errors,
                'company_person_form': company_person_form,
                'user_form': user_form,
                'company': company,
                'company_person': company_person,
                'company_person_full_name': company_person_full_name,
                'is_external': is_external
            }
            return render(request, template_name, context)
    else:
        user_form = CustomUserFormForCompanyPerson(instance=user)
        company_person_form = CompanyPersonEditForm(instance=company_person)

    return render(request, template_name, {
        'user_form': user_form,
        'company_person_form': company_person_form,
        'company_person_full_name': company_person_full_name,
        'company': company,
        'company_person': company_person,
        'is_external': is_external
    })


# def company_person_edit_view(request, company_name, company_person_name):
#     user = request.user

#     if not user.is_authenticated or user.user_type != "company_person":
#         return redirect("login")

#     company = Company.objects.get(name=company_name)
#     company_person = CompanyPerson.objects.get(user=user, company=company)
#     company_person_full_name = company_person.user.get_full_name()

#     if company_person_full_name != company_person_name:
#         return redirect("login")

#     is_external = False
#     profile_picture = company.user.profile_picture
#     profile_picture_url = str(profile_picture) if profile_picture else ""
#     if profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://'):
#         is_external = True

#     user_form = CustomUserFormForCompanyPerson(request.POST or None, request.FILES or None, instance=user)
#     company_person_form = CompanyPersonEditForm(request.POST or None, instance=company_person)

#     if request.method == 'POST':
#         if user_form.is_valid() and company_person_form.is_valid():
#             user_form.save()
#             company_person.user = user
#             company_person_form.save()
#             messages.success(request, "Profile updated successfully.")
#             return redirect('company_dashboard')
#         else:
#             errors = {
#                 'company_person_form_errors': company_person_form.errors,
#                 'user_form_errors': user_form.errors
#             }
#             context = {
#                 **errors,
#                 'company_person_form': company_person_form,
#                 'user_form': user_form,
#                 'company': company,
#                 'company_person': company_person,
#                 'company_person_full_name': company_person_full_name,
#                 'is_external': is_external
#             }
#             print("Form is not valid")
#             print(errors)
#             template = 'company/edit_company_admin.html' if company_person.is_admin else 'company/edit_company_person.html'
#             return render(request, template, context)
#     else:
#         user_form = CustomUserFormForCompanyPerson(instance=user)
#         company_person_form = CompanyPersonEditForm(instance=company_person)

#     context = {
#         'user_form': user_form,
#         'company_person_form': company_person_form,
#         'company_person_full_name': company_person_full_name,
#         'company': company,
#         'company_person': company_person,
#         'is_external': is_external
#     }

#     template = 'company/edit_company_admin.html' if company_person.is_admin else 'company/edit_company_person.html'
#     return render(request, template, context)


# def add_job_view(request, company_name):
#     user = request.user

#     if user.is_authenticated and user.user_type == "Company":
#         try:
#             company = Company.objects.get(user=request.user, name=company_name)
#             if request.method == 'POST':
#                 form = JobForm(request.POST)
#                 if form.is_valid():
#                     job = form.save(commit=False)
#                     job.company = company
#                     job.save()
#                     form.save_m2m()  # for skill_requirements
#                     return redirect('company_dashboard', company_name=company.name)
#             else:
#                 form = JobForm()
#                 return render(request, 'company/add_job.html', {'form': form, 'company': company})
#         except Company.DoesNotExist:
#             return redirect('company_register_1')
#     else:
#         return redirect('login')


# @login_required(login_url='login')
# def add_job_view(request, company_name, company_person_name):
#     user = request.user
#     print(f"[DEBUG] Logged in user: {user}")

#     # Ensure only company users can access
#     if user.user_type != "company_person":
#         print("[ERROR] User is not a company_person")
#         return redirect('login')

#     # Get the company
#     company = get_object_or_404(Company, name=company_name)
#     print(f"[DEBUG] Found company: {company.name}")

#     try:
#         company_person = CompanyPerson.objects.get(user=user, company=company)
#         company_person_full_name = company_person.user.get_full_name()
#         print(f"[DEBUG] Company person full name: {company_person_full_name}")
#     except CompanyPerson.DoesNotExist:
#         print("[ERROR] CompanyPerson not found for user")
#         return redirect("login")

#     if company_person_full_name != company_person_name:
#         print("[ERROR] Name mismatch")
#         return redirect("login")

#     if request.method == 'POST':
#         job_form = JobForm(request.POST)
#         print(f"[DEBUG] Received POST data: {request.POST}")

#         if job_form.is_valid():
#             print("[SUCCESS] Job form is valid")
#             job = job_form.save(commit=False)
#             job.company = company
#             job.posted_by = company_person
#             job.save()
#             job_form.save_m2m()
#             print(f"[DEBUG] Job saved: {job.title} - ID: {job.id}")

#             # Calculate payment amount
#             try:
#                 salary = float(job.salary)
#                 inr_amount = round(salary / 10, 2)
#                 print(f"[DEBUG] Calculated payment amount: {inr_amount}")
#                 if inr_amount < 100000:
#                     # Convert to USD if less than 1,00,000 INR
#                     payment_amount = inr_amount 
#                     print(f"[DEBUG] Converted to USD: {payment_amount}")
#                 else:
#                     inr_amount = 5000.00
#                     # Use INR if more than or equal to 1,00,000 INR
#                     payment_amount = inr_amount 
#                     print(f"[DEBUG] Using INR amount: {payment_amount}")

#             except (TypeError, ValueError):
#                 print("[WARNING] Invalid salary, setting default payment amount")
#                 inr_amount = 1000.00
#                 payment_amount = inr_amount 
#             # Configure PayPal before creating payment
#             configure_paypal()

#             # Create PayPal payment
#             payment = paypalrestsdk.Payment({
#                 "intent": "sale",
                
#                 "payer": {
#                     "payment_method": "paypal"
#                 },
#                 "redirect_urls": {
#                     "return_url": request.build_absolute_uri('/payment/success/'),
#                     "cancel_url": request.build_absolute_uri('/payment/cancel/')
#                 },
#                 "transactions": [{
#                     "item_list": {
#                         "items": [{
#                             "name": f"Job Posting: {job.title}",
#                             "sku": f"job-{job.id}",
#                             "price": f"{payment_amount:.2f}",
#                             "currency": "USD",
#                             "quantity": 1
#                         }]
#                     },
#                     "description": f"Service fee for posting a job titled '{job.title}' on Jobify platform",
#                     "amount": {
#                         "total": f"{payment_amount:.2f}",
#                         "currency": "USD"
#                     },
                    
#                 }]
#             })

#             if payment.create():
#                 print("[SUCCESS] PayPal payment created")
#                 JobPayment.objects.create(
#                     job=job,
#                     payment_id=payment.id,
#                     payment_status='created',
#                     payment_amount=payment_amount,
#                     payment_currency='INR'
#                 )

#                 for link in payment.links:
#                     print(f"[DEBUG] PayPal link: {link.rel} - {link.href}")
#                     if link.rel == "approval_url":
#                         print("[INFO] Redirecting to PayPal approval URL")
#                         return redirect(link.href)

#                 print("[ERROR] No PayPal approval URL found")
#                 return HttpResponse("No approval URL found.", status=500)
#             else:
#                 print(f"[ERROR] PayPal payment creation failed: {payment.error}")
#                 return HttpResponse("Payment creation failed", status=500)

#         else:
#             print("[ERROR] Job form is invalid")
#             print(f"[DEBUG] Form errors: {job_form.errors}")
#             return render(request, 'company/add_job.html', {
#                 'job_form': job_form,
#                 'company': company,
#                 'form_errors': job_form.errors
#             })
#     else:
#         job_form = JobForm()

#     return render(request, 'company/add_job.html', {
#         'job_form': job_form,
#         'company': company
#     })

# Cashfree API credentials (use sandbox for testing)
CASHFREE_APP_ID = settings.CASHFREE_APP_ID
CASHFREE_SECRET_KEY = settings.CASHFREE_SECRET_KEY

# @login_required(login_url='login')
# def add_job_view(request, company_name, company_person_name):
#     user = request.user
#     print(f"[DEBUG] Logged in user: {user}")

#     # Ensure only company users can access
#     if user.user_type != "company_person":
#         print("[ERROR] User is not a company_person")
#         return redirect('login')

#     # Get the company
#     company = get_object_or_404(Company, name=company_name)
#     print(f"[DEBUG] Found company: {company.name}")

#     try:
#         company_person = CompanyPerson.objects.get(user=user, company=company)
#         company_person_full_name = company_person.user.get_full_name()
#         print(f"[DEBUG] Company person full name: {company_person_full_name}")
#     except CompanyPerson.DoesNotExist:
#         print("[ERROR] CompanyPerson not found for user")
#         return redirect("login")

#     if company_person_full_name != company_person_name:
#         print("[ERROR] Name mismatch")
#         return redirect("login")

#     if request.method == 'POST':
#         job_form = JobForm(request.POST)
#         print(f"[DEBUG] Received POST data: {request.POST}")

#         if job_form.is_valid():
#             print("[SUCCESS] Job form is valid")
#             job = job_form.save(commit=False)
#             job.company = company
#             job.posted_by = company_person
#             job.save()
#             job_form.save_m2m()
#             print(f"[DEBUG] Job saved: {job.title} - ID: {job.id}")

#             # Calculate payment amount (mocking the process)
#             try:
#                 salary = float(job.salary)
#                 payment_amount = round(salary / 10, 2)
#                 print(f"[DEBUG] Calculated payment amount: {payment_amount}")
#             except (TypeError, ValueError):
#                 print("[WARNING] Invalid salary, setting default payment amount")
#                 payment_amount = 1000.00

#             # Create Cashfree order
#             order_id = create_cashfree_order(payment_amount , job , company_person)
#             print("Cashfree order ID:", order_id)

#             if not order_id:
#                 print("[ERROR] Cashfree order creation failed")
#                 return JsonResponse({'error': 'Failed to create payment order'}, status=500)
#             # Save job payment details
#             job_payment = JobPayment.objects.create(
                
#                 job=job,
#                 payment_id=order_id,
#                 payer_id = str(company_person.id),
#                 payment_status='created',
#                 payment_amount=payment_amount,
#                 payment_currency='INR'  # Cashfree works with INR for India
#             )

#             # Return the payment URL for Cashfree
#             return JsonResponse({
#                 'payment_url': f'https://test.cashfree.com/billpay/checkout/post/submit',
#                 'order_id': order_id,
#                 'payment_amount': payment_amount,
#                 'job_payement' : job_payment
#             })

#         else:
#             print("[ERROR] Job form is invalid")
#             return render(request, 'company/add_job.html', {
#                 'job_form': job_form,
#                 'company': company,
#                 'form_errors': job_form.errors
#             })
#     else:
#         job_form = JobForm()

#     return render(request, 'company/add_job.html', {
#         'job_form': job_form,
#         'company': company,
#         'company_person_full_name'  : company_person_full_name
#     })

# FINAL
# def add_job_view(request, company_name, company_person_name):
#     user = request.user
#     if user.user_type != "company_person":
#         return redirect('login')

#     company = get_object_or_404(Company, name=company_name)

#     try:
#         company_person = CompanyPerson.objects.get(user=user, company=company)
#     except CompanyPerson.DoesNotExist:
#         return redirect("login")

#     company_person_full_name = company_person.user.get_full_name()
#     if company_person_full_name != company_person_name:
#         return redirect("login")

#     if request.method == 'POST':
#         job_form = JobForm(request.POST)
#         location_form = LocationFormForJob(request.POST)

#         if job_form.is_valid() and location_form.is_valid():
#             job = job_form.save(commit=False)
#             location = location_form.save(commit=False)
#             job.company = company
#             job.posted_by = company_person
#             job.is_active = False
#             job.job_location = location
#             location.save()
#             job.save()
#             job_form.save_m2m()

#             try:
#                 salary = float(job.salary)
#                 payment_amount = round(salary / 10, 2)
#             except (TypeError, ValueError):
#                 payment_amount = 1000.00

#             return_url = "http://localhost:8000/payment/callback/"
#             order_id = f"ORDER-{job.id}"
#             customer_id = f"USER-{company_person.id}"
#             customer_email = company_person.user.email or "test@example.com"
#             customer_phone = company_person.user.phone_number or "9999999999"  # Replace with real field
#             print("Customer Phone : " , customer_phone)
#             payment_details = create_cashfree_order(
#                 amount=payment_amount,
#                 order_id=order_id,
#                 customer_id=customer_id,
#                 return_url=return_url,
#                 customer_email=customer_email,
#                 customer_phone=customer_phone )

#             print("[DEBUG] The Payment Details : " , payment_details)

#             if payment_details:
#                 payment_session_id = payment_details.get('payment_session_id')
#                 print("The Payment Session ID : " , payment_session_id)
#                 if payment_session_id:
#                     # For popup checkout, render a page with JS snippet
#                     return render(request, 'cashfree/popup_checkout.html', {
#                         'payment_session_id': payment_session_id, 
#                         'company_name' : company.name , 
#                         'company_person_full_name' : company_person_full_name,

#                     })
#                 else:
#                     return JsonResponse({'error': 'Missing payment session ID'}, status=500)
#             else:
#                 return JsonResponse({'error': 'Failed to create payment order'}, status=500)

#         else:
#             return render(request, 'company/add_job.html', {
#                 'job_form': job_form,
#                 'location_form': location_form,
#                 'company': company,
#                 'form_errors': job_form.errors
#             })

#     else:
#         job_form = JobForm()
#         location_form = LocationFormForJob()
#         return render(request, 'company/add_job.html', {
#             'job_form': job_form,
#             'location_form': location_form,
#             'company': company,
#             'company_person_full_name': company_person_full_name
#         })

def add_job_view(request, company_name, company_person_name):
    user = request.user
    if user.user_type != "company_person":
        return redirect('login')

    company = get_object_or_404(Company, name=company_name)

    try:
        company_person = CompanyPerson.objects.get(user=user, company=company)
    except CompanyPerson.DoesNotExist:
        return redirect("login")
    company_name = company.name
    company_person_full_name = company_person.user.get_full_name()
    if company_person_full_name != company_person_name:
        return redirect("login")

    if request.method == 'POST':
        job_form = JobForm(request.POST)
        location_form = LocationFormForJob(request.POST)

        if job_form.is_valid() and location_form.is_valid():
            job_data = job_form.cleaned_data

            print("[DEBUG] : The Job Data is : " , job_data)
            location_data = location_form.cleaned_data

            try:
                salary = float(job_data.get("salary", 10000))
                payment_amount = round(salary / 10, 2)
            except (TypeError, ValueError):
                payment_amount = 1000.00

            # Create a temporary ID to store the job data
            temp_id = str(uuid.uuid4())
            cache.set(temp_id, {
                "job_data": job_data,
                "location_data": location_data,
                "company_id": company.id,
                "company_person_id": company_person.id,
            }, timeout=60 * 100)

            return_url = f"http://localhost:8000/payment/callback/?temp_id={temp_id}"
            order_id = f"ORDER-{temp_id}"
            customer_id = f"USER-{company_person.id}"
            customer_email = company_person.user.email or "test@example.com"
            customer_phone = company_person.user.phone_number or "9999999999"

            payment_details = create_cashfree_order(
                amount=payment_amount,
                order_id=order_id,
                customer_id=customer_id,
                return_url=return_url,
                customer_email=customer_email,
                customer_phone=customer_phone
            )

            if payment_details:
                print("[DEBUG] The Payment Details : " , payment_details)
                payment_session_id = payment_details.get('payment_session_id')
                if payment_session_id:
                    return render(request, 'cashfree/popup_checkout.html', {
                        'payment_session_id': payment_session_id,
                        'company_name': company_name,
                        'company_person_full_name': company_person_full_name,
                        'temp_id' : temp_id,
                        'payment_amount': payment_amount,
                    })
                else:
                    return JsonResponse({'error': 'Missing payment session ID'}, status=500)
            else:
                return JsonResponse({'error': 'Failed to create payment order'}, status=500)

        else:
            return render(request, 'company/add_job.html', {
                'job_form': job_form,
                'location_form': location_form,
                'company': company,
                'form_errors': job_form.errors
            })

    else:
        job_form = JobForm()
        location_form = LocationFormForJob()
        return render(request, 'company/add_job.html', {
            'job_form': job_form,
            'location_form': location_form,
            'company': company,
            'company_person_full_name': company_person_full_name
        })

@csrf_exempt
def payment_callback_view(request):
    print("[DEBUG] Payment Callback View")
    temp_id = request.GET.get('temp_id')
    try:
        form_data = json.loads(request.body)  # Parse JSON body
        payment_status = form_data.get('payment_status')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    print("[DEBUG] The temporary ID : " , temp_id)
    print("[DEBUG] The Payment Status : " , payment_status)

    if not temp_id and payment_status:
        return JsonResponse({'error': 'Missing data'}, status=400)

    data = cache.get(temp_id)
    if not data:
        return HttpResponse("Payment expired or invalid", status=410)

    if payment_status != "success":
        return HttpResponse("Payment not successful", status=400)

    try:
        company = Company.objects.get(id=data["company_id"])
        print("[DEBUG] Company Name is : " , company.name)
        company_person = CompanyPerson.objects.get(id=data["company_person_id"])
        is_edit = data.get("is_edit", False)

        if is_edit:
            # Edit existing job
            job = Job.objects.get(id=data["job_id"])
            print("[DEBUG] Updating existing Job:", job.id)
            location_data = data.get("location_data")
            print("[DEBUG] Location Data in the Form : " , location_data)
            if not location_data:
                return JsonResponse({'status': 'error', 'message': 'Location data missing'})
            if job.job_location:
                for key, value in location_data.items():
                    setattr(job.job_location, key, value)
                job.job_location.save()
                print("[DEBUG] Updated Location:", job.job_location)
            else:
                # In rare case there's no location, create one
                location = Location.objects.create(**location_data)
                job.job_location = location

            # for field, value in job_data.items():
            #     setattr(job, field, value)

            job_data = data.get("job_data", {})
            print("[DEBUG] The Job Data : " , job_data)
            # job.title=job_data.get("title")
            # job.description=job_data.get("description")
            # job.salary=job_data.get("salary")
            # job.job_type=job_data.get("job_type")
            # job.expected_start_date=job_data.get("expected_start_date")
            # job.experience_required=job_data.get("experience_required")
            # job.job_language=job_data.get("job_language")
            # job.number_of_people=job_data.get("number_of_people")
            # job.work_location_type=job_data.get("work_location_type")
            # job.company_goal=job_data.get("company_goal")
            # job.work_environment=job_data.get("work_environment")
            # job.additional_questions=job_data.get("additional_questions")
            # job.requirements=job_data.get("requirements")
            # job.application_deadline=job_data.get("application_deadline")
            # job.company=company
            # job.posted_by=company_person
            # job.save()
            # print("[DEBUG] Job Updated : " , job)

            for key, value in job_data.items():
                setattr(job, key, value)
            job.company = company
            job.posted_by = company_person
            job.save()
            print("[DEBUG] Updated Job:", job)

        else:
            # Save location
            location_data = data.get("location_data", {})
            location = Location.objects.create(**location_data)

            # Save job
            job_data = data.get("job_data", {})
            print("[DEBUG] The Job Data : " , job_data)
            job = Job.objects.create(
                title=job_data.get("title"),
                description=job_data.get("description"),
                salary=job_data.get("salary"),
                job_type=job_data.get("job_type"),
                expected_start_date=job_data.get("expected_start_date"),
                experience_required=job_data.get("experience_required"),
                job_language=job_data.get("job_language"),
                number_of_people=job_data.get("number_of_people"),
                work_location_type=job_data.get("work_location_type"),
                company_goal=job_data.get("company_goal"),
                work_environment=job_data.get("work_environment"),
                additional_questions=job_data.get("additional_questions"),
                requirements=job_data.get("requirements"),
                application_deadline=job_data.get("application_deadline"),
                company=company,
                posted_by=company_person,
                job_location=location
            )
            print("[DEBUG] Job Created : " , job)

        # Save payment
        JobPayment.objects.create(
            job=job,
            payment_id=f"CF-{uuid.uuid4().hex[:10]}",
            payment_status="success",
            payer_id=company_person.id,
            payment_amount = round(float(job.salary or 0) / 10, 2),
            payment_currency="INR"
        )

        # Clean up
        cache.delete(temp_id)

        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({"error": f"Save error: {str(e)}"}, status=500)


CASHFREE_ORDER_URL = "https://sandbox.cashfree.com/pg/orders"  # Use test URL or live accordingly

def create_cashfree_order(amount, order_id, customer_id, return_url, customer_email, customer_phone):
    client_id = os.getenv("client_id")
    client_secret = os.getenv("client_secret")
    environment = os.getenv("environment")
    
    # Correct endpoint based on the environment
    if environment == "SANDBOX":
        api_url = "https://sandbox.cashfree.com/pg/orders"
    else:
        api_url = "https://api.cashfree.com/pg/orders"

    # Prepare the order data
    order_data = {
        "order_id": order_id,
        "order_amount": amount,
        "order_currency": "INR",
        "order_meta": {
            "return_url": return_url
        },
        "customer_details": {
            "customer_id": customer_id,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
        }
    }

    headers = {
        'x-client-id': client_id,
        'x-client-secret': client_secret,
        'Content-Type': 'application/json',
        'x-api-version' : '2025-01-01',
    }
    print("[DEBUG] The Order Data : ", order_data['customer_details'])
    try:
        print("The Final Payload:", json.dumps(order_data, indent=2))
        # Send POST request to create order
        response = requests.post(api_url, json=order_data, headers=headers, verify=False)
        
        # Check the response
        if response.status_code == 200:
            response_data = response.json()
            print("[DEBUG] The Order ID is : " , response_data['order_id'])
            if "payment_session_id" in response_data:
                return {
                    "order_id": response_data["order_id"],
                    "payment_session_id": response_data.get("payment_session_id", "Not Available")
                }
            else:
                return {"error": "Order creation failed, no session id found", "details": response_data}
        else:
            return {"error": f"Failed to create order: {response.status_code}", "details": response.text}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


        
def cashfree_popup_page(request):
    return render(request, 'cashfree/popup_checkout.html')

# def company_all_jobs_view(request, company_name):
#     user = request.user
#     print(f"[DEBUG] Logged in user: {user}")

#     # Ensure only company users can access
#     if user.user_type != "company_person":
#         print("[ERROR] User is not a company_person")
#         return redirect('login')

    

#     if user.is_authenticated and user.user_type == "company_person":
#         try:
#             # Get the company
#             company = get_object_or_404(Company, name=company_name)
#             print(f"[DEBUG] Found company: {company.name}")
#             company_person = CompanyPerson.objects.get(user = user)
#             company_person_full_name = company_person.user.get_full_name()
#             jobs = Job.objects.filter(company=company).order_by('-created_at')

#             is_external = False
#             profile_picture = company.user.profile_picture
#             profile_picture_url = str(profile_picture) if profile_picture else ""
#             if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
#                 print(profile_picture_url)
#                 is_external = True
#             else:
#                 is_external = False
#         except Company.DoesNotExist:
#             return redirect('company_register_1')

#         return render(request, 'company/all_jobs.html', {
#             'company': company,
#             'jobs': jobs,
#             'company_person' : company_person,
#             'company_person_full_name' : company_person_full_name,
#             'is_external' : is_external
#         })
#     else:
#         return redirect('login')
    

def company_all_jobs_view(request, company_name):
    user = request.user
    print(f"[DEBUG] Logged in user: {user}")

    if not user.is_authenticated or user.user_type != "company_person":
        print("[ERROR] User is not authenticated or not a company_person")
        return redirect('login')

    try:
        company = get_object_or_404(Company, name=company_name)
        print(f"[DEBUG] Found company: {company.name}")
        company_person = CompanyPerson.objects.get(user=user, company=company)
        company_person_full_name = company_person.user.get_full_name()
        jobs = Job.objects.filter(company=company).order_by('-created_at')

        profile_picture = company.user.profile_picture
        profile_picture_url = str(profile_picture) if profile_picture else ""
        is_external = profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')

        # ✅ Choose template based on admin status
        template_name = 'company/admin_all_jobs.html' if company_person.is_admin else 'company/all_jobs.html'

        return render(request, template_name, {
            'company': company,
            'jobs': jobs,
            'company_person': company_person,
            'company_person_full_name': company_person_full_name,
            'is_external': is_external
        })

    except Company.DoesNotExist:
        return redirect('company_register_1')
    except CompanyPerson.DoesNotExist:
        return redirect('login')


def edit_job(request, company_name,  job_id):
    user = request.user
    if user.user_type != "company_person":
        return redirect('login')

    company = get_object_or_404(Company, name=company_name)

    try:
        company_person = CompanyPerson.objects.get(user=user, company=company)
    except CompanyPerson.DoesNotExist:
        return redirect("login")

    company_person_full_name = company_person.user.get_full_name()
    

    job = get_object_or_404(Job, id=job_id, company=company)

    if request.method == 'POST':
        job_form = JobForm(request.POST, instance=job)
        location_form = LocationFormForJob(request.POST, instance=job.job_location)

        if job_form.is_valid() and location_form.is_valid():
            job_data = job_form.cleaned_data
            location_data = location_form.cleaned_data
            print("[DEBUG] Job Data : " , job_data)
            print("[DEBUG] Location Data : " , location_data)
            payment_amount = 1000.00
           

            temp_id = str(uuid.uuid4())
            cache.set(temp_id, {
                "is_edit": True,
                "job_data": job_data,
                "location_data": location_data,
                "company_id": company.id,
                "company_person_id": company_person.id,
                "edit_mode": True,
                "job_id": job.id
            }, timeout=60 * 100)

            return_url = f"http://localhost:8000/payment/callback/?temp_id={temp_id}"
            order_id = f"ORDER-{temp_id}"
            customer_id = f"USER-{company_person.id}"
            customer_email = company_person.user.email or "test@example.com"
            customer_phone = company_person.user.phone_number or "9999999999"

            payment_details = create_cashfree_order(
                amount=payment_amount,
                order_id=order_id,
                customer_id=customer_id,
                return_url=return_url,
                customer_email=customer_email,
                customer_phone=customer_phone
            )

            if payment_details:
                payment_session_id = payment_details.get('payment_session_id')
                if payment_session_id:
                    return render(request, 'cashfree/popup_checkout.html', {
                        'payment_session_id': payment_session_id,
                        'company_name': company_name,
                        'company_person_full_name': company_person_full_name,
                        'temp_id': temp_id,
                        'payment_amount': payment_amount,
                    })
                else:
                    return JsonResponse({'error': 'Missing payment session ID'}, status=500)
            else:
                return JsonResponse({'error': 'Failed to create payment order'}, status=500)
        else:
            return render(request, 'company/edit_job.html', {
                'job_form': job_form,
                'location_form': location_form,
                'company': company,
                'company_person_full_name': company_person_full_name,
                'form_errors': job_form.errors
            })

    else:
        job_form = JobForm(instance=job)
        location_form = LocationFormForJob(instance=job.job_location)
        return render(request, 'company/edit_job.html', {
            'job_form': job_form,
            'location_form': location_form,
            'company': company,
            'company_person_full_name': company_person_full_name
        })


def delete_job(request, job_id):
    user = request.user
    if user.is_authenticated and user.user_type == "company_person":
        try:

            company_person = get_object_or_404(CompanyPerson, user=user)
            if company_person.is_admin:
                company = company_person.company
                job = get_object_or_404(Job, id=job_id, company=company)
            
                job.delete()
                messages.success(request, "Job deleted successfully.")
                return redirect('company_dashboard')
            else:
                messages.error(request, "You are not authorized to perform this action.")
                return redirect('company_dashboard')
        except CompanyPerson.DoesNotExist:
            return redirect('pre-signup')
    else:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('login')
    
def view_team_members(request, company_name):
    user = request.user
    print(f"[DEBUG] Logged in user: {user}")

    # Check if user is authenticated and a company_person
    if not user.is_authenticated or user.user_type != "company_person":
        print("[ERROR] Unauthorized access or not a company_person")
        return redirect('login')

    # Get the company object based on the company_name slug
    company = get_object_or_404(Company, name=company_name)
    company_person = CompanyPerson.objects.get(user=user , company = company)
    
    is_external = False
    profile_picture = company.user.profile_picture
    profile_picture_url = str(profile_picture) if profile_picture else ""
    if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
        print(profile_picture_url)
        is_external = True
    else:
        is_external = False

    company_person_full_name = company_person.user.get_full_name()
    # Fetch all non-admin team members of the company
    team_members = CompanyPerson.objects.filter(company=company)

    context = {
        'company': company,
        'team_members': team_members,
        'is_external' : is_external,
        'company_person_full_name'  :company_person_full_name,
        'company_person'  : company_person
    }
    return render(request, 'company/view_team.html', context)


def add_team_member(request , company_name , company_person_name):
    print("[DEBUG] Adding Team Member View")
    user = request.user

    print("[DEBUG] User is : " , user)
    if not user.is_authenticated or user.user_type != "company_person":
        messages.error(request, "You must be a company user to add team members.")
        return redirect('login')
    
    try:
        company = Company.objects.get(name=company_name)
    except Company.DoesNotExist:
        messages.error(request, "Company not found.")
        return redirect('company_dashboard')  # or some other appropriate redirect

    try:
        company_person = CompanyPerson.objects.get(user=user, company=company)
    except CompanyPerson.DoesNotExist:
        messages.error(request, "You are not part of this company.")
        return redirect('company_dashboard')
    company_person_full_name = company_person.user.get_full_name()

    if company_person_full_name != company_person_name:
        return redirect("login")
    
    is_external = False
    profile_picture = company.user.profile_picture
    profile_picture_url = str(profile_picture) if profile_picture else ""
    if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
        print(profile_picture_url)
        is_external = True
    else:
        is_external = False


    if request.method == "POST":
        print("[DEBUG] POST method")
        user_form = CustomUserFormForTeamMember(request.POST, request.FILES)
        team_form = AddTeamMemberForm(request.POST)

        print("[DEBUG] company_name:", company_name)
        print("[DEBUG] company_person_name:", company_person_name)

        if user_form.is_valid() and team_form.is_valid():
            print("[DEBUG] user_form cleaned data:", user_form.cleaned_data)
            print("[DEBUG] user_form cleaned data:", team_form.cleaned_data)
            country_code = request.POST.get('country_code')
            phone_number = user_form.cleaned_data.get('phone_number')
            full_phone_number = country_code + phone_number

            
            # Save the new user
            user = user_form.save(commit=False)
            user.username = user.email
            user.password = make_password("password")
            user.phone_number = full_phone_number
            user.user_type = "company_person"
            user.save()
            print("[DEBUG] User is Saved : ", user)
            # Save the team member and link the created user
            team_member = team_form.save(commit=False)
            team_member.user = user
            team_member.company = company_person.company  # Assuming `request.user.company` exists
            team_member.save()
            print("[DEBUG] Team Member Saved : " , team_member)

            messages.success(request, f"Team member {user.first_name} {user.last_name} added successfully!")
            return redirect('company_team_members' , company.name)
        else:
            print("[DEBUG] Form is not VALID")
            # Print errors of both forms
            print("[DEBUG] User Form Errors: ", user_form.errors)
            print("[DEBUG] Team Form Errors: ", team_form.errors)
           
            errors = {
                'team_form_errors': team_form.errors,
                'user_form_errors': user_form.errors,
            }
            context = {**errors, 
                'user_form': user_form,
                'team_form': team_form,
                'is_external' : is_external,
                'company_person_full_name'  : company_person_full_name,
                'company_person'  : company_person, 
                'company'  : company
            }
            return render(request, 'company/add_team_member.html', context)
    

    else:
        user_form = CustomUserFormForTeamMember()
        team_form = AddTeamMemberForm()

    context = {
        'user_form': user_form,
        'team_form': team_form,
        'is_external' : is_external,
        'company_person_full_name'  : company_person_full_name,
        'company_person'  : company_person, 
        'company'  : company
    }
    return render(request, 'company/add_team_member.html', context)

def edit_team_member(request, company_name, company_person_name, member_id):
    print("[DEBUG] Editing Team Member View")
    user = request.user

    if not user.is_authenticated or user.user_type != "company_person":
        messages.error(request, "You must be a company user to edit team members.")
        return redirect('login')

    try:
        company = Company.objects.get(name=company_name)
    except Company.DoesNotExist:
        messages.error(request, "Company not found.")
        return redirect('company_dashboard')

    try:
        company_person = CompanyPerson.objects.get(user=user, company=company)
    except CompanyPerson.DoesNotExist:
        messages.error(request, "You are not part of this company.")
        return redirect('company_dashboard')

    company_person_full_name = company_person.user.get_full_name()
    if company_person_full_name != company_person_name:
        return redirect("login")

    # Validate profile picture logic for sidebar/avatar
    is_external = False
    profile_picture = company.user.profile_picture
    profile_picture_url = str(profile_picture) if profile_picture else ""
    if profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://'):
        is_external = True

    # Get the team member to edit
    team_member = get_object_or_404(CompanyPerson, id=member_id, company=company)
    team_user = team_member.user

    if request.method == "POST":
        print("[DEBUG] POST method")
        user_form = CustomUserFormForTeamMember(request.POST, request.FILES, instance=team_user)
        team_form = AddTeamMemberForm(request.POST, instance=team_member)

        if user_form.is_valid() and team_form.is_valid():
            country_code = request.POST.get('country_code')
            phone_number = user_form.cleaned_data.get('phone_number')
            full_phone_number = country_code + phone_number

            user = user_form.save(commit=False)
            user.phone_number = full_phone_number
            user.username = user.email  # Ensure username stays synced with email
            user.password = make_password("password")
            user.save()

            team_form.save()

            messages.success(request, f"Team member {user.first_name} {user.last_name} updated successfully!")
            return redirect('company_team_members', company.name)
        else:
            print("[DEBUG] Form is not VALID")
            print("[DEBUG] User Form Errors: ", user_form.errors)
            print("[DEBUG] Team Form Errors: ", team_form.errors)

            context = {
                'user_form': user_form,
                'team_form': team_form,
                'company': company,
                'company_person': company_person,
                'company_person_full_name': company_person_full_name,
                'is_external': is_external,
                'team_member': team_member,
            }
            return render(request, 'company/edit_team_member.html', context)

    else:
        user_form = CustomUserFormForTeamMember(instance=team_user)
        team_form = AddTeamMemberForm(instance=team_member)

    context = {
        'user_form': user_form,
        'team_form': team_form,
        'company': company,
        'company_person': company_person,
        'company_person_full_name': company_person_full_name,
        'is_external': is_external,
        'team_member': team_member,
    }
    return render(request, 'company/edit_team_member.html', context)


def remove_team_member(request, company_name, company_person_name ,  member_id):
    user = request.user
    print(f"[DEBUG] Logged in user: {user}")

    # Check if user is authenticated and a company_person
    if not user.is_authenticated or user.user_type != "company_person":
        print("[ERROR] Unauthorized access or not a company_person")
        return redirect('login')
    # Get the company object based on the company_name slug
    company = get_object_or_404(Company, name=company_name)
    company_person = CompanyPerson.objects.get(user=user , company = company)
    
    is_external = False
    profile_picture = company.user.profile_picture
    profile_picture_url = str(profile_picture) if profile_picture else ""
    if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
        print(profile_picture_url)
        is_external = True
    else:
        is_external = False

    # Get the company object based on the company_name slug
    company = get_object_or_404(Company, name=company_name)
    company_person = CompanyPerson.objects.get(user=user, company=company)
    company_person_full_name = company_person.user.get_full_name()
    # Fetch the team member to be removed
    team_member = get_object_or_404(CompanyPerson, id=member_id, company=company)

    # Prevent the user from removing themselves
    if team_member == company_person:
        messages.error(request, "You cannot remove yourself from the team.")
        return redirect('company_team_members', company_name=company.name)

    team_member.user.delete()
    # Remove the team member
    team_member.delete()
    messages.success(request, f"Team member {team_member.user.get_full_name()} removed successfully!")
    print("[DEBUG] Team Member Deleted : " , team_member)
     # Fetch all non-admin team members of the company
    team_members = CompanyPerson.objects.filter(company=company)

    context = {
        'company': company,
        'team_members': team_members,
        'is_external' : is_external,
        'company_person_full_name'  :company_person_full_name,
        'company_person'  : company_person
    }
    print(f"[DEBUG] Redirecting to company_team_members: {company.name}")
    return redirect('company_team_members', company_name=company.name)


# def view_applications_view(request , company_name):
#     user = request.user
#     try:
#         company_person = CompanyPerson.objects.get(user=user)
#         company = Company.objects.get(name = company_name)
#     except CompanyPerson.DoesNotExist:
#         return render(request, "error.html", {"message": "You are not authorized to view this page."})

#     company_person_full_name = company_person.user.get_full_name()
#     is_external = False
#     profile_picture = company.user.profile_picture
#     profile_picture_url = str(profile_picture) if profile_picture else ""
#     if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
#         print(profile_picture_url)
#         is_external = True
#     else:
#         is_external = False
#     # Get all jobs posted by the company and their related applications
#     jobs = Job.objects.filter(company=company)
    
#     jobs_with_applications = []
#     for job in jobs:
#         # Get applications for each job
#         applications = job.applications.all()
        
#         # Append job and applications to the list
#         jobs_with_applications.append({
#             'job': job,
#             'applications': applications
#         })
#     print("[DEBUG] Job With Applications  : " , jobs_with_applications)

#     return render(request, "company/view_applications.html", {
#         "jobs_with_applications": jobs_with_applications , 'company': company,
#             'company_person': company_person,
#             'company_person_full_name': company_person_full_name,
#             'is_external': is_external,
#     })

def view_applications_view(request, company_name):
    user = request.user
    try:
        company_person = CompanyPerson.objects.get(user=user)
        company = Company.objects.get(name=company_name)
    except CompanyPerson.DoesNotExist:
        return render(request, "error.html", {"message": "You are not authorized to view this page."})

    company_person_full_name = company_person.user.get_full_name()
    is_external = False
    profile_picture = company.user.profile_picture
    profile_picture_url = str(profile_picture) if profile_picture else ""
    if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
        print(profile_picture_url)
        is_external = True
    else:
        is_external = False
    
    # Get all jobs posted by the company and their related applications
    jobs = Job.objects.filter(company=company)
    
    jobs_with_applications = []
    for job in jobs:
        applications = job.applications.all()
        jobs_with_applications.append({
            'job': job,
            'applications': applications
        })
    
    print("[DEBUG] Jobs With Applications:", jobs_with_applications)

    # ✅ Choose template based on admin status
    template_name = 'company/view_applications_admin.html' if company_person.is_admin else 'company/view_applications.html'

    return render(request, template_name, {
        "jobs_with_applications": jobs_with_applications,
        'company': company,
        'company_person': company_person,
        'company_person_full_name': company_person_full_name,
        'is_external': is_external,
    })


# def view_applicant(request, application_id):
#     user = request.user
#     company_person = CompanyPerson.objects.get(user=user)
#     company = company_person.company


#     company_person_full_name = company_person.user.get_full_name()
#     is_external = False
#     profile_picture = company.user.profile_picture
#     profile_picture_url = str(profile_picture) if profile_picture else ""
#     if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
#         print(profile_picture_url)
#         is_external = True
#     else:
#         is_external = False


#     application = get_object_or_404(Application, id=application_id)

#     context = {
#         'application': application,
#         'job_seeker': application.job_seeker,
#         'user': application.job_seeker.user,
#         'job': application.job,
#         'company': company,
#         'company_person': company_person,
#         'company_person_full_name': company_person_full_name,
#         'is_external': is_external,
#     }
#     return render(request, 'company/view_applicant.html', context)

def view_applicant(request, application_id):
    user = request.user
    
    # Fetch the current logged-in company person and their associated company
    company_person = CompanyPerson.objects.get(user=user)
    company = company_person.company

    company_person_full_name = company_person.user.get_full_name()
    is_external = False
    profile_picture = company.user.profile_picture
    profile_picture_url = str(profile_picture) if profile_picture else ""
    if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
        print(profile_picture_url)
        is_external = True
    else:
        is_external = False

    # Get the application object
    application = get_object_or_404(Application, id=application_id)

    # Determine the correct template based on admin status
    template_name = 'company/view_applicant_admin.html' if company_person.is_admin else 'company/view_applicant.html'

    context = {
        'application': application,
        'job_seeker': application.job_seeker,
        'job_seeker': application.job_seeker.user,
        'job': application.job,
        'company': company,
        'company_person': company_person,
        'company_person_full_name': company_person_full_name,
        'is_external': is_external,
    }

    return render(request, template_name, context)


def update_application_status(request, application_id, action):

    user = request.user
    company_person = CompanyPerson.objects.get(user=user)
    company = company_person.company


    company_person_full_name = company_person.user.get_full_name()
    

    application = get_object_or_404(Application, id=application_id)

    if request.user != company_person.user:
        messages.error(request, "You are not authorized to update this application.")
        return redirect('company_dashboard')

    if action in ['accept', 'rejected', 'review']:
        application.status = action
        application.save()
        messages.success(request, f"Application marked as '{action}'.")
    else:
        messages.error(request, "Invalid action.")
        
    return redirect('view_applicant' , application.id)

# def get_matching_jobs_for_user(user):
#     desired = user.desired_position.lower().strip()

#     categories = {
#         "developer": {
#             "keywords": ["developer", "programmer", "software engineer", "web developer", "engineer"],
#             "industries": ["Technology", "Software", "IT Services"]
#         },
#         "data": {
#             "keywords": ["data analyst", "data scientist", "machine learning", "ai", "ml"],
#             "industries": ["Analytics", "Technology", "Research", "AI"]
#         },
#         "designer": {
#             "keywords": ["designer", "ui", "ux", "graphic"],
#             "industries": ["Design", "Media", "Creative", "Marketing"]
#         },
#         "marketing": {
#             "keywords": ["marketing", "seo", "content", "brand"],
#             "industries": ["Marketing", "Advertising", "Media"]
#         }
#     }

#     matched_keywords = []
#     matched_industries = []

#     for key, data in categories.items():
#         if key in desired:
#             matched_keywords = data["keywords"]
#             matched_industries = data["industries"]
#             break

#     # If nothing matched, just use desired text
#     if not matched_keywords:
#         matched_keywords = [desired]

#     # Build query
#     job_query = Q()
#     for keyword in matched_keywords:
#         job_query |= (
#             Q(job_position__icontains=keyword) |
#             Q(skill_requirements__name__icontains=keyword) |
#             Q(job_description__icontains=keyword)
#         )

#     # Add industry filtering if any
#     if matched_industries:
#         industry_query = Q()
#         for industry in matched_industries:
#             industry_query |= Q(company__industry__icontains=industry)
#         job_query &= industry_query

#     # Final job list
#     return Job.objects.filter(job_query).distinct().order_by('-posted_at')


def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'job_detail.html', {'job': job})




def generate_resume_pdf(user, profile):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    width, height = A4
    left_col_width = width * 0.35
    right_col_width = width * 0.65

    styles = getSampleStyleSheet()
    normal = styles['Normal']
    heading = ParagraphStyle('Heading', fontSize=18, leading=22, spaceAfter=12, fontName="Helvetica-Bold", alignment=1)
    subheading = ParagraphStyle('Subheading', fontSize=14, leading=16, fontName="Helvetica-Bold")
    small = ParagraphStyle('Small', fontSize=10, leading=13)

    # ==== Top Header (Name & Title) ====
    name = f"<para align=center><b>{user.first_name} {user.last_name}</b></para>"
    title = f"<para align=center>{profile.desired_position}</para>"
    elements.append(Paragraph(name, heading))
    elements.append(Paragraph(title, normal))
    elements.append(Spacer(1, 20))

    # ==== Columns (Left and Right) ====
    left_data = []
    right_data = []

    # ---- Left Column (Contact Info, Skills, and Certificates) ----
    contact_info = [
        Paragraph("<b>Contact Information</b>", subheading),
        Paragraph(f"Email: {user.email}", small),
        Paragraph(f"Phone: {user.phone_number}", small),
        Paragraph(f"Location: {profile.address.street_address}, {profile.address.city}, {profile.address.state}, {profile.address.country}", small),
        Spacer(1, 10),
    ]

    skills_info = [
        Paragraph("<b>Skills</b>", subheading),
    ]
    if profile.skills:
        for skill in profile.skills.split(","):
            skills_info.append(Paragraph(f"• {skill.strip()}", small))
    else:
        skills_info.append(Paragraph("No skills listed.", small))

    certificates_info = [
        Paragraph("<b>Certificates</b>", subheading),
    ]
    print(f"Certificates: {profile.certificates.all()}")
    if profile.certificates.exists():  # Check if there are certificates
        for cert in profile.certificates.all():  # Loop through related certificates
            print("Certificate Name : " , cert)
            certificates_info.append(Paragraph(f"• {cert.name}", small))
            certificates_info.append(Paragraph(f"• {cert.certificate_file}", small))
    else:
        certificates_info.append(Paragraph("No certificates listed.", small))

    left_data.extend(contact_info + [Spacer(1, 10)] + skills_info + [Spacer(1, 10)] + certificates_info)

    # ---- Right Column (Work Experience, Education) ----
    print(f"Education: {profile.education.all()}")
    if profile.education.exists():
        for edu in profile.education.all():
            print("Education:", edu)
            right_data.append(Paragraph(f"• {edu.degree} in {edu.field_of_study}", small))
            right_data.append(Paragraph(f"• {edu.school_name}, {edu.school_address}", small))
            right_data.append(Paragraph(f"• Duration: {edu.start_year} to {edu.end_year or 'Present'}", small))
    else:
        right_data.append(Paragraph("No education details listed.", small))

        
    if profile.work_experience:
        right_data.append(Paragraph("<b>Work Experience</b>", subheading))
        right_data.append(Paragraph(str(profile.work_experience), normal))
        right_data.append(Spacer(1, 10))


    print(f"Experiences: {profile.experiences.all()}")
    if profile.experiences.exists():
        for exp in profile.experiences.all():
            print("Experience:", exp)
            right_data.append(Paragraph(f"• {exp.position} at {exp.company_name}", small))
            right_data.append(Paragraph(f"• Duration: {exp.start_date} to {exp.end_date or 'Present'}", small))
            right_data.append(Paragraph(f"• Description: {exp.description}", small))
    else:
        right_data.append(Paragraph("No work experiences listed.", small))


    # ---- Build the table ----
    table = Table(
        [[left_data, right_data]],
        colWidths=[left_col_width, right_col_width],
    )
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f0f0f0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0,0), (0,0), 20),
        ('RIGHTPADDING', (0,0), (0,0), 10),
        ('LEFTPADDING', (1,0), (1,0), 20),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Add gridlines for table cells
    ]))

    elements.append(table)

    # ==== Save to buffer ====
    doc.build(elements)
    buffer.seek(0)
    return buffer



def error_page(request):
    return render(request , 'error.html')


# Generate a random temporary password
def generate_temp_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def change_password_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')

        user = request.user

        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Keep user logged in after password change
            messages.success(request, "Password changed successfully!" , extra_tags= "change_password_tags")
            return redirect('settings')  # or wherever you want
        else:
            messages.error(request, "Old password is incorrect." , extra_tags= "change_password_tags")

    return render(request, 'change_password.html')




def forgot_password(request):
    context = {
        'error': None,
        'success': None,
        'temp_password_sent': False,
        'email': '',
    }

    if request.method == "POST":
        if 'send_temp_password' in request.POST:
            email = request.POST.get("email")
            user = CustomUser.objects.filter(email=email).first()

            if user:
                temp_pass = generate_temp_password()
                request.session['temp_pass'] = temp_pass
                request.session['reset_email'] = email
                request.session.set_expiry(300)

                send_mail(
                    "Your Temporary Password",
                    f"Use this temporary password to reset your password: {temp_pass}",
                    "noreply@jobify.com",
                    [email],
                )
                context['temp_password_sent'] = True
                context['email'] = email
            else:
                context['error'] = "No account found with this email address."

        elif 'reset_password' in request.POST:
            temp_password = request.POST.get("temp_password")
            new_password = request.POST.get("new_password")

            session_temp_pass = request.session.get('temp_pass')
            email = request.session.get('reset_email')

            if not (session_temp_pass and email):
                context['error'] = "Session expired. Please try again."
            elif session_temp_pass != temp_password:
                context['error'] = "Invalid temporary password."
            else:
                try:
                    user = CustomUser.objects.get(email=email)
                    user.set_password(new_password)
                    user.save()
                    context['success'] = "Password reset successfully. You can now log in."
                    # clear session keys
                    request.session.pop('temp_pass', None)
                    request.session.pop('reset_email', None)
                except CustomUser.DoesNotExist:
                    context['error'] = "User not found."

    return render(request, "forgot_reset_password.html", context)


def delete_account(request):
    try:
        user = request.user
        # Optionally, you can delete associated data like profile, job applications, etc.
        user.delete()  # Deletes the user account
        messages.success(request, "Your account has been successfully deleted.")
        return redirect('goodbye')  # Redirect to home or login page after deletion
    except Exception as e:
        messages.error(request, f"An error occurred while deleting your account: {str(e)}")
        return redirect('profile')

def goodbye_view(request):
    return render(request, 'good_bye.html') 



def admin_dashboard_view(request):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('login')

    # Date range for the last 30 days
    today = timezone.now()
    last_30_days = today - timedelta(days=30)
    last_30_days_range = [today - timedelta(days=i) for i in range(30)]
    # pastel_colors = ['#AEC6CF', '#F7A7B2', '#FFB7B2']
    pastel_colors = [
        "#BAE1FF",  # Light Blue
        "#E0BBE4",  # Light Purple
        "#D5AAFF",  # Lavender
        "#FFFFBA",  # Light Yellow
        "#FFDFBA",  # Light Orange
        "#BAFFC9",  # Light Green
        "#C2F0C2",  # Mint
        "#FFD1DC",  # Pink
        "#B5EAD7",  # Aqua
        "#FFB3BA",  # Light Pink
        ]

    # 1. Total Jobs and Applications in last 30 days
    total_jobs = Job.objects.filter(created_at__gte=last_30_days).count()
    total_applications = Application.objects.filter(applied_at__gte=last_30_days).count()

    # 2. Job Applications by Status (Approved, Pending, Rejected)
    # Human-readable status mapping
    STATUS_DISPLAY_MAPPING = {
        'pending': 'Pending',
        'review': 'In Review',
        'shortlisted': 'Shortlisted',
        'rejected': 'Rejected',
        'accepted': 'Approved'
    }

    # # Get status counts across all job applications
    # status_counts = Application.objects.values('status').annotate(count=Count('id'))

    # # Build graph data
    # job_status_graph_data = {
    #     'status': [STATUS_DISPLAY_MAPPING.get(item['status'], item['status']) for item in status_counts],
    #     'count': [item['count'] for item in status_counts],
    # }

    # # Generate Plotly bar chart
    # job_status_fig = px.bar(
    #     job_status_graph_data,
    #     x='status',
    #     y='count',
    #     title="Application Status Breakdown (All Jobs)",
    #     color='status',
    #     color_discrete_sequence=pastel_colors
    # )


    work_location_data = Application.objects.values('job__work_location_type') \
        .annotate(count=Count('id')) \
        .order_by('-count')

    location_labels = [item['job__work_location_type'].capitalize() for item in work_location_data]
    location_counts = [item['count'] for item in work_location_data]

    location_fig = px.pie(
        names=location_labels,
        values=location_counts,
        title="Applications by Work Location Type",
        color_discrete_sequence=pastel_colors,
        hole=0.5  # donut-style
    )

    # 4. User Activity Reports (New Users)
    new_users = CustomUser.objects.filter(date_joined__gte=last_30_days).count()
    new_seekers = CustomUser.objects.filter(user_type='job_seeker', date_joined__gte=last_30_days).count()
    new_employers = CustomUser.objects.filter(user_type='company', date_joined__gte=last_30_days).count()

    # 5. Most Applied Jobs
    # most_applied_jobs = Job.objects.annotate(application_count=Count('applications')).order_by('-application_count')[:5]
    # most_applied_jobs_data = {
    #     'job_title': [job.title for job in most_applied_jobs],
    #     'applications': [job.application_count for job in most_applied_jobs],
    # }

    # # Create most applied jobs bar chart with pastel colors
    # most_applied_jobs_fig = px.bar(most_applied_jobs_data, x='job_title', y='applications', title="Most Applied Jobs", 
    #                                color='job_title', color_discrete_sequence=pastel_colors)

    # Get language counts
    language_counts = Job.objects.values('job_language').annotate(count=Count('id')).order_by('-count')

    # Mapping from value to label
    LANGUAGE_DISPLAY_MAPPING = dict(Job.LANGUAGE_CHOICES)

    # Prepare data
    language_chart_data = {
        'language': [LANGUAGE_DISPLAY_MAPPING.get(item['job_language'], item['job_language']) for item in language_counts],
        'count': [item['count'] for item in language_counts],
    }

    # Build Plotly Bar Chart
    language_fig = px.bar(
        language_chart_data,
        x='language',
        y='count',
        title="Jobs by Required Language",
        color='language',
        color_discrete_sequence=pastel_colors
    )

    # 7. Top Job Categories
    category_stats = Job.objects.values('job_type').annotate(
        total_jobs=Count('id'),
        total_applications=Count('applications')
    )
    category_stats_data = {
        'category': [stat['job_type'] for stat in category_stats],
        'jobs': [stat['total_jobs'] for stat in category_stats],
        'applications': [stat['total_applications'] for stat in category_stats],
    }
    # Create top job categories bar chart with pastel colors
    category_stats_fig = px.bar(category_stats_data, x='category', y=['jobs', 'applications'], title="Top Job Categories", 
                                color_discrete_sequence=pastel_colors)

    # 8. Salary Insights (Salary Distribution)
    salary_data = Job.objects.values('salary').annotate(salary_count=Count('id'))
    salary_distribution_data = {
        'salary': [entry['salary'] for entry in salary_data],
        'count': [entry['salary_count'] for entry in salary_data],
    }
    # Create salary distribution histogram with pastel colors
    salary_distribution_fig = px.histogram(salary_distribution_data, x='salary', y='count', title="Salary Distribution", 
                                           color_discrete_sequence=pastel_colors)

    # 9. Applications Over Time (Daily or Weekly)
    applications_over_time = Application.objects.filter(applied_at__gte=last_30_days) \
                                                .values('applied_at__date') \
                                                .annotate(count=Count('id')) \
                                                .order_by('applied_at__date')
    applications_time_data = {
        'date': [app['applied_at__date'] for app in applications_over_time],
        'applications_count': [app['count'] for app in applications_over_time],
    }
    # Create applications over time line chart with pastel colors
    applications_time_fig = px.line(applications_time_data, x='date', y='applications_count', title="Applications Over Time", 
                                    line_shape="linear", markers=True, color_discrete_sequence=pastel_colors)

    # Group jobs by month and count
    jobs_over_time = (
        Job.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # Prepare data
    time_data = {
        'month': [item['month'].strftime('%B %Y') for item in jobs_over_time],
        'count': [item['count'] for item in jobs_over_time],
    }

    # Create line chart
    jobs_time_fig = px.line(
        time_data,
        x='month',
        y='count',
        title="Jobs Posted Over Time",
        markers=dict(colors=pastel_colors),
        line_shape='linear'
    )
    # Step 1: Aggregate job seekers by country
    country_counts = (
        JobSeekerProfile.objects
        .values('address__country')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Step 2: Prepare chart data
    country_data = {
        'country': [entry['address__country'] or 'Unknown' for entry in country_counts],
        'count': [entry['count'] for entry in country_counts],
    }

    # Step 3: Generate pie chart
    job_seeker_country_fig = px.pie(
        country_data,
        names='country',
        values='count',
        title='Job Seekers by Country',
        hole=0.4,  # donut style
        color_discrete_sequence=pastel_colors
    )
    # Step 1: Aggregate companies by industry
    industry_counts = (
        Company.objects
        .values('industry')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Step 2: Prepare chart data
    industry_data = {
        'industry': [entry['industry'] or 'Unknown' for entry in industry_counts],
        'count': [entry['count'] for entry in industry_counts],
    }


    # Step 3: Generate horizontal bar chart
    company_industry_fig = px.bar(
        industry_data,
        x='count',
        y='industry',
        orientation='h',
        title='Companies by Industry',
        color='industry',
        color_discrete_sequence=pastel_colors
    )

    company_industry_fig.update_layout(
        yaxis_title='Industry',
        xaxis_title='Number of Companies',
        plot_bgcolor='white',
        margin=dict(l=80, r=30, t=50, b=50),
        height=400
    )

    # Step 1: Aggregate company counts by founded year
    founded_year_counts = (
        Company.objects
        .values('founded')
        .annotate(count=Count('id'))
        .order_by('founded')
    )

    # Step 2: Prepare chart data
    founded_data = {
        'Year Founded': [entry['founded'] for entry in founded_year_counts],
        'Company Count': [entry['count'] for entry in founded_year_counts],
    }


    # Step 3: Create a bar chart
    company_founded_fig = px.bar(
        founded_data,
        x='Year Founded',
        y='Company Count',
        title='Company Registrations Over the Years',
        color='Company Count',
        color_continuous_scale=pastel_colors,
        template='plotly_white'
    )

    # Optional: Customize layout
    company_founded_fig.update_layout(
        xaxis_title='Founded Year',
        yaxis_title='Number of Companies',
        title_font_size=22,
        title_font_family='Arial',
        bargap=0.2,
    )

    # Query data
    size_counts = Company.objects.values('company_size').annotate(count=Count('id'))

    labels = [entry['company_size'] for entry in size_counts]
    values = [entry['count'] for entry in size_counts]

    # Define donut chart
    company_size_fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.5,  # Donut style
        marker=dict(colors=pastel_colors),
        textinfo='percent+label'
    )])

    company_size_fig.update_layout(
        title='Company Size Distribution',
        margin=dict(t=40, b=0, l=0, r=0),
        height=400
    )

    # Aggregate count of companies per country from headquarters_address
    headquarters_location = (
        Company.objects
        .values('headquarters_address__country')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    countries = [entry['headquarters_address__country'] for entry in headquarters_location]
    counts = [entry['count'] for entry in headquarters_location]

    # Create choropleth map
    headquarters_location_fig = px.choropleth(
        locations=countries,
        locationmode="country names",
        color=counts,
        hover_name=countries,
        color_continuous_scale=pastel_colors,
        title="Company Headquarters Distribution by Country",
    )

    headquarters_location_fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        margin=dict(t=40, b=0, l=0, r=0),
        height=500
    )

    activity_data = []
    for date in last_30_days_range:
        active_users_count = CustomUser.objects.filter(last_login__gte=date, last_login__lt=date + timedelta(days=1)).count()
        activity_data.append({'date': date.date(), 'active_users': active_users_count})

    # Create a DataFrame for plotting
    dates = [entry['date'] for entry in activity_data]
    active_users = [entry['active_users'] for entry in activity_data]

    # Create a line chart to display active users per day
    activity_fig = px.line(
        x=dates,
        y=active_users,
        labels={'x': 'Date', 'y': 'Active Users'},
        title="User Activity Based on Last Login (Last 30 Days)"
    )

    activity_fig.update_layout(
        height=500,
        margin=dict(t=40, b=30, l=40, r=40),
        xaxis_title='Date',
        yaxis_title='Active Users',
        xaxis_tickformat='%Y-%m-%d'
    )

    user_joined_data = []
    for date in last_30_days_range:
        users_count = CustomUser.objects.filter(date_joined__gte=date, date_joined__lt=date + timedelta(days=1)).count()
        user_joined_data.append({'date': date, 'users_joined': users_count})

    # Create scatter plot data
    dates = [entry['date'] for entry in user_joined_data]
    users_joined = [entry['users_joined'] for entry in user_joined_data]

    # Create scatter plot
    user_joined_fig = px.scatter(
        x=dates,
        y=users_joined,
        labels={'x': 'Date', 'y': 'Users Joined'},
        title="User Join Data (Last 30 Days)",

    )

    user_joined_fig.update_layout(
        height=500,
        margin=dict(t=40, b=30, l=40, r=40),
        xaxis_title='Date',
        yaxis_title='Users Joined',
        xaxis_tickformat='%Y-%m-%d',
    )
    user_joined_fig.update_traces(mode='markers+lines', marker=dict(size=8, color=pastel_colors[4]))

    # Count phone verified vs unverified users
    verified_count = CustomUser.objects.filter(is_phone_verified=True).count()
    unverified_count = CustomUser.objects.filter(is_phone_verified=False).count()

    # Prepare data
    labels = ['Phone Verified', 'Not Verified']
    values = [verified_count, unverified_count]

    # Create donut chart
    phone_verification_fig = px.pie(
        names=labels,
        values=values,
        hole=0.4,  # donut style
        title="Phone Verification Status of Users",
        color_discrete_sequence=['#10B981', '#EF4444']  # Tailwind green & red
    )

    phone_verification_fig.update_layout(
        height=450,
        margin=dict(t=40, b=30, l=40, r=40),
        showlegend=True
    )

    # Step 1: Get counts of users per education level
    education_counts = Education.objects.values('level').annotate(count=Count('id')).order_by('-count')

    # Step 2: Map DB values to display labels
    EDUCATION_DISPLAY_MAPPING = dict(Education.LEVEL_CHOICES)

    # Step 3: Prepare data dictionary
    education_chart_data = {
        'education_level': [EDUCATION_DISPLAY_MAPPING.get(item['level'], item['level']) for item in education_counts],
        'count': [item['count'] for item in education_counts],
    }

    # Step 4: Create scatter plot
    education_level_fig = px.scatter(
        education_chart_data,
        x='education_level',
        y='count',
        title="Users by Education Level (Scatter)",
        color='education_level',
        size='count',  # Bubbles sized by user count
        color_discrete_sequence=pastel_colors
    )

    # Step 5: Layout cleanup (optional)
    education_level_fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_title='Education Level',
        yaxis_title='Number of Users',
        showlegend=False
    )
    # Step 1: Get counts of users per field of study
    field_counts = Education.objects.values('field').annotate(count=Count('id')).order_by('-count')

    # Step 2: Map DB values to display labels (if applicable, you can adjust this)
    FIELD_DISPLAY_MAPPING = dict(Education.FIELD_CHOICES)  # Add a dictionary if you need to map field codes to display names, e.g.
    # FIELD_DISPLAY_MAPPING = {'IT': 'Information Technology', 'ENG': 'Engineering'}

    # Step 3: Prepare data dictionary
    field_chart_data = {
        'field_of_study': [FIELD_DISPLAY_MAPPING.get(item['field'], item['field']) for item in field_counts],
        'count': [item['count'] for item in field_counts],
    }

    # Step 4: Create scatter plot
    field_of_study_fig = px.scatter(
        field_chart_data,
        x='field_of_study',
        y='count',
        title="Users by Field of Study (Scatter)",
        color='field_of_study',
        size='count',  # Bubbles sized by user count
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    # Step 5: Layout cleanup (optional)
    field_of_study_fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_title='Field of Study',
        yaxis_title='Number of Users',
        showlegend=False
    )

    # Aggregate payment data by company
    payment_data = JobPayment.objects.values('job__company__name') \
        .annotate(total_payment=Sum('payment_amount')) \
        .order_by('-total_payment')

    # Prepare data for the bubble chart
    company_names = [item['job__company__name'] for item in payment_data]
    total_payments = [item['total_payment'] for item in payment_data]

    # Ensure total_payments is a list of numeric values (if it's not already)
    total_payments = [float(payment) for payment in total_payments]

    # Create the Bubble Chart
    payment_fig = px.scatter(
        x=company_names,
        y=total_payments,
        size=total_payments,  # Using total_payment to determine bubble size
        title="Total Payments Received by Company",
        labels={'x': 'Company', 'y': 'Total Payment Amount'},
        hover_name=company_names,
        size_max=50,  # Adjust bubble size max limit
        color=total_payments,  # Color by payment amount
        color_continuous_scale='Viridis'  # You can change the color scale
    )



    # Convert Plotly figures to HTML for rendering
    # job_status_graph = job_status_fig.to_html(full_html=False)
    # most_applied_jobs_graph = most_applied_jobs_fig.to_html(full_html=False)
    work_location_chart = location_fig.to_html(full_html=False)
    category_stats_graph = category_stats_fig.to_html(full_html=False)
    salary_distribution_graph = salary_distribution_fig.to_html(full_html=False)
    applications_time_graph = applications_time_fig.to_html(full_html=False)
    job_language_graph = language_fig.to_html(full_html=False)
    jobs_over_time_graph = jobs_time_fig.to_html(full_html=False)
    job_seeker_address_graph = job_seeker_country_fig.to_html(full_html=False)
    company_industry_graph = company_industry_fig.to_html(full_html=False)
    company_founded_graph = company_founded_fig.to_html(full_html=False)
    company_size_graph = company_size_fig.to_html(full_html=False)
    company_headquarters_graph = headquarters_location_fig.to_html(full_html=False)
    user_activity_graph = activity_fig.to_html(full_html=False)
    user_joined_graph = user_joined_fig.to_html(full_html=False)
    user_phone_verification_graph = phone_verification_fig.to_html(full_html=False)
    fig = px.bar(x=["A", "B", "C"], y=[10, 20, 30])
    simple_graph = fig.to_html(full_html=False)
    job_seeker_education_level_graph = education_level_fig.to_html(full_html=False)
    job_seeker_field_of_study_graph = field_of_study_fig.to_html(full_html=False)
    payment_graph = payment_fig.to_html(full_html=False)
    # Prepare context for rendering
    context = {
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'new_users': new_users,
        'new_seekers': new_seekers,
        'new_employers': new_employers,
        # 'job_status_graph': job_status_graph,
        # 'most_applied_jobs_graph': most_applied_jobs_graph,
        'category_stats_graph': category_stats_graph,
        'salary_distribution_graph': salary_distribution_graph,
        'applications_time_graph': applications_time_graph,
        'work_location_chart': work_location_chart,
        'job_language_graph' : job_language_graph,
        'jobs_over_time_graph' : jobs_over_time_graph,
        'job_seeker_address_graph' : job_seeker_address_graph,
        'company_industry_graph' : company_industry_graph,
        'company_founded_graph' : company_founded_graph,
        'company_size_graph' : company_size_graph,
        'company_headquarters_graph' : company_headquarters_graph,
        'user_activity_graph' : user_activity_graph,
        'user_joined_graph' : user_joined_graph,
        'user_phone_verification_graph' : user_phone_verification_graph,
        'job_seeker_education_level_graph' : job_seeker_education_level_graph,
        'job_seeker_field_of_study_graph' : job_seeker_field_of_study_graph,
        'payment_graph' : payment_graph,
        'user' : user
    }

    return render(request, 'admin/dashboard.html', context)


def all_users_by_type(request):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('login')
    
    job_seekers = JobSeekerProfile.objects.all()
    employers = CompanyPerson.objects.all()

    return render(request, 'admin/all_users.html', {
        'job_seekers': job_seekers,
        'employers': employers,
        'user' : user
    })

def delete_user(request, user_id):
    user = request.user
    if not user.is_authenticated and not user.is_superuser:
        messages.error(request, "Unauthorized access.")
        return redirect('admin_dashboard')  # Replace with your admin dashboard view name

    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    messages.success(request, "User has been deleted.")
    return redirect('manage_users')


def company_report_view(request):
    user = request.user

    if user.is_authenticated and user.user_type == "company_person":
        pastel_colors = ["#FFB3BA",  # Light Pink
        "#FFDFBA",  # Light Orange
        "#FFFFBA",  # Light Yellow
        "#BAFFC9",  # Light Green
        "#BAE1FF",  # Light Blue
        "#E0BBE4",  # Light Purple
        "#D5AAFF",  # Lavender
        "#C2F0C2",  # Mint
        "#FFD1DC",  # Pink
        "#B5EAD7",  # Aqua
        ]

        today = timezone.now()
        last_30_days = today - timedelta(days=30)

        # Get the company linked to the logged-in user
        company_person = CompanyPerson.objects.get(user=request.user)
        company = company_person.company
        company_person_full_name = company_person.user.get_full_name()
        # Filter company jobs
        company_jobs = Job.objects.filter(company=company)

        # 1. Total Jobs and Applications in last 30 days
        total_jobs = company_jobs.filter(created_at__gte=last_30_days).count()
        total_applications = Application.objects.filter(job__in=company_jobs, applied_at__gte=last_30_days).count()

        # 2. Job Applications by Status
        status_counts = Application.objects.filter(job__in=company_jobs).values('status').annotate(count=Count('id'))
        status_dict = {status['status']: status['count'] for status in status_counts}

        # Application status mapping
        STATUS_DISPLAY_MAPPING = {
            'pending': 'Pending',
            'review': 'In Review',
            'shortlisted': 'Shortlisted',
            'rejected': 'Rejected',
            'accepted': 'Approved'
        }

        # 2. Job Applications by Status (actual values from DB)
        status_counts = Application.objects.filter(job__in=company_jobs).values('status').annotate(count=Count('id'))

        # Debug: print what statuses are returned
        print("Status counts:", list(status_counts))

        # Build graph data using mapping (only include statuses present in DB)
        job_status_graph_data = {
            'status': [STATUS_DISPLAY_MAPPING.get(item['status'], item['status']) for item in status_counts],
            'count': [item['count'] for item in status_counts],
        }

        # Build Plotly graph
        job_status_fig = px.bar(
            job_status_graph_data,
            x='status',
            y='count',
            title="Application Status Breakdown",
            color='status',
            color_discrete_sequence=pastel_colors
        )

        # 4. Hiring Progress (People Needed vs Applications Received)
        hiring_progress = Job.objects.annotate(
            people_needed_int=Cast('number_of_people', IntegerField()),
            applications_received_int=Cast('current_applicants', IntegerField()),
            progress=Cast('current_applicants', IntegerField()) * 100.0 / Cast('number_of_people', IntegerField())
        )
        # 3. Most Applied Jobs
        most_applied_jobs = company_jobs.annotate(application_count=Count('applications')).order_by('-application_count')[:5]
        most_applied_jobs_data = {
            'job_title': [job.title for job in most_applied_jobs],
            'applications': [job.application_count for job in most_applied_jobs],
        }
        most_applied_jobs_fig = px.bar(most_applied_jobs_data, x='job_title', y='applications', title="Most Applied Jobs")

        hiring_progress_data = {
            'job_title': [job.title for job in hiring_progress],
            'people_needed': [job.people_needed_int for job in hiring_progress],
            'applications': [job.applications_received_int for job in hiring_progress],
        }

        hiring_progress_fig = px.bar(
            hiring_progress_data,
            x='job_title',
            y=['people_needed', 'applications'],
            barmode='group',
            title="Hiring Progress (Applications vs Required)"
        )



        # 5. Payments Made by the Company
        payments = JobPayment.objects.filter(
            payer_id=company_person.id,  # or request.user if company is on user
            created_at__gte=last_30_days
        )

        payments_data = payments.annotate(date=TruncDate('created_at')) \
                                .values('date') \
                                .annotate(total=Sum('payment_amount')) \
                                .order_by('date')

        payments_made_data = {
            'date': [entry['date'] for entry in payments_data],
            'total': [entry['total'] for entry in payments_data],
        }

        payments_made_fig = px.bar(
            payments_made_data,
            x='date',
            y='total',
            title="Your Company Payments (Last 30 Days)"
        )


        # Applications over time (all company jobs)
        applications_by_date = Application.objects.filter(
            job__in=company_jobs
        ).annotate(
            date=TruncDate('applied_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # Prepare data for plotly
        applications_over_time_data = {
            'date': [entry['date'] for entry in applications_by_date],
            'applications': [entry['count'] for entry in applications_by_date],
        }

        # Plot
        applications_over_time_fig = px.line(
            applications_over_time_data,
            x='date',
            y='applications',
            title="Applications Over Time",
            markers=True,
            line_shape="linear"
        )


        hiring_team = company.persons.all()
        # Convert Plotly figures to HTML
        job_status_graph = job_status_fig.to_html(full_html=False)
        most_applied_jobs_graph = most_applied_jobs_fig.to_html(full_html=False)
        hiring_progress_graph = hiring_progress_fig.to_html(full_html=False)
        payments_made_graph = payments_made_fig.to_html(full_html=False)
        applications_over_time_graph = applications_over_time_fig.to_html(full_html=False)

        is_external = False
        profile_picture = company.user.profile_picture
        profile_picture_url = str(profile_picture) if profile_picture else ""
        if profile_picture_url and (profile_picture_url.startswith('http://') or profile_picture_url.startswith('https://')):
            print(profile_picture_url)
            is_external = True
        else:
        
            is_external = False

        print("[DEBUG] Status :  " , status_dict)

        context = {
            'total_jobs': total_jobs,
            'total_applications': total_applications,
            'job_status_graph': job_status_graph,
            'most_applied_jobs_graph': most_applied_jobs_graph,
            'hiring_progress_graph': hiring_progress_graph,
            'payments_made_graph': payments_made_graph,
            'company' : company, 
            'company_person' : company_person,
            'company_person_full_name' : company_person_full_name, 
            'is_external' : is_external,
            'hiring_team' : hiring_team,
            'applications_over_time_graph' : applications_over_time_graph
  
        }

        return render(request, 'company/company_reports.html', context)

    return redirect('login')