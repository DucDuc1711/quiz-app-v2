import subprocess
import sys

venv_python = r"c:\Users\nuyan\Downloads\du an python\quiz-app-v2\backend\.venv\Scripts\python.exe"

result = subprocess.run([venv_python, "-m", "pytest", "backend/tests", "-q", "--tb=short"], 
                        capture_output=True, text=True, timeout=180)
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
print("RETURNCODE:", result.returncode)
sys.exit(result.returncode)