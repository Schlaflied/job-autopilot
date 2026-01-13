"""
Test all dependencies for Resume Export feature
测试所有新增依赖是否正确安装
"""
import sys

def test_dependencies():
    """Test all required dependencies"""
    print("🔍 Testing Resume Export dependencies...\n")
    
    deps = [
        ("PIL", "Pillow"),
        ("PyPDF2", "PyPDF2"),
        ("streamlit_sortables", "streamlit-sortables"),
        ("pdf2image", "pdf2image"),
        ("spacy", "spacy"),
        ("sklearn", "scikit-learn"),
    ]
    
    failed = []
    
    for mod, pkg in deps:
        try:
            __import__(mod)
            print(f"✅ {pkg}")
        except ImportError as e:
            print(f"❌ {pkg}: {e}")
            failed.append(pkg)
    
    print("\n" + "="*50)
    
    if failed:
        print(f"\n❌ {len(failed)} dependencies failed:")
        for pkg in failed:
            print(f"   - {pkg}")
        print("\nInstall missing dependencies:")
        print(f"pip install {' '.join(failed)}")
        sys.exit(1)
    else:
        print("\n✅ All dependencies installed successfully!")
        print("\n📦 Testing spacy model...")
        
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
            print("✅ spacy model 'en_core_web_sm' loaded")
        except OSError:
            print("⚠️  spacy model 'en_core_web_sm' not found")
            print("Download it with: python -m spacy download en_core_web_sm")
        
        print("\n🎉 Resume Export dependencies are ready!")


if __name__ == "__main__":
    test_dependencies()
