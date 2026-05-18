#!/usr/bin/env python3
"""
LFC VBS 2026 "Deliverance" — Print-Ready PDF Generator

Generates all worksheet, coloring, drawing, word search, and discussion pages
for Levels 1-4, Days 1-3.
"""

import json
import os
import sys
from pathlib import Path
from jinja2 import Template
from weasyprint import HTML
from wordsearch import generate_wordsearch, generate_crossword, generate_scramble

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = BASE_DIR / "templates"
ASSETS_DIR = BASE_DIR / "assets"
SVG_DIR = ASSETS_DIR / "svg"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_content():
    with open(DATA_DIR / "content.json") as f:
        return json.load(f)


def load_svg(filename):
    """Load an SVG file and return its contents."""
    path = SVG_DIR / filename
    if path.exists():
        return path.read_text()
    return None


def load_base_template():
    with open(TEMPLATE_DIR / "base.html") as f:
        return f.read()


# ─── Page Header HTML ────────────────────────────────────────────────
def page_header_html(level_info, day_info=None):
    level_label = f"Level {level_info['level']} &mdash; {level_info['audience']}"
    h = f'''<div class="page-header">
  <div class="header-row">
    <div class="header-left">
      <span class="header-title">Deliverance</span>
      <span class="header-subtitle">Exodus, Law, Tabernacle</span>
    </div>
    <div class="header-right">
      <span class="header-level-badge">{level_label}</span>
    </div>
  </div>
</div>'''
    if day_info:
        h += f'''
<div class="day-banner">
  <div class="day-banner-inner">
    <div class="day-banner-left"><h2>Day {day_info["day"]}: {day_info["title"]}</h2></div>
    <div class="day-banner-right"><span class="scripture-ref">{day_info.get("scripture", "")}</span></div>
  </div>
</div>'''
    return h


# ─── Coloring Page ───────────────────────────────────────────────────
COLORING_DIR = ASSETS_DIR / "coloring"

# (level, day) -> image filename in assets/coloring/
IMG_MAP_COLORING = {
    (1, 1): "moses_staff",
    (1, 2): "nile_blood",
    (1, 3): "red_sea_parting",
    (2, 1): "moses_pharaoh",
    (2, 2): "hail_egypt",
    (2, 3): "red_sea_crossing",
}


