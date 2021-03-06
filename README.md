6.170 Repo Management
=====================

A set of tools to manage a Github or Github enterprise instance that is setup for a class.

Usage
-----

###Load the python virtualenv

    >> virtualenv env.d
    >> . env.d/bin/activate
    >> pip install -r requirements.txt

To use the scripts, first clone the repository to a local folder on your computer.

###Configuration

To make sure that everything is configured correctly, first open the config.ini file, and fill in your github organization and your github enterprise IP. If you do not run a Github Enterprise instance, make sure that the enterprise field is false, and you can ignore the IP_ADDRESS field.

###Generating your Authentication Token

To use any of the functions described below, you will need an authenitication token. You can only have one token at any point in time. This token will be stored in a file called token.txt. DO NOT DELETE THIS TXT FILE. If you delete the file, you will need to also delete the key on the github website before you will be able to login to the API. In order to generate this token, you will need to be an admin of whatever organization(class) you are trying to use the scripts for.

    >> ./umbra.sh auth

###Setting up the Assignment Repositories

    >> ./umbra.sh setup <projectName> <studentFile>

Before you can run this command, you will need to have a base assignment repository, as well as a file that contains a list of students. For the assignment repository, make sure that you already have your starter code files in the repository, as this command will clone that repository into the student team repositories.

If you want to have the repositories setup with issues that your students will be able to see, comment on, and close, they need to be setup before you run this command. The issues cannot have any labels on them, nor can they ever have been closed. This command will also copy over pull requests, so it may be easier not to make pull requests to the base assignment repository, as they will also be visible to your students.

For the file that contains a list of students, there should be one team per line. It doesn't matter which order the pairs of github usernames are in, so long as they are separated by whitespace. There can be at most two people on a team. It is also possible for there to be a single person on the team. For this case, just put that person's github username on a line BY ITSELF, so that it would be a singleton.

    //Students File
    mchoi ycai
    ljthomas
    
This command will not work if you do not have an auth token, or you are not an Admin of your organization.

###Just Create a set of Repositories

    >>./umbra.sh baseMake <repoName> <studentsFile>
    
If a user needs to do debugging, or has no need for the validation or issue migration steps that occur in umbra setup, they can run this command. It will just create a set of repositories based off the students file, and push the contents of the base repository to them. It will not validate that the teams are correct, nor will it migrate any of the issues from the base repository over to the newly created repositories. If you decide you do want to migrate over issues, see the umbra migrateIssues command.

###Collect Student Repositories

    >> ./umbra.sh collect <ProjectName>

Clone all repos beloning to the supplied project_name and store them
in a new subfolder of the ./cloned_repos directory. These repositories are pushable, so you can put a scores.txt file in them, and students will be able to see that if you commit and push while in the cloned repository.

###Removing Repositories

    >> ./umbra.sh clean <BaseProject>
    
This command will remove all auto-generated repositories that were created from the files in the Base Repository. This command will not delete the base repository though. If there was an error in the setupRepos process, and you need to start over, you can run this command, and it will destroy all of the autogenerated repositories. It will not destroy any teams that have been auto-generated, and those can be cleaned up more easily by hand.

###Migrating issues after a repository has been created

    >>./umbra.sh migrateIssues <BaseProject>
    
This command will migrate all issues from the BaseProject repository to the autogenerated repositories. If there are already issues there that match the issues being migrated, they will be duplicated. This method is mostly for debugging, if a user needs to create the repositories and migrate the issues in different steps. 

###References

Most of the code and a good amount of the Documentation comes from the MIT 6170 Web Development Project. Their Repository can be found at https://github.com/hogbait/6170_repo_management


