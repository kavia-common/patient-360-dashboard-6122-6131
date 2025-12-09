#!/bin/bash
cd /home/kavia/workspace/code-generation/patient-360-dashboard-6122-6131/patient_portal_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

