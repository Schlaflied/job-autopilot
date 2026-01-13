# Job Autopilot - Resume Generator
# AI-powered resume tailoring with ATS optimization

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from modules.ai_agent import ai_agent
from modules.logger_config import app_logger

load_dotenv()

class ResumeGenerator:
    """
    Generate ATS-optimized resumes tailored to job descriptions
    
    Features:
    - AI-powered keyword extraction from JD
    - Resume tailoring based on master resume + JD
    - .docx and PDF export
    - 1-page constraint
    - ATS-friendly formatting (no tables, simple layout)
    """
    
    def __init__(self):
        self.output_dir = "data/resumes"
        os.makedirs(self.output_dir, exist_ok=True)
        app_logger.info("Resume generator initialized")
    
    def load_master_resume(self, resume_path: str = None) -> Optional[Dict]:
        """
        Load master resume from markdown or JSON
        
        Args:
            resume_path: Path to master resume file
        
        Returns:
            dict: Parsed resume data
        """
        if not resume_path:
            # Try to find master resume in default locations
            possible_paths = [
                "Yuting Sun Master Resume.md",
                "data/master_resume.md",
                "master_resume.json"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    resume_path = path
                    break
        
        if not resume_path or not os.path.exists(resume_path):
            app_logger.error("Master resume not found!")
            return None
        
        try:
            with open(resume_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse markdown resume (simple parser)
            resume_data = self._parse_markdown_resume(content)
            app_logger.info(f"Loaded master resume from {resume_path}")
            return resume_data
        
        except Exception as e:
            app_logger.error(f"Failed to load master resume: {e}")
            return None
    
    def _parse_markdown_resume(self, content: str) -> Dict:
        """
        Parse markdown resume into structured data
        Supports various markdown heading levels (####, ##, #)
        """
        import re
        
        lines = content.split('\n')
        
        resume = {
            "name": "",
            "contact": {},
            "summary": "",
            "experience": [],
            "education": [],
            "skills": {},
            "certifications": [],
            "projects": []
        }
        
        current_section = None
        current_job = None
        summary_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line or line == '---' or line == '----':
                continue
            
            # Detect section headers (#### Level or ## Level)
            header_match = re.match(r'^#{1,6}\s+(.+)', line)
            if header_match:
                section_title = header_match.group(1).strip().lower()
                
                # Save previous job before switching sections
                if current_job and current_section == 'experience':
                    resume['experience'].append(current_job)
                    current_job = None
                
                if 'header' in section_title:
                    current_section = 'header'
                elif 'summary' in section_title or 'profile' in section_title:
                    current_section = 'summary'
                elif 'education' in section_title:
                    current_section = 'education'
                elif 'experience' in section_title:
                    current_section = 'experience'
                elif 'skill' in section_title:
                    current_section = 'skills'
                elif 'project' in section_title or 'saas' in section_title:
                    current_section = 'projects'
                continue
            
            # Parse Header section (name, contact)
            if current_section == 'header':
                # First line with | is contact info
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4:
                        resume['name'] = parts[0]
                        resume['contact']['location'] = parts[1]
                        resume['contact']['phone'] = parts[2]
                        resume['contact']['email'] = parts[3]
                
                # Extract URLs
                if 'linkedin' in line.lower() or 'Linkedin' in line:
                    url = re.search(r'https?://[^\s]+', line)
                    if url:
                        resume['contact']['linkedin'] = url.group()
                
                if 'github' in line.lower():
                    url = re.search(r'https?://[^\s]+', line)
                    if url:
                        resume['contact']['github'] = url.group().rstrip(')')
                
                if 'portfolio' in line.lower() or 'Learning and Development' in line:
                    url = re.search(r'https?://[^\s]+', line)
                    if url:
                        resume['contact']['portfolio'] = url.group().rstrip(')')
            
            # Parse Summary
            elif current_section == 'summary':
                if line.startswith('*') and line.endswith('*'):
                    # Remove italic markers
                    summary_lines.append(line.strip('*').strip())
                elif line:
                    summary_lines.append(line)
            
            # Parse Education
            elif current_section == 'education':
                if line.startswith('-') or line.startswith('•'):
                    edu_line = line.lstrip('-•').strip()
                    
                    # Remove markdown bold markers
                    edu_line = edu_line.replace('**', '')
                    
                    # Split by em dash or double space
                    if '–' in edu_line:
                        parts = edu_line.split('–', 1)
                        resume['education'].append({
                            "title": parts[0].strip(),
                            "details": [parts[1].strip()] if len(parts) > 1 else []
                        })
                    else:
                        resume['education'].append({
                            "title": edu_line,
                            "details": []
                        })
            
            # Parse Experience
            elif current_section == 'experience':
                # Job title line (bold, starts with **)
                if line.startswith('**') and '—' in line:
                    # Save previous job
                    if current_job:
                        resume['experience'].append(current_job)
                    
                    # Parse: **Company — Job Title**
                    line_clean = line.strip('*').strip()
                    if '—' in line_clean:
                        parts = line_clean.split('—', 1)
                        company = parts[0].strip()
                        title = parts[1].strip()
                    else:
                        company = line_clean
                        title = ""
                    
                    current_job = {
                        "title": title,
                        "company": company,
                        "duration": "",
                        "details": []
                    }
                
                # Duration line (italic, starts with *)
                elif line.startswith('*') and ('|' in line or '–' in line):
                    duration_line = line.strip('*').strip()
                    if '|' in duration_line:
                        parts = duration_line.split('|')
                        if current_job:
                            current_job['duration'] = parts[-1].strip()
                    else:
                        if current_job:
                            current_job['duration'] = duration_line
                
                # Bullet points
                elif line.startswith('-') or line.startswith('•'):
                    if current_job:
                        detail = line.lstrip('-•').strip()
                        current_job['details'].append(detail)
            
            # Parse Skills
            elif current_section == 'skills':
                if line.startswith('-') or line.startswith('•'):
                    skill_line = line.lstrip('-•').strip()
                    
                    # Check if it has a category (e.g., "EdTech Tools:")
                    if '**' in skill_line and ':' in skill_line:
                        # Extract category and skills
                        match = re.match(r'\*\*(.+?)\*\*:\s*(.+)', skill_line)
                        if match:
                            category = match.group(1).strip()
                            skills_content = match.group(2).strip()
                            resume['skills'][category] = skills_content
                    elif ':' in skill_line:
                        # Without bold markers
                        parts = skill_line.split(':', 1)
                        if len(parts) == 2:
                            category = parts[0].strip()
                            skills_content = parts[1].strip()
                            resume['skills'][category] = skills_content
                    else:
                        # Flat skill
                        if not isinstance(resume['skills'], dict):
                            resume['skills'] = []
                        if isinstance(resume['skills'], list):
                            resume['skills'].append(skill_line)
            
            # Parse Projects
            elif current_section == 'projects':
                if line.startswith('**') and ':' in line:
                    # Project title and description
                    project_line = line.strip('*').strip()
                    resume['projects'].append(project_line)
                elif line and not line.startswith('#'):
                    # Continue project description
                    if resume['projects']:
                        resume['projects'][-1] += ' ' + line
        
        # Add last job if exists
        if current_job and current_section == 'experience':
            resume['experience'].append(current_job)
        
        # Combine summary lines
        if summary_lines:
            resume['summary'] = ' '.join(summary_lines)
        
        app_logger.info(f"Parsed MD resume: {resume.get('name', 'Unknown')} - {len(resume.get('experience', []))} jobs")
        
        return resume
    
    def tailor_resume(self, master_resume: Dict, job_description: str, job_title: str, company: str) -> Dict:
        """
        Use AI to tailor resume for specific job
        
        Args:
            master_resume: Base resume data
            job_description: Target job JD
            job_title: Job title
            company: Company name
        
        Returns:
            dict: Tailored resume data
        """
        app_logger.info(f"Tailoring resume for {job_title} at {company}")
        
        # Build AI prompt
        prompt = f"""You are an expert resume writer specializing in ATS optimization.

**Task**: Tailor this resume for the following job, ensuring it passes ATS and appeals to HR.

**Job Details**:
- Title: {job_title}
- Company: {company}
- Job Description:
{job_description[:1500]}

**Master Resume**:
{json.dumps(master_resume, indent=2)}

**Requirements**:
1. Extract key skills/keywords from JD
2. Reorder/emphasize relevant experience
3. Add job-specific keywords naturally
4. Keep 1-page length (max 600 words)
5. Maintain truthfulness (don't fabricate)
6. Use action verbs and quantifiable achievements
7. Return JSON format matching master resume structure

**Output JSON** (experience items should include company, role, duration, bullets):
"""
        
        try:
            # Call GPT-4o-mini
            response = ai_agent.client.chat.completions.create(
                model=ai_agent.model,
                messages=[
                    {"role": "system", "content": "You are an expert ATS-optimized resume writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content
            
            # Extract JSON from response
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()
            
            tailored_resume = json.loads(result)
            app_logger.info("Resume tailored successfully")
            
            return tailored_resume
        
        except Exception as e:
            app_logger.error(f"Resume tailoring failed: {e}")
            # Fallback: return master resume
            return master_resume
    
    def export_docx(self, resume_data: Dict, filename: str) -> str:
        """
        Export resume to .docx format (ATS-friendly)
        
        Args:
            resume_data: Resume data dict
            filename: Output filename
        
        Returns:
            str: Path to generated file
        """
        doc = Document()
        
        # Set narrow margins (ATS prefers simple layout)
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.7)
            section.right_margin = Inches(0.7)
        
        # Name (centered, bold, larger)
        name = doc.add_paragraph(resume_data.get('name', 'Your Name'))
        name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        name.runs[0].bold = True
        name.runs[0].font.size = Pt(16)
        
        # Contact info (centered, smaller)
        contact = resume_data.get('contact', {})
        contact_text = ' | '.join([
            contact.get('email', ''),
            contact.get('phone', ''),
            contact.get('location', ''),
            contact.get('linkedin', '')
        ])
        contact_para = doc.add_paragraph(contact_text)
        contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_para.runs[0].font.size = Pt(10)
        
        doc.add_paragraph()  # Spacer
        
        # Summary
        if resume_data.get('summary'):
            summary_heading = doc.add_paragraph('PROFESSIONAL SUMMARY')
            summary_heading.runs[0].bold = True
            summary_heading.runs[0].font.size = Pt(11)
            
            summary_text = doc.add_paragraph(resume_data['summary'])
            summary_text.runs[0].font.size = Pt(10)
            doc.add_paragraph()
        
        # Experience
        if resume_data.get('experience'):
            exp_heading = doc.add_paragraph('PROFESSIONAL EXPERIENCE')
            exp_heading.runs[0].bold = True
            exp_heading.runs[0].font.size = Pt(11)
            
            for exp in resume_data['experience']:
                # Job title + company
                job_line = doc.add_paragraph()
                job_line.add_run(exp.get('title', '')).bold = True
                
                if exp.get('company'):
                    job_line.add_run(f" | {exp['company']}")
                
                if exp.get('duration'):
                    job_line.add_run(f" | {exp['duration']}")
                
                job_line.runs[0].font.size = Pt(10)
                
                # Bullets
                for detail in exp.get('details', []):
                    bullet = doc.add_paragraph(detail, style='List Bullet')
                    bullet.runs[0].font.size = Pt(10)
                
                doc.add_paragraph()  # Spacer between jobs
        
        # Education
        if resume_data.get('education'):
            edu_heading = doc.add_paragraph('EDUCATION')
            edu_heading.runs[0].bold = True
            edu_heading.runs[0].font.size = Pt(11)
            
            for edu in resume_data['education']:
                edu_line = doc.add_paragraph(edu.get('title', ''))
                edu_line.runs[0].bold = True
                edu_line.runs[0].font.size = Pt(10)
                
                for detail in edu.get('details', []):
                    doc.add_paragraph(detail, style='List Bullet').runs[0].font.size = Pt(10)
        
        # Skills
        if resume_data.get('skills'):
            skills_heading = doc.add_paragraph('SKILLS')
            skills_heading.runs[0].bold = True
            skills_heading.runs[0].font.size = Pt(11)
            
            skills_text = ', '.join(resume_data['skills'])
            doc.add_paragraph(skills_text).runs[0].font.size = Pt(10)
        
        # Save
        filepath = os.path.join(self.output_dir, filename)
        doc.save(filepath)
        app_logger.info(f"Resume exported to {filepath}")
        
        return filepath
    
    
    def export_pdf(self, resume_data: Dict, filename: str) -> str:
        """
        Export resume to PDF format with template styling
        
        Args:
            resume_data: Resume data dict (may include _meta from template)
            filename: Output filename
        
        Returns:
            str: Path to generated file
        """
        from reportlab.lib.colors import HexColor
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Extract template metadata if present
        meta = resume_data.get('_meta', {})
        fonts = meta.get('fonts', {})
        margins = meta.get('margins', {'top': 0.5, 'bottom': 0.5, 'left': 0.7, 'right': 0.7})
        line_spacing = meta.get('line_spacing', 1.0)
        colors = meta.get('colors', {'text': '#000000', 'headings': '#000000'})
        
        # Create document with template margins
        doc = SimpleDocTemplate(
            filepath, 
            pagesize=letter,
            topMargin=margins.get('top', 0.5)*inch,
            bottomMargin=margins.get('bottom', 0.5)*inch,
            leftMargin=margins.get('left', 0.7)*inch,
            rightMargin=margins.get('right', 0.7)*inch
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # Get font configs (default to Arial if not specified)
        name_font = fonts.get('name', {'family': 'Helvetica', 'size': 16, 'bold': True})
        heading_font = fonts.get('heading', {'family': 'Helvetica', 'size': 11, 'bold': True})
        body_font = fonts.get('body', {'family': 'Helvetica', 'size': 10, 'bold': False})
        
        # Convert colors
        heading_color = HexColor(colors.get('headings', '#000000'))
        text_color = HexColor(colors.get('text', '#000000'))
        
        # Name style with template font
        name_style = ParagraphStyle(
            'Name',
            parent=styles['Title'],
            fontName='Helvetica-Bold' if name_font.get('bold') else 'Helvetica',
            fontSize=name_font.get('size', 16),
            textColor=heading_color,
            alignment=1,
            spaceAfter=6 * line_spacing
        )
        story.append(Paragraph(resume_data.get('name', 'Your Name'), name_style))
        
        # Contact info with links
        contact = resume_data.get('contact', {})
        contact_parts = []
        if contact.get('email'):
            contact_parts.append(contact['email'])
        if contact.get('phone'):
            contact_parts.append(contact['phone'])
        if contact.get('location'):
            contact_parts.append(contact['location'])
        
        contact_text = ' | '.join([p for p in contact_parts if p])
        contact_style = ParagraphStyle(
            'Contact',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=body_font.get('size', 10),
            alignment=1,
            spaceAfter=12 * line_spacing
        )
        story.append(Paragraph(contact_text, contact_style))
        
        # Add LinkedIn, GitHub, Portfolio links
        links = []
        if contact.get('linkedin'):
            links.append(f'<a href="{contact["linkedin"]}">LinkedIn</a>')
        if contact.get('github'):
            links.append(f'<a href="{contact["github"]}">GitHub</a>')
        if contact.get('portfolio'):
            links.append(f'<a href="{contact["portfolio"]}">Portfolio</a>')
        
        if links:
            links_text = ' | '.join(links)
            story.append(Paragraph(links_text, contact_style))
            story.append(Spacer(1, 0.1*inch * line_spacing))
        
        # Heading style
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold' if heading_font.get('bold') else 'Helvetica',
            fontSize=heading_font.get('size', 11),
            textColor=heading_color,
            spaceAfter=6 * line_spacing
        )
        
        # Body style
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=body_font.get('size', 10),
            leading=body_font.get('size', 10) * line_spacing * 1.2,
            textColor=text_color
        )
        
        # Use section_order from _meta if available, otherwise default order
        section_order = ['summary', 'experience', 'skills', 'education']
        
        for section in section_order:
            if section == 'summary' and resume_data.get('summary'):
                story.append(Paragraph('<b>PROFESSIONAL SUMMARY</b>', heading_style))
                story.append(Paragraph(resume_data['summary'], body_style))
                story.append(Spacer(1, 0.1*inch * line_spacing))
            
            elif section == 'experience' and resume_data.get('experience'):
                story.append(Paragraph('<b>PROFESSIONAL EXPERIENCE</b>', heading_style))
                for exp in resume_data['experience']:
                    title_text = f"<b>{exp.get('title', '')}</b>"
                    if exp.get('company'):
                        title_text += f" | {exp['company']}"
                    if exp.get('duration'):
                        title_text += f" | {exp['duration']}"
                    
                    story.append(Paragraph(title_text, body_style))
                    
                    for detail in exp.get('details', []):
                        story.append(Paragraph(f"• {detail}", body_style))
                    
                    story.append(Spacer(1, 0.04*inch * line_spacing))
            
            elif section == 'skills' and resume_data.get('skills'):
                story.append(Paragraph('<b>SKILLS</b>', heading_style))
                
                skills_data = resume_data['skills']
                
                # Check if skills is dict (categorized) or list (flat)
                if isinstance(skills_data, dict):
                    # Categorized: {"EdTech Tools": "H5P, Articulate...", "AI & Development": "Python..."}
                    for category, skills_content in skills_data.items():
                        category_line = f"• <b>{category}:</b> {skills_content}"
                        story.append(Paragraph(category_line, body_style))
                elif isinstance(skills_data, list):
                    # Flat list - group every 10 per line  
                    chunk_size = 10
                    for i in range(0, len(skills_data), chunk_size):
                        chunk = skills_data[i:i+chunk_size]
                        story.append(Paragraph(f"• {', '.join(chunk)}", body_style))
                else:
                    # String fallback
                    story.append(Paragraph(f"• {str(skills_data)}", body_style))
                
                story.append(Spacer(1, 0.05*inch * line_spacing))
            
            elif section == 'education' and resume_data.get('education'):
                story.append(Paragraph('<b>EDUCATION</b>', heading_style))
                for edu in resume_data['education']:
                    story.append(Paragraph(f"<b>{edu.get('title', '')}</b>", body_style))
                    for detail in edu.get('details', []):
                        story.append(Paragraph(detail, body_style))
                    story.append(Spacer(1, 0.04*inch * line_spacing))
        
        # Build PDF
        doc.build(story)
        app_logger.info(f"PDF exported to {filepath}")
        
        return filepath
    
    # ============================================================
    # Template System (Phase 2 - Resume Export Feature)
    # ============================================================
    
    def load_template(self, template_name: str) -> Optional[Dict]:
        """
        Load template configuration from JSON
        
        Args:
            template_name: Template name (e.g., "classic_single_column")
        
        Returns:
            dict: Template configuration
        """
        template_path = f"data/templates/{template_name}.json"
        
        if not os.path.exists(template_path):
            app_logger.error(f"Template not found: {template_name}")
            return None
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            app_logger.info(f"Loaded template: {template_name}")
            return template
        except Exception as e:
            app_logger.error(f"Failed to load template: {e}")
            return None
    
    def apply_template(self, resume_data: Dict, template: Dict) -> Dict:
        """
        Apply template settings to resume data
        
        Args:
            resume_data: Resume content
            template: Template configuration
        
        Returns:
            dict: Resume with template metadata
        """
        # Reorder sections based on template
        ordered_resume = {}
        for section in template['section_order']:
            if section in resume_data:
                ordered_resume[section] = resume_data[section]
        
        # Keep other sections that aren't in template order
        for key, value in resume_data.items():
            if key not in ordered_resume:
                ordered_resume[key] = value
        
        # Add template metadata
        ordered_resume['_meta'] = {
            'template': template['name'],
            'line_spacing': template.get('line_spacing', 1.0),
            'fonts': template.get('fonts', {}),
            'margins': template.get('margins', {}),
            'layout': template.get('layout', 'single_column')
        }
        
        app_logger.info(f"Applied template: {template['name']}")
        return ordered_resume
    
    # ============================================================
    # Multi-Format Resume Parsing
    # ============================================================
    
    def parse_pdf_resume(self, pdf_path: str) -> Optional[Dict]:
        """
        Parse PDF resume using pdfminer.six (better than PyPDF2) + AI structuring
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            dict: Structured resume data
        """
        try:
            from pdfminer.high_level import extract_text
            
            app_logger.info(f"Parsing PDF resume: {pdf_path}")
            
            # Extract text from PDF (pdfminer.six preserves more structure)
            text = extract_text(pdf_path)
            
            app_logger.info(f"Extracted {len(text)} characters from PDF")
            
            # If text is too short, might be a scanned PDF
            if len(text) < 100:
                app_logger.warning("PDF text too short, might be scanned. Consider OCR.")
                return None
            
            # Use AI to structure the text
            return self._parse_with_ai(text)
        
        except Exception as e:
            app_logger.error(f"Failed to parse PDF: {e}")
            return None
    
    def parse_docx_resume(self, docx_path: str) -> Optional[Dict]:
        """
        Parse DOCX resume using docx2txt (better text extraction than python-docx)
        
        Args:
            docx_path: Path to DOCX file
        
        Returns:
            dict: Structured resume data
        """
        try:
            import docx2txt
            
            app_logger.info(f"Parsing DOCX resume: {docx_path}")
            
            # Extract all text including text from tables
            text = docx2txt.process(docx_path)
            
            app_logger.info(f"Extracted {len(text)} characters from DOCX")
            
            if len(text) < 100:
                app_logger.warning("DOCX text too short")
                return None
            
            # Use AI to structure the text
            return self._parse_with_ai(text)
        
        except Exception as e:
            app_logger.error(f"Failed to parse DOCX: {e}")
            return None
    
    def _parse_with_ai(self, text: str) -> Optional[Dict]:
        """
        Use AI to parse unstructured resume text into JSON
        CRITICAL: Preserve ALL details, especially:
        - Each job's individual bullet points
        - Skills categorization
        - All links and contact info
        
        Args:
            text: Raw resume text
        
        Returns:
            dict: Structured resume data
        """
        try:
            # Use full text, don't truncate
            text_to_parse = text[:5000] if len(text) > 5000 else text
            
            prompt = f"""Parse this resume into JSON. EXTRACT ALL INFORMATION WITHOUT LOSING ANY DETAILS.

Resume Text:
{text_to_parse}

CRITICAL RULES:
1. **PRESERVE EVERY BULLET POINT** under each job separately
2. **KEEP SKILLS CATEGORIZED** if they have categories (e.g., "EdTech Tools:", "AI & Development:")
3. **EXTRACT ALL URLs** (LinkedIn, GitHub, Portfolio)
4. **KEEP ALL JOB DETAILS** (each job must have its own details array)

Return EXACTLY this JSON structure:
{{
  "name": "Full Name",
  "contact": {{
    "email": "email@example.com",
    "phone": "phone number",
    "location": "city, province",
    "linkedin": "COMPLETE LinkedIn URL",
    "github": "COMPLETE GitHub URL", 
    "portfolio": "COMPLETE Portfolio URL"
  }},
  "summary": "complete professional summary",
  "experience": [
    {{
      "title": "Job Title 1",
      "company": "Company Name",
      "duration": "Start Date - End Date",
      "details": [
        "EVERY bullet point for THIS job",
        "Do NOT merge with other jobs",
        "Keep ALL achievements"
      ]
    }},
    {{
      "title": "Job Title 2",
      "company": "Company 2",
      "duration": "Start - End",
      "details": [
        "All bullet points for THIS job only"
      ]
    }}
  ],
  "education": [
    {{
      "title": "Degree, Major",
      "details": ["University, Dates"]
    }}
  ],
  "skills": {{
    "EdTech Tools and Instructional Design": "H5P, Articulate Suite, Canva, etc",
    "AI & Development": "RAG, Python, JavaScript, etc",
    "HR Practices": "Recruitment, etc"
  }},
  "projects": ["project if present"],
  "certifications": ["cert if present"]
}}

IMPORTANT:
- If skills have categories (e.g., "EdTech Tools:", "AI & Development:"), use dict format
- If skills are flat list, return array
- DO NOT merge bullet points from different jobs
- KEEP EVERY SINGLE DETAIL

Return ONLY valid JSON, no markdown, no extra text."""

            response = ai_agent.client.chat.completions.create(
                model=ai_agent.model,
                messages=[
                    {"role": "system", "content": "You are a resume parser. Extract ALL information exactly as written. Do NOT summarize or merge content. PRESERVE structure. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.05,  # Extremely low for accurate extraction
                max_tokens=3000
            )
            
            result = response.choices[0].message.content
            
            # Extract JSON from response
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()
            
            resume_data = json.loads(result)
            
            # Log what was extracted
            job_count = len(resume_data.get('experience', []))
            app_logger.info(f"Successfully parsed resume: {resume_data.get('name', 'Unknown')} - {job_count} jobs")
            
            return resume_data
        
        except Exception as e:
            app_logger.error(f"AI parsing failed: {e}")
            return None
    
    # ============================================================
    # AI Compression (1-page constraint)
    # ============================================================
    
    def compress_to_one_page(self, resume_data: Dict, job_description: str, 
                            template: Optional[Dict] = None, 
                            mode: str = "balanced") -> Optional[Dict]:
        """
        Compress resume to fit 1 page using AI
        
        Args:
            resume_data: Full resume
            job_description: Target job description
            template: Template config (for word limit)
            mode: 'aggressive', 'balanced', or 'conservative'
        
        Returns:
            dict: Compressed resume
        """
        try:
            # Calculate word limit based on template
            if template and template.get('layout') == 'two_column':
                base_limit = 700
            else:
                base_limit = 600
            
            # Adjust for line spacing
            if template:
                line_spacing = template.get('line_spacing', 1.0)
                if line_spacing < 1.0:
                    base_limit += 50  # Tighter spacing allows more words
            
            # Compression ratios
            ratios = {
                "aggressive": 0.80,  # 80% compression
                "balanced": 0.70,
                "conservative": 0.60
            }
            
            target_words = int(base_limit * (1 - ratios.get(mode, 0.70)))
            
            app_logger.info(f"Compressing resume to ~{target_words} words ({mode} mode)")
            
            # AI compression prompt - PRESERVE important info
            prompt = f"""You are compressing a resume to ~{target_words} words while PRESERVING ALL ESSENTIAL INFORMATION.

CURRENT: {self._count_words(resume_data)} words → TARGET: {target_words} words
MODE: {mode}

Job Description:
{job_description[:500]}...

Full Resume:
{json.dumps(resume_data, indent=2)}

ABSOLUTE REQUIREMENTS - DO NOT REMOVE:
1. **KEEP ALL contact info** (email, phone, LinkedIn URL, GitHub URL, Portfolio URL)
2. **KEEP EVERY job entry** (all titles, companies, dates)
3. **KEEP ALL education entries** 
4. **KEEP ALL SPECIFIC tool names** (e.g., "H5P, Articulate, Canvas" not just "EdTech Tools")
5. **KEEP ALL SPECIFIC skill names** (e.g., "Python, JavaScript" not just "Programming")
6. **PRESERVE JSON structure** exactly

HOW TO COMPRESS (only shorten bullet points):
✅ DO: Remove filler words ("Responsible for", "Assisted in", "Helped with")
✅ DO: Combine similar points ("Managed X and Y" → "Managed X, Y")
✅ DO: Use abbreviations where clear (Project Manager → PM)
❌ DON'T: Remove job entries
❌ DON'T: Generalize specific tool names
❌ DON'T: Remove contact links
❌ DON'T: Skip education or certifications

EXAMPLE:
Before: "Responsible for developing comprehensive training documentation and multimedia content using H5P, Articulate Suite, and Adobe Captivate that significantly improved internal processes"
After: "Developed training docs and multimedia (H5P, Articulate, Adobe Captivate), improving processes by 20%"

Return ONLY compressed JSON with SAME structure."""

            response = ai_agent.client.chat.completions.create(
                model=ai_agent.model,
                messages=[
                    {"role": "system", "content": "You are a resume compression expert. KEEP ALL job entries, contact links, and specific tool names. Only shorten descriptions. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Very low for consistency
                max_tokens=3500  # Increased to handle full resume
            )
            
            result = response.choices[0].message.content
            
            # Extract JSON
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()
            
            compressed = json.loads(result)
            
            # Add word count metadata
            word_count = self._count_words(compressed)
            compressed['_word_count'] = word_count
            
            app_logger.info(f"Compressed resume to {word_count} words")
            
            return compressed
        
        except Exception as e:
            app_logger.error(f"Compression failed: {e}")
            return None
    
    def _count_words(self, resume_data: Dict) -> int:
        """Count approximate words in resume"""
        text = json.dumps(resume_data)
        # Remove JSON syntax
        text = text.replace('{', '').replace('}', '').replace('[', '').replace(']', '')
        text = text.replace('"', '').replace(',', ' ')
        words = text.split()
        return len(words)

# Global instance
resume_generator = ResumeGenerator()

if __name__ == "__main__":
    # Test
    gen = ResumeGenerator()
    master = gen.load_master_resume()
    
    if master:
        print("Master resume loaded:")
        print(f"Name: {master.get('name')}")
        print(f"Experience items: {len(master.get('experience', []))}")
