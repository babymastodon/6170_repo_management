6.170 Repo Management
=====================

A set of tools to manage the student Github repos for the 6.170
web development class.

Usage
-----

#Load the python virtualenv

    >> virtualenv env.d
    >> . env.d/bin/activate
    >> pip install -r requirements.txt

#Getting the Github Auth Token

    >> python run.py get_auth_token

Prompts you for your github username and password, and stores the
resulting token in token.txt. Some of the commands will not run unless 
a valid auth token is present.

You must be an admin of the 6.170 repo for the commands to work properly.

#Creating Student Repositories

    >> python run.py make_repos project_name << "file containing list of students"

Reads from stdin. Each line should have two tokens separated by whitespace.
The first token is the student's athena name. The second is the github
id (username) beloning to the student.

Adds each user to the 6.170 organization, create a "team" for that user,
create a repo with the name "username_project" where "username" is the athena
name, and "project" is the project name provided on the command line. Will
give admin privilages of the repository to that user's team

Addtionally, the new repository will be initialized with a clone of the
github.com:6170/project_name.git repository.

    >> python run.py clone_repos project_name

Clone all repos beloning to the supplied project_name and store them
in a new subfolder of the ./cloned_repos directory.
