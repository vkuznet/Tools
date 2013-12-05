#!/usr/bin/env python
#-*- coding: utf-8 -*-
#pylint: disable-msg=
"""
File       : content.py
Author     : Valentin Kuznetsov <vkuznet AT gmail dot com>
Description: Access group content via Facebook API

This script allows to get Facebook group content either in plain form:

From:
Type:
Link:
Date:
Desc:
Mesg:

or in CSV (comma separated values) suitable for importing it into various
applications, e.g. Excel.

To access the group you must be its member and need to know group id as well as
acquire Facebook authentication token. The former is embeded in a code (feel
free to change gid to value of your group of interest) and later can be
accessed via Facebook developers link. The URL of the link will be printed out
on stdout or can be accessed directly as

https://developers.facebook.com/tools/explorer/?method=GET&path=YOUR_GROUP_ID

This script works in interactive mode or capable to fetch group content at
once. The interactive mode fetches first 10 posts and give you a prompt to
fetch more. The whole content can be fetched by specifiying "all" flag in the
input. Here are examples how you should invoke the script:

To get script help

    ./fb_content.py -help

    Usage: fb_content.py <output data format, e.g. csv or plain>
                         <get records, e.g. all or day> <FB token>

To get interactive modes:

    ./fb_content.py plain day TOKEN
    ./fb_content.py csv day TOKEN

To get whole group content

    ./fb_content.py plain all TOKEN
    ./fb_content.py csv all TOKEN

Here you need to substitute TOKEN with a string you obtain from Facebook API
page (see link above or follow on-screen instructions).

For more information please consult the following URLs:
Facebook API: https://github.com/pythonforfacebook/facebook-sdk
              https://developers.facebook.com/docs/graph-api/using-graph-api/

"""

# system modules
import os
import sys
from urlparse import parse_qsl

# Facebook API
import facebook

def main(oformat=None, action=None, token=None):
    "Main function"
    # Fifi's group id
    gid=489931094350860

    # Get token from, replace GID with actual group id
    if  not token:
        print "Get your access token from:"
        url = 'https://developers.facebook.com/tools/explorer/?method=GET&path=%s'\
            % gid
        print url, '\n'
        msg = 'Enter your token here: '
        token = str(raw_input(msg)).strip()

    if  not action:
        msg = 'Do you want recursively scan records or receive all of them: '
        action = raw_input(msg)

    if  not oformat:
        msg = 'Which data format you would like csv or plain? '
        oformat = raw_input(msg)

    if  action == 'all':
        get_data(oformat, token, gid, kwds=None, action=action)
    else:
        # start fetching data recursively
        get_data(oformat, token, gid)

def get_data(oformat, token, gid, kwds=None, action=None):
    "Get data for given group id and user token"
    graph = facebook.GraphAPI(token)
    url = "/%s/feed" % gid
    if  kwds:
        data = graph.request(url, kwds)
    else:
        data = graph.request(url)
    if  oformat == 'csv' and not kwds:
        print 'From,Type,Link,Date,Description,Message'
    for row in data['data']:
        person = row.get('from', {})
        if  person and 'name' in person:
            person = person['name'].encode('utf-8', 'ignore')
        dtype = row.get('type', '')
        link  = row.get('link', '').encode('utf-8', 'ignore')
        date  = row.get('created_time', '')
        desc  = row.get('description', '').encode('utf-8', 'ignore')
        msg   = row.get('message', '').encode('utf-8', 'ignore')
        if  oformat == 'plain':
            print "From: ", person
            print "Type: ", dtype
            print "Link: ", link
            print "Date: ", date
            print "Desc: ", desc
            print "Mesg: ", msg
        elif oformat == 'csv':
            desc = desc.replace(',', ' ').replace('\n', ' ')
            msg  = msg.replace(',', ' ').replace('\n', ' ')
            print "%s,%s,%s,%s,%s,%s" \
                    % (person, dtype, link, date, desc, msg)
        else:
            print 'Unsupported output data format'
            sys.exit(1)
    if  'paging' in data and 'next' in data['paging']:
        next = data['paging']['next']
        args = dict(parse_qsl(next))
    else:
        args = {}
    for key, _ in args.items():
        if  key.startswith('https'):
            del args[key]
    if  action and action == 'all':
        get_data(oformat, token, gid, args, action)
    else:
        more = "Do you want to retrieve more: "
        action = raw_input(more)
        if  str(action).lower() in ['y', 'yes']:
            get_data(oformat, token, gid, args)

if __name__ == '__main__':
    usage = 'Usage: %s <output data format, e.g. csv or plain>' % __file__
    usage += ' <get records, e.g. all or day> <FB token>'
    if  len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help', '-help', 'help']:
        print usage
        sys.exit(0)
    oformat = sys.argv[1] if len(sys.argv)==2 else 'plain'
    action = sys.argv[2] if len(sys.argv)>=3 else 'day'
    token = sys.argv[3] if len(sys.argv)==4 else None
    main(oformat, action, token)
