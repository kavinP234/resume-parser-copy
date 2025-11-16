import re
import json
from typing import List, Dict, Any

# Output template structure
output_template = {
    'candidate_name': '',
    'contact_info': {
        'location': '',
        'phone_number': '',
        'email_address': [],
        'personal_urls': []
    },
    'job_title': '',
    'bio': '',
    'work_output': [],
    'skills': [],
    'education': [],
    'professional_development': [],  # list of certifications, research publications, awards, open source contributions
    'other_info': [],  # list of language skills, interests, hobbies, extracurricular activities
}


# Template structures for specific sections
work_experience_template = {
    'company_name': '',
    'job_title': '',
    'start_date': '',
    'end_date': '',
    'description': ''
}

education_template = {
    'qualification': '',
    'establishment': '',
    'country': '',
    'year': ''
}

# Regular expression patterns for contact information extraction
github_pattern = r'(https://github\.com/[A-Za-z0-9_-]+)'
linkedin_pattern = r'(https://www\.linkedin\.com/in/[A-Za-z0-9_-]+)'
personal_website_pattern = r'(https?://(?!github\.com|linkedin\.com)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}(?:/[^\s]*)?)'
email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'


def extract_emails(content: str) -> List[str]:
    """
    Extract email addresses from text content.
    
    Args:
        content (str): The text content to search for emails
        
    Returns:
        List[str]: List of unique email addresses found
    """
    emails = re.findall(email_pattern, content, re.IGNORECASE)
    # Remove duplicates while preserving order
    seen = set()
    unique_emails = []
    for email in emails:
        if email.lower() not in seen:
            seen.add(email.lower())
            unique_emails.append(email)
    return unique_emails


def extract_github_and_linkedin_urls(text: str) -> List[str]:
    """
    Extract GitHub and LinkedIn profile URLs from text.
    
    Args:
        text (str): The text content to search for URLs
        
    Returns:
        List[str]: List of unique GitHub and LinkedIn URLs found
    """
    github_urls = re.findall(github_pattern, text)
    linkedin_urls = re.findall(linkedin_pattern, text)
    
    # Combine and remove duplicates
    all_urls = github_urls + linkedin_urls
    seen = set()
    unique_urls = []
    for url in all_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls


def extract_personal_urls(text: str) -> List[str]:
    """
    Extract personal website URLs (excluding GitHub and LinkedIn).
    
    Args:
        text (str): The text content to search for URLs
        
    Returns:
        List[str]: List of personal website URLs
    """
    websites = re.findall(personal_website_pattern, text)
    # Filter out common non-personal sites and duplicates
    common_domains = ['facebook.com', 'twitter.com', 'instagram.com', 'youtube.com']
    seen = set()
    personal_urls = []
    
    for url in websites:
        if not any(domain in url for domain in common_domains):
            if url not in seen:
                seen.add(url)
                personal_urls.append(url)
    
    return personal_urls


def extract_phone_numbers(content: str) -> List[str]:
    """
    Extract phone numbers from text content.
    
    Args:
        content (str): The text content to search for phone numbers
        
    Returns:
        List[str]: List of phone numbers found
    """
    phones = re.findall(phone_pattern, content)
    # Clean up the phone numbers
    cleaned_phones = []
    for phone in phones:
        # Remove common separators and extra spaces
        cleaned = re.sub(r'[-.\s()]', '', phone).strip()
        if len(cleaned) >= 10:  # Basic validation for phone number length
            cleaned_phones.append(cleaned)
    
    return cleaned_phones


def clean_text_content(text: str) -> str:
    """
    Clean and normalize text content from resumes.
    
    Args:
        text (str): Raw text extracted from resume
        
    Returns:
        str: Cleaned and normalized text
    """
    # Remove extra whitespace and normalize line breaks
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # Remove special characters that might interfere with parsing
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
    
    return text.strip()


