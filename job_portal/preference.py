import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def ai_score_jobs(jobs_data, seeker_profile):
    results = []

    # Filter out jobs that are already full
    jobs_data = [job for job in jobs_data if not job.is_full()]

    # Combine preference-based textual fields from the JobSeekerProfile model
    user_pref_text = ' '.join([
        seeker_profile.desired_position or '',
        seeker_profile.skills or '',
        seeker_profile.job_type or '',
        seeker_profile.location_preference or '',
        seeker_profile.onsite_location or '',
    ])

    # Prepare TF-IDF corpus for job descriptions and related information from the Job model
    job_texts = []
    for job in jobs_data:
        job_texts.append(' '.join([
            job.title,
            job.description,
            job.job_location.address if job.job_location else '',
            job.job_type,
        ]))

    if not job_texts:
        return []  # Return empty list if no jobs to score

    # TF-IDF + Cosine similarity to compute similarity between user preferences and job details
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([user_pref_text] + job_texts)
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    # Attach scores to jobs based on similarity and additional factors
    for job, similarity_score in zip(jobs_data, similarities):
        score = similarity_score

        # Bonus for salary match
        if seeker_profile.expected_salary and job.salary:
            if job.salary >= seeker_profile.expected_salary:
                score += 0.2

        # Bonus for relocation match
        if seeker_profile.relocation and seeker_profile.relocation.lower() == 'yes':
            if job.work_location_type != 'remote':
                score += 0.2
        elif seeker_profile.relocation and seeker_profile.relocation.lower() == 'no':
            if job.work_location_type == 'remote':
                score += 0.2

        # Bonus for location preference match
        if seeker_profile.location_preference and seeker_profile.location_preference == job.work_location_type:
            score += 0.2

        results.append((job, score))

    # Sort jobs by combined score in descending order
    results.sort(key=lambda x: x[1], reverse=True)

    return [job for job, score in results]
