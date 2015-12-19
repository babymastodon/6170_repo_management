# -*- coding: utf-8 -*-

import sys, os
import requests
import inspect
import json
import getpass
import datetime
import re

from ConfigParser import SafeConfigParser

tasks = []

#Sets up the organization name and the IP address of the github instance
parser=SafeConfigParser()
parser.read('config.ini')
ORG_NAME=parser.get('class_setup','org_name')
IP_ADDRESS=parser.get('server_setup','ip_address')
ENTERPRISE=parser.get('server_setup','enterprise')

class TaskFailure(Exception):
    pass


#tasks cannot have kwargs
class Task(object):
    def __init__(self, f, name, help_text, args):
        self.f = f
        self.help_text = help_text
        self.args = args
        self.name = name
    def __call__(self, *args):
        if len(args) != len(self.args):
            l = len(self.args)
            raise TaskFailure("{} expects {} argument{}: {}".format(
                self.name, l, 's' if l!=1 else '',' '.join(self.args)))
        self.f(*args)
        print "Success!!"

def task(help_text=''):
    def decorator(f):
        task_name = f.__name__
        args = inspect.getargspec(f).args
        t = Task(f, task_name, help_text, args)
        tasks.append(t)
        return t
    return decorator

def usage():
    print
    print "Usage:"
    print
    print "    >> python run.py task_name arg1 arg2 ..."
    print
    print
    print "Available Tasks:"
    for t in tasks:
        print
        print "    >> python run.py {} {}".format(t.name,' '.join(t.args))
        print
        print "        {}".format(t.help_text.strip().replace('\n','\n        '))
    print

def run():
    try:
        print "Running Task"
        task_name = sys.argv[1]
    except:
        task_name = None
    for t in tasks:
        if t.name == task_name:
            try:
                t(*sys.argv[2:])
            except TaskFailure as e:
                print
                print e.message
                print
            return
    usage()

##########################################
#
#   Task definitions
#
##########################################


