import pypdf
import re
import os
import json

SEMESTERS_MAP = {
    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
    'FIRST': 1, 'SECOND': 2, 'THIRD': 3, 'FOURTH': 4, 'FIFTH': 5, 'SIXTH': 6, 'SEVENTH': 7, 'EIGHTH': 8, 'NINTH': 9, 'TENTH': 10,
    '1ST': 1, '2ND': 2, '3RD': 3, '4TH': 4, '5TH': 5, '6TH': 6, '7TH': 7, '8TH': 8, '9TH': 9, '10TH': 10
}

# Complete mapping of each structure PDF to the official department name
FILE_TO_DEPTS = {
    'CSE.pdf': ['B.Tech in Computer Science & Engineering'],
    'CSE20.pdf': ['B.Tech in Computer Science & Engineering'],
    'IT.pdf': ['B.Tech in Information Technology'],
    'ECE.pdf': ['B.Tech in Electronics & Communication Engineering'],
    'EE.pdf': ['B.Tech in Electrical Engineering'],
    'ME.pdf': ['B.Tech in Mechanical Engineering'],
    'CE.pdf': ['B.Tech in Civil Engineering'],
    'AIML20.pdf': ['B.Tech in Artificial Intelligence & Machine Learning'],
    'CSEAIML20.pdf': ['B.Tech in Computer Science & Engineering (Artificial Intelligence and Machine Learning)'],
    'AIDS20.pdf': ['B.Tech in Artificial Intelligence & Data Science'],
    'CSBS20.pdf': ['B.Tech in Computer Science & Business Systems'],
    'CSEDS20.pdf': ['B.Tech in Computer Science & Engineering (Data Science)'],
    'CSECS22.pdf': ['B.Tech in Computer Science & Engineering (Cyber Security)'],
    'CSEIOT22.pdf': ['B.Tech in Computer Science & Engineering (Internet of Things)'],
    'CSEITCS20.pdf': ['B.Tech in Computer Science & Engineering (IoT and Cyber Security including Blockchain Technology)'],
    'CSD21.pdf': ['B.Tech in Computer Science & Design'],
    'DS20.pdf': ['B.Tech in Data Science'],
    'BTECH_ECS23.pdf': ['B.Tech in Electronics and Computer Science'],
    'BT.pdf': ['B.Tech in Biotechnology'],
    'CHE.pdf': ['B.Tech in Chemical Engineering'],
    'AE.pdf': ['B.Tech in Automobile Engineering'],
    'BME.pdf': ['B.Tech in Biomedical Engineering'],
    'AEIE.pdf': ['B.Tech in Applied Electronics & Instrumentation Engineering'],
    'EEE.pdf': ['B.Tech in Electrical & Electronics Engineering'],
    'FT.pdf': ['B.Tech in Food Technology'],
    'TT.pdf': ['B.Tech in Textile Technology'],
    'LT.pdf': ['B.Tech in Leather Technology'],
    'APM.pdf': ['B.Tech in Apparel & Production Management'],
    'CVE.pdf': ['B.Tech in Civil & Environmental Engineering'],
    'CVE23.pdf': ['B.Tech in Civil & Environmental Engineering'],
    'RBT20.pdf': ['B.Tech in Robotics'],
    'EECE25.pdf': ['B.Tech in Electrical & Computer Engineering'],
    'ICE.pdf': ['B.Tech in Instrumentation & Control Engineering'],
    'CurriculumBAE26.pdf': ['B.Tech in Agricultural Engineering'],
    'BARCH.pdf': ['Bachelor of Architecture'],
    'BHMCT.pdf': ['Bachelor in Hotel Management & Catering Technology'],
    'BPHARM21.pdf': ['Bachelor of Pharmacy'],
    'BPHARM20.pdf': ['Bachelor of Pharmacy'],
    'BPHARM.pdf': ['Bachelor of Pharmacy'],
    'BBA23.pdf': ['BBA in Business Admin'],
    'BBA25.pdf': ['BBA in Business Admin'],
    'BCA23.pdf': ['BCA in Computer Science'],
    'BCA25.pdf': ['BCA in Computer Science'],
    'CURRICULUM_BCA.pdf': ['BCA in Computer Science'],
}

