#!/usr/bin/env python

import subprocess
import re
import itertools
import sys

def ip4_to_arpa(address):
    if re.match(r'^\d+\.\d+\.\d+\.\d+$', address):
        parts = address.split('.')
        if max(int(s, 10) for s in parts) <= 255:
            return '.'.join(parts[::-1]) + '.in-addr.arpa'
    return None

def tel_to_arpa(address):
    if re.match(r'^\+\d+$', address):
        address = address[1:]
        return '.'.join(address[::-1]) + '.e164.arpa'
    return None

# 2001:980:2405:1111::1

def ip6_to_arpa(address):
    address = address.replace('-', ':')
    if re.match(r'^[0-9a-f:]+$', address):
        parts = address.split(':')
        if  all(0 <= len(p) <= 4 for p in parts) \
        and (0 < len(parts) <= 8):
            try:
                e = parts.index('')
            except ValueError:
                e = -1
            while e >= 0 and parts[e] == '':
                print parts
                parts[e:e+1] = ['', '0']
                if len(parts) > 8:
                    parts[e:e+1] = []
            for i in range(0, len(parts) - 1):
                while len(parts[i]) < 4:
                    parts[i] = '0' + parts[i]
            parts = ''.join(parts)
            print repr(parts)
            return '.'.join(parts[::-1]) + '.ip6.arpa'
    return None

def arpa_address(address):
    return ip4_to_arpa(address) \
        or tel_to_arpa(address) \
        or ip6_to_arpa(address)

def memoize(cache, key_func=lambda a: a):
    def memoize_dec(f):
        def memoize_func(*a):
            key = key_func(a)
            if key not in cache:
                cache[key] = f(*a)
            return cache[key]
        return memoize_func
    return memoize_dec
       

def wrap(callable):
    def wrap_dec(f):
        def wrap_func(*a):
            return callable(f(*a))
        return wrap_func
    return wrap_dec

def run(cmd, stdin=None):
    if stdin:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        p.stdin.write(stdin)
        p.stdin.close()
        if p.returncode:
            raise Exception('{0}: {1}'.format(p.returncode, p.stdout.read()))
    else:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        if p.returncode:
            raise Exception('{0}: {1}'.format(p.returncode, p.stdout.read()))

    stderr = p.stderr.read()
    if stderr:
        raise Exception(stderr)

    result = p.stdout.read()
    print result
    return result

def resolver(t='ANY'):
    #memoize({}, key_func=lambda a: (a[0].lower(), a[1].lower()))
    @memoize({})
    def resolve(hostname, dns_server):
        query = "dig +norecurse +noall +authority +answer +additional -t {2} {0} @{1}".format(hostname, dns_server.strip(), t)
        print query
        try:
            result = run(query)
        except:
            return []
        return [ re.split(r'[ \t]+', a) for a in result.split('\n')[:-1] if not a.startswith(';') ]
    return resolve

RESOLVER=resolver()

@wrap(list)
def rec_query(hostname, dns_server, resolver=RESOLVER):
    result = resolver(hostname, dns_server)
    is_auth = any(r[-1] == dns_server for r in result if r[3] == 'NS')
    is_finished = all(r[0] == '.' for r in result if r[3] == 'NS')
    yield (dns_server.lower(), result)
    for answer in result:
        if not is_auth and not is_finished and answer[3] == 'NS':
            for sub_answer in rec_query(hostname, answer[-1].lower(), resolver):
                yield sub_answer

@wrap(list)
def root_query(hostname, roots='a', resolver=RESOLVER):
    for r in roots:
        root_server = r + '.root-servers.net.'
        for answer in rec_query(hostname, root_server, resolver): 
            yield answer

@wrap(lambda L: sorted(list(set(L))))
def gen_tree(result):
    for dns, answers in result:
        is_auth = any(a[-1] == dns for a in answers if a[3] == 'NS')
        is_finished = all(a[0] == '.' for a in answers if a[3] == 'NS')
        if not is_auth and not is_finished:
            for answer in answers:
                if answer[3] == 'NS':
                    yield (dns, answer[-1])

@wrap(dict)
def gen_labels(result):
    for dns, answers in result:
        label = '@ {0} :\n{1}'.format(
            dns,
            '\n'.join(' '.join(answer) for answer in answers))
        yield (dns, label)

def gen_graph(title, tree, labels, filename):
    import pygraphviz as pg

    nodes = dict((key, dict((item[1], None) for item in group))
        for (key, group) in itertools.groupby(tree, lambda n: n[0]))

    graph = pg.AGraph(nodes, splines='polyline', rankdir='TB')
    if not filename.endswith('.dot'):
        graph.layout(prog='dot')

    all_keys = set([i for (i,_) in tree] + [i for (_,i) in tree])
    for key in all_keys:
        if key not in labels:
            continue
        node = graph.get_node(key)
        node.attr['label'] = labels[key].replace('\n', '\\l') + '\\l'
        node.attr['shape'] = 'box'
        #node.attr['height'] = 0.0
        node.attr['fontsize'] = 10.0

    if filename.endswith('.dot'):
        with open(filename, 'wb') as f:
            f.write(graph.to_string())
    else:
        graph.layout(prog='dot')
        graph.draw(filename)

if __name__ == '__main__':
    if len(sys.argv) == 2:    
        result = root_query(sys.argv[1])
        for dns_server, answers in result:
            print '###', dns_server
            for answer in answers:
                print ' '.join(answer)
            print

