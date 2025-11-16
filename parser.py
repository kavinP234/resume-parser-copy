import argparse
import json
import logging
import os
import sys
import time
from copy import deepcopy
from pathlib import Path

import docx
import openai
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from openai import OpenAI

import threading

from pydantic_models_prompts import Education, WorkExperience
from pydantic_models_prompts import (
    basic_details_prompt, fallback_basic_info_prompt,
    skills_prompt, fallback_skills_prompt,
    fallback_education_prompt, companies_prompt, work_experience_prompt
)
from utils import extract_emails, extract_github_and_linkedin_urls
from utils import output_template

logger = logging.getLogger()
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)

logger.addHandler(stream_handler)

load_dotenv()


class ResumeManager:
    def __init__(self, resume_f, model_name, extension=None):
        self.output = deepcopy(output_template)
        self.resume = get_resume_content(resume_f, extension)
        self.model_name = model_name
        self.client = OpenAI()
        self.companies = []

    def process_file(self):
        all_threads = []
        for target in [
            self.extract_work_experience,
            self.extract_basic_info,
            self.extract_education,
            self.extract_skills
        ]:
            thread = threading.Thread(target=target)
            all_threads.append(thread)
            thread.start()

        for thread in all_threads:
            thread.join()

    def extract_pydantic(self, target_schema):
        """Extract structured data using OpenAI with JSON mode"""
        start = time.time()
        
        # Create a schema description for the AI
        schema_description = f"""
        Extract information and return as a JSON array of objects with the following fields:
        {', '.join(target_schema.__fields__.keys())}
        
        Each object should represent one entry (education or work experience).
        """
        
        prompt = f"""
        {schema_description}
        
        Resume Content:
        {self.resume}
        
        Return only valid JSON array.
        """
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a resume parser. Extract structured data and return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=10,
            )
            
            result = completion.choices[0].message.content
            parsed_result = json.loads(result)
            
            # Convert to list of target schema objects
            extracted_data = []
            if isinstance(parsed_result, list):
                for item in parsed_result:
                    try:
                        # Create instance of the target schema
                        obj = target_schema(**item)
                        extracted_data.append(obj)
                    except Exception as e:
                        logger.warning(f"Failed to parse item: {item}, error: {e}")
                        continue
            elif isinstance(parsed_result, dict):
                # Handle case where result is a dict with a list inside
                for key, value in parsed_result.items():
                    if isinstance(value, list):
                        for item in value:
                            try:
                                obj = target_schema(**item)
                                extracted_data.append(obj)
                            except Exception as e:
                                logger.warning(f"Failed to parse item: {item}, error: {e}")
                                continue
                        break
            
            end = time.time()
            seconds = end - start
            return extracted_data, seconds
            
        except Exception as e:
            end = time.time()
            seconds = end - start
            logger.error(f"Extraction error: {e}")
            return [], seconds

    def query_model(self, query, json_mode=True):
        start = time.time()

        try:
            if json_mode:
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": query}],
                    response_format={'type': 'json_object'},
                    timeout=15,
                )
            else:
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": query}],
                    timeout=15,
                )

            end = time.time()
            seconds = end - start
            result = completion.choices[0].message.content
            return result, seconds
            
        except Exception as e:
            end = time.time()
            seconds = end - start
            logger.error(f"Query error: {e}")
            return "{}" if json_mode else "", seconds

    def extract_basic_info(self):
        query = basic_details_prompt.format(resume=self.resume)
        output, seconds = self.query_model(query)
        
        try:
            output_json = json.loads(output)
            logger.debug(f"# Basic Info Extract:\n{output_json}")
            logger.info(f"# Basic Info Extraction took {seconds} seconds")

            # Extract basic info with fallbacks
            self.output['candidate_name'] = output_json.get('name', '')
            self.output['job_title'] = output_json.get('job_title', '')
            self.output['bio'] = output_json.get('bio', '')
            
            # Contact info
            if 'location' in output_json:
                self.output['contact_info']['location'] = output_json['location']
            if 'phone' in output_json:
                self.output['contact_info']['phone_number'] = output_json['phone']
                
        except json.JSONDecodeError:
            logger.warning("Basic info extraction returned invalid JSON, using fallback")
            self.fallback_basic_info()

        # Always extract emails and URLs directly from text
        self.output['contact_info']['email_address'] = extract_emails(self.resume)
        self.output['contact_info']['personal_urls'] = extract_github_and_linkedin_urls(self.resume)

    def fallback_basic_info(self):
        """Fallback method for basic info extraction"""
        try:
            # Extract name
            name_query = fallback_basic_info_prompt.format(query='name', resume=self.resume)
            name, _ = self.query_model(name_query, json_mode=False)
            self.output['candidate_name'] = name.strip() if name else ""
            
            # Extract job title
            title_query = fallback_basic_info_prompt.format(query='current or last job title', resume=self.resume)
            title, _ = self.query_model(title_query, json_mode=False)
            self.output['job_title'] = title.strip() if title else ""
            
        except Exception as e:
            logger.error(f"Fallback basic info error: {e}")

    def extract_skills(self):
        try:
            query = skills_prompt.format(resume=self.resume)
            output, seconds = self.query_model(query)
            output_json = json.loads(output)
            
            logger.debug(f"# Skills Extract:\n{output_json}")
            logger.info(f"# Skills Extraction took {seconds} seconds")
            
            self.output['skills'] = output_json.get('skills', [])
            self.output['professional_development'] = output_json.get('professional_development', [])
            self.output['other_info'] = output_json.get('other', [])
            
        except (json.JSONDecodeError, KeyError, Exception) as e:
            logger.warning(f"Skills extraction failed: {e}, using fallback")
            query = fallback_skills_prompt.format(resume=self.resume)
            output, seconds = self.query_model(query, json_mode=False)
            logger.debug(f"# Skills Extract Fallback:\n{output}")
            logger.info(f"# Skills Extraction took {seconds} seconds")
            
            # Parse comma-separated skills
            if output:
                skills = [skill.strip() for skill in output.split(',') if skill.strip()]
                self.output['skills'] = skills

    def extract_education(self):
        try:
            output, seconds = self.extract_pydantic(Education)
            logger.debug(f"# Education Extract:\n{output}")
            logger.info(f"# Education Extraction took {seconds} seconds")
            
            # Convert to JSON-serializable format
            self.output['education'] = [json.loads(x.json()) for x in output]

        except Exception as e:
            logger.warning(f"Education extraction failed: {e}, using fallback")
            query = fallback_education_prompt.format(resume=self.resume)
            output, seconds = self.query_model(query, json_mode=False)
            logger.debug(f"# Education Extract Fallback:\n{output}")
            logger.info(f"# Education Extraction took {seconds} seconds")
            
            # Store the raw text output
            self.output['education'] = output if output else ""

    def extract_work_experience(self):
        try:
            output, seconds = self.extract_pydantic(WorkExperience)
            logger.debug(f"# Work Experience Extract:\n{output}")
            logger.info(f"# Work Experience Extraction took {seconds} seconds")
            
            self.output['work_output'] = [json.loads(x.json()) for x in output]
            
        except Exception as e:
            logger.warning(f"Work extraction failed: {e}, using fallback")
            self.fallback_extract_work_experience()

    def fallback_extract_work_experience(self):
        query = companies_prompt.format(resume=self.resume)
        output, _ = self.query_model(query, json_mode=False)

        all_threads = []

        for line in output.split('\n'):
            if "answer" in line.lower() or not line.strip():
                continue
                
            entry = line.split(',')
            if len(entry) >= 1:
                company_name = entry[0].strip()
                if not company_name:
                    continue
                    
                role = entry[1].strip() if len(entry) > 1 else ""
                
                thread = threading.Thread(target=self.get_intermediary_work_experience, args=(company_name, role))
                all_threads.append(thread)
                thread.start()

        for thread in all_threads:
            thread.join()

    def get_intermediary_work_experience(self, company_name, role):
        query = work_experience_prompt.format(resume=self.resume, role=role, company=company_name)
        output, seconds = self.query_model(query, json_mode=True)
        
        try:
            parsed_output = json.loads(output)
            logger.debug(f"# Intermediary Work Experience Extract:\n{parsed_output}")
            logger.info(f"# Intermediary Work Experience Extraction took {seconds} seconds")
            
            self.output['work_output'].append(parsed_output)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse work experience for {company_name}: {e}")


