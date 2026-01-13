"""
Generate template preview images for Resume Export feature
自动生成 4 张模板预览图：600x800px JPG

依赖：reportlab, pdf2image, Pillow, poppler
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.resume_generator import resume_generator
from pdf2image import convert_from_path
from PIL import Image

# Poppler path (user's installation)
POPPLER_PATH = r"D:\Windows Poppler\poppler-25.12.0\Library\bin"

def generate_preview_images():
    """Generate template preview images automatically"""
    
    print("🎨 Generating template preview images...\n")
    
    # Different sample data for each template to show variety
    sample_resumes = {
        "classic_single_column": {
            "name": "John Smith",
            "contact": {
                "email": "john.smith@example.com",
                "phone": "(416) 555-0123",
                "location": "Toronto, ON",
                "linkedin": "linkedin.com/in/johnsmith"
            },
            "summary": "Experienced Software Engineer with 7+ years in full-stack development. Proven track record of building scalable web applications and leading technical teams.",
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "duration": "2020 - Present",
                    "details": [
                        "Led development of microservices architecture, improving system reliability by 40%",
                        "Mentored team of 5 junior developers, reducing onboarding time by 30%"
                    ]
                },
                {
                    "title": "Software Engineer",
                    "company": "StartupCo",
                    "duration": "2017 - 2020",
                    "details": [
                        "Built RESTful APIs serving 10K+ requests/minute",
                        "Implemented CI/CD pipeline, reducing deployment time from hours to minutes"
                    ]
                }
            ],
            "education": [
                {"title": "B.Sc. Computer Science", "details": ["University of Toronto, 2017"]}
            ],
            "skills": ["Python", "JavaScript", "React", "Node.js", "Docker", "AWS", "PostgreSQL"]
        },
        "modern_single_column": {
            "name": "Emily Chen",
            "contact": {
                "email": "emily.chen@example.com",
                "phone": "(647) 555-0456",
                "location": "Vancouver, BC",
                "linkedin": "linkedin.com/in/emilychen"
            },
            "summary": "Creative Product Designer with 5+ years specializing in UX/UI design for SaaS products. Passionate about creating intuitive user experiences.",
            "skills": ["Figma", "Sketch", "Adobe XD", "User Research", "Prototyping", "Design Systems"],  # Skills first
            "experience": [
                {
                    "title": "Lead Product Designer",
                    "company": "Design Studio",
                    "duration": "2021 - Present",
                    "details": [
                        "Redesigned core product, increasing user engagement by 35%",
                        "Established design system used across 8 product teams"
                    ]
                }
            ],
            "education": [
                {"title": "BFA Graphic Design", "details": ["Emily Carr University, 2019"]}
            ]
        },
        "classic_two_column": {
            "name": "David Lee",
            "contact": {
                "email": "david.lee@example.com",
                "phone": "(778) 555-0789",
                "location": "Calgary, AB"
            },
            "skills": ["Project Management", "Agile", "Scrum", "Budget Planning", "Stakeholder Management"],
            "education": [
                {"title": "MBA", "details": ["University of Alberta, 2018"]},
                {"title": "B.Eng Industrial Engineering", "details": ["McGill University, 2015"]}
            ],
            "summary": "Results-driven Project Manager with 6+ years delivering complex technical projects on time and under budget.",
            "experience": [
                {
                    "title": "Senior Project Manager",
                    "company": "Global Enterprises",
                    "duration": "2019 - Present",
                    "details": [
                        "Managed $2M+ projects with teams of 15+ members across 3 countries",
                        "Delivered 12 major projects with 98% on-time completion rate"
                    ]
                }
            ]
        },
        "modern_two_column": {
            "name": "Sarah Johnson",
            "contact": {
                "email": "sarah.j@example.com",
                "phone": "(514) 555-9012",
                "location": "Montreal, QC"
            },
            "skills": ["Data Analysis", "Python", "SQL", "Tableau", "Machine Learning", "Statistics"],
            "certifications": ["Google Data Analytics Certificate", "AWS Certified Solutions Architect"],
            "summary": "Data Analyst with 4+ years turning complex data into actionable business insights. Expertise in predictive modeling and data visualization.",
            "experience": [
                {
                    "title": "Data Analyst",
                    "company": "Analytics Inc",
                    "duration": "2020 - Present",
                    "details": [
                        "Built predictive models that improved sales forecasting accuracy by 25%",
                        "Created interactive dashboards serving 50+ stakeholders daily"
                    ]
                }
            ],
            "education": [
                {"title": "M.Sc. Data Science", "details": ["McGill University, 2020"]}
            ]
        }
    }
    
    templates = [
        ("classic_single_column", "classic_single.jpg"),
        ("modern_single_column", "modern_single.jpg"),
        ("classic_two_column", "classic_two.jpg"),
        ("modern_two_column", "modern_two.jpg")
    ]
    
    os.makedirs("assets/templates", exist_ok=True)
    
    for template_name, jpg_name in templates:
        print(f"📄 Generating preview for {template_name}...")
        
        try:
            # Get sample resume for this template
            sample_resume = sample_resumes.get(template_name, sample_resumes["classic_single_column"])
            
            # Apply template first
            template_config = resume_generator.load_template(template_name)
            if template_config:
                sample_resume = resume_generator.apply_template(sample_resume, template_config)
            
            # 1. Generate PDF with template
            pdf_filename = f"temp_{template_name}.pdf"
            pdf_path = resume_generator.export_pdf(sample_resume, pdf_filename)
            
            # 2. Convert PDF to PNG (first page only)
            images = convert_from_path(
                pdf_path,
                dpi=150,
                first_page=1,
                last_page=1,
                poppler_path=POPPLER_PATH
            )
            png_image = images[0]
            
            # 3. Crop to 3:4 aspect ratio (600x800)
            width, height = png_image.size
            target_aspect = 600 / 800  # 0.75
            current_aspect = width / height
            
            if current_aspect > target_aspect:
                # Too wide, crop width
                new_width = int(height * target_aspect)
                left = (width - new_width) // 2
                png_image = png_image.crop((left, 0, left + new_width, height))
            else:
                # Too tall, crop height
                new_height = int(width / target_aspect)
                top = (height - new_height) // 2
                png_image = png_image.crop((0, top, width, top + new_height))
            
            # 4. Resize to exactly 600x800
            png_image = png_image.resize((600, 800), Image.LANCZOS)
            
            # 5. Save as JPG
            jpg_path = f"assets/templates/{jpg_name}"
            png_image.convert("RGB").save(jpg_path, "JPEG", quality=90)
            
            # Clean up temp PDF
            os.remove(pdf_path)
            
            print(f"✅ Saved {jpg_path} (600x800px)\n")
        
        except Exception as e:
            print(f"❌ Failed to generate {template_name}: {e}\n")
            continue
    
    print("🎉 All template previews generated successfully!")
    print("\nGenerated files:")
    for _, jpg_name in templates:
        jpg_path = f"assets/templates/{jpg_name}"
        if os.path.exists(jpg_path):
            size_kb = os.path.getsize(jpg_path) / 1024
            print(f"  ✅ {jpg_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    try:
        generate_preview_images()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check poppler is installed: pdftoppm -h")
        print(f"2. Verify poppler path: {POPPLER_PATH}")
        print("3. Install dependencies: pip install pdf2image Pillow reportlab")
        sys.exit(1)
