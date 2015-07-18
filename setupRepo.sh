#!/bin/bash

echo "Setting up the Repositories"
python run.py make_repos $1 < $2

python run.py fetch_all_issues $1
python run.py create_new_issues $1

echo "Verifying that the repos were set up correctly"
python run.py verify_repos $1 < $2

rm issues_*.json
