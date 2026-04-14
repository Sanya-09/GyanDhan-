import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

base='https://www.coventry.ac.uk'
seed='https://www.coventry.ac.uk/international-students-hub/'
headers={'User-Agent':'Mozilla/5.0'}

terms=['ielts','toefl','pte','duolingo','kaplan','waiver','medium of instruction','moi']
seen=set();queue=[seed]
hits=[]

while queue and len(seen)<120:
    url=queue.pop(0)
    if url in seen:
        continue
    seen.add(url)
    try:
        r=requests.get(url,headers=headers,timeout=20)
        if r.status_code>=400:
            continue
        soup=BeautifulSoup(r.text,'lxml')
        text=' '.join(soup.stripped_strings)
        low=text.lower()
        for t in terms:
            if t in low:
                # capture nearby snippets
                pattern=rf'([^\.\n]{{0,120}}{re.escape(t)}[^\.\n]{{0,200}})'
                for m in re.finditer(pattern, low, flags=re.I):
                    snippet=text[m.start():m.end()]
                    hits.append((url,t,snippet))
        for a in soup.find_all('a',href=True):
            h=a['href']
            u=h if h.startswith('http') else urljoin(base,h)
            u=u.split('#')[0]
            if u.startswith(base+'/international-students-hub/') and u not in seen and u not in queue:
                queue.append(u)
    except Exception:
        pass

print('scanned',len(seen),'hits',len(hits))
# show condensed top snippets with numbers
num_re=re.compile(r'(ielts|toefl|pte|duolingo|kaplan|waiver|medium of instruction|moi)[^\.\n]{0,120}(\d+(?:\.\d+)?)',re.I)
shown=0
for url,t,s in hits:
    if num_re.search(s.lower()) or 'waiv' in s.lower() or 'medium of instruction' in s.lower() or 'moi' in s.lower():
        print('\nURL:',url)
        print('TERM:',t)
        print('SNIP:',s[:260].replace('\n',' '))
        shown+=1
    if shown>=50:
        break
