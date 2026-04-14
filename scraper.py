#!/usr/bin/env python
"""Coventry University scraper: discover and extract 5 valid course pages."""

import json
import logging
import re
import time
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.coventry.ac.uk"
LISTING_URL = "https://www.coventry.ac.uk/study-at-coventry/postgraduate-study/az-course-list/"
ENTRY_REQUIREMENTS_URL = "https://www.coventry.ac.uk/international-students-hub/entry-requirements/"
ENGLISH_REQUIREMENTS_URL = "https://www.coventry.ac.uk/international-students-hub/apply/english-requirements/"
OUTPUT_FILE = "coventry_courses.json"
MAX_COURSES = 5
REQUEST_TIMEOUT = 20
REQUEST_DELAY = 1.5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
}

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip() if text else ""


def fetch_soup(url: str) -> Optional[BeautifulSoup]:
    try:
        log.info(f"Fetching: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as exc:
        log.warning(f"Fetch failed: {url} ({exc})")
        return None


def is_error_page(soup: BeautifulSoup) -> bool:
    h1 = soup.find("h1")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    h1_text = h1.get_text(" ", strip=True).lower() if h1 else ""
    text = (title + " " + h1_text).lower()
    return "404" in text or "page not found" in text or "error" in h1_text


def looks_like_course_page(soup: BeautifulSoup) -> bool:
    if is_error_page(soup):
        return False
    if soup.find("div", class_="course-title"):
        return True
    h1 = soup.find("h1")
    return bool(h1 and "course" not in h1.get_text(" ", strip=True).lower())


def discover_course_urls(limit: int = MAX_COURSES) -> list[str]:
    soup = fetch_soup(LISTING_URL)
    if not soup:
        return []

    candidates: list[str] = []
    seen_base: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/course-structure/" not in href:
            continue
        full = href if href.startswith("http") else urljoin(BASE_URL, href)
        base = full.split("?", 1)[0]
        if base not in seen_base:
            seen_base.add(base)
            candidates.append(full)

    valid: list[str] = []
    for url in candidates:
        page = fetch_soup(url)
        if not page:
            continue
        if looks_like_course_page(page):
            valid.append(url)
        if len(valid) >= limit:
            break
        time.sleep(0.5)

    return valid


def parse_feature_boxes(soup: BeautifulSoup) -> dict[str, str]:
    data: dict[str, str] = {}
    for box in soup.select("div.feature-box"):
        heading = box.find("h3")
        if not heading:
            continue
        key = clean(heading.get_text(" ", strip=True)).lower()
        value = clean(box.get_text(" ", strip=True).replace(heading.get_text(" ", strip=True), "", 1))
        if key and value:
            data[key] = value
    return data


def extract_ielts(page_text: str) -> str:
    match = re.search(r"IELTS[^\d]*(\d(?:\.\d)?)", page_text, re.IGNORECASE)
    return match.group(1) if match else "NA"


def extract_test_score(page_text: str, test_name: str) -> str:
    patterns = {
        "toefl": r"TOEFL[^\d]{0,30}(\d{2,3})",
        "pte": r"PTE[^\d]{0,40}(\d{2,3})",
        "duolingo": r"Duolingo[^\d]{0,30}(\d{2,3})",
        "kaplan": r"Kaplan[^\d]{0,50}(\d{1,3})",
    }
    pattern = patterns.get(test_name)
    if not pattern:
        return "NA"
    matches = re.findall(pattern, page_text, re.IGNORECASE)
    if not matches:
        return "NA"

    values = []
    for raw in matches:
        try:
            val = int(raw)
        except ValueError:
            continue
        if test_name == "pte" and 30 <= val <= 90:
            values.append(val)
        elif test_name == "duolingo" and 60 <= val <= 170:
            values.append(val)
        elif test_name == "toefl" and 50 <= val <= 120:
            values.append(val)
        elif test_name == "kaplan" and 40 <= val <= 100:
            values.append(val)

    if not values:
        return "NA"
    return str(min(values))


def get_global_requirements() -> dict:
    entry_soup = fetch_soup(ENTRY_REQUIREMENTS_URL)
    english_soup = fetch_soup(ENGLISH_REQUIREMENTS_URL)

    defaults = {
        "ug_ielts": "6.0",
        "pg_ielts": "6.5",
        "ug_toefl": "79",
        "pg_toefl": "88",
        "india_boards": "NA",
        "india_pg_university_relaxation": "NA",
        "india_waiver_class12": "NA",
        "english_waiver_moi": "NA",
    }

    if entry_soup:
        entry_text = entry_soup.get_text(" ", strip=True)

        toefl_scores = [int(x) for x in re.findall(r"TOEFL[^\d]{0,30}(\d{2,3})", entry_text, flags=re.IGNORECASE)]
        if toefl_scores:
            defaults["ug_toefl"] = str(min(toefl_scores))
            defaults["pg_toefl"] = str(max(toefl_scores))

        india_block_match = re.search(r"India(.*?)Indonesia", entry_text, flags=re.IGNORECASE)
        india_block = india_block_match.group(1) if india_block_match else ""

        if india_block:
            boards = [
                "Central boards",
                "Maharashtra",
                "Karnataka",
                "Tamil Nadu",
                "Andhra Pradesh",
                "Kerala",
                "Uttarakhand",
            ]
            found_boards = [b for b in boards if re.search(re.escape(b), india_block, flags=re.IGNORECASE)]
            if found_boards:
                defaults["india_boards"] = ", ".join(found_boards)

            waiver_match = re.search(
                r"(65% in Standard XII English[^.]{0,220})",
                india_block,
                flags=re.IGNORECASE,
            )
            if waiver_match:
                defaults["india_waiver_class12"] = clean(waiver_match.group(1))

            relax_match = re.search(
                r"(students from the following universities[^.]{0,260})",
                india_block,
                flags=re.IGNORECASE,
            )
            if relax_match:
                defaults["india_pg_university_relaxation"] = clean(relax_match.group(1))

        waiver_moi_match = re.search(
            r"([A-Z][^.]{0,220}(?:waived|exempt)[^.]{0,180}IELTS[^.]*\.)",
            entry_text,
            flags=re.IGNORECASE,
        )
        if waiver_moi_match:
            defaults["english_waiver_moi"] = clean(waiver_moi_match.group(1))

    if english_soup:
        english_text = english_soup.get_text(" ", strip=True)
        moi_match = re.search(
            r"(other acceptable SELT tests[^.]{0,220}|other English language test from a reputable provider[^.]{0,220})",
            english_text,
            flags=re.IGNORECASE,
        )
        if moi_match:
            defaults["english_waiver_moi"] = clean(moi_match.group(1))

    return defaults


def extract_fee(soup: BeautifulSoup) -> str:
    # Prefer UK full-time fee cell when available.
    priorities = [
        "td.Fees-UK-FullTime",
        "td[class*='Fees-UK']",
        "td[class*='Fees-International']",
    ]
    for sel in priorities:
        cell = soup.select_one(sel)
        if cell:
            return clean(cell.get_text(" ", strip=True))
    return "NA"


def extract_course_data(url: str, global_requirements: dict) -> dict:
    soup = fetch_soup(url)
    if not soup:
        return default_row(url)
    if is_error_page(soup):
        return default_row(url)

    page_text = soup.get_text(" ", strip=True)

    title_h1 = soup.select_one("div.course-title h1") or soup.find("h1")
    program_name = clean(title_h1.get_text(" ", strip=True)) if title_h1 else "NA"

    campus_node = soup.select_one("div.feature-box span.campus")
    campus = clean(campus_node.get_text(" ", strip=True)) if campus_node else "NA"

    level_node = soup.select_one("span.campus-label")
    study_level = "NA"
    if level_node:
        texts = [clean(t) for t in level_node.stripped_strings if clean(t).lower() != "study level:"]
        if texts:
            study_level = texts[-1]

    if study_level == "NA":
        lower = url.lower() + " " + program_name.lower()
        if any(x in lower for x in ["msc", "mba", "ma", "llm"]):
            study_level = "Postgraduate"
        elif any(x in lower for x in ["bsc", "ba", "beng"]):
            study_level = "Undergraduate"

    features = parse_feature_boxes(soup)
    duration = features.get("duration", "NA")
    intake = features.get("start date", features.get("year of entry", "NA"))

    min_ielts = extract_ielts(page_text)
    if min_ielts == "NA":
        if study_level.lower().startswith("post"):
            min_ielts = global_requirements.get("pg_ielts", "NA")
        elif study_level.lower().startswith("under"):
            min_ielts = global_requirements.get("ug_ielts", "NA")

    min_toefl = extract_test_score(page_text, "toefl")
    if min_toefl == "NA":
        if study_level.lower().startswith("post") or "conversion" in study_level.lower():
            min_toefl = global_requirements.get("pg_toefl", "NA")
        elif study_level.lower().startswith("under"):
            min_toefl = global_requirements.get("ug_toefl", "NA")

    min_pte = extract_test_score(page_text, "pte")
    min_duolingo = extract_test_score(page_text, "duolingo")
    kaplan_score = extract_test_score(page_text, "kaplan")
    kaplan_value = kaplan_score if kaplan_score != "NA" else "NA"

    return {
        "program_course_name": program_name,
        "university_name": "Coventry University",
        "course_website_url": url,
        "campus": campus,
        "country": "United Kingdom",
        "address": "Coventry University, Priory Street, Coventry, CV1 5FB, United Kingdom",
        "study_level": study_level,
        "course_duration": duration,
        "all_intakes_available": intake,
        "mandatory_documents_required": "NA",
        "yearly_tuition_fee": extract_fee(soup),
        "scholarship_availability": "NA",
        "gre_gmat_mandatory_min_score": "NA",
        "indian_regional_institution_restrictions": global_requirements.get("india_pg_university_relaxation", "NA"),
        "class_12_boards_accepted": global_requirements.get("india_boards", "NA"),
        "gap_year_max_accepted": "NA",
        "min_duolingo": min_duolingo,
        "english_waiver_class12": global_requirements.get("india_waiver_class12", "NA"),
        "english_waiver_moi": global_requirements.get("english_waiver_moi", "NA"),
        "min_ielts": min_ielts,
        "kaplan_test_of_english": kaplan_value,
        "min_pte": min_pte,
        "min_toefl": min_toefl,
        "ug_academic_min_gpa": "NA",
        "twelfth_pass_min_cgpa": "NA",
        "mandatory_work_exp": "NA",
        "max_backlogs": "NA",
    }


def default_row(url: str) -> dict:
    return {
        "program_course_name": "NA",
        "university_name": "Coventry University",
        "course_website_url": url,
        "campus": "NA",
        "country": "United Kingdom",
        "address": "Coventry University, Priory Street, Coventry, CV1 5FB, United Kingdom",
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


def main() -> None:
    log.info("=" * 52)
    log.info("Coventry University Course Scraper")
    log.info("=" * 52)

    urls = discover_course_urls(MAX_COURSES)
    log.info(f"Valid courses discovered: {len(urls)}")

    if not urls:
        log.warning("No valid course URLs discovered.")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)
        return

    global_requirements = get_global_requirements()
    log.info("International entry requirements scraped for fallback fields.")

    rows = []
    for i, url in enumerate(urls, 1):
        log.info(f"[{i}/{len(urls)}] {url}")
        rows.append(extract_course_data(url, global_requirements))
        if i < len(urls):
            time.sleep(REQUEST_DELAY)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    log.info(f"Saved {len(rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