class GithubWrapper(object):
    def __init__(self, token):
        self.token = token
    """
    This method has the url for the github instance API. It must be this way, with the trailing /
    so that it can connect and authenticate when you generate your authentication token.
    """
    @staticmethod
    def url(s):
        if(ENTERPRISE == "False"):
            return "https://api.github.com/{}".format(s.strip('/'))
        else:
            return "https://{}/api/v3/{}".format(IP_ADDRESS,s.strip('/')) 

    def do(self,f, path, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['Authorization'] = "token {}".format(self.token)
        url = self.url(path)
        return getattr(requests,f)(url,**kwargs)

    def __getattr__(self,name):
        if name in ['get','post','delete','put','head','options']:
            def tmp(path,*args,**kwargs):
                return self.do(name,path,**kwargs)
            return tmp

    def has_admin_access(self):
        path = '/orgs/{}'.format(ORG_NAME)
        r = self.post(path,data=json.dumps({}))
        return r.status_code == 200

    """
    Attempts to load the api using the token that was generated when the user ran get_auth_token
    """
    @staticmethod
    def load():
        token = ''
        try:
            with open("token.txt") as f:
                token = f.read().strip()
        except:
            pass
        g = GithubWrapper(token)
        if not g.has_admin_access():
            raise TaskFailure("Github api token is either missing or invalid. "\
                    "Please run the get_auth_token task to create a new one")
        return g

    def save(self):
        with open("token.txt","w") as f:
            f.write(self.token)

    """
    This method will look for a team name that is defined by the users. If it exists, it will return
    that team, otherwise it will create it, and then return the team.
    """
    def get_or_create_team(self,team_name):
        team = self.get_team(team_name)
        if team == None:
            data = {
                    "name":team_name,
                    "permission":"push",
                    }
            print "Creating team with name {}".format(team_name)
            r = self.post("/orgs/{}/teams".format(ORG_NAME), data=json.dumps(data))
            if r.status_code != 201:
                raise TaskFailure("Failed to create team")
            return r.json()
        else:
            return team

    """
    This method just looks for a team that is defined by the team name, and will return it.
    """
    def get_team(self, team_name):
        all_teams = self.get("orgs/{}/teams".format(ORG_NAME)).json()
        all_teams_dict = dict((x['name'],x['id']) for x in all_teams)
        if team_name not in all_teams_dict:
            return None
        else:
            team_id = all_teams_dict[team_name]
            print "Fetching team {}".format(team_id)
            r = self.get("/teams/{}".format(team_id))
            if r.status_code != 200:
                raise TaskFailure("Failed to fetch team")
        return r.json()

    """
    This method adds a user to a team, where both the team member as well as the user's name
    """
    def add_user_to_team(self, github_name, team):
        print github_name
        print "Adding user {} to team {}".format(github_name, team['id'])
        print "Added a member"
        r = self.put("/teams/{}/members/{}/".format(team['id'], github_name),headers={"Content-Length":'0'})
        if r.status_code != 204:
            raise TaskFailure("Failed to add user to team, user does not exist.")

    """
    Formats the new team name as the first(alphabet) partner_second Partner. It will then add both to the team.
    """
    def add_single_user(self, firstPart):
        team_name = "{}".format(firstPart)
        team = self.get_or_create_team(team_name)
        self.add_user_to_team(firstPart, team)
        return team


        
    """
    Formats the new team name as the first(alphabet) partner_second Partner. It will then add both to the team.
    """
    def add_user(self, firstPart, secondPart):
        team_name = "{}_{}".format(firstPart,secondPart)
        team = self.get_or_create_team(team_name)
        self.add_user_to_team(firstPart, team)
        self.add_user_to_team(secondPart, team)
        return team

    """
    Creates a new repository and has it assigned to a team, denoted by team_id
    """
    def create_repo(self, repo_name, team_id):
        data = {
                "name":repo_name,
                "private":True,
                "team_id":team_id,
                }
        r = self.post('/orgs/{}/repos'.format(ORG_NAME),data=json.dumps(data))
        if r.status_code != 201:
            raise TaskFailure("Failed to create repo: {}".format(r.content))
        return r.json()

    """
    Allows a team to push to and edit a repository
    """
    def add_repo_to_team(self, repo_name, team):
        print "Adding repo {} to team {}".format(repo_name, team['id'])
        r = self.put("/teams/{}/repos/{}/{}".format(team['id'],ORG_NAME,repo_name),headers={"Content-Length":'0'})
        if r.status_code != 204:
            raise TaskFailure("Failed to add repo to team: {}".format(r.content))

    """
    Removes both push permission as well as edit permission for a team's repository
    """
    def remove_repo_from_team(self, repo_name, team):
        print "Removing repo {} from team {}".format(repo_name, team['id'])
        r = self.delete("/teams/{}/repos/{}/{}".format(team['id'],ORG_NAME,repo_name),headers={"Content-Length":'0'})
        if r.status_code != 204:
            raise TaskFailure("Failed to remove repo from team: {}".format(r.content))
    
    def iterate_endpoint(self, endpoint):
        counter = 1
        while True:
            r = self.get(endpoint,params={'page':counter, 'per_page':1000})
            repos = r.json()
            if len(repos) == 0:
                return
            for r in repos:
                yield r
            counter += 1

    def iterate_repos(self):
        return self.iterate_endpoint("orgs/{}/repos".format(ORG_NAME))

    def iterate_teams(self):
        #TODO: github fixed the iteration bug with the /repos endpoint,
        # but someone should pester them about the /teams endpoint
        r = self.get("/orgs/{}/teams".format(ORG_NAME))
        return r.json()

    def fetch_members(self):
        print "Fetching all members of {}".format(ORG_NAME)
        r = self.get("/orgs/{}/members".format(ORG_NAME),headers={"Content-Length":'0'})
        if r.status_code != 200:
            raise TaskFailure("Failed to fetch members list: {}".format(r.content))
        return r.json()

    def fetch_team_members(self, team):
        print "Fetching all members of {}".format(team["name"])
        r = self.get("/teams/{}/members".format(team["id"]),headers={"Content-Length":'0'})
        if r.status_code != 200:
            raise TaskFailure("Failed to fetch members list: {}".format(r.content))
        return r.json()

    """
    Gets all the comments from a specific repository, specifically its pull request comments
    """
    def fetch_repo_comments(self, repo):
        print "Getting comments for {}".format(repo)
        r = self.get("/repos/{}/{}/pulls/comments".format(ORG_NAME,repo))
       # r = self.get("/repos/{}/{}/pulls/comments".format(ORG_NAME, repo))
        if r.status_code != 200:
            raise TaskFailure("Failed to fetch comments: {}".format(r.content))
        return r.json()

    """
    Finds all the issues associated with a repository and returns them as a list
    """
    def fetch_repo_issues(self, repo, issueNum):
        print "Getting issues for {}".format(repo)
        r = self.get("/repos/{}/{}/issues/{}".format(ORG_NAME,repo,issueNum))
        if r.status_code != 200:
            return
        content = r.json()
        elements = []
        elements.append(content[u'title'])  # append the title of the issue to the list
        elements.append(content[u'body'])   # append the body of the issue to the list
        return elements

    """
    Adds an issue by adding json through the POST command with the Github API
    """
    def add_issue_to_repo(self, repo, issueTitle, issueBody):
        print "Adding issues to {}".format(repo)
        r = self.post("/repos/{}/{}/issues".format(ORG_NAME,repo),json={"title":issueTitle, "body":issueBody})
        if r.status_code != 201:
            raise TaskFailure("Failed to create issues: {}".format(r.content))

    """
    Deletes a repository by sending the delete signal through the Github API
    """
    def delete_repo(self,repo):
        print "Deleting Repository {}".format(repo)
        r = self.delete("/repos/{}/{}".format(ORG_NAME,repo))
        if r.status_code != 204:
            raise TaskFailure("Failed to destroy repository: {}".format(r.content))
                        
        
    

@task("""
Gets a Github API token and stores it in token.txt
The token will be used for all subsequent requests
to the Github API.
""")
def get_auth_token():
    print ORG_NAME
    print "Enter your Github credentials"
    username = raw_input("Username: ")
    password = getpass.getpass("Password: ")
    url = GithubWrapper.url('/authorizations')
    data = {
            "scopes":['gist','delete_repo','repo:status',
                'repo','public_repo','user'],
            "note":"Github education repo management token",
            }
    r = requests.post(url,data=json.dumps(data),auth=(username,password))
    if r.status_code != 201:
        raise TaskFailure("Your github credentials were invalid")
    g = GithubWrapper(r.json()['token'])
    if not g.has_admin_access():
        raise TaskFailure("Your github account does not have admin access to "\
                "the organization. Please make yourself an owner.")
    g.save()


@task("""
Creates a repo with the name "username_project"

Reads from stdin. Each line should have two tokens
separated by whitespace. The first token is the
student's athena name. The second is the github id
(username) beloning to the student.

The repository will be initialized with the
a clone of git@YourHostName.com:{}/project_name.git
""".format(ORG_NAME))
def make_repos(project_name):
    g = GithubWrapper.load()
    failures = []
    try:
        cwd = os.getcwd()
        os.chdir("/tmp")
        os.system("rm -rf {}".format(project_name))
        handout_code_repo = "https://{}/{}/{}.git".format(IP_ADDRESS,ORG_NAME,project_name)
        print handout_code_repo
        clone_successful = os.system("git clone {}".format(handout_code_repo)) == 0
        if not clone_successful:
            raise TaskFailed("Could not clone {}. Make sure that the repository exists, and that"\
                    "your github private key is installed on this system".format(project_name))
        os.chdir(project_name)
        #pull all of the remote branches
        os.system("git pull --all")
        os.system("for branch in `git branch -a | grep remotes | grep -v HEAD | grep -v master`; do git branch --track ${branch##*/} $branch; done;")
        for line in sys.stdin:
            if not line:
                print "Encountered empty line. Exiting"
                return
            print "Processing: {}".format(line)
            failures.append(line)
            try:
                usernames = line.split()
                usernames.sort()
                if(len(usernames) == 1):
                   firstPart = usernames[0]
                   secondPart = ""
                else:
                   firstPart = usernames[0]
                   secondPart = usernames[1]
            except:
                print 'Line: "{}" must be of the form "first_partner second_partner". Skipping'.format(line)
                continue
            try:
                print 'Adding user'
                if (secondPart == ""):  #Added singleton teams
                   team=g.add_single_user(firstPart)
                else:
                   team = g.add_user(firstPart,secondPart)
            except Exception as e:
                print "Failed to add user: {}".format(e)
                continue
            try:
                if (secondPart == ""):  #Adding singleton Repos
                   repo_name = "{}_{}".format(project_name,firstPart)
                   print 'Creating repo: {}'.format(repo_name)
                   repo = g.create_repo(repo_name,team['id'])
                else:
                   repo_name = "{}_{}_{}".format(project_name,firstPart,secondPart)
                   print 'Creating repo: {}'.format(repo_name)
                   repo = g.create_repo(repo_name,team['id'])
            except Exception as e:
                print "Failed to create repo: {}".format(e)
                continue
            print "Pushing the handout code"
            push_successful = os.system("git push --all {}".format(repo['clone_url'])) == 0
            if not push_successful:
                print "Failed to initialize repository with the handout code"
            failures = failures[:-1]
    finally:
        print "Failures: {}".format(failures)
        os.system("rm -rf {}".format(project_name))
        os.chdir(cwd)

@task("""
Clones all repos beloning to the supplied project_name
and stores them in a new subfolder of the ./cloned_repos
directory.
""")
def clone_repos(project_name):
    g = GithubWrapper.load()
    dirname = os.path.join("cloned_repos","{} {}".format(
        project_name, str(datetime.datetime.now())))
    os.makedirs(dirname)
    try:
        cwd = os.getcwd()
        os.chdir(dirname)
        for r in g.iterate_repos():
            if re.match(r'{}+.*$'.format(project_name),r['name']):
                print "Cloning {}".format(r['ssh_url'])
                clone_success = os.system("git clone {}".format(r['ssh_url'])) == 0
                if not clone_success:
                    print "Clone Failed"
    finally:
        os.chdir(cwd)

@task("""
Reads from stdin. Same input format as make_repos.

Verifies that all of the repos in the provided list of
names have been created and have the proper permissions.
""")
def verify_repos(project_name):
    g = GithubWrapper.load()
    all_repos = list(g.iterate_repos())
    all_repos_dict = dict((x['name'],x) for x in all_repos)
    all_teams = list(g.iterate_teams())
    all_teams_dict = dict((x['name'],x) for x in all_teams)
    for line in sys.stdin:
        if not line:
            print "Encountered empty line. Exiting"
            return
        print "Processing: {}".format(line)
        try:
            usernames = line.split()
            usernames.sort()
            if(len(usernames) == 1):
                firstPart = usernames[0]
                secondPart = ""
            else:
                firstPart = usernames[0]
                secondPart = usernames[1]
        except:
            print 'Line: "{}" must be of the form "firstPart secondPart". Skipping'.format(line)
            continue
        
        if (secondPart == ""):  #Adding singleton Repos
            repo_name = "{}_{}".format(project_name,firstPart)
            print 'Verifying repo: {}'.format(repo_name)
            team_name = "{}".format(firstPart)
        else:
            repo_name = "{}_{}_{}".format(project_name,firstPart,secondPart)
            print 'Verifying repo: {}'.format(repo_name)
            team_name = '{}_{}'.format(firstPart,secondPart)
            
        if not team_name in all_teams_dict:
            print "Missing team: {}".format(team_name)
            continue
        team_id  = all_teams_dict[team_name]['id']
        team = g.get("teams/{}".format(team_id)).json()
        if not team['members_count']==1 | 2:
            print "Team should only have one member: {}".format(team_name)
        if g.get("teams/{}/members/{}".format(team_id,secondPart)).status_code != 204:
            print "Missing membership: {} should be a member of team {}".format(secondPart, team_name)
        if not repo_name in all_repos_dict:
            print "Missing repo: {}".format(repo_name)
            continue
        repo_name = all_repos_dict[repo_name]['name']
        if g.get("teams/{}/repos/{}/{}".format(team_id, ORG_NAME, repo_name)).status_code != 204:
            print "Team is missing repo: {} should be controlled by team {}".format(repo_name, team_name)

@task("""
Reads from stdin. Input should be same as make_repos

Adds all students to the specified github team.
""")
def add_users_to_team(team_name):
    g = GithubWrapper.load()
    failures = []
    for line in sys.stdin:
        if not line:
            print "Encountered empty line. Exiting"
            return
        print "Processing: {}".format(line)
        try:
            usernames = line.split()
            print "Split"
            usernames.sort()
            print usernames
            if(len(usernames) == 1):
                firstPart = usernames[0]
                secondPart = ""
            else:
                firstPart = usernames[0]
                secondPart = usernames[1]
        except:
            print 'Line: "{}" must be of the form "first_partner second_partner". Skipping'.format(line)
            continue
        try:
            team = g.get_or_create_team(team_name)
            g.add_user_to_team(secondPart, team)
        except Exception as e:
            print "Failed to add {} to team. {}".format(secondPart, e)
            failures.append(secondPart)
            continue
    print "Failures: {}".format(failures)

@task("""
Takes two arguments: project_name and team_name.

Removes all repositories belonging to project_name from the team "team_name".
This task is useful for undo-ing making all repositories for a specific project
public.
""")
def remove_project_from_team(project_name, team_name):
    g = GithubWrapper.load()
    team = g.get_or_create_team(team_name)
    print team
    failures = []
    for r in g.iterate_repos():
        try:
            if re.match("{}+.*".format(project_name),r['name']):
                g.remove_repo_from_team(r['name'],team)
        except:
            failures.append(r['name'])
    print "Failures: {}".format(failures)

@task("""
Takes two arguments: project_name and team_name.

Adds all repositories belonging to project_name to
the team "team_name". This task is useful for
making all repositories for a specific project public.
""")
def add_project_to_team(project_name, team_name):
    g = GithubWrapper.load()
    team = g.get_or_create_team(team_name)
    print team
    failures = []
    for r in g.iterate_repos():
        try:
            if re.match("{}+.*".format(project_name),r['name']):
                g.add_repo_to_team(r['name'],team)
        except:
            failures.append(r['name'])
    print "Failures: {}".format(failures)

@task("""
Reads input from stdin. The first token is the team
    name. Each following token is a github name of
    a team member.
""")
def make_final_project_repos():
    g = GithubWrapper.load()
    failures = []
    for line in sys.stdin:
        print "processing: ".format(line)
        try:
            tokens = line.split()
            team_name = tokens[0]
            members = tokens[1:]
            team = g.get_or_create_team(team_name)
            for m in members:
                g.add_user_to_team(m, team)
            g.create_repo(team_name, team['id'])
        except Exception as e:
            print e
            failures.append(line)
    print "Failures: {}".format(failures)

@task("""
Returns all members in the org, where a member is defined as someone who
belongs to at least 1 team in the organization.
""")
def fetch_members():
    g = GithubWrapper.load()
    members = []
    members.extend(g.fetch_members())

    for member in members:
        print member['login']

    print "{} members found".format(len(members))

@task("""
Returns a list of all members belonging to the
given team.
""")
def fetch_team_members(team_name):
    g = GithubWrapper.load()
    team = g.get_team(team_name)
    if team == None:
        raise TaskFailure("Team {} does not exist".format(team_name))

    members = []
    members.extend(g.fetch_team_members(team))

    for member in members:
        print member['login']

    print "{} members found".format(len(members))

    
@task("""
Finds all repos that contains proj_name and generates a formatted HTML file
with all comments. Provides a link to pull request comments 
""")
def fetch_all_comments(proj_name):
    OUTPUT_FILE = "comments_{}.html".format(proj_name.replace(' ',')'))
    # The HTML template is split into intro and conclusion files so that
    # output can be written progressively.
    INTRO = open('html/comments_intro.html').read()
    CONCLUSION = open('html/comments_conclusion.html').read()
    COMMENT_TEMPLATE = open('html/comment.html').read()

    print "Fetching all comments for projects containing {}".format(proj_name)
    print "Generating output in {}".format(OUTPUT_FILE)

    g = GithubWrapper.load()
    with open(OUTPUT_FILE, "w") as f:
        f.write(INTRO)
        f.write("<h1>Pull request comments: {}</h1>".format(proj_name))
        for r in filter(lambda r: proj_name in r['name'], g.iterate_repos()):
            f.write('<h2><a href="{}">{}</a></h2>'.format(r['html_url'], r['name']))
            comments = g.fetch_repo_comments(r['name'])
            if comments:
                f.write("<ul>")
                for comment in comments:
                    content = COMMENT_TEMPLATE.format(
                        comment['user']['avatar_url'], comment['user']['login'],
                        comment['user']['login'], comment['body'].encode('ascii', 'xmlcharrefreplace'),
                        comment['_links']['html']['href'], comment['path']
                    )
                    f.write('<li>{}</li>'.format(content))
                f.write("</ul>")
        now = datetime.datetime.now()
        #now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") - probably outdated
        f.write(CONCLUSION.format(now))


@task("""
Finds all repositories that match the project name specified and will output their 
issues in a json file. There will be 1 .json file per issue, and there can be a maximum
of 15 issues.
""")
def fetch_all_issues(proj_name):
    #loads the authentication token
    g = GithubWrapper.load()
    for i in range(1,15):
        OUTPUT_FILE="issues_{}_{}.json".format(proj_name.replace(' ','}'),i) #Can fetch a maximum of 15 issues
        with open(OUTPUT_FILE, "w") as f:
            #gets the .json from the repository
            content = g.fetch_repo_issues(proj_name, i)
            #writes that json to a file
            if (content == ''):
                return
            else:
                f.write("{}".format(content))


@task("""
Adds the new issues to the cloned repositories by taking the element list and pulling the 
title of the issue out of it and creating a new issue around it. Input is the name of 
the base repository that everything is cloned from. This can add a maximum of 15 issues.
""")
def create_new_issues(proj_name):
    g = GithubWrapper.load()
    
    for r in g.iterate_repos():
        if re.match(r'{}+_.*$'.format(proj_name),r['name']):
            
            for i in range(1,15):                                      #Can add a maximum of 15 issues
                cutoff = i+1
                if not "issues_{}_{}".format(proj_name,cutoff):
                    print "Completed Copying issues"
                    break
                
                eltList = open("issues_{}_{}.json".format(proj_name,i)).read()
                if(eltList == "None"):
                    print "Completed Copying Issues"
                    break
                
                for line in eltList:
                    #parses out the title and the body from the list passed by the above methods
                    elements = re.findall(".'(.*?)'",eltList)
                    title=elements[0]
                    body=elements[1]
                
                newProj = r['name']
                g.add_issue_to_repo(newProj,title, body)
    


@task("""
Will delete all auto-generated repositories and teams, making it easier to test and debug. Input
will be the base repository, which is not deleted, although any repositories that were cloned from
it will be.
""")
def delete_repos(baseProj):
    g = GithubWrapper.load()

    for r in g.iterate_repos():
        if re.match(r'{}+_.*$'.format(baseProj),r['name']):
            g.delete_repo(r['name'])

    
            
    
@task("""
Will automatically assign the ORG_NAME and IP_NAME variables so that they will not
have to be hardcoded in. This will be read in from a config file or on stdin. This 
function is deprected, and will not influence anything in the global scope.
""")
def configuration():
    failures = []
    for line in sys.stdin:
        if not line:
            print "Encountered Empty Line, exiting"
            return
        else:
            settingUp = line.split()
            ORG_NAME = settingUp[0]
            IP_ADDRESS = settingUp[1]
            print ORG_NAME
            print IP_ADDRESS
    print failures

        
if __name__ == '__main__':
    run()


