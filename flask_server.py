import json, os, sys, urllib
from flask import Flask, redirect, request
from itertools import takewhile

app = Flask(__name__)
env = {
  'tag': 'python',
  'user': 'Tsutomu-KKE@github',
  'host': None,
  'port': '8888',
  'page': '1',
  'per_page': '20',
}

@app.route('/config')
def config():
    env.update({i:j for i, j in request.args.items()})
    return '<html><head><title>Qiita記事</title></head><body>' + \
           '<h1>ENV</h1>%s</body></html>'%env

@app.route('/')
def root():
    qu = urllib.parse.quote(env['user'])
    req = 'http://qiita.com/api/v2/items?query=tag%3A' \
          +urllib.parse.quote(env['tag'])+'+user%3A'+qu+'&page=' \
          +env['page']+'&per_page='+env['per_page']
    dt = json.loads(urllib.request.urlopen(req).read().decode())
    nm = dt[0]['user']['name']
    ic = dt[0]['user']['profile_image_url']
    rr = []
    print('<%s>'%env)
    for i, d in enumerate(dt):
        rr.append('<li><a href="%s" target="_blank">%s</a></li>'%(d['url'][16:], d['title']))
    return '<html><head><title>Qiita記事</title></head><body><img src="%s" />'%ic + \
           '<h3><a href="http://qiita.com/%s">Qiita</a>: '%qu + \
           '%sの%sの検索結果</h3><ol>%s</ol></body></html>'%(nm, env['tag'], '\n'.join(rr))

def parse_str(ss):
    tt = list(takewhile(lambda s: not s.startswith('```'), ss))
    ss = ss[len(tt):]
    cell_type = 'raw' if len(tt) == 0 else 'markdown'
    if cell_type == 'raw':
        nm = ss[0][(ss[0]+':').index(':')+1:]
        tg = ss[0][3:len(ss[0])-len(nm)].rstrip(':')
        ss = ss[1:]
        if tg.startswith('py') or tg == 'bash':
            cell_type = 'code'
        tt = list(takewhile(lambda s: not s.startswith('```'), ss))
        ss = ss[len(tt):]
        if cell_type == 'code':
            tt = list(takewhile(lambda s: not s.startswith('>>>'), tt))
        if ss:
            ss = ss[1:]
        tt = ([('%%' if tg == 'bash' else '# ') + tg] if tg else []) + tt
    return cell_type, tt, ss

@app.route('/<path:url>')
def make_ipynb(url):
    if url.startswith('http://'):
        url = url[7:]
    if not url.startswith('qiita.com/'):
        url = 'qiita.com/' + url
    s = urllib.request.urlopen('http://'+url+'.md').read().decode().rstrip()
    ss = s.replace('\\', '\\\\').replace('\t', '\\t').replace('"', '\\"').split('\n')
    fn = ss[0]
    ss[0] = '# ' + ss[0]
    cdin = '   "execution_count": null,\n   "outputs": [],\n   '
    rr = []
    while ss:
        cell_type, tt, ss = parse_str(ss)
        s = '\\n",\n    "'.join(tt)
        if s:
            rr.append("""\
   "cell_type": "%s",
   "metadata": {},
%s   "source": [
    "%s"
   ]
"""%(cell_type, '' if cell_type != 'code' else cdin, '\\n",\n    "'.join(tt)))
    fn += '.ipynb'
    with open(fn, 'w') as fp:
        fp.write("""\
{
 "cells": [
  {
""")
        fp.write('  },\n  {\n'.join(rr))
        fp.write("""\
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.5.1"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 0
}\n""")
    if not env['host']:
        env['host'] = request.base_url[7:request.base_url.index(':', 6)]
    return redirect('http://'+env['host']+':'+env['port']+'/notebooks/'+fn)

if __name__ == '__main__':
    #app.debug=True
    os.system('jupyter notebook --ip=* --port=8888 --no-browser &')
    app.run('0.0.0.0', 5000)
