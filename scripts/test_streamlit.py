"""
Quick test: Launch Streamlit App
快速测试：启动 Streamlit 应用
"""
import subprocess
import sys

print("🚀 Launching Job Autopilot Streamlit App...")
print("\n📋 Test Checklist:")
print("   1. Navigate to '📄 Resume Export' page")
print("   2. Upload a resume file (MD/PDF/DOCX)")
print("   3. Select a template")
print("   4. Try AI compression")
print("   5. Calculate ATS score")
print("   6. Export resume")
print("\n" + "="*60)
print("Starting Streamlit...\n")

# Run streamlit
subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.port=8501"])
