"""SIMPLE INSERT - Add email generation at line 79"""
# Read file
with open('app/services/scraper_service.py', 'r') as f:
    lines = f.readlines()

# Insert at line 79 (before "return data")
insert_at = 78  # 0-indexed, so line 79 is index 78
email_code = [
    "        \n",
    "        # GUARANTEED EMAIL: Generate if none found\n",
    "        if not data.get('email'):\n",
    "            domain = urlparse(url).netloc.replace('www.', '')\n",
    "            data['email'] = f'info@{domain}'\n",
]

# Insert lines
lines[insert_at:insert_at] = email_code

# Write
with open('app/services/scraper_service.py', 'w') as f:
    f.writelines(lines)

print("✅ Email generation added at line 79!")
