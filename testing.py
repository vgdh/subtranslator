import re


text = "{\\an8}Hey, we got here right in time, Mav."

text = re.sub(r'\{[^}]*\}', '', text)
# Remove any extra whitespace that might be left
text = re.sub(r'\s+', ' ', text).strip()
print(text)