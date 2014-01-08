#!/usr/bin/env python

import os
import re

import xhttp

import dns.dnsgraph

_hack_svg_re = re.compile(r'^(<text.*>)(.+) (\d+) IN (CNAME|A|AAAA|NS|PTR) (.+)(</text>)$')

def _hack_svg(lines):
    for (i, line) in enumerate(lines):
        m = _hack_svg_re.match(line)
        m = m and list(m.groups())
        if m:
            m[1] = '<a xlink:href="' + m[1] + '">' + m[1] + '</a>'
            m[4] = '<a xlink:href="' + m[4] + '">' + m[4] + '</a>'
            lines[i] = '{0}{1} {2} IN {3} {4}{5}'.format(*m)
    return '\n'.join(lines)

class DNSRedirect(xhttp.Resource):
    @xhttp.get({ 'roots?': r'[a-m]+' })
    def GET(self, request, hostname):
        location = dns.dnsgraph.arpa_address(hostname) 
        if not location:
            location = hostname + '.svg'
        if request['x-get']['roots']:
            location += '?roots={0}'.format(request['x-get']['roots'])
        return {
            'x-status': xhttp.status.SEE_OTHER,
            'location': location
        }

class DNSGraph(xhttp.Resource):
    @xhttp.get({ 'roots?': r'[a-m]+' })
    def GET(self, request, hostname, ext):
        location = dns.dnsgraph.arpa_address(hostname)
        if location:
            if request['x-get']['roots']:
                location += '?roots={0}'.format(request['x-get']['roots'])
            return {
                'x-status': xhttp.status.SEE_OTHER,
                'location': location
            }
       
        roots = request['x-get']['roots'] or 'a' 

        filename = '/tmp/dns-{0}.{1}'.format(os.getpid(), ext)
        content_type = {
            'png': 'image/png',
            'svg': 'image/svg+xml',
            'dot': 'text/plain'
        }[ext]

        answer = dns.dnsgraph.root_query(hostname, roots, dns.dnsgraph.resolver())
        tree = dns.dnsgraph.gen_tree(answer)
        labels = dns.dnsgraph.gen_labels(answer)

        dns.dnsgraph.gen_graph(hostname, tree, labels, filename)

        try:
            with open(filename, 'rb') as f:
                body = _hack_svg(f.read().split('\n')) if ext == 'svg' else f.read()
            return {
                'x-status': xhttp.status.OK,
                'x-content': body,
                'content-type': content_type
            }
        finally:
            os.remove(filename)

class DNSRouter(xhttp.Router):
    def __init__(self):
        super(DNSRouter, self).__init__(
            (r'^/dns/([a-z0-9\.-]+)\.(png|dot|svg)$',      DNSGraph()),
            (r'^/dns/(\+?[a-z0-9\.:-]+)$',                 DNSRedirect())
        )

app = DNSRouter()
app = xhttp.catcher(app)
app = xhttp.xhttp_app(app)

if __name__ == '__main__':
    xhttp.run_server(app)


