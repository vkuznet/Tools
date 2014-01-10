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
import json
import codecs
import urllib
import urllib2
from optparse import OptionParser
from urlparse import parse_qsl

if sys.version_info < (2, 6):
    raise Exception("This tool requires python 2.6 or greater")

def request(token, path, args=None, post_args=None, timeout=None):
    """Fetch data from Facebook"""
    args = args or {}

    if  token:
        if  post_args is not None:
            post_args["access_token"] = token
        else:
            args["access_token"] = token
    post_data = urllib.urlencode(post_args) if post_args else None
    url = 'https://graph.facebook.com/' +  path + '?' + urllib.urlencode(args)
    try:
        stream = urllib2.urlopen(url, post_data, timeout=timeout)
    except urllib2.HTTPError, exc:
        msg = 'HTTPError %s' % str(exc.read())
        raise Exception(msg)
    except Exception as exc:
        msg = 'Fail to fetch data upstream: %s' % str(exc)
        raise Exception(msg)
    try:
        info = stream.info()
        if  info.maintype == 'text':
            resp = json.loads(stream.read())
        elif info.maintype == 'image':
            mimetype = info['content-type']
            resp = {'data': stream.read(), 'url':stream.url, 'mime-type':mimetype}
        else:
            raise Exception('Do not support %s' % info.maintype)
    finally:
        stream.close()
    if  resp and isinstance(resp, dict) and resp.get("error"):
        err = resp.get('error', {})
        msg = 'Error: type %s, message %s' % (error['type'], error['message'])
        raise Exception(msg)
    return resp

def fb_fetcher(gid, oformat=None, action=None, token=None):
    "Main function"

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
    if  not token:
        print "Please provide access token"
        sys.exit(1)
    url = "/%s/feed" % gid
    data = request(token, url, kwds)
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
            print u"%s,%s,%s,%s,%s,%s" \
                    % (unicode(person, 'utf-8'), dtype, link, date,
                            unicode(desc, 'utf-8'), unicode(msg, 'utf-8'))
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
        try:
            get_data(oformat, token, gid, args, action)
        except:
            return
    else:
        more = "Do you want to retrieve more: "
        action = raw_input(more)
        if  str(action).lower() in ['y', 'yes']:
            get_data(oformat, token, gid, args)

class FBOptionParser(object):
    "Option parser"
    def __init__(self):
        self.parser = OptionParser()
        self.parser.add_option("-f", "--format", action="store", type="string",
            default="plain", dest="format",
            help="specify output format, e.g. plain, csv")
        self.parser.add_option("-a", "--action", action="store", type="string",
            default="day", dest="action",
            help="fetch record duration, e.g. all, day")
        self.parser.add_option("-t", "--token", action="store", type="string",
            default="", dest="token",
            help="Facebook access token")
        self.parser.add_option("-g", "--gid", action="store", type=long,
            default=489931094350860, dest="gid",
            help="Facebook group-id, default is Fifi's group")
    def options(self):
        "Returns parse list of options"
        return self.parser.parse_args()

def main():
    optmgr = FBOptionParser()
    opts, _ = optmgr.options()
    fb_fetcher(opts.gid, opts.format, opts.action, opts.token)

if __name__ == '__main__':
    main()
