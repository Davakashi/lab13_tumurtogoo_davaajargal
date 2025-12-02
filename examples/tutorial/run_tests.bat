@echo off
REM Script to run all tests and generate coverage reports for Windows

cd /d "%~dp0"

echo Installing dependencies...
pip install -q pytest pytest-cov hypothesis

echo.
echo === Running Pynguin Tests ===
pytest tests_pynguin --cov=flaskr --cov-report=html:coverage_pynguin -q

echo.
echo === Running Hypothesis Tests ===
pytest tests_hypothesis --cov=flaskr --cov-report=html:coverage_hypothesis -q

echo.
echo === Running AI Tests ===
pytest tests_ai --cov=flaskr --cov-report=html:coverage_ai -q

echo.
echo === Coverage Reports Generated ===
echo Pynguin: coverage_pynguin\html\index.html
echo Hypothesis: coverage_hypothesis\html\index.html
echo AI: coverage_ai\html\index.html

pause

