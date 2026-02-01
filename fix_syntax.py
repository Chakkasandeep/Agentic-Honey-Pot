import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the problematic logger line (it has embedded newlines)
content = re.sub(
    r'logger\.info\(f"Extracted.*?emails.*?"\)\)',
    'pass  # Extraction logging removed due to syntax issue',
    content,
    flags=re.DOTALL
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed!")