def detect_sem(line):
    # Year-Semester combinations, e.g. "Second Year Third Semester" or "Third Year Fifth Semester"
    m_combo = re.search(
        r'(FIRST|SECOND|THIRD|FOURTH|FIFTH|1ST|2ND|3RD|4TH|5TH)\s*YEAR[\-–—\s:]+(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|1ST|2ND|3RD|4TH|5TH|6TH|7TH|8TH|9TH|10TH|[0-9IVX]+)\s*SEMESTER',
        line,
        re.IGNORECASE
    )
    if m_combo:
        s_str = m_combo.group(2).upper().strip()
        if s_str in SEMESTERS_MAP:
            return SEMESTERS_MAP[s_str]
        clean = re.sub(r'(ST|ND|RD|TH)$', '', s_str)
        if clean in SEMESTERS_MAP:
            return SEMESTERS_MAP[clean]

    # Explicit semester headings: "Semester-III", "Semester III", "Semester: 1", "1st. Semester", "(3rd Sem)"
    m_sem = re.search(
        r'(?:Semester[:\-–—\s]*([0-9IVX]+|First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|1st\.?|2nd\.?|3rd\.?|4th\.?|5th\.?|6th\.?|7th\.?|8th\.?|9th\.?|10th\.?)'
        r'|([0-9IVX]+|First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|1st\.?|2nd\.?|3rd\.?|4th\.?|5th\.?|6th\.?|7th\.?|8th\.?|9th\.?|10th\.?)[:\-–—\s]*Semester'
        r'|\(([0-9IVX]+|1st|2nd|3rd|4th|5th|6th|7th|8th)[\-–—\s]*Sem\))',
        line,
        re.IGNORECASE
    )
    if m_sem:
        raw_val = (m_sem.group(1) or m_sem.group(2) or m_sem.group(3)).rstrip('.').upper().strip()
        if raw_val in SEMESTERS_MAP:
            return SEMESTERS_MAP[raw_val]
        clean = re.sub(r'(ST|ND|RD|TH)$', '', raw_val)
        if clean in SEMESTERS_MAP:
            return SEMESTERS_MAP[clean]

    return None

# Unified Regex pattern for course codes (including parenthesis codes like CE(BS)301)
CODE_PATTERN = re.compile(
    r'\b('
    r'[A-Z]{2,4}\([A-Z]{2,4}\)[0-9]{3}[A-Z0-9/]*'
    r'|(?:PCC|ESC|BSC|HSMC|PEC|OEC|PROJ|PC|PE|OE|MC|ES|BS|HM|PW|HS)[ \-–—]*(?:[A-Z]{1,4}[ \-–—]*)?[0-9]{3}[A-Z0-9/]*'
    r'|[A-Z]{2,5}[ \-–—]*[0-9]{3}[A-Z0-9/]*'
    r'|(?:ARCH|BBA|BCA|BHM|BHMCT|BP|PH|BIO|CHE|MTH|ENV)[ \-–—]*[0-9]{3}[A-Z0-9/]*'
    r')\b',
    re.IGNORECASE
)

CREDIT_PATTERN = re.compile(r'\b([0-5](?:\.[0-9]+)?)\b')

