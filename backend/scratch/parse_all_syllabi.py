import pypdf
import re
import os
import json

SEMESTERS_MAP = {
    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8,
    'FIRST': 1, 'SECOND': 2, 'THIRD': 3, 'FOURTH': 4, 'FIFTH': 5, 'SIXTH': 6, 'SEVENTH': 7, 'EIGHTH': 8,
    '1ST': 1, '2ND': 2, '3RD': 3, '4TH': 4, '5TH': 5, '6TH': 6, '7TH': 7, '8TH': 8
}

FILE_TO_DEPT = {
    'CSE.pdf': 'B.Tech in Computer Science & Engineering',
    'IT.pdf': 'B.Tech in Information Technology',
    'ECE.pdf': 'B.Tech in Electronics & Communication Engineering',
    'EE.pdf': 'B.Tech in Electrical Engineering',
    'ME.pdf': 'B.Tech in Mechanical Engineering',
    'CE.pdf': 'B.Tech in Civil Engineering',
    'AIML20.pdf': 'B.Tech in Artificial Intelligence & Machine Learning',
    'AIDS20.pdf': 'B.Tech in Artificial Intelligence & Data Science',
    'CSBS20.pdf': 'B.Tech in Computer Science & Business Systems',
    'CSEDS20.pdf': 'B.Tech in Computer Science & Engineering (Data Science)',
    'CSECS22.pdf': 'B.Tech in Computer Science & Engineering (Cyber Security)',
    'CSEIOT22.pdf': 'B.Tech in Computer Science & Engineering (Internet of Things)',
    'BT.pdf': 'B.Tech in Biotechnology',
    'CHE.pdf': 'B.Tech in Chemical Engineering',
    'AE.pdf': 'B.Tech in Automobile Engineering',
    'BME.pdf': 'B.Tech in Biomedical Engineering',
    'AEIE.pdf': 'B.Tech in Applied Electronics & Instrumentation Engineering',
    'EEE.pdf': 'B.Tech in Electrical & Electronics Engineering',
    'FT.pdf': 'B.Tech in Food Technology',
    'TT.pdf': 'B.Tech in Textile Technology',
    'LT.pdf': 'B.Tech in Leather Technology',
    'APM.pdf': 'B.Tech in Apparel & Production Management',
    'CVE.pdf': 'B.Tech in Civil & Environmental Engineering',
    'RBT20.pdf': 'B.Tech in Robotics',
    'EECE25.pdf': 'B.Tech in Electrical & Computer Engineering',
}

def detect_sem(line):
    # Year-Semester combinations like "SECOND YEAR - THIRD SEMESTER" or "SECOND YEAR FIRST SEMESTER"
    m_combo = re.search(r'(FIRST|SECOND|THIRD|FOURTH|1ST|2ND|3RD|4TH)\s*YEAR[\-–—\s]+(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|1ST|2ND|3RD|4TH|5TH|6TH|7TH|8TH)\s*SEMESTER', line, re.IGNORECASE)
    if m_combo:
        y_str = m_combo.group(1).upper()
        s_str = m_combo.group(2).upper()
        # If second word is THIRD, FOURTH, FIFTH, etc. (already semester 3, 4, 5)
        clean_s = re.sub(r'(ST|ND|RD|TH)$', '', s_str)
        if clean_s in SEMESTERS_MAP:
            direct_val = SEMESTERS_MAP[clean_s]
            if direct_val > 2:
                return direct_val
        y_num = 1 if 'FIRST' in y_str or '1' in y_str else (2 if 'SECOND' in y_str or '2' in y_str else (3 if 'THIRD' in y_str or '3' in y_str else 4))
        s_num = 1 if 'FIRST' in s_str or '1' in s_str else 2
        return (y_num - 1) * 2 + s_num

    # Semester mentions with optional hyphens: "Semester-III", "Semester - 4", "3rd Semester", etc.
    m_sem = re.search(
        r'(?:Semester[\-–—\s]*([0-9IVX]+|First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth)'
        r'|([0-9](?:st|nd|rd|th)?|First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|[IVX]+)[\-–—\s]*Semester'
        r'|\(([0-9](?:st|nd|rd|th)?|[IVX]+)[\-–—\s]*Sem\))',
        line,
        re.IGNORECASE
    )
    if m_sem:
        val = (m_sem.group(1) or m_sem.group(2) or m_sem.group(3)).upper().strip()
        val = re.sub(r'(ST|ND|RD|TH)$', '', val)
        return SEMESTERS_MAP.get(val)

    return None

