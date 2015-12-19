#!/bin/bash

#The umbra script is a command line based tool that will allow a
#user to complete a variety of tasks. These include setting up authorization,
#creating student teams and repositories, migrating issues, deleting
#repositories, and collecting assignments. To see a full list of commands
#run ./umbra.sh without any arguments. This program is a wrapper for the
#run.py program, and calls tasks directly from that program.

if [ "$1" == auth ]; then
    python run.py get_auth_token
    exit 1;
fi

#This will execute a full create/validate/migrateIssues for a homework assignment
if [ "$1" == setup ]; then
    if [ "$2" == "" ] || [ "$3" == "" ] ; then
	echo "No repository name / students file selected. Correct usage is ./umbra.sh setup repoName studentFile"
	exit 1;
    fi
   python run.py make_repos $2 < $3
   python run.py fetch_all_issues $2
   python run.py create_new_issues $2
   python run.py verify_repos $2 < $3
   rm issues_*.json
   exit 1;
fi

#This will only create the student team and assignment repositories. No validation occurs, and no issue migration happens
if [ "$1" == baseMake ]; then
    if [ "$2" == "" ] || [ "$3" == "" ] ; then
	echo "No repository name / students file selected. Correct usage is ./umbra.sh baseMake repoName studentFile"
	exit 1;
    fi
    python run.py make_repos $2 < $3
    exit 1;
fi

#This will only migrate issues from a base repository to all repositories matching the pattern baseRepo_*
if [ "$1" == migrateIssues ]; then
    if [ "$2" == "" ]; then
	echo "No repository name selected. Correct usage is ./umbra.sh migrateIssues baseRepoName"
	exit 1;
    fi
   python run.py fetch_all_issues $2
   python run.py create_new_issues $2
   rm issues_*.json
   exit 1;
fi

#This will remove all autogenerated repositories. NOTE: THIS DOES NOT REMOVE TEAMS, AND IS IRREVERSABLE.
if [ "$1" == clean ]; then
    if [ "$2" == "" ]; then
	echo "No repository name selected. Correct usage is ./umbra.sh clean baseRepoName"
	exit 1;
    fi
    python run.py delete_repos $2
    exit 1;
fi

#Collects a homework assignment, storing it in the directory ./cloned_repos/BaseName_Timestamp
if [ "$1" == collect ]; then
    if [ "$2" == "" ]; then
	echo "No repository name selected. Correct usage is ./umbra.sh collect baseRepoName"
	exit 1;
    fi
    python run.py clone_repos $2
fi


echo "Incorrect usage. Correct usage is: ./umbra.sh [auth|setup|baseMake|migrateIssues|clean|collect] [optional_repo_name] [optional_student_file]"
