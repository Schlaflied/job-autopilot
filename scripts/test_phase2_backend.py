"""
Phase 2 Backend Testing Script
测试 Resume Export 新功能
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.resume_generator import resume_generator
from modules.ats_scorer import ats_scorer
from modules.database import get_database_info, init_db

def test_all():
    """Run all Phase 2 backend tests"""
    print("="*60)
    print("🧪 Testing Phase 2: Backend Features")
    print("="*60 + "\n")
    
    # Test 1: Database Configuration
    print("1️⃣  Testing Database Configuration...")
    try:
        db_info = get_database_info()
        print(f"   ✅ Database Type: {db_info['type']}")
        print(f"   ✅ Location: {db_info['location']}")
        print(f"   ✅ Suitable For: {db_info['suitable_for']}")
        if 'file' in db_info:
            print(f"   ✅ File: {db_info['file']}")
        print()
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
        return False
    
    # Test 2: Template System
    print("2️⃣  Testing Template System...")
    try:
        template = resume_generator.load_template("classic_single_column")
        assert template is not None, "Template loading failed"
        assert template['name'] == "Classic Single Column"
        print(f"   ✅ Loaded template: {template['name']}")
        print(f"   ✅ Layout: {template['layout']}")
        print(f"   ✅ Line spacing: {template['line_spacing']}")
        print()
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
        return False
    
    # Test 3: Template Application
    print("3️⃣  Testing Template Application...")
    try:
        sample_resume = {
            "name": "Test User",
            "summary": "Test summary",
            "experience": [],
            "skills": ["Python", "SQL"]
        }
        
        applied = resume_generator.apply_template(sample_resume, template)
        assert '_meta' in applied
        assert applied['_meta']['template'] == template['name']
        print(f"   ✅ Template applied successfully")
        print(f"   ✅ Metadata added: {list(applied['_meta'].keys())}")
        print()
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
        return False
    
    # Test 4: Word Count
    print("4️⃣  Testing Word Count...")
    try:
        word_count = resume_generator._count_words(sample_resume)
        print(f"   ✅ Word count: {word_count} words")
        print()
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
        return False
    
    # Test 5: ATS Scorer
    print("5️⃣  Testing ATS Scorer...")
    try:
        test_resume_text = """
        Senior Product Manager with 5 years experience.
        Skills: Python, SQL, Product Management, Agile, User Research
        Led AI products with 30% revenue growth.
        """
        
        test_jd = """
        Looking for Senior Product Manager with:
        - Product Management experience
        - AI/ML product experience
        - Python and data analysis skills
        - Agile methodology
        - User research
        - Kubernetes experience
        """
        
        result = ats_scorer.score_resume(test_resume_text, test_jd)
        print(f"   ✅ ATS Score: {result['score']}/100")
        print(f"   ✅ Missing Keywords: {len(result['missing_keywords'])}")
        if result['missing_keywords']:
            print(f"   ✅ Example missing: {result['missing_keywords'][0]}")
        print(f"   ✅ Suggestions: {len(result['suggestions'])}")
        print()
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
        return False
    
    # Test 6: Database Initialization
    print("6️⃣  Testing Database Initialization...")
    try:
        init_db()
        print("   ✅ Database tables created/verified")
        print()
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
        return False
    
    # Summary
    print("="*60)
    print("✅ All Phase 2 Backend Tests Passed!")
    print("="*60)
    print("\n📝 Next Steps:")
    print("   1. Phase 3: Implement Frontend UI")
    print("   2. Create Resume Export page in Streamlit")
    print("   3. Integrate template selector, AI compression, ATS scoring")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = test_all()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
