with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 300 (index 299)
lines[299] = '        logger.info(f"Extracted: Bank={len(intelligence[\'bankAccounts\'])}, UPI={len(intelligence[\'upiIds\'])}, Phone={len(intelligence[\'phoneNumbers\'])}, Email={len(intelligence[\'emails\'])}")\n'

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed!")
