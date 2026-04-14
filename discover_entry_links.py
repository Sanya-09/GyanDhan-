import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

root = 'https://www.coventry.ac.uk/international-students-hub/entry-requirements/'
base = 'https://www.coventry.ac.uk'
headers = {'User-Agent': 'Mozilla/5.0'}

r = requests.get(root, headers=headers, timeout=20)
r.raise_for_status()
soup = BeautifulSoup(r.text, 'lxml')

links = []
for a in soup.find_all('a', href=True):
    h = a['href']
    u = h if h.startswith('http') else urljoin(base, h)
    if '/international-students-hub/' in u:
        links.append(u.split('#')[0])

uniq = []
seen = set()
for u in links:
    if u not in seen:
        seen.add(u)
        uniq.append(u)

print('total_links', len(uniq))
for u in uniq[:50]:
    print(u)
