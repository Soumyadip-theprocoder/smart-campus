import re
import os

html_path = r'C:\Users\Soumy\.gemini\antigravity-ide\brain\9f186b82-7747-4758-8b0d-0d83de658881\.system_generated\steps\1355\content.md'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

row_pattern = re.compile(r'<tr>(.*?)</tr>', re.DOTALL | re.IGNORECASE)
cell_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL | re.IGNORECASE)
href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
tag_cleaner = re.compile(r'<[^>]+>')

rows = row_pattern.findall(html)
print(f'Total rows: {len(rows)}')

all_links = set()
prog_data = []
for r in rows:
    cells = cell_pattern.findall(r)
    if len(cells) >= 12:
        name = tag_cleaner.sub('', cells[1]).replace('&amp;', '&').strip()
        code = tag_cleaner.sub('', cells[2]).strip()
        session = tag_cleaner.sub('', cells[3]).strip()
        struct_links = href_pattern.findall(cells[4])
        sem_links = {}
        for s_idx in range(1, 9):
            if len(cells) > 4 + s_idx:
                s_links = href_pattern.findall(cells[4 + s_idx])
                if s_links:
                    sem_links[s_idx] = s_links
                    all_links.update(s_links)
        if struct_links:
            all_links.update(struct_links)
        if name and not name.startswith('Program'):
            prog_data.append({
                'name': name,
                'code': code,
                'session': session,
                'struct': struct_links,
                'sems': sem_links
            })

print(f'Valid program rows: {len(prog_data)}')
print(f'Total distinct PDF links on the page: {len(all_links)}')

struct_pdfs = [l for l in all_links if 'CourseStructure' in l or 'Structure' in l]
print(f'\nDistinct CourseStructure PDFs ({len(struct_pdfs)}):')
for p in sorted(struct_pdfs):
    print(' ', p)

print(f'\nAll programs and their structures:')
by_prog = {}
for p in prog_data:
    pname = p['name']
    if pname not in by_prog:
        by_prog[pname] = []
    by_prog[pname].append((p['session'], p['struct'], list(p['sems'].keys())))

for pname, sessions in sorted(by_prog.items()):
    print(f"\n{pname}:")
    for sess, st, sems in sessions:
        print(f"   [{sess}] Struct: {st} | Sems: {sems}")
