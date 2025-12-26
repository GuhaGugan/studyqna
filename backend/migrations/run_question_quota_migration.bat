@echo off
echo Running question quota migration...
cd /d %~dp0..
python migrations\add_question_quotas.py
pause