code_token_re = re.compile(
    r'\b('
    r'(?:PCC|ESC|BSC|HSMC|PEC|OEC|PROJ|PC|PE|OE|MC|ES|BS|HM|PW|HS)[ \-–—]*(?:[A-Z]{1,4}[ \-–—]*)?[0-9]{3}[A-Z0-9/]*'
    r'|[A-Z]{2,4}\s*(?:\([A-Z]+\))?\s*[0-9]{3}[A-Z0-9/]*'
    r'|(?:HU|EC|EE|ME|CE|CS|IT|BT|CH|CHE|AE|AUE|EI|FT|TT|LT)[ \-–—]*[0-9]{3}[A-Z0-9/]*'
    r')\b',
    re.IGNORECASE
)

def parse_pdf(file_path):
    reader = pypdf.PdfReader(file_path)
    full_text = ''
    for p in reader.pages:
        full_text += '\n' + p.extract_text()

    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    courses = []
    current_sem = None

    for idx, line in enumerate(lines):
        sem_found = detect_sem(line)
        if sem_found:
            current_sem = sem_found

        if not current_sem:
            continue

        m_code = code_token_re.search(line)
        if m_code:
            raw_code = m_code.group(1).strip()
            if not any(c.isdigit() for c in raw_code):
                continue

            code_end = m_code.end()
            after_code = line[code_end:].strip()

            num_match = re.search(r'\s+([0-9\.\-]+(?:\s+[0-9\.\-]+)*)$', after_code)
            credits = 3.0
            if num_match:
                num_str = num_match.group(1).strip()
                title = after_code[:num_match.start()].strip()
                tokens = [float(x) for x in num_str.split() if re.match(r'^[0-9]+(?:\.[0-9]+)?$', x)]
                if tokens:
                    credits = tokens[-1]
            else:
                title = after_code

            # Next line append if title truncated
            if len(title) < 4 and idx + 1 < len(lines):
                next_l = lines[idx + 1]
                if not code_token_re.search(next_l) and not detect_sem(next_l):
                    title = title + ' ' + next_l
            elif idx + 1 < len(lines) and any(title.endswith(x) for x in ['&', 'and', 'of', 'in', 'for']):
                next_l = lines[idx + 1]
                if not code_token_re.search(next_l) and not detect_sem(next_l):
                    title = title + ' ' + next_l

            title = title.strip(' .,-:')
            if not title or len(title) < 3 or any(k in title.upper() for k in ['TOTAL', 'CREDITS', 'SEMESTER', 'CONTACT HOURS', 'SL.NO', 'FIELD', 'COURSE NO', 'PAPERS']):
                continue

            clean_code = re.sub(r'[–—]', '-', raw_code)
            clean_code = re.sub(r'\s+', '', clean_code)

            is_lab = '9' in clean_code or any(k in title.lower() for k in ['lab', 'laboratory', 'workshop', 'practice', 'sessional', 'drawing'])
            is_proj = any(k in title.lower() for k in ['project', 'internship', 'seminar', 'viva'])
            subject_type = 'lab' if is_lab else ('seminar' if is_proj else 'lecture')

            sessions = 3
            if is_lab:
                sessions = 2 if credits <= 1.0 else (4 if credits >= 2.0 else 3)
            elif credits == 4.0:
                sessions = 4
            elif credits == 2.0:
                sessions = 2
            elif credits == 1.0:
                sessions = 1

            courses.append({
                'semester': current_sem,
                'code': clean_code,
                'name': title,
                'credits': credits,
                'subject_type': subject_type,
                'sessions_per_week': sessions,
            })

    return courses

all_dept_courses = {}
total_count = 0

for fname, dept_name in FILE_TO_DEPT.items():
    fpath = os.path.join('scratch/pdfs', fname)
    if os.path.exists(fpath):
        parsed = parse_pdf(fpath)
        unique = {}
        for c in parsed:
            key = (c['code'], c['semester'])
            if key not in unique:
                unique[key] = c
        courses_list = list(unique.values())
        all_dept_courses[dept_name] = courses_list
        sems = sorted(list(set(c['semester'] for c in courses_list)))
        print(f"{dept_name:55} -> {len(courses_list):2} courses | Sems: {sems}")
        total_count += len(courses_list)

print(f"\nSuccessfully extracted {total_count} courses across {len(all_dept_courses)} departments!")
with open('scratch/all_courses.json', 'w', encoding='utf-8') as f:
    json.dump(all_dept_courses, f, indent=2)