def find_coloring_image(name):
    """Find the coloring image file by name (any extension)."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        path = COLORING_DIR / f"{name}.{ext}"
        if path.exists():
            return path
    return None


def make_coloring_page(level_info, day_info):
    key = (level_info["level"], day_info["day"])
    img_name = IMG_MAP_COLORING.get(key, "")
    img_path = find_coloring_image(img_name) if img_name else None

    if img_path:
        rel_path = img_path.relative_to(BASE_DIR)
        img_html = f'<img src="{rel_path}" alt="{img_name}">'
    else:
        img_html = '''<svg viewBox="0 0 500 600" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="480" height="580" fill="none" stroke="#D4C4A8" stroke-width="2" stroke-dasharray="8,4" rx="12"/>
  <text x="250" y="300" text-anchor="middle" font-family="Georgia" font-size="16" fill="#A09080">[Coloring artwork placeholder]</text>
</svg>'''

    coloring = day_info["activities"]["coloring"]
    html = f'''<div class="page">
  {page_header_html(level_info, day_info)}
  <div class="activity-label">Coloring!</div>
  <div class="activity-instruction">{coloring["instruction"]}</div>
  <div class="coloring-outer">
    <div class="coloring-area">
      {img_html}
    </div>
  </div>
  <div class="attribution">LFC VBS 2026</div>
</div>'''
    return html


# ─── Drawing Page ────────────────────────────────────────────────────
def make_drawing_page(level_info, day_info):
    drawing = day_info["activities"]["drawing"]

    html = f'''<div class="page">
  {page_header_html(level_info, day_info)}
'''
    # Reading/Introduce reference (L1-L2)
    if "reading" in day_info:
        html += f'  <div class="reading-ref">{day_info["reading"]}</div>\n'

    # Key concept (L1-L2)
    if "key_concept" in day_info and level_info["level"] in (1, 2):
        html += f'''  <div class="key-concept">
    <div class="key-concept-label">Key Concept</div>
    {day_info["key_concept"]}
  </div>\n'''

    html += f'''  <div class="activity-label">Drawing!</div>
  <div class="activity-instruction">{drawing["instruction"]}</div>
  <div class="drawing-area-short"></div>
  <div class="attribution">LFC VBS 2026</div>
</div>'''
    return html


# ─── Worksheet Page (Levels 3 & 4) ──────────────────────────────────
def make_worksheet_page(level_info, day_info):
    html = f'''<div class="page">
  {page_header_html(level_info, day_info)}
  <div class="worksheet-intro">Complete the worksheet below.</div>
'''

    # Reading reference
    if "reading" in day_info:
        html += f'  <div class="reading-ref">{day_info["reading"]}</div>\n'

    # Summary (Level 1/2)
    if "summary" in day_info:
        html += f'  <div class="summary-text">{day_info["summary"]}</div>\n'

    # Key concept(s)
    if "key_concept" in day_info:
        html += f'''  <div class="key-concept">
    <div class="key-concept-label">Key Concept</div>
    {day_info["key_concept"]}
  </div>\n'''
    elif "key_concepts" in day_info:
        html += '  <div class="key-concept">\n    <div class="key-concept-label">Key Concepts</div>\n    <ul style="margin:4px 0 0 18px; font-size:10pt;">\n'
        for kc in day_info["key_concepts"]:
            html += f"      <li>{kc}</li>\n"
        html += "    </ul>\n  </div>\n"

    # Catechism Q&A
    if "catechism_qa" in day_info:
        html += '  <div class="catechism-block">\n'
        html += f'    <h3>Today\'s Shorter Catechism Q &amp; A\'s</h3>\n'
        for qa in day_info["catechism_qa"]:
            html += f'''    <div class="catechism-qa">
      <div class="catechism-q">Q. {qa["q_num"]}. {qa["question"]}</div>
      <div class="catechism-a">A. {qa["answer"]}</div>
    </div>\n'''
        html += "  </div>\n"

    # List activity
    if "list" in day_info.get("activities", {}):
        list_act = day_info["activities"]["list"]
        html += f'''  <div class="list-activity">
    <h3>{list_act["prompt"]}</h3>
    <ul class="list-lines">
'''
        for _ in range(10):
            html += '      <li></li>\n'
        html += "    </ul>\n  </div>\n"

    html += f'  <div class="attribution">LFC VBS 2026</div>\n</div>'
    return html


# ─── Discussion Page (Level 4) ───────────────────────────────────────
def make_discussion_page(level_info, day_info):
    html = f'''<div class="page">
  {page_header_html(level_info, day_info)}
'''
    if "discussion_questions" in day_info:
        html += '  <div class="discussion-section">\n'
        html += '    <h3>Discussion Questions</h3>\n'
        html += '    <ol class="discussion-list">\n'
        for q in day_info["discussion_questions"]:
            html += f"      <li>{q}</li>\n"
        html += "    </ol>\n  </div>\n"

        # Answer lines after each question
        html += '  <div class="notes-section" style="margin-top:12px;">\n'
        html += '    <h3>Notes</h3>\n'
        html += '    <ul class="list-lines">\n'
        for _ in range(18):
            html += '      <li></li>\n'
        html += "    </ul>\n  </div>\n"

    html += f'  <div class="attribution">LFC VBS 2026</div>\n</div>'
    return html


# ─── Word Search Page (Levels 3 & 4) ────────────────────────────────
def make_wordsearch_page(level_info, day_info):
    ws = day_info["activities"]["wordsearch"]
    words = ws["words"]

    grid_size = max(max(len(w) for w in words) + 2, 15)
    grid_size = min(grid_size, 18)
    grid, placed = generate_wordsearch(words, size=grid_size)

    html = f'''<div class="page">
  {page_header_html(level_info, day_info)}
  <div class="wordsearch-section">
    <h3>Word Search</h3>
    <div class="wordsearch-prompt">{ws["prompt"]}</div>
    <table class="wordsearch-grid">
'''
    for row in grid:
        html += "      <tr>"
        for cell in row:
            html += f"<td>{cell}</td>"
        html += "</tr>\n"
    html += "    </table>\n"

    # Word bank
    display_words = sorted([w.upper().replace(" ", "") for w in words])
    html += '    <div class="word-bank">\n'
    html += '      <div class="word-bank-title">Word Bank</div>\n'
    html += '      <div class="word-bank-words">\n'
    for w in display_words:
        html += f"        <span>{w}</span>\n"
    html += "      </div>\n    </div>\n"

    html += f'''  </div>
  <div class="attribution">LFC VBS 2026</div>
</div>'''
    return html


# ─── Crossword Page (Levels 3 & 4, Day 2) ────────────────────────────
def make_crossword_page(level_info, day_info):
    cw = day_info["activities"]["crossword"]
    words = cw["words"]

    grid, (rows, cols), placed = generate_crossword(words)

    html = f'''<div class="page">
  {page_header_html(level_info, day_info)}
  <div class="crossword-section">
    <h3>Criss-Cross Puzzle</h3>
    <div class="crossword-prompt">{cw["prompt"]}</div>
    <table class="crossword-grid">
'''
    # Build a set of filled cells for rendering
    filled = {}
    for p in placed:
        r, c = p['row'], p['col']
        for i, ch in enumerate(p['word']):
            if p['direction'] == 'across':
                filled[(r, c + i)] = ch
            else:
                filled[(r + i, c)] = ch

    # Build a map of numbered cells
    numbered = {}
    for p in placed:
        key = (p['row'], p['col'])
        if key not in numbered:
            numbered[key] = p['number']

    for r in range(rows):
        html += "      <tr>"
        for c in range(cols):
            if (r, c) in filled:
                num = numbered.get((r, c))
                num_span = f'<span class="crossword-num">{num}</span>' if num else ''
                html += f'<td class="crossword-cell">{num_span}</td>'
            else:
                html += '<td class="crossword-blank"></td>'
        html += "</tr>\n"
    html += "    </table>\n"

    # Across / Down clue lists (show hints, not words)
    across = sorted([p for p in placed if p['direction'] == 'across'], key=lambda p: p['number'])
    down = sorted([p for p in placed if p['direction'] == 'down'], key=lambda p: p['number'])
    clues = cw.get("clues", {})

    html += '    <div class="crossword-clues">\n'
    html += '      <div class="crossword-clues-col">\n'
    html += '        <div class="clue-list-title">Across</div>\n'
    html += '        <div class="clue-list">\n'
    for p in across:
        hint = clues.get(p["word"].upper(), p["word"].upper())
        html += f'          <div class="clue-item">{p["number"]}. {hint}</div>\n'
    html += '        </div>\n      </div>\n'
    html += '      <div class="crossword-clues-col">\n'
    html += '        <div class="clue-list-title">Down</div>\n'
    html += '        <div class="clue-list">\n'
    for p in down:
        hint = clues.get(p["word"].upper(), p["word"].upper())
        html += f'          <div class="clue-item">{p["number"]}. {hint}</div>\n'
    html += '        </div>\n      </div>\n'
    html += '    </div>\n'

    # Word bank (sorted alphabetically)
    bank_words = sorted([p["word"].upper() for p in placed])
    html += '    <div class="word-bank">\n'
    html += '      <div class="word-bank-title">Word Bank</div>\n'
    html += '      <div class="word-bank-words">\n'
    for w in bank_words:
        html += f'        <span>{w}</span>\n'
    html += '      </div>\n    </div>\n'

    html += f'''  </div>
  <div class="attribution">LFC VBS 2026</div>
</div>'''

    answer_data = {
        'type': 'crossword',
        'rows': rows,
        'cols': cols,
        'filled': filled,
        'numbered': numbered,
        'placed': placed,
        'level_info': level_info,
        'day_info': day_info,
    }
    return html, answer_data


# ─── Word Scramble Page (Levels 3 & 4, Day 3) ────────────────────────
def make_scramble_page(level_info, day_info):
    sc = day_info["activities"]["scramble"]
    words = sc["words"]
    secret_msg = sc.get("secret_message")

    scramble_data, secret_message = generate_scramble(words, secret_message=secret_msg)

    html = f'''<div class="page">
  {page_header_html(level_info, day_info)}
  <div class="scramble-section">
    <h3>Word Scramble</h3>
    <div class="scramble-prompt">{sc["prompt"]}</div>
    <table class="scramble-table">
'''
    for i, item in enumerate(scramble_data):
        num = i + 1
        blanks = ''
        for j in range(len(item['original'])):
            if item['secret_index'] is not None and j == item['secret_index']:
                blanks += '<span class="scramble-blank scramble-circled"></span>'
            else:
                blanks += '<span class="scramble-blank"></span>'

        html += f'''      <tr>
        <td class="scramble-num">{num}.</td>
        <td class="scramble-clue">{item['scrambled']}</td>
        <td class="scramble-answer">{blanks}</td>
      </tr>
'''

    html += "    </table>\n"

    # Secret message blanks
    if secret_message:
        msg_letters = secret_message.upper().replace(" ", "")
        html += '    <div class="scramble-secret">\n'
        html += '      <div class="scramble-secret-label">Secret Message:</div>\n'
        html += '      <div class="scramble-secret-blanks">\n'
        char_idx = 0
        for ch in secret_message.upper():
            if ch == ' ':
                html += '        <span class="scramble-secret-space"></span>\n'
            else:
                html += '        <span class="scramble-blank scramble-circled"></span>\n'
                char_idx += 1
        html += '      </div>\n    </div>\n'

    html += f'''  </div>
  <div class="attribution">LFC VBS 2026</div>
</div>'''

    answer_data = {
        'type': 'scramble',
        'scramble_data': scramble_data,
        'secret_message': secret_message,
        'level_info': level_info,
        'day_info': day_info,
    }
    return html, answer_data


# ─── Puzzle Page Dispatcher ───────────────────────────────────────────
def make_puzzle_page(level_info, day_info):
    """Pick puzzle type based on day number.

    Returns (html, answer_data) where answer_data is a dict for crossword/scramble
    answer keys, or None for word search pages.
    """
    day = day_info["day"]
    activities = day_info["activities"]

    if day == 2 and "crossword" in activities:
        return make_crossword_page(level_info, day_info)
    elif day == 3 and "scramble" in activities:
        return make_scramble_page(level_info, day_info)
    else:
        # Day 1 or fallback: word search (no answer key)
        return make_wordsearch_page(level_info, day_info), None


# ─── Answer Key Pages ────────────────────────────────────────────────
def make_crossword_answer_page(answer_data):
    """Render a filled-in crossword grid as an answer key."""
    level_info = answer_data['level_info']
    day_info = answer_data['day_info']
    rows = answer_data['rows']
    cols = answer_data['cols']
    filled = answer_data['filled']
    numbered = answer_data['numbered']
    placed = answer_data['placed']

    html = f'''<div class="page">
  {page_header_html(level_info, day_info)}
  <div class="answer-key-title">Answer Key &mdash; Criss-Cross Puzzle</div>
  <table class="crossword-grid answer-grid">
'''
    for r in range(rows):
        html += "      <tr>"
        for c in range(cols):
            if (r, c) in filled:
                num = numbered.get((r, c))
                num_span = f'<span class="crossword-num">{num}</span>' if num else ''
                html += f'<td class="crossword-cell answer-cell">{num_span}<span class="answer-letter">{filled[(r, c)]}</span></td>'
            else:
                html += '<td class="crossword-blank"></td>'
        html += "</tr>\n"
    html += "  </table>\n"

    # Across / Down word lists
    across = sorted([p for p in placed if p['direction'] == 'across'], key=lambda p: p['number'])
    down = sorted([p for p in placed if p['direction'] == 'down'], key=lambda p: p['number'])

    html += '  <div class="crossword-clues">\n'
    html += '    <div class="crossword-clues-col">\n'
    html += '      <div class="clue-list-title">Across</div>\n'
    html += '      <div class="clue-list">\n'
    for p in across:
        html += f'        <div class="clue-item">{p["number"]}. {p["word"].upper()}</div>\n'
    html += '      </div>\n    </div>\n'
    html += '    <div class="crossword-clues-col">\n'
    html += '      <div class="clue-list-title">Down</div>\n'
    html += '      <div class="clue-list">\n'
    for p in down:
        html += f'        <div class="clue-item">{p["number"]}. {p["word"].upper()}</div>\n'
    html += '      </div>\n    </div>\n'
    html += '  </div>\n'

    html += f'''  <div class="attribution">LFC VBS 2026</div>
</div>'''
    return html


def make_scramble_answer_page(answer_data):
    """Render the word scramble answers and secret message."""
    level_info = answer_data['level_info']
    day_info = answer_data['day_info']
    scramble_data = answer_data['scramble_data']
    secret_message = answer_data['secret_message']

    html = f'''<div class="page">
  {page_header_html(level_info, day_info)}
  <div class="answer-key-title">Answer Key &mdash; Word Scramble</div>
  <div class="answer-list">
'''
    for i, item in enumerate(scramble_data):
        html += f'    <div class="answer-item"><span class="answer-num">{i + 1}.</span> <span class="answer-scrambled">{item["scrambled"]}</span> &rarr; <span class="answer-word">{item["original"].upper()}</span></div>\n'
    html += '  </div>\n'

    if secret_message:
        html += '  <div class="answer-secret">\n'
        html += '    <div class="answer-secret-label">Secret Message:</div>\n'
        html += f'    <div class="answer-secret-word">{secret_message.upper()}</div>\n'
        html += '  </div>\n'

    html += f'''  <div class="attribution">LFC VBS 2026</div>
</div>'''
    return html


# ─── Letterhead Page ─────────────────────────────────────────────────
def make_letterhead_page():
    html = '''<div class="page">
  <div class="cover-page">
    <div class="cover-org">Little Farms Chapel</div>
    <div class="cover-vbs-label">Vacation Bible School 2026</div>
    <div class="cover-title">Deliverance</div>
    <div class="cover-subtitle">Exodus &middot; Law &middot; Tabernacle</div>
    <div class="cover-rule"></div>
    <div class="cover-verse">
      &ldquo;And God spoke all these words, saying, I am the LORD your God,
      who brought you out of the land of Egypt, out of the house of slavery.&rdquo;<br>
      <strong>&mdash; Exodus 20:1&ndash;2</strong>
    </div>
    <div class="cover-details">
      3 Days &middot; 4 Levels &middot; Exodus, Law, Tabernacle
    </div>
    <div class="cover-bottom-rule"></div>
    <div class="cover-footer">LFC VBS 2026</div>
  </div>
</div>'''
    return html


# ─── Level Divider Page ──────────────────────────────────────────────
def make_level_divider_page(level_info):
    html = f'''<div class="page">
  <div class="level-divider">
    <div class="level-divider-pre">LFC VBS 2026 &middot; Deliverance</div>
    <div class="level-divider-num">Level {level_info["level"]}</div>
    <div class="level-divider-audience">{level_info["audience"]}</div>
    <div class="level-divider-rule"></div>
    <div class="level-divider-days">
      Day 1: Slavery<br>
      Day 2: The Plagues<br>
      Day 3: The Passover and Red Sea Crossing
    </div>
  </div>
</div>'''
    return html


# ─── Main Assembly ───────────────────────────────────────────────────
def _build_level_pages(level_info):
    """Build activity pages and answer key pages for a single level.

    Returns (activity_pages, answer_pages) where answer_pages is populated
    only for levels 3 & 4.
    """
    level_num = level_info["level"]
    pages = []
    answer_keys = []

    for day_info in level_info["days"]:
        if level_num in (1, 2):
            # Levels 1 & 2: Drawing + Coloring pages
            pages.append(make_drawing_page(level_info, day_info))
            pages.append(make_coloring_page(level_info, day_info))

        elif level_num == 3:
            # Level 3: Worksheet + Puzzle
            pages.append(make_worksheet_page(level_info, day_info))
            puzzle_html, answer_data = make_puzzle_page(level_info, day_info)
            pages.append(puzzle_html)
            if answer_data:
                answer_keys.append(answer_data)

        elif level_num == 4:
            # Level 4: Worksheet + Discussion + Puzzle
            pages.append(make_worksheet_page(level_info, day_info))
            pages.append(make_discussion_page(level_info, day_info))
            puzzle_html, answer_data = make_puzzle_page(level_info, day_info)
            pages.append(puzzle_html)
            if answer_data:
                answer_keys.append(answer_data)

    # Generate answer key pages for levels 3 & 4
    answer_pages = []
    for ak in answer_keys:
        if ak['type'] == 'crossword':
            answer_pages.append(make_crossword_answer_page(ak))
        elif ak['type'] == 'scramble':
            answer_pages.append(make_scramble_answer_page(ak))

    return pages, answer_pages


def generate_all():
    content = load_content()
    base_html = load_base_template()
    all_pages = []

    # Cover / Letterhead
    all_pages.append(make_letterhead_page())

    for level_info in content["levels"]:
        # Level divider
        all_pages.append(make_level_divider_page(level_info))

        activity_pages, answer_pages = _build_level_pages(level_info)
        all_pages.extend(activity_pages)
        all_pages.extend(answer_pages)

    # Combine all pages
    pages_html = "\n".join(all_pages)
    full_html = base_html.replace("{{ content }}", pages_html)

    # Write intermediate HTML for debugging
    html_path = OUTPUT_DIR / "vbs2026_master.html"
    html_path.write_text(full_html)
    print(f"HTML written to {html_path}")

    # Generate PDF
    pdf_path = OUTPUT_DIR / "LFC_VBS_2026_Deliverance_Master.pdf"
    print("Generating PDF (this may take a moment)...")
    HTML(string=full_html, base_url=str(BASE_DIR)).write_pdf(str(pdf_path))
    print(f"PDF written to {pdf_path}")

    # Also generate per-level PDFs for easier printing
    for level_info in content["levels"]:
        level_num = level_info["level"]
        level_pages = [make_level_divider_page(level_info)]

        activity_pages, answer_pages = _build_level_pages(level_info)
        level_pages.extend(activity_pages)
        level_pages.extend(answer_pages)

        level_html = base_html.replace("{{ content }}", "\n".join(level_pages))
        level_pdf = OUTPUT_DIR / f"LFC_VBS_2026_Level_{level_num}.pdf"
        HTML(string=level_html, base_url=str(BASE_DIR)).write_pdf(str(level_pdf))
        print(f"Level {level_num} PDF written to {level_pdf}")


if __name__ == "__main__":
    generate_all()
