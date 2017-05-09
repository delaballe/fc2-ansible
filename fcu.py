#!/usr/bin/env python
# -*- coding: utf-8 -*-
__copyright__ = """
    Copyright 2017 Cyril Gratecos®

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
__license__ = "Apache® 2.0"
__version__= "1.0"
__web__= {
    'github': '',
    'home': ''
}
__author__= {
    "firstname": "Cyril",
    "name": "Gratecos",
    "email": "cyril.gratecos@gmail.com",
    "web": {
        "home": "http://www.gratecos.net",
        "github": "https://github.com/delaballe"
    }
}
__contributors__= [
    {
    "firstname": "",
    "name": "",
    "email": "",
    "web": {
        "home": "",
        "github": ""
        }
    }
]

from bson import json_util
import os, sys
import json, yaml
import boto3
import pprint
import re

rootdir = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
confdir = os.path.join(rootdir, '..', "config")

os.environ["AWS_CONFIG_FILE"]=os.path.join(confdir, 'outscale.ini')

pp = pprint.PrettyPrinter(indent=2)

with open(os.path.join(confdir, "fc2.yml")) as stream:
    try:
        provider_conf = yaml.load(stream)
    except yaml.YAMLError as e:
        print(e)

session = boto3.session.Session()

credentials = session.get_credentials()

fc2 = session.client(
    'ec2',
    api_version="2016-09-15",
    use_ssl=True,
    region_name='eu-west-2',
    endpoint_url='https://fcu.eu-west-2.outscale.com'
)

def convert(s):
    a = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')
    return a.sub(r'_\1', s).lower()

def convertJSON(j):
    out = {}
    for k in j:
        newK = convert(k)
        if isinstance(j[k],dict):
            out[newK] = convertJSON(j[k])
        elif isinstance(j[k],list):
            out[newK] = convertArray(j[k])
        else:
            out[newK] = j[k]
    return out

def convertArray(a):
    newArr = []
    for i in a:
        if isinstance(i,list):
            newArr.append(convertArray(i))
        elif isinstance(i, dict):
            newArr.append(convertJSON(i))
        else:
            newArr.append(i)
    return newArr

def get_instances(host=None):
    instances = []
    response = fc2.describe_instances()
    if host:
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if instance['PublicIpAddress'] == host:
                    a = json.loads(json.dumps(instance, default=json_util.default))
                    instances.append(convertJSON(a))
                    return instances
    else:
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                a = json.loads(json.dumps(instance, default=json_util.default))
                instances.append(convertJSON(a))
        return instances

def get_ip(instance):
  try:
    return instance['public_ip_address']
  except:
    return instance['private_ip_address']

def get_roles(instances):
    roles = {'all': {'hosts': [], 'vars': {} }, '_meta': {'hostvars': { }}}
    for i in instances:
        roles['all']['hosts'].append(get_ip(i))
        roles['_meta']['hostvars'][get_ip(i)] =  yaml.safe_load(json.dumps(i))
        try:
          tags = i['tags']
        except:
          tags = []
        for t in tags:
            if t['key'] == 'roles':
                t['value'] = t['value'].replace("'","").replace("[","").replace("]","")
                i_roles = [str(l).strip() for l in t['value'].strip().split(",")]
                for role in i_roles:
                    if role:
                        try:
                          roles[role]['hosts'].append(get_ip(i))
                        except:
                            roles[role] = {'hosts':[], 'vars': {}}

            if t['key'] == 'parent':
                t['value'] = t['value'].replace("'","").replace("[","").replace("]","")
                i_parents = [str(p).strip() for p in t['value'].strip().split(",")]
                for parent in i_parents:
                    try:
                      roles[parent]['children'].append(get_ip(i))
                    except:
                        roles[parent]['children'] = []
                        roles[parent]['children'].append(get_ip(i))
    return roles

def get_host_vars(instances):
    if instances:
        return yaml.safe_load(json.dumps(instances[0]))
    else:
        return {}

def inventory(host=None):
    if not host:
        instances = get_instances()
        if instances:
            roles = get_roles(instances)
            pp.pprint(yaml.safe_load(json.dumps(roles)))
        else:
            pp.pprint({})
    else:
        instances = get_instances(host=host)
        host_vars = get_host_vars(instances)
        pp.pprint(host_vars)



if __name__ == "__main__":

    import argparse

    # We create the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, help="Get one host from the Outscale inventory")
    parser.add_argument('--list', action='store_true', help="Get all hosts from the Outscale inventory")
    parser.add_argument('-v', '--version', action='store_true', help="Show version")
    parser.add_argument('-l', '--license', action='store_true', help="Show License information")

    # We parse tha arguments and put result in _args object
    _args = parser.parse_args()

    # We return the help message if no arguments
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    else:
        if _args.list:
            inventory()
            parser.exit(0)

        if _args.host:
            inventory(host=_args.host)
            parser.exit(0)

        if _args.license:
            print str("\n    "+__license__)
            print __copyright__
            parser.exit(0)

        if _args.version:
            print sys.argv[0], "Version :", __version__
            parser.exit(0)
