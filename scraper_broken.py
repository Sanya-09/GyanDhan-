import json
import time
import re
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.coventry.ac.uk"
COURSE_LISTING_URL = "https://www.coventry.ac.uk/study-at-coventry/find-a-course/"
MAX_COURSES = 5
REQUEST_DELAY = 2          
REQUEST_TIMEOUT = 20       
OUTPUT_FILE = "coventry_courses.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

logging.basicConfig(
    level=logging.INFO,
    """
    Extracts detailed course data from a Coventry University course page.
    Uses CSS selectors targeting the actual page structure with fallback patterns.
    """
log = logging.getLogger(__name__)

def get_page(url: str) -> Optional[BeautifulSoup]:
    """Fetch a URL and return a BeautifulSoup object, or None on failure."""
    try:
        log.info(f"Fetching: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except requests.exceptions.HTTPError as e:
        log.warning(f"HTTP error for {url}: {e}")
    except requests.exceptions.ConnectionError as e:
        log.warning(f"Connection error for {url}: {e}")
    except requests.exceptions.Timeout:
        log.warning(f"Timeout for {url}")
    except Exception as e:
        log.warning(f"Unexpected error for {url}: {e}")
    return None


def clean(text: Optional[str]) -> str:
    """Strip and normalise whitespace; return '' if None."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())


def find_text(soup: BeautifulSoup, *selectors, default="NA") -> str:
    """Try CSS selectors in order; return the first non-empty text found."""
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            t = clean(el.get_text())
            if t:
                return t
    return default


def find_all_text(soup: BeautifulSoup, selector: str) -> str:
    # Look for course name in h1 inside .course-title
    course_title_div = soup.find("div", class_="course-title")
    if course_title_div:
        h1 = course_title_div.find("h1")
        program_course_name = h1.get_text(strip=True) if h1 else "NA"
    else:
        program_course_name = find_text(soup, "h1", default="NA")
def find_section_text(soup: BeautifulSoup, heading_pattern: str) -> str:
    """
    Find a section whose heading matches heading_pattern (case-insensitive)
    and return the text of the following sibling paragraph/div.
    """
    # Look in .feature-box elements for Location heading
    campus = "NA"
    feature_boxes = soup.find_all("div", class_="feature-box")
    for box in feature_boxes:
        h3 = box.find("h3")
        if h3 and "location" in h3.get_text(strip=True).lower():
            # Found location box, get campus span
            campus_span = box.find("span", class_="campus")
            if campus_span:
                campus = campus_span.get_text(strip=True)
                break
    
    for tag in soup.find_all(["h2", "h3", "h4", "strong", "dt"]):
        campus = find_section_text(soup, r"campus|location")
            if parent_nxt:
                return clean(parent_nxt.get_text())
    return "NA"


    # Try to find study level in .campus-label.-title
    study_level = ""
    campus_label = soup.find("span", class_="campus-label")
    if campus_label:
        # Get text content excluding the <sr-only> tag
        text_nodes = [t.strip() for t in campus_label.strings if t.strip()]
        if text_nodes:
            study_level = text_nodes[-1]  # Last text node is usually the level

# ─────────────────────────────────────────────
# STEP 1 – DISCOVER COURSE URLs
# ─────────────────────────────────────────────
def discover_course_urls(limit: int = MAX_COURSES) -> list[str]:
    """
    Visit the main course listing page and harvest individual course URLs.
    Falls back to a curated list if the listing page structure changes.
    """
    soup = get_page(COURSE_LISTING_URL)
    urls: list[str] = []
    # Look in .feature-box for Duration heading
    course_duration = "NA"
    for box in feature_boxes:
        h3 = box.find("h3")
        if h3 and h3.get_text(strip=True).lower() == "duration":
            # Found duration box
            p = box.find("p")
            if p:
                course_duration = clean(p.get_text(strip=True))
            break
            if re.search(r"/(course|courses|study-at-coventry)/", href, re.IGNORECASE):
                full = href if href.startswith("http") else BASE_URL + href
    # Look in .feature-box for Start date or Year of entry
    all_intakes_available = "NA"
    for box in feature_boxes:
        h3 = box.find("h3")
        if h3:
            h3_text = h3.get_text(strip=True).lower()
            if "start date" in h3_text or "intake" in h3_text:
                # Found start date box
                p = box.find("p")
                if p:
                    all_intakes_available = clean(p.get_text(strip=True))
                break
            elif "year of entry" in h3_text:
                # Found year of entry, collect all radio button labels
                labels = box.find_all("label")
                if labels:
                    all_intakes_available = ", ".join([label.get_text(strip=True) for label in labels])
    # If auto-discovery found enough unique course pages, return them
    if len(urls) >= limit:
    # Look for fees in tables with Fees-UK-FullTime or similar classes
    yearly_tuition_fee = "NA"
    fee_cells = soup.find_all("td", class_=lambda x: x and "Fees-" in x)
    if fee_cells:
        # Get first fee (usually UK Full-time)
        yearly_tuition_fee = clean(fee_cells[0].get_text(strip=True))
    fallback = [
        "https://www.coventry.ac.uk/course-structure/pg/eec/data-science-and-computational-intelligence-msc/",
        "https://www.coventry.ac.uk/course-structure/ug/eec/computer-science-bsc-hons/",
        "https://www.coventry.ac.uk/course-structure/pg/bbm/international-business-mba/",
        "https://www.coventry.ac.uk/course-structure/ug/hls/nursing-adult-bsc-hons/",
        group=1,
    ]
    return fallback[:limit]


# ─────────────────────────────────────────────
# STEP 2 – EXTRACT DATA FROM ONE COURSE PAGE
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# STEP 2 – EXTRACT DATA FROM ONE COURSE PAGE
# ─────────────────────────────────────────────
def extract_course_data(url: str) -> dict:
    """
    Fetch a single course page and extract all required fields.
    Returns a dict with all schema fields, using 'NA' for missing values.
    """

    soup = get_page(url)

    # ✅ FIX 1: Handle failed requests properly
    if not soup:
        log.warning(f"Skipping URL due to fetch failure: {url}")
        return {
            "program_course_name": "NA",
            "university_name": "Coventry University",
            "course_website_url": url,
            "campus": "NA",
            "country": "United Kingdom",
            "address": "NA",
            "study_level": "NA",
            "course_duration": "NA",
            "all_intakes_available": "NA",
            "mandatory_documents_required": "NA",
            "yearly_tuition_fee": "NA",
            "scholarship_availability": "NA",
            "gre_gmat_mandatory_min_score": "NA",
            "indian_regional_institution_restrictions": "NA",
            "class_12_boards_accepted": "NA",
            "gap_year_max_accepted": "NA",
            "min_duolingo": "NA",
            "english_waiver_class12": "NA",
            "english_waiver_moi": "NA",
            "min_ielts": "NA",
            "kaplan_test_of_english": "NA",
            "min_pte": "NA",
            "min_toefl": "NA",
            "ug_academic_min_gpa": "NA",
            "twelfth_pass_min_cgpa": "NA",
            "mandatory_work_exp": "NA",
            "max_backlogs": "NA",
        }

    page_text = soup.get_text(" ", strip=True)

    # ── program_course_name ───────────────────────────────────────────
    program_course_name = find_text(
        soup,
        "h1.course-title", "h1.page-title", "h1",
        default="NA"
    )

    university_name = "Coventry University"
    course_website_url = url

    # ── campus ───────────────────────────────────────────────────────
    campus = find_section_text(soup, r"campus|location")
    if campus == "NA":
        campus = find_text(
            soup,
            "[data-testid='campus']",
            ".campus-name",
            ".course-detail__campus",
            default="NA"
        )

    country = "United Kingdom"
    address = "Coventry University, Priory Street, Coventry, CV1 5FB, United Kingdom"

    # ── study_level ───────────────────────────────────────────────────
    study_level = find_text(
        soup,
        ".course-detail__level", "[data-testid='level']", ".study-level",
        default=""
    )

    if not study_level:
        combined = (url + " " + program_course_name).lower()
        if "msc" in combined or "mba" in combined:
            study_level = "Postgraduate"
        elif "bsc" in combined:
            study_level = "Undergraduate"
        else:
            study_level = "NA"

    # ── course_duration ───────────────────────────────────────────────
    course_duration = find_text(
        soup,
        ".course-detail__duration", "[data-testid='duration']", ".duration",
        default="NA"
    )

    # ── intake ───────────────────────────────────────────────────────
    all_intakes_available = find_text(
        soup,
        ".course-detail__start", "[data-testid='start-date']", ".start-date",
        default="NA"
    )

    # ── fees ─────────────────────────────────────────────────────────
    yearly_tuition_fee = find_text(
        soup,
        ".course-detail__fee", "[data-testid='fees']", ".tuition-fee",
        default="NA"
    )

    # ── IELTS ────────────────────────────────────────────────────────
    min_ielts = find_in_text(
        page_text,
        r"IELTS[^\d]*(\d\.\d)",
        group=0,
        default="NA"
    )

    return {
        "program_course_name": program_course_name,
        "university_name": university_name,
        "course_website_url": course_website_url,
        "campus": campus,
        "country": country,
        "address": address,
        "study_level": study_level,
        "course_duration": course_duration,
        "all_intakes_available": all_intakes_available,
        "mandatory_documents_required": "NA",
        "yearly_tuition_fee": yearly_tuition_fee,
        "scholarship_availability": "NA",
        "gre_gmat_mandatory_min_score": "NA",
        "indian_regional_institution_restrictions": "NA",
        "class_12_boards_accepted": "NA",
        "gap_year_max_accepted": "NA",
        "min_duolingo": "NA",
        "english_waiver_class12": "NA",
        "english_waiver_moi": "NA",
        "min_ielts": min_ielts,
        "kaplan_test_of_english": "NA",
        "min_pte": "NA",
        "min_toefl": "NA",
        "ug_academic_min_gpa": "NA",
        "twelfth_pass_min_cgpa": "NA",
        "mandatory_work_exp": "NA",
        "max_backlogs": "NA",
    }
# ─────────────────────────────────────────────
# STEP 3 – MAIN ORCHESTRATOR
# ─────────────────────────────────────────────
def main():
    log.info("=" * 55)
    log.info("  Coventry University Course Scraper  ")
    log.info("=" * 55)

    # 1. Find course URLs
    course_urls = discover_course_urls(limit=MAX_COURSES)
    log.info(f"Will scrape {len(course_urls)} course(s).")

    results = []
    seen_urls = set()

    for idx, url in enumerate(course_urls, start=1):
        if url in seen_urls:
            log.warning(f"Duplicate URL skipped: {url}")
            continue
        seen_urls.add(url)

        log.info(f"[{idx}/{len(course_urls)}] Processing: {url}")
        data = extract_course_data(url)
        results.append(data)
        log.info(f"  → Course: {data['program_course_name']}")

        # Be polite – wait between requests
        if idx < len(course_urls):
            log.info(f"  Waiting {REQUEST_DELAY}s before next request …")
            time.sleep(REQUEST_DELAY)

    # 2. Save output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    log.info(f"\n✓ Done! Saved {len(results)} course record(s) → {OUTPUT_FILE}")
    return results


if __name__ == "__main__":
    main()
