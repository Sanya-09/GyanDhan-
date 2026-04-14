#!/usr/bin/env python
"""Analyze one course page to find correct CSS selectors."""
import requests
from bs4 import BeautifulSoup

url = 'https://www.coventry.ac.uk/course-structure/pg/eec/data-science-and-computational-intelligence-msc/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    response = requests.get(url, timeout=20, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    
    # Save the HTML for manual analysis
    with open('course_page_analysis.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    
    print('✓ Page fetched and saved to course_page_analysis.html')
    
    # Extract and analyze key sections
    print('\n=== ANALYZING PAGE STRUCTURE ===\n')
    
    # Get page title
    if soup.title:
        print(f'Page title: {soup.title.string}')
    
    # Look for course name
    h1 = soup.find('h1')
    if h1:
        print(f'H1 text: {h1.get_text(strip=True)}')
    
    # Find all divs with class names that might contain data
    print('\n--- Classes that might contain course info ---')
    divs_with_class = soup.find_all('div', class_=True)
    
    # Get unique class names that might be relevant
    relevant_keywords = ['course', 'duration', 'fee', 'intake', 'level', 'study', 'campus', 'key', 'fact', 'detail', 'info']
    found_classes = set()
    for div in divs_with_class:
        classes = div.get('class', [])
        class_str = ' '.join(classes).lower()
        for keyword in relevant_keywords:
            if keyword in class_str:
                found_classes.add(' '.join(classes))
    
    for cls in sorted(found_classes)[:20]:  # Limit output
        print(f'  .{cls}')
    
    # Look for specific data patterns
    print('\n--- Data patterns found in page text ---')
    page_text = soup.get_text()
    
    # Duration patterns
    if '2 years' in page_text:
        print('✓ Found "2 years" in page')
    if 'years' in page_text.lower():
        # Find context around "years"
        for line in page_text.split('\n'):
            if 'year' in line.lower() and len(line) < 60:
                print(f'  Duration context: "{line.strip()}"')
                break
    
    # Fee patterns
    if '£' in page_text:
        print('✓ Found £ symbol in page')
        for line in page_text.split('\n'):
            if '£' in line and len(line) < 80:
                print(f'  Fee context: "{line.strip()}"')
                break
    
    # Intake patterns
    if 'september' in page_text.lower() or 'january' in page_text.lower():
        print('✓ Found intake month references')
    
    # Specifically look for divs that contain "Duration", "Fee", etc as labels
    print('\n--- Looking for labeled sections ---')
    all_text = soup.find_all(string=True)
    labels_found = {}
    for i, text in enumerate(all_text):
        text_strip = text.strip().lower()
        if text_strip in ['duration', 'fee', 'intake', 'level', 'campus', 'mode']:
            # Found a label, check next elements
            parent = text.parent
            following_text = parent.next_sibling
            if following_text:
                content = following_text.get_text(strip=True) if hasattr(following_text, 'get_text') else str(following_text).strip()
                if content and len(content) < 100:
                    labels_found[text_strip] = {
                        'parent_tag': parent.name,
                        'parent_class': parent.get('class'),
                        'content': content[:80]
                    }
    
    for label, info in labels_found.items():
        print(f'  {label}: {info}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
