import re
import requests
from bs4 import BeautifulSoup

urls = [
    'https://www.coventry.ac.uk/postgraduate-study/az-course-list/',
    'https://www.coventry.ac.uk/undergraduate-study/az-course-list/',
    'https://www.coventry.ac.uk/study-at-coventry/postgraduate-study/az-course-list/',
]
headers = {'User-Agent': 'Mozilla/5.0'}

for u in urls:
    print('\n===', u)
    try:
        r = requests.get(u, headers=headers, timeout=20)
        print('status:', r.status_code, 'len:', len(r.text))
        soup = BeautifulSoup(r.text, 'lxml')
        links = []
        for a in soup.find_all('a', href=True):
            h = a['href']
            if '/course-structure/' in h:
                if h.startswith('/'):
                    h = 'https://www.coventry.ac.uk' + h
                links.append(h)
        uniq = []
        seen = set()
        for l in links:
            if l not in seen:
                seen.add(l)
                uniq.append(l)
        print('course links found:', len(uniq))
        for l in uniq[:8]:
            print(' -', l)
    except Exception as e:
        print('error:', e)
