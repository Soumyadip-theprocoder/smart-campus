import os
import re

d = r'c:/Users/Soumy/.gemini/antigravity/scratch/smart-campus/frontend/src'

for root, dirs, files in os.walk(d):
    for f in files:
        if f.endswith('.jsx'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            new_content = content
            # Replace white translucent backgrounds
            new_content = re.sub(
                r'(background(?:Color)?):\s*[\'"`]rgba\(255,\s*255,\s*255,\s*0\.\d+\)[\'"`]',
                r"\1: 'var(--color-bg-glass)'",
                new_content
            )
            # Replace dark translucent backgrounds (like rgba(0,0,0,0.2))
            new_content = re.sub(
                r'(background(?:Color)?):\s*[\'"`]rgba\(0,\s*0,\s*0,\s*0\.\d+\)[\'"`]',
                r"\1: 'var(--color-bg-hover)'",
                new_content
            )
            # Replace white translucent borders
            new_content = re.sub(
                r'border:\s*[\'"`]1px solid rgba\(255,\s*255,\s*255,\s*0\.\d+\)[\'"`]',
                r"border: '1px solid var(--color-border)'",
                new_content
            )
            # Replace #000 backgrounds
            new_content = re.sub(
                r'(background(?:Color)?):\s*[\'"`]#000[\'"`]',
                r"\1: 'var(--color-bg-elevated)'",
                new_content
            )
            
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                print(f"Updated {f}")
