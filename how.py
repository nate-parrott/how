#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google import search
from urlparse import urlparse
import requests
import bs4
from termcolor import colored

def how(query):
    has_result = False
    for r in get_results(query):
        print r.data
        has_result = True
        break
    if not has_result:
        print "No results!"

def get_results(query):
    prefix = "bash "
    for url in search(prefix + query, stop=10):
        debug("Found search result:", url)
        for result in results_from_url(url):
            yield result

def results_from_url(url):
    stack_exchange_site = which_stack_exchange_site_is_this_url(url)
    debug("Stack exchange site:", stack_exchange_site)
    if stack_exchange_site:
        question_id = get_stack_exchange_question_id_from_url(url)
        debug("Question id:", question_id)
        if question_id:
            title, answers = fetch_title_and_answers(stack_exchange_site, question_id)
            debug(len(answers), "answers")
            for answer in answers:
                r = Result(answer, title)
                if r.usable:
                    yield r

def debug(*args):
    return
    print " ".join(map(repr, args))

def fetch_title_and_answers(stack_exchange_site, question_id):
    url = "https://api.stackexchange.com/2.2/questions/{0}?order=desc&sort=votes&site={1}&filter=!-*f(6rf)dKXe".format(question_id, stack_exchange_site)
    debug(url)
    resp = requests.get(url).json()['items'][0]
    return resp['title'], resp['answers']

class Result(object):
    def __init__(self, data, question_title):
        self.question_title = question_title
        self.usable = False
        soup = bs4.BeautifulSoup(data['body'], 'html.parser')
        blocks = list(soup.children)
        blocks = [b for b in blocks if isinstance(b, bs4.Tag)]
        blocks_as_data = []
        for block in blocks:
            text = block.text.strip()
            if len(text) == 0:
                continue
            
            truncate_length = 200
            is_code = block.name == "pre"
            if is_code:
                self.usable = True
                truncate_length = 500
            data = truncate(text.encode('utf-8'), truncate_length)
            if is_code:
                data = colored(data, attrs=['bold'])
            blocks_as_data.append(data)
        
        max_blocks = 6
        if len(blocks_as_data) > max_blocks:
            blocks_as_data = blocks_as_data[:max_blocks]
            blocks_as_data.append(ELLIPSE)
        
        self.data = "\n" + colored(question_title.encode('utf-8'), 'red') + "\n\n" + "\n\n".join(blocks_as_data) + "\n"

# HELPERS

ELLIPSE = colored(u"[…]".encode('utf-8'), 'blue')

def which_stack_exchange_site_is_this_url(url):
    host = urlparse(url).netloc
    if host.startswith('www.'): host = host[4:]
    return {
        "unix.stackexchange.com": "unix",
        "stackoverflow.com": "stackoverflow",
        "superuser.com": "superuser"
    }.get(host)

def get_stack_exchange_question_id_from_url(url):
    path = urlparse(url).path
    prefix = '/questions/'
    if path.startswith(prefix):
        return path[len(prefix):].split('/')[0]

def truncate(data, n_chars):
    if len(data) < n_chars:
        return data
    else:
        return data[:n_chars] + " " + ELLIPSE

def test_answer_html_parsing():
    html = """<p>The following command will do it for you. Use caution though.</p>

<pre><code>rm -rf directoryname
</code></pre>"""
    print Result({"body": html}).data

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        how(" ".join(sys.argv[1:]))
    else:
        print "Usage: how <question about the terminal>"
