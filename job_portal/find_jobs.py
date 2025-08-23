import numpy as np
from django.db.models import Q
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Job


def enhanced_job_recommendation(query_text, query_salary, jobs_data, weight_text=0.85, weight_salary=0.15):
    if not jobs_data:
        return []

    job_texts = [
        " ".join([
            job.get('title', ''),
            job.get('description', ''),
            job.get('job_type', ''),
            job.get('job_language', ''),
            job.get('company_name', '')
        ])
        for job in jobs_data
    ]

    # Combine the query and job texts
    corpus = [query_text] + job_texts

    # TF-IDF for semantic relevance
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(corpus)
    query_vector = tfidf_matrix[0]
    job_vectors = tfidf_matrix[1:]

    # Textual similarity (cosine)
    text_similarities = cosine_similarity(query_vector, job_vectors).flatten()

    # Salary similarity (smaller difference = better match)
    job_salaries = np.array([
        float(job.get('salary', 0) or 0) for job in jobs_data
    ])
    salary_diffs = np.abs(job_salaries - float(query_salary))
    max_diff = salary_diffs.max() if salary_diffs.max() != 0 else 1
    salary_similarities = 1 - (salary_diffs / max_diff)

    # Combined weighted score
    final_scores = weight_text * text_similarities + weight_salary * salary_similarities

    # Attach scores and sort
    scored_jobs = [
        {**job, 'score': round(score, 4)}
        for job, score in zip(jobs_data, final_scores)
    ]
    scored_jobs.sort(key=lambda x: x['score'], reverse=True)

    return scored_jobs



def build_job_dict_list(jobs_queryset):
    job_dict_list = []
    for job in jobs_queryset:
        job_dict = {
            'id': job.id,
            'title': job.title,
            'description': job.description[:200] + '...' if len(job.description) > 200 else job.description,
            'job_type': job.get_job_type_display(),
            'job_language': job.get_job_language_display(),
            'salary': job.salary,
            'work_location_type': job.get_work_location_type_display(),
            "company": {
                    "name": job.company.name,
                    "description": job.company.description,
                    "website": job.company.website,
                    "industry": job.company.industry,
                    "tagline": job.company.tagline,
                    "linkedin_profile": job.company.linkedin_profile,
                    "registration_number": job.company.registration_number,
                    "business_license": job.company.business_license.url if job.company.business_license else '',
                    "company_policy_link": job.company.company_policy_link,
                    "founded": job.company.founded,
                    "company_size": job.company.company_size,
                    "headquarters_address": {
                        "address": job.company.headquarters_address.street_address,
                        "city": job.company.headquarters_address.city,
                        "state": job.company.headquarters_address.state,
                        "country": job.company.headquarters_address.country
                    } if job.company.headquarters_address else None,
                    "locations": [
                        {
                            "address": loc.address,
                            "city": loc.city,
                            "state": loc.state,
                            "country": loc.country
                        }
                        for loc in job.company.company_locations.all()
                    ]
                },
            
            'location': job.job_location.city if job.job_location else 'N/A',
            'experience_required': job.experience_required,
            'posted_by': f"{job.posted_by.user.first_name} {job.posted_by.user.last_name}" if job.posted_by else 'N/A',
            'application_deadline': job.application_deadline.strftime('%Y-%m-%d') if job.application_deadline else 'N/A',
            'created_at': job.created_at.strftime('%Y-%m-%d'),
            'is_full': job.is_full(),
            # Convert CSV to list by splitting by comma
            "requirements": job.get_requirements(),

            "custom_questions": [
                    {"question": question.strip()}
                    for question in job.additional_questions.split(",")
                ] if job.additional_questions else [],
        }
        job_dict_list.append(job_dict)
    return job_dict_list

def get_jobs_by_search_term(search_term):
    return Job.objects.select_related('company').filter(
        Q(title__icontains=search_term) |
        Q(description__icontains=search_term) |
        Q(company__name__icontains=search_term) |
        Q(job_type__icontains=search_term) |
        Q(job_language__icontains=search_term)
    )

def get_jobs_by_profile(seeker_profile):
    return Job.objects.all()  # You can later add filters based on seeker prefs

def get_ai_recommendations(seeker_profile, search_term=None):
    query_salary = seeker_profile.expected_salary or 0

    seeker_query_text = " ".join([
        seeker_profile.skills or '',
        seeker_profile.desired_position or '',
        seeker_profile.about or '',
    ]).strip()

    jobs_qs = Job.objects.all()
    jobs_data = build_job_dict_list(jobs_qs)

    # 1. If search term, prioritize search-based jobs
    if search_term:
        search_matches = enhanced_job_recommendation(search_term, query_salary, jobs_data)
    else:
        search_matches = []

    # 2. Then profile-based
    profile_matches = enhanced_job_recommendation(seeker_query_text, query_salary, jobs_data)

    # 3. Merge logic
    job_ids_added = set()
    result = {
        "highly_recommended": [],
        "matching_search": [],
        "matching_profile": [],
        "all_jobs": [],
    }


    for job in search_matches[:5]:
        if job['id'] not in job_ids_added:
            result["matching_search"].append(job)
            job_ids_added.add(job['id'])

    for job in profile_matches[:5]:
        if job['id'] not in job_ids_added:
            result["matching_profile"].append(job)
            job_ids_added.add(job['id'])

    for job in (search_matches + profile_matches):
        if job['id'] not in job_ids_added:
            result["highly_recommended"].append(job)
            job_ids_added.add(job['id'])

    for job in jobs_data:
        if job['id'] not in job_ids_added:
            result["all_jobs"].append(job)

    return result