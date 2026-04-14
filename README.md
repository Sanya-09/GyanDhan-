# Coventry University Course Scraper

> **Assignment**: GyanDhan / Senbonzakura Consultancy Pvt. Ltd.  
> **Target site**: https://www.coventry.ac.uk/  
> **Output**: 5 course records in JSON format
> Name - Sanya Agarwal
> Sap ID- 500120145

---

## What This Scraper Does

1. Opens the official Coventry University course listing page
2. Automatically discovers individual course page URLs
3. Visits each course page and extracts all required fields
4. Saves the results as `coventry_courses.json`

All data is scraped **only from official Coventry University webpages** (`coventry.ac.uk`).

---
  
## Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | HTTP requests |
| `beautifulsoup4` | HTML parsing |
| `lxml` | Fast HTML parser (used by BeautifulSoup) |

> Python 3.10 or higher is required.

---

## Setup

### 1. Clone / download the project

```
coventry_scraper/
├── scraper.py          ← main scraper
├── README.md           ← this file
└── requirements.txt    ← dependencies
```

### 2. (Optional but recommended) Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## How to Run

```bash
python scraper.py
```

The script will:
- Print progress logs to the terminal
- Create `coventry_courses.json` in the same directory when finished

Example terminal output:
```
15:02:01 [INFO] ═══════════════════════════════════════════════════════
15:02:01 [INFO]   Coventry University Course Scraper
15:02:01 [INFO] ═══════════════════════════════════════════════════════
15:02:01 [INFO] Fetching: https://www.coventry.ac.uk/study-at-coventry/find-a-course/
15:02:03 [INFO] Will scrape 5 course(s).
15:02:03 [INFO] [1/5] Processing: https://www.coventry.ac.uk/course-structure/...
...
15:02:18 [INFO] ✓ Done! Saved 5 course record(s) → coventry_courses.json
```

---

## Output Format

The file `coventry_courses.json` contains a JSON **array** of 5 objects.  
Each object follows this schema:

```json
[
  {
    "program_course_name": "Data Science and Computational Intelligence MSc",
    "university_name": "Coventry University",
    "course_website_url": "https://www.coventry.ac.uk/course-structure/...",
    "campus": "Coventry",
    "country": "United Kingdom",
    "address": "Coventry University, Priory Street, Coventry, CV1 5FB, United Kingdom",
    "study_level": "Postgraduate",
    "course_duration": "1 year full-time / 2 years part-time",
    "all_intakes_available": "September 2025",
    "mandatory_documents_required": "Degree certificate, transcripts, personal statement, two references",
    "yearly_tuition_fee": "£16,900 per year",
    "scholarship_availability": "Vice-Chancellor's Excellence Scholarship available",
    "gre_gmat_mandatory_min_score": "NA",
    "indian_regional_institution_restrictions": "NA",
    "class_12_boards_accepted": "NA",
    "gap_year_max_accepted": "NA",
    "min_duolingo": "NA",
    "english_waiver_class12": "NA",
    "english_waiver_moi": "NA",
    "min_ielts": "IELTS 6.5 overall with no component below 5.5",
    "kaplan_test_of_english": "NA",
    "min_pte": "NA",
    "min_toefl": "NA",
    "ug_academic_min_gpa": "NA",
    "twelfth_pass_min_cgpa": "NA",
    "mandatory_work_exp": "NA",
    "max_backlogs": "NA"
  },
  ...
]
```

### Field Notes

| Field | Notes |
|-------|-------|
| `program_course_name` | Full official name including award (BSc, MSc, etc.) |
| `course_website_url` | Direct URL to the course page on `coventry.ac.uk` |
| `campus` | Extracted from the course page; may say "Coventry" or "London" |
| `study_level` | Inferred from award type or URL path (`ug`/`pg`) |
| `min_ielts` | Raw text block from the English requirements section |
| Any missing field | Returns `"NA"` |

---

## How It Works (Technical Overview)

```
scraper.py
│
├── discover_course_urls()
│     └── Fetches the listing page → extracts hrefs containing /course/
│         Falls back to a curated list if auto-discovery fails
│
├── extract_course_data(url)
│     ├── get_page()          – safe HTTP fetch with error handling
│     ├── find_text()         – CSS-selector based extraction
│     ├── find_section_text() – heading→next-sibling extraction
│     └── find_in_text()      – regex extraction on plain text
│
└── main()
      ├── Calls discover_course_urls()
      ├── Loops over URLs, calls extract_course_data() each time
      ├── Sleeps 2 seconds between requests (polite scraping)
      └── Writes results to coventry_courses.json
```

---

## Handling Missing Values

- If a field cannot be found on the page → stored as `"NA"`
- If the page fails to load → all fields for that course are `"NA"` (the URL is still recorded)
- Duplicate URLs are skipped automatically

---

## Notes & Limitations

- Coventry University's site uses JavaScript for some content. If a field consistently returns `"NA"`, the page may require a JavaScript-capable browser (Selenium). The scraper uses plain HTTP requests which works for most pages.
- Respectful scraping: a 2-second delay is added between each request.
- The scraper targets `coventry.ac.uk` only — no third-party platforms are used.