def parse_pdf_file(filepath):
    try:
        reader = pypdf.PdfReader(filepath)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []

    full_text = ""
    for p in reader.pages:
        txt = p.extract_text()
        if txt:
            full_text += "\n" + txt

    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    courses = []
    current_sem = 1
    seen_in_file = set()

    for idx, line in enumerate(lines):
        detected = detect_sem(line)
        if detected:
            current_sem = detected

        m_code = CODE_PATTERN.search(line)
        if m_code:
            code = m_code.group(1).strip()
            # Clean up code format
            code = re.sub(r'\s+', '-', code).upper()
            code = re.sub(r'[\-–—]+', '-', code)

            # Avoid false positives like dates or section numbers
            if len(code) < 4 or not any(c.isdigit() for c in code):
                continue

            # Extract course title from line after code
            code_end = m_code.end()
            line_after = line[code_end:].strip()
            # If line_after is empty or too short, look ahead up to 2 lines
            title = line_after
            look_idx = idx + 1
            while len(title) < 4 and look_idx < min(idx + 3, len(lines)):
                next_l = lines[look_idx].strip()
                if not CODE_PATTERN.search(next_l) and not detect_sem(next_l):
                    title += " " + next_l
                look_idx += 1

            # Clean title: strip trailing numbers (hours/credits)
            # Remove credit numbers from end of title
            title = re.sub(r'\b[0-9]+(?:\.[0-9]+)?\s+[0-9]+(?:\.[0-9]+)?\s+[0-9]+(?:\.[0-9]+)?\s+[0-9]+(?:\.[0-9]+)?\s+[0-9]+(?:\.[0-9]+)?$', '', title)
            title = re.sub(r'\b[0-9]+(?:\.[0-9]+)?\s+[0-9]+(?:\.[0-9]+)?\s+[0-9]+(?:\.[0-9]+)?$', '', title)
            title = re.sub(r'\b[0-9]+(?:\.[0-9]+)?\s+[0-9]+(?:\.[0-9]+)?$', '', title)
            title = re.sub(r'\b[0-9]+(?:\.[0-9]+)?$', '', title)
            title = re.sub(r'[\(\[]?[0-9]+[LTP][\)\]]?', '', title, flags=re.I)
            title = re.sub(r'[\ufffd\u2013\u2014]', '-', title)
            title = re.sub(r'\s+', ' ', title).strip(' .,-:')

            if len(title) < 3 or any(w in title.lower() for w in ['curriculum structure', 'table of contents', 'page of', 'applicable from']):
                continue

            # Subject type
            c_low = (code + " " + title).lower()
            if any(k in c_low for k in ['lab', 'laboratory', 'practical', 'sessional', 'studio', 'workshop']):
                sub_type = 'lab'
                sessions = 2
            elif any(k in c_low for k in ['seminar', 'project', 'viva', 'internship', 'training']):
                sub_type = 'seminar'
                sessions = 1
            else:
                sub_type = 'lecture'
                sessions = 3

            # Default credits
            credits = 1.5 if sub_type == 'lab' else (3.0 if sub_type == 'lecture' else 2.0)

            # Check if credits were in the line
            m_cred = re.findall(r'\b([0-5](?:\.[0-9]+)?)\b', line[code_end:])
            if m_cred:
                try:
                    val = float(m_cred[-1])
                    if 0.5 <= val <= 8.0:
                        credits = val
                except ValueError:
                    pass

            key = (code, current_sem)
            if key not in seen_in_file:
                seen_in_file.add(key)
                courses.append({
                    'code': code[:20],
                    'name': title[:200],
                    'semester': current_sem,
                    'credits': credits,
                    'subject_type': sub_type,
                    'sessions_per_week': sessions
                })

    return courses


if __name__ == '__main__':
    pdf_dir = 'scratch/pdfs'
    all_extracted = {}
    total_courses = 0

    for fname, dept_names in sorted(FILE_TO_DEPTS.items()):
        fpath = os.path.join(pdf_dir, fname)
        if not os.path.exists(fpath):
            continue
        c_list = parse_pdf_file(fpath)
        for dept in dept_names:
            if dept not in all_extracted:
                all_extracted[dept] = []
            all_extracted[dept].extend(c_list)
        total_courses += len(c_list)
        print(f"{fname:20} -> {len(c_list):3} courses parsed | Depts: {dept_names}")

    print("\n" + "=" * 60)
    print(f"Total departments covered: {len(all_extracted)}")
    print(f"Total course entries extracted: {total_courses}")
    print("=" * 60)

    # Save to scratch/comprehensive_courses.json
    out_path = 'scratch/comprehensive_courses.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_extracted, f, indent=2)
    print(f"Saved extracted catalog to {out_path}")