def get_resume_content(file_path, extension=None):
    if not extension:
        extension = os.path.splitext(file_path)[1]
        
    if extension == '.pdf':
        pdf_reader = PdfReader(file_path)
        content = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                content += text + "\n"
                
    elif extension in ['.docx', '.doc']:
        doc = docx.Document(file_path)
        content = ""
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                content += paragraph.text + "\n"

    else:
        sys.exit(f"Unsupported file type {extension}")
        
    return content.strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse a Resume with Open AI GPT models")
    parser.add_argument("file_path", help="Path to the resume, accepted types .pdf or .docx")
    parser.add_argument("--model_name", default='gpt-3.5-turbo-1106',
                        help="Name of the model, default to gpt-3.5-turbo-1106")

    args = parser.parse_args()
    logging.info(f"Processing {args.file_path}")

    resume_manager = ResumeManager(args.file_path, args.model_name)

    start_time = time.time()
    resume_manager.process_file()
    end_time = time.time()

    resume_name = Path(args.file_path).stem
    output_file_path = f"parsed_outputs/{resume_name}_output.json"
    
    # Create directory if it doesn't exist
    os.makedirs("parsed_outputs", exist_ok=True)
    
    with open(output_file_path, 'w') as file:
        json.dump(resume_manager.output, file, indent=2)

    print(json.dumps(resume_manager.output, indent=2))

    seconds = end_time - start_time
    m, s = divmod(seconds, 60)
    logger.info(f"Total time {int(m)} min {int(s)} seconds")