import json
import re
import requests
from bs4 import BeautifulSoup

headers={'User-Agent':'Mozilla/5.0'}

with open('coventry_courses.json',encoding='utf-8') as f:
    data=json.load(f)

entry_url='https://www.coventry.ac.uk/international-students-hub/entry-requirements/'
entry_text=requests.get(entry_url,headers=headers,timeout=30).text.lower()

results=[]
for row in data:
    url=row['course_website_url']
    html=requests.get(url,headers=headers,timeout=30).text
    soup=BeautifulSoup(html,'lxml')
    text=soup.get_text(' ',strip=True)
    low=text.lower()

    checks={}
    # direct checks
    name=row['program_course_name']
    checks['name_on_page']= name!='NA' and name.lower() in low

    campus=row['campus']
    checks['campus_on_page']= campus!='NA' and campus.lower() in low

    duration=row['course_duration']
    checks['duration_on_page']= duration!='NA' and all(tok.lower() in low for tok in duration.split()[:3])

    fee=row['yearly_tuition_fee']
    checks['fee_on_page']= fee!='NA' and ('£' in fee and '£' in text)

    ielts=row['min_ielts']
    checks['ielts_on_page']= ielts!='NA' and re.search(r'ielts[^\d]{0,20}'+re.escape(ielts), low) is not None

    toefl=row.get('min_toefl','NA')
    checks['toefl_on_course_page']= toefl!='NA' and re.search(r'toefl[^\d]{0,20}'+re.escape(toefl), low) is not None
    checks['toefl_on_entry_page']= toefl!='NA' and re.search(r'toefl[^\d]{0,20}'+re.escape(toefl), entry_text) is not None

    pte=row.get('min_pte','NA')
    checks['pte_on_course_page']= pte!='NA' and re.search(r'pte[^\d]{0,20}'+re.escape(pte), low) is not None

    waiver=row.get('english_waiver_moi','NA')
    checks['waiver_sentence_on_course_page']= waiver!='NA' and waiver.lower() in low
    checks['waiver_sentence_on_entry_page']= waiver!='NA' and waiver.lower() in entry_text

    results.append((row['program_course_name'],checks))

for name,checks in results:
    print('\nCOURSE:',name)
    for k,v in checks.items():
        print(f'  {k}: {v}')
