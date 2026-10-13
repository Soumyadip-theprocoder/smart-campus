import re
import os

html_path = r'C:\Users\Soumy\.gemini\antigravity-ide\brain\9f186b82-7747-4758-8b0d-0d83de658881\.system_generated\steps\1355\content.md'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

href_pattern = re.compile(r'href=["\']([^"\']+\.pdf)["\']', re.IGNORECASE)
links = set(href_pattern.findall(html))
print(f'Total distinct PDF links found: {len(links)}')

struct_links = [l for l in links if 'CourseStructure' in l or 'Structure' in l or 'CURRICULUM' in l]
print(f'\nStructure / Curriculum links ({len(struct_links)}):')
for l in sorted(struct_links):
    print(' ', l)

syll_links = [l for l in links if l not in struct_links]
print(f'\nOther Syllabus links ({len(syll_links)}):')
for l in sorted(syll_links)[:25]:
    print(' ', l)
