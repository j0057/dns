#!/usr/bin/env python

import os
import re

import webob
import core

import dnsgraph as dns

def arpa_address(hostname):
    hostname = hostname.replace(' ', '+')
    if re.match(r'^\d+\.\d+\.\d+\.\d+$', hostname):
        return '{0}.in-addr.arpa'.format('.'.join(hostname.split('.')[::-1]))
    if re.match(r'\+\d+', hostname):
        return '{0}.e164.arpa'.format('.'.join(hostname.replace('+', '')[::-1]))
    return None

class DNSRedirect(core.Resource):
    def GET(self, request, hostname):
        location = arpa_address(hostname)

        if not location:
            location = '/dns/{0}.png'.format(hostname)

        if 'roots' in request.GET:
            location += '?roots={0}'.format(request.GET['roots'])

        return webob.Response(status=303, location=location)

class DNSTest(core.Resource):
    def GET(self, request, hostname, ext):
        location = arpa_address(hostname)
        if location:
            if 'roots' in request.GET:
                location += '?roots={0}'.format(request.GET['roots'])
            return webob.Response(status=303, location=location)
        
        hostname = hostname.replace('\\', '\\\\')
        hostname = hostname.replace('"', '\\"')
        hostname = '"' + hostname + '"'

        roots = request.GET.get('roots', 'a')

        filename = '/tmp/dns-{0}.{1}'.format(os.getpid(), ext)
        content_type = {
            'png': 'image/png',
            'svg': 'image/svg+xml',
            'dot': 'text/plain'
        }[ext]

        answer = dns.root_query(hostname, roots, dns.resolver())
        tree = dns.gen_tree(answer)
        labels = dns.gen_labels(answer)
        dns.gen_graph(hostname, tree, labels, filename)

        try:
            with open(filename, 'rb') as f:
                return webob.Response(content_type=content_type, body=f.read())
        finally:
            os.remove(filename)

