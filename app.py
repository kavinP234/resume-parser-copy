import streamlit as st
import time
import json
import tempfile
import os
from pathlib import Path

# Set page config
st.set_page_config(
    page_title="Resume Parser",
    page_icon="📄",
    layout="wide"
)

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .result-section {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .section-header {
        color: #1f77b4;
        font-size: 1.3rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="main-header">🧠 AI Resume Parser</h1>', unsafe_allow_html=True)
    
    # Sidebar for instructions
    with st.sidebar:
        st.header("Instructions")
        st.markdown("""
        1. Upload a PDF resume
        2. Click 'Parse Resume' 
        3. View extracted information
        
        **Extracts:**
        - Personal details
        - Work experience  
        - Education
        - Skills
        - Contact information
        """)
        
        st.header("Requirements")
        st.markdown("""
        - PDF format only
        - Max file size: 200MB
        - English content works best
        """)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Upload Resume")
        uploaded_file = st.file_uploader(
            "Choose a PDF file", 
            type="pdf",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            # Display file info
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.2f} KB"
            }
            st.json(file_details)
            
            # Preview PDF
            st.subheader("PDF Preview")
            st.write("Note: Preview may not show all content accurately")
    
    with col2:
        if uploaded_file is not None:
            # Show PDF preview
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Display PDF
            try:
                with open(tmp_path, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="400" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
            except:
                st.warning("Could not display PDF preview")
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    # Parse button
    if uploaded_file is not None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            parse_btn = st.button(
                "🚀 Parse Resume", 
                use_container_width=True,
                type="primary"
            )
        
        if parse_btn:
            try:
                with st.spinner("🔍 Analyzing resume content..."):
                    start_time = time.time()
                    
                    # Import and use ResumeManager
                    from parser import ResumeManager
                    
                    # Create temporary file for processing
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    try:
                        # Initialize and process resume
                        resume_manager = ResumeManager(tmp_path, 'gpt-3.5-turbo-1106', extension='.pdf')
                        resume_manager.process_file()
                        
                        end_time = time.time()
                        processing_time = end_time - start_time
                        
                        # Display success message
                        st.success(f"✅ Resume parsed successfully in {processing_time:.2f} seconds!")
                        
                        # Display results in expandable sections
                        display_results(resume_manager.output)
                        
                    finally:
                        # Clean up temp file
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                            
            except ImportError as e:
                st.error(f"❌ Import error: {e}")
                st.info("Please make sure all required files are in the same directory")
            except Exception as e:
                st.error(f"❌ Error processing resume: {e}")
                st.info("This might be due to API issues or file format problems")

def display_results(output_data):
    """Display the parsed resume data in an organized way"""
    
    # Basic Information
    with st.expander("👤 Basic Information", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            if output_data.get('candidate_name'):
                st.metric("Candidate Name", output_data['candidate_name'])
            if output_data.get('job_title'):
                st.metric("Job Title", output_data['job_title'])
        
        with col2:
            if output_data.get('bio'):
                st.write("**Bio/Summary:**")
                st.info(output_data['bio'])
    
    # Contact Information
    contact_info = output_data.get('contact_info', {})
    if any(contact_info.values()):
        with st.expander("📞 Contact Information"):
            col1, col2 = st.columns(2)
            
            with col1:
                if contact_info.get('location'):
                    st.write(f"**Location:** {contact_info['location']}")
                if contact_info.get('phone_number'):
                    st.write(f"**Phone:** {contact_info['phone_number']}")
            
            with col2:
                if contact_info.get('email_address'):
                    st.write(f"**Email:** {', '.join(contact_info['email_address'])}")
                if contact_info.get('personal_urls'):
                    st.write(f"**URLs:** {', '.join(contact_info['personal_urls'])}")
    
    # Work Experience
    work_experience = output_data.get('work_output', [])
    if work_experience:
        with st.expander("💼 Work Experience"):
            for i, work in enumerate(work_experience, 1):
                st.markdown(f"**{i}. {work.get('company_name', 'Unknown Company')}**")
                st.write(f"Position: {work.get('job_title', 'N/A')}")
                st.write(f"Duration: {work.get('start_date', 'N/A')} to {work.get('end_date', 'N/A')}")
                if work.get('description'):
                    st.write(f"Description: {work['description']}")
                st.write("---")
    
    # Education
    education = output_data.get('education', [])
    if education:
        with st.expander("🎓 Education"):
            for i, edu in enumerate(education, 1):
                st.markdown(f"**{i}. {edu.get('qualification', 'Unknown Qualification')}**")
                st.write(f"Institution: {edu.get('establishment', 'N/A')}")
                st.write(f"Country: {edu.get('country', 'N/A')}")
                st.write(f"Year: {edu.get('year', 'N/A')}")
                st.write("---")
    
    # Skills
    skills = output_data.get('skills', [])
    if skills:
        with st.expander("🛠️ Skills"):
            if isinstance(skills, list):
                cols = st.columns(3)
                for i, skill in enumerate(skills):
                    cols[i % 3].success(skill)
            else:
                st.write(skills)
    
    # Professional Development
    professional_dev = output_data.get('professional_development', [])
    if professional_dev:
        with st.expander("📜 Professional Development"):
            if isinstance(professional_dev, list):
                for item in professional_dev:
                    st.write(f"• {item}")
            else:
                st.write(professional_dev)
    
    # Other Information
    other_info = output_data.get('other_info', [])
    if other_info:
        with st.expander("🌟 Additional Information"):
            if isinstance(other_info, list):
                for item in other_info:
                    st.write(f"• {item}")
            else:
                st.write(other_info)
    
    # Raw JSON data (collapsed by default)
    with st.expander("📊 Raw JSON Data"):
        st.json(output_data)
    
    # Download button for JSON data
    json_str = json.dumps(output_data, indent=2)
    st.download_button(
        label="📥 Download JSON Results",
        data=json_str,
        file_name="parsed_resume.json",
        mime="application/json"
    )

# Add base64 import at the top level
import base64

if __name__ == "__main__":
    main()