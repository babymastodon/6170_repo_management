# -*- coding: utf-8 -*-

import sys, os
import requests
import inspect
import json
import getpass


tasks = []

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
    @staticmethod
    def url(s):
        return "https://api.github.com/{}".format(s.lstrip('/'))
    def do(self,f, path, **kwargs):
        if 'header' not in kwargs:
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
        path = '/orgs/6170'
        r = self.post(path,data=json.dumps({}))
        return r.status_code == 200

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

@task("""
Gets a Github API token and stores it in token.txt
The token will be used for all subsequent requests
to the Github API.
""")
def get_auth_token():
    print "Enter your Github credentials"
    username = raw_input("Username: ")
    password = getpass.getpass("Password: ")
    url = GithubWrapper.url('/authorizations')
    data = {
            "scopes":['gist','delete_repo','repo:status',
                'repo','public_repo','user'],
            "note":"6.170 student repo management script",
            }
    r = requests.post(url,data=json.dumps(data),auth=(username,password))
    if r.status_code != 201:
        raise TaskFailure("Your github credentials were invalid")
    g = GithubWrapper(r.json['token'])
    if not g.has_admin_access():
        raise TaskFailure("Your github account does not have admin access to "\
                "the 6.170 organization. Please make yourself an owner.")
    g.save()


@task("""
Creates a repo with the name "username_project"

Reads from stdin. Each line should have two tokens
separated by whitespace. The first token is the
student's athena name. The second is the github id
(username) beloning to the student.
""")
def make_repos(project_name):
    g = GithubWrapper.load()


@task("""
Clones all repos beloning to the supplied project_name
and stores them in a new subfolder of the ./cloned_repos
directory.
""")
def clone_repos(project_name):
    print "MOO"






if __name__ == '__main__':
    run()
