# -*- coding: utf-8 -*-

import sys, os
import requests
import inspect


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
        self.f(args)

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

#tries to load the auth token from token.txt
def load_auth_token():
    pass

##########################################
#
#   Task definitions
#
##########################################


@task("""
Gets a Github API token and stores it in token.txt
The token will be used for all subsequent requests
to the Github API.
""")
def get_auth_token():
    print "MOO"


@task("""
Creates a repo with the name "username_project"

Reads from stdin. Each line should have two tokens
separated by whitespace. The first token is the
student's athena name. The second is the github id
(username) beloning to the student.
""")
def make_repos(project_name):
    print "MOO"


@task("""
Clones all repos beloning to the supplied project_name
and stores them in a new subfolder of the ./cloned_repos
directory.
""")
def clone_repos(project_name):
    print "MOO"






if __name__ == '__main__':
    run()
