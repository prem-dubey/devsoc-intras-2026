

import json
import os
import re
from tqdm import tqdm


# -----------------------------
# CONFIG
# -----------------------------

DROP_SECTION_KEYWORDS = {
    "additional resources",
    "external links",
    "references",
    "categories",
    "category",
    "time table",
    "timetable",
    "tools",
    "appearance",
    "statistics",
    "navigation",
    "see also",
    "further reading",
    "bibliography",
    "links",
    "related articles",
}

MIN_SECTION_LENGTH = 40


# -----------------------------
# SECTION FILTER
# -----------------------------

def should_drop_section(heading: str, text: str) -> bool:
    """
    Decide whether a section should be discarded completely
    """

    h = heading.lower().strip()

    # 1. Drop by section heading
    if h in DROP_SECTION_KEYWORDS:
        return True

    # 2. Drop if section is mostly categories
    if re.search(r"Category:", text):
        return True

    # 3. Drop tiny / meaningless sections
    if len(text.strip()) < MIN_SECTION_LENGTH:
        return True

    return False


# -----------------------------
# SECTION CLEANER
# -----------------------------

def clean_section_text(heading: str, text: str) -> str:
    """
    Light, safe text cleaning that preserves facts
    """

    # Remove duplicated heading line at start
    text = re.sub(
        rf"^{re.escape(heading)}\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove MediaWiki magic words
    text = re.sub(r"__NOTOC__", "", text)
    text = re.sub(r"__NOEDITSECTION__", "", text)

    # Remove category lines (extra safety)
    text = re.sub(r"Category:.*", "", text)

    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


# -----------------------------
# PAGE CLEANER
# -----------------------------

def clean_page(page_json: dict) -> dict:
    """
    Cleans a single page JSON
    """

    cleaned_sections = []

    for sec in page_json.get("sections", []):
        heading = sec.get("heading", "").strip()
        text = sec.get("text", "").strip()

        if not heading or not text:
            continue

        if should_drop_section(heading, text):
            continue

        cleaned_text = clean_section_text(heading, text)

        if len(cleaned_text) < MIN_SECTION_LENGTH:
            continue

        cleaned_sections.append({
            "page": page_json["title"],
            "section": heading,
            "text": cleaned_text,
            "url": page_json["url"]
        })

    return {
        "title": page_json["title"],
        "url": page_json["url"],
        "sections": cleaned_sections,
        "edges": page_json.get("edges", [])
    }


# -----------------------------
# RUN CLEANING ON ALL FILES
# -----------------------------

def run_cleaning(input_dir="raw_pages", output_dir="clean_pages"):
    os.makedirs(output_dir, exist_ok=True)

    files = [f for f in os.listdir(input_dir) if f.endswith(".json")]

    for fname in tqdm(files, desc="Cleaning pages"):
        with open(os.path.join(input_dir, fname), "r", encoding="utf-8") as f:
            page = json.load(f)

        cleaned_page = clean_page(page)

        # Skip pages that end up empty
        if not cleaned_page["sections"]:
            continue

        with open(os.path.join(output_dir, fname), "w", encoding="utf-8") as f:
            json.dump(cleaned_page, f, indent=2, ensure_ascii=False)



# Chunking all of the files 
def chunk_data(input_dir = "clean_data" , output_dir = "chunked_data"):
    chunked_sections = []
    os.makedirs(output_dir, exist_ok=True)
    files = [f for f in os.listdir(input_dir) if f.endswith(".json")]

    for fname in tqdm(files , desc="Chunking Pages"):
        with open (os.path.join(input_dir, fname ) , "r" , encoding="utf-8") as f:
            page_new = json.load(f)

        page = page_new.get("title", "").strip()
        for section_new in page_new.get("sections" , []):
            section = section_new.get("section" , "").strip()
            if not section or not page:
                continue

            chunked_sections.append({
                "chunk_id": f"{page}::{section}",
                "page": page,
                "section": section,
                "text": section_new.get("text" , "").strip(),
                "url": section_new.get("url" , "").strip()
            })


    with open(os.path.join(output_dir, fname), "w", encoding="utf-8") as f:
        json.dump(chunked_sections, f, indent=2, ensure_ascii=False)




if __name__ == "__main__":
    run_cleaning(
        input_dir="data",     # your 3243 JSON files
        output_dir="clean_data"   # cleaned output
    )
    chunk_data(
        input_dir="clean_data",
        output_dir="chunked_data"
    )
