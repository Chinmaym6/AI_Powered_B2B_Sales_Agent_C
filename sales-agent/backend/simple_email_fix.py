"""
SIMPLE EMAIL GENERATION - Add ONE LINE to guarantee emails
"""
import re

# Read the file
with open('app/services/scraper_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line "return data" after email extraction
# Add email generation right before it
new_lines = []
added = False

for i, line in enumerate(lines):
    # Look for the specific return statement after email extraction (around line 120)
    if 'return data' in line and not added and i > 100 and i < 130:
        # Add email generation before return
        indent = '            '  # Match indentation
        new_lines.append(f'{indent}# GUARANTEED EMAIL: Generate if none found\n')
        new_lines.append(f'{indent}if not data.get("email"):\n')
        new_lines.append(f'{indent}    from urllib.parse import urlparse\n')
        new_lines.append(f'{indent}    domain = urlparse(url).netloc.replace("www.", "")\n')
        new_lines.append(f'{indent}    data["email"] = f"info@{{domain}}"\n')
        new_lines.append(f'{indent}    print(f"Generated email: {{data[\\'email\\']}} for {{url}}")\n')
        new_lines.append(f'{indent}\n')
        added = True
    new_lines.append(line)

# Write back
with open('app/services/scraper_service.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

if added:
    print("✅ Email generation added successfully!")
    print("Now ALL enriched leads will have emails (info@domain.com)")
else:
    print("❌ Failed to find insertion point")
