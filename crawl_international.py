import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

base='https://www.coventry.ac.uk'
seed='https://www.coventry.ac.uk/international-students-hub/'
headers={'User-Agent':'Mozilla/5.0'}

seen=set()
queue=[seed]
found=[]

for _ in range(120):
    if not queue:
        break
    url=queue.pop(0)
    if url in seen:
        continue
    seen.add(url)
    try:
        r=requests.get(url,headers=headers,timeout=20)
        if r.status_code>=400:
            continue
        soup=BeautifulSoup(r.text,'lxml')
        text=soup.get_text(' ',strip=True)
        low=text.lower()
        if any(k in low for k in ['ielts','toefl','pte','duolingo','kaplan','waiver','medium of instruction','moi']):
            found.append((url,text[:1200]))
        for a in soup.find_all('a',href=True):
            h=a['href']
            full=h if h.startswith('http') else urljoin(base,h)
            full=full.split('#')[0]
            if full.startswith(base+'/international-students-hub/') and full not in seen and full not in queue:
                queue.append(full)
    except Exception:
        pass

print('pages_scanned',len(seen))
print('pages_with_keywords',len(found))
for u,_ in found:
    print(u)

# print first snippets for strongest pages
print('\n--- snippets ---')
for u,t in found[:6]:
    print('\nURL:',u)
    m=re.findall(r'((?:IELTS|TOEFL|PTE|Duolingo|Kaplan|waiv\w+|MOI)[^.]{0,140})',t,flags=re.I)
    for x in m[:8]:
        print(' ',x)
