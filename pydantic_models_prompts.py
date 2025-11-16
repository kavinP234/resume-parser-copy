from typing import List, Optional
from pydantic import BaseModel, Field
import json

# --------------------------------------------------------------------------------------------------------------- #
# Basic Info model and prompts
class BasicInfo(BaseModel):
    name: str = Field(description="name of the candidate")
    bio: str = Field(description="Bio, profile, introduction or summary of the candidate")
    job_title: str = Field(description="current or latest job title of the candidate")
    location: Optional[str] = Field(description="location of the candidate")
    phone: Optional[str] = Field(description="phone number of the candidate")


def get_basic_info_format_instructions():
    return """Return a JSON object with the following structure:
{
    "name": "string",
    "bio": "string", 
    "job_title": "string",
    "location": "string (optional)",
    "phone": "string (optional)"
}"""


basic_details_prompt = f"""
Extract the basic information from the resume and return as JSON with the following structure:
{get_basic_info_format_instructions()}

Resume:
{{resume}}
"""


fallback_basic_info_prompt = """
What is the {query}?
RESUME:
{resume}
ANSWER:
"""


# --------------------------------------------------------------------------------------------------------------- #
# Work Experience model and prompts
class WorkExperience(BaseModel):
    """Work experiences"""
    company_name: str = Field(description="name of the company")
    job_title: str = Field(description="job title")
    start_date: str = Field(description="start date, if not present use 'None'")
    end_date: str = Field(description="end date, if not present use 'None'")
    description: Optional[str] = Field(description="description, if not present use 'None' ")


class SingleWorkExperience(BaseModel):
    """Work experiences"""
    company_name: str = Field(description="name of the company")
    job_title: str = Field(description="job title")
    start_date: str = Field(description="start date, if not present use 'None'")
    end_date: str = Field(description="end date, if not present use 'None'")
    description: Optional[str] = Field(description="description, if not present use 'None' ")


def get_work_experience_format_instructions():
    return """Return a JSON object with the following structure:
{
    "company_name": "string",
    "job_title": "string",
    "start_date": "string",
    "end_date": "string", 
    "description": "string (optional)"
}"""


work_experience_template = f"""
What was this person work experience at {{company}} as a {{role}}?

RESUME:
{{resume}}

{get_work_experience_format_instructions()}
"""


companies_prompt = """
What companies did this candidate work at and what was their job title? Only use the resume to answer, do not make up answers. Use the template to format the answer:

TEMPLATE:
company 1, job title 1
company 2, job title 2
company 3, job title 3

RESUME:
{resume}

ANSWER:
"""


# --------------------------------------------------------------------------------------------------------------- #
# Skills and other info model and prompts
class Skills(BaseModel):
    skills: List[str] = Field(description="list of skills, programming languages, IT tools, software skills")
    professional_development: Optional[List[str]] = Field(
        description="list of professional certifications that are not related to university degrees. Include research publications, awards, open source contributions or patents if any. Only extract answers from the resume, do not make up answers")
    other: Optional[List[str]] = Field(
        description="language skills, interests, hobbies, extra-curricular activities. Only extract answers from the resume, do not make up answers")


def get_skills_format_instructions():
    return """Return a JSON object with the following structure:
{
    "skills": ["list", "of", "skills"],
    "professional_development": ["list", "of", "certifications", "awards"],
    "other": ["list", "of", "languages", "hobbies"]
}"""


skills_template = f"""
Extract the information:

* Skills section contains technical skills, programming languages, IT tools, software skills.
* Professional development section contains the list of certifications other than university degrees, research publications, awards, open source contributions or patents.
* Other section is for language skills, interests, hobbies, extra-curricular activities.

Only extract answers from the resume, do not make up answers.

RESUME:
{{resume}}

{get_skills_format_instructions()}
"""


fallback_skills_prompt = """
What are the skills in this resume?
RESUME:
{resume}

Answer with a comma separated list.
"""


# --------------------------------------------------------------------------------------------------------------- #
# Education model and prompts
class Education(BaseModel):
    """Education qualification"""
    qualification: str = Field(description="university or high-school education qualification or degree")
    establishment: Optional[str] = Field(description="establishment where the qualification was obtained")
    country: Optional[str] = Field(description="country where the qualification was obtained")
    year: Optional[str] = Field(description="year when the qualification was obtained")


def get_education_format_instructions():
    return """Return a JSON array of education objects with the following structure:
[
    {{
        "qualification": "string",
        "establishment": "string (optional)",
        "country": "string (optional)",
        "year": "string (optional)"
    }}
]"""


# Prompt Template to extract education degrees in a structured output
fallback_education_prompt = """
What are the university education degrees? Use the template to format the answer. Only use the resume to answer, do not make up answers. If there is no education mentioned in the resume, just answer with 'None'

TEMPLATE:
Qualification, Name of establishment, Country (if applicable), Year
Qualification, Name of establishment, Country (if applicable), Year

RESUME:
{resume}

ANSWER:
"""


# --------------------------------------------------------------------------------------------------------------- #
# Simple prompt functions that return formatted strings
def create_basic_details_prompt(resume_text):
    return f"""
Extract the basic information from the resume and return as JSON with the following structure:
{get_basic_info_format_instructions()}

Resume:
{resume_text}
"""


def create_skills_prompt(resume_text):
    return f"""
Extract skills and related information from the resume:

* Skills: technical skills, programming languages, IT tools, software skills.
* Professional Development: certifications, research publications, awards, open source contributions, patents.
* Other: language skills, interests, hobbies, extra-curricular activities.

Only extract information that is explicitly mentioned in the resume.

{get_skills_format_instructions()}

Resume:
{resume_text}
"""


def create_work_experience_prompt(company, role, resume_text):
    return f"""
Extract work experience information for {company} as {role}.

{get_work_experience_format_instructions()}

Resume:
{resume_text}
"""


def create_education_prompt(resume_text):
    return f"""
Extract education information from the resume.

{get_education_format_instructions()}

Resume:
{resume_text}
"""