def validate_email_format(output_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and format email addresses in the output data.
    
    Args:
        output_data (Dict[str, Any]): The parsed resume data
        
    Returns:
        Dict[str, Any]: Output data with validated email format
    """
    if 'contact_info' in output_data and 'email_address' in output_data['contact_info']:
        emails = output_data['contact_info']['email_address']
        if isinstance(emails, str):
            # Convert string to list if needed
            output_data['contact_info']['email_address'] = [emails]
        elif not isinstance(emails, list):
            output_data['contact_info']['email_address'] = []
    
    return output_data


def format_work_experience(work_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format and validate work experience data.
    
    Args:
        work_data (List[Dict[str, Any]]): Raw work experience data
        
    Returns:
        List[Dict[str, Any]]: Formatted work experience data
    """
    formatted_work = []
    
    for work in work_data:
        formatted_entry = work_experience_template.copy()
        
        # Map fields from raw data to template
        for key in formatted_entry.keys():
            if key in work and work[key]:
                formatted_entry[key] = work[key]
            elif key == 'description' and work.get(key):
                # Clean up description text
                desc = work[key]
                if isinstance(desc, str):
                    desc = re.sub(r'\s+', ' ', desc).strip()
                formatted_entry[key] = desc
        
        formatted_work.append(formatted_entry)
    
    return formatted_work


def format_education(education_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format and validate education data.
    
    Args:
        education_data (List[Dict[str, Any]]): Raw education data
        
    Returns:
        List[Dict[str, Any]]: Formatted education data
    """
    formatted_education = []
    
    for edu in education_data:
        formatted_entry = education_template.copy()
        
        # Map fields from raw data to template
        for key in formatted_entry.keys():
            if key in edu and edu[key]:
                formatted_entry[key] = edu[key]
        
        formatted_education.append(formatted_entry)
    
    return formatted_education


def sanitize_output(output_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize and clean the final output data.
    
    Args:
        output_data (Dict[str, Any]): The raw output data
        
    Returns:
        Dict[str, Any]: Sanitized output data
    """
    # Create a deep copy to avoid modifying original
    sanitized = output_template.copy()
    
    # Copy all fields that exist in both templates
    for key in sanitized.keys():
        if key in output_data and output_data[key] is not None:
            if key == 'contact_info' and isinstance(output_data[key], dict):
                # Handle nested contact_info
                for contact_key in sanitized['contact_info'].keys():
                    if contact_key in output_data['contact_info'] and output_data['contact_info'][contact_key]:
                        sanitized['contact_info'][contact_key] = output_data['contact_info'][contact_key]
            else:
                sanitized[key] = output_data[key]
    
    # Ensure lists are properly formatted
    list_fields = ['skills', 'professional_development', 'other_info', 'work_output', 'education']
    for field in list_fields:
        if field in sanitized and not isinstance(sanitized[field], list):
            if sanitized[field]:
                sanitized[field] = [sanitized[field]]
            else:
                sanitized[field] = []
    
    # Validate email format
    sanitized = validate_email_format(sanitized)
    
    return sanitized


def save_output_to_file(output_data: Dict[str, Any], filename: str, output_dir: str = "parsed_outputs") -> str:
    """
    Save parsed output to a JSON file.
    
    Args:
        output_data (Dict[str, Any]): The parsed resume data
        filename (str): Base filename for output
        output_dir (str): Output directory name
        
    Returns:
        str: Path to the saved file
    """
    import os
    from pathlib import Path
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)
    
    # Generate output file path
    output_path = os.path.join(output_dir, f"{filename}_output.json")
    
    # Sanitize data before saving
    sanitized_data = sanitize_output(output_data)
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sanitized_data, f, indent=2, ensure_ascii=False)
    
    return output_path


def load_output_from_file(filepath: str) -> Dict[str, Any]:
    """
    Load parsed output from a JSON file.
    
    Args:
        filepath (str): Path to the JSON file
        
    Returns:
        Dict[str, Any]: Loaded resume data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_all_contact_info(content: str) -> Dict[str, List[str]]:
    """
    Extract all contact information from resume content.
    
    Args:
        content (str): The resume text content
        
    Returns:
        Dict[str, List[str]]: Dictionary containing all extracted contact info
    """
    return {
        'emails': extract_emails(content),
        'github_linkedin_urls': extract_github_and_linkedin_urls(content),
        'personal_urls': extract_personal_urls(content),
        'phone_numbers': extract_phone_numbers(content)
    }


# Utility functions for data validation
def is_valid_resume_data(data: Dict[str, Any]) -> bool:
    """
    Basic validation for resume data structure.
    
    Args:
        data (Dict[str, Any]): Data to validate
        
    Returns:
        bool: True if data has basic resume structure
    """
    required_fields = ['candidate_name', 'job_title']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return False
    
    return True


def get_resume_statistics(output_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Generate statistics about the parsed resume.
    
    Args:
        output_data (Dict[str, Any]): Parsed resume data
        
    Returns:
        Dict[str, int]: Statistics about the resume
    """
    stats = {
        'work_experience_count': len(output_data.get('work_output', [])),
        'education_count': len(output_data.get('education', [])),
        'skills_count': len(output_data.get('skills', [])),
        'certifications_count': len(output_data.get('professional_development', [])),
        'other_info_count': len(output_data.get('other_info', []))
    }
    
    return stats