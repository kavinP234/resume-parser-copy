from typing import List, Optional
from langchain.pydantic_v1 import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate


# --------------------------------------------------------------------------------------------------------------- #
# Basic Info model and prompts
class BasicInfo(BaseModel):
    name: str = Field(description="name of the candidate")
    bio: str = Field(description="Bio, profile, introduction or summary of the candidate")
    job_title: str = Field(description="current or latest job title of the candidate")
    location: Optional[str] = Field(description="location of the candidate")
    phone: Optional[str] = Field(description="phone number of the candidate")


basic_info_parser = PydanticOutputParser(pydantic_object=BasicInfo)

basic_details_prompt = PromptTemplate(
    template="{resume}\n{format_instructions}\n",
    input_variables=["resume"],
    partial_variables={"format_instructions": basic_info_parser.get_format_instructions()},
)


fallback_basic_info_prompt = PromptTemplate(
    template="What is the {query}?\nRESUME:\n{resume}\nANSWER:\n",
    input_variables=["query", "resume"]
)


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


work_experience_parser = PydanticOutputParser(pydantic_object=SingleWorkExperience)

work_experience_template = """
What was this person work experience at {company} as a {role} ?\n
\nRESUME:\n
{resume}\n
{format_instructions}\n
"""

work_experience_prompt = PromptTemplate(
    template=work_experience_template,
    input_variables=["company", "role", "resume"],
    partial_variables={"format_instructions": work_experience_parser.get_format_instructions()},
)


companies_prompt = PromptTemplate(
    template="What companies did this candidate work at and what was their job title ? Only use the resume to answer, "
             "do not make up answers. Use the template to format the answer:\nTEMPLATE\n:"
             "company 1, job title 1\n"
             "company 2, job title 3\n"
             "company 3, job title 3\n"
             "\nRESUME\n{resume}\n"
             "ANSWER:\n",
    input_variables=["resume"],
)


# --------------------------------------------------------------------------------------------------------------- #
# Skills and other info model and prompts
class Skills(BaseModel):
    skills: List[str] = Field(description="list of skills, programming languages, IT tools, software skills")
    professional_development: Optional[List[str]] = Field(
        description="list of professional certifications that are not related to university degrees. "
                    "Include research publications, awards, open source contributions or patents if any. "
                    "Only extract answers from the resume, do not make up answers")
    other: Optional[List[str]] = Field(
        description="language skills, interests, hobbies, extra-curricular activities. "
                    "Only extract answers from the resume, do not make up answers")


skills_parser = PydanticOutputParser(pydantic_object=Skills)

skills_template = """
Extract the information:\n
* Skills section contains technical skills, programming languages, IT tools, software skills.\n
* Professional development section contains the list of certifications other than university degrees, research 
publications, awards, open source contributions or patents.\n
* Other section is for language skills, interests, hobbies, extra-curricular activities\n
Only extract answers from the resume, do not make up answers\n
RESUME:\n{resume}\n{format_instructions}\n
"""

skills_prompt = PromptTemplate(
    template=skills_template,
    input_variables=["resume"],
    partial_variables={"format_instructions": skills_parser.get_format_instructions()},
)

fallback_skills_prompt = PromptTemplate(
    template="""What are the skills in this resume ?\nRESUME:\n{resume}\n
        Answer with a comma separated list.""",
    input_variables=["resume"]
)


# --------------------------------------------------------------------------------------------------------------- #
# Education model and prompts
class Education(BaseModel):
    """Education qualification"""
    qualification: str = Field(description="university or high-school education qualification or degree")
    establishment: Optional[str] = Field(description="establishment where the qualification was obtained")
    country: Optional[str] = Field(description="country where the qualification was obtained")
    year: Optional[str] = Field(description="year when the qualification was obtained")


# Prompt Template to extract education degrees in a structured output
fallback_education_prompt = PromptTemplate(
    template="What are the university education degrees ? Use the template to format the answer. "
             "Only use the resume to answer, do not make up answers. "
             "If there is no education mentioned in the resume, just answer with 'None'"
             "\nTEMPLATE\n:"
             "Qualification, Name of establishment, Country (if applicable), Year \n"
             "Qualification, Name of establishment, Country (if applicable), Year \n"
             "\nRESUME\n{resume}\n"
             "ANSWER:\n",
    input_variables=["resume"],
)


# --------------------------------------------------------------------------------------------------------------- #
# Updated models for compatibility with newer LangChain versions
class EducationV2(BaseModel):
    """Education qualification"""
    qualification: str = Field(description="university or high-school education qualification or degree")
    establishment: Optional[str] = Field(description="establishment where the qualification was obtained")
    country: Optional[str] = Field(description="country where the qualification was obtained")
    year: Optional[str] = Field(description="year when the qualification was obtained")


class WorkExperienceV2(BaseModel):
    """Work experiences"""
    company_name: str = Field(description="name of the company")
    job_title: str = Field(description="job title")
    start_date: str = Field(description="start date, if not present use 'None'")
    end_date: str = Field(description="end date, if not present use 'None'")
    description: Optional[str] = Field(description="description, if not present use 'None' ")


# Alternative prompt templates for better compatibility
alternative_skills_prompt = """
Please extract the following information from the resume:

TECHNICAL SKILLS: Extract all technical skills, programming languages, IT tools, and software skills.

PROFESSIONAL DEVELOPMENT: Extract certifications (excluding university degrees), research publications, awards, open source contributions, or patents.

OTHER INFORMATION: Extract language skills, interests, hobbies, and extra-curricular activities.

Return the results as a JSON object with the following structure:
{
    "skills": ["list", "of", "skills"],
    "professional_development": ["list", "of", "certifications", "awards"],
    "other_info": ["list", "of", "languages", "hobbies"]
}

RESUME:
{resume}
"""

alternative_basic_info_prompt = """
Extract the following basic information from the resume:

- Name of the candidate
- Bio, profile, introduction or summary
- Current or latest job title
- Location (if available)
- Phone number (if available)

Return the results as a JSON object with the following structure:
{
    "name": "Candidate Name",
    "bio": "Candidate bio/summary",
    "job_title": "Current job title",
    "location": "Location if available",
    "phone": "Phone number if available"
}

RESUME:
{resume}
"""

alternative_work_experience_prompt = """
Extract work experience information for {company} as {role}.

Return as JSON with:
{{
    "company_name": "{company}",
    "job_title": "{role}",
    "start_date": "start date or None",
    "end_date": "end date or None", 
    "description": "job description or None"
}}

RESUME:
{resume}
"""

alternative_education_prompt = """
Extract all education qualifications from the resume.

Return as a list of JSON objects with:
[
    {{
        "qualification": "degree name",
        "establishment": "school/university name", 
        "country": "country if available",
        "year": "year if available"
    }}
]

RESUME:
{resume}
"""