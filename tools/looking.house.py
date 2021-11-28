import sys, os
sys.path.append(os.getcwd().replace("/tools",""))

from requests_html import HTMLSession
from Class.base import Base
import json, re, os

html = HTMLSession()
response = html.get('https://looking.house/points.php')
rows = response.html.find('tr > td > a')

results = {}
for index, row in enumerate(rows):
    if index % 2 == 0:
        provider = rows[index+1].text
        link = "looking.house" + list(row.links)[0]
        if not provider in results: results[provider] = {}
        ipv4s = re.findall("([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})",row.text, re.MULTILINE | re.DOTALL)
        ipv6s = re.findall('([\da-f]{4}:[\da-f]{1,4}:[\d\w:]{1,})',row.text, re.MULTILINE | re.DOTALL)
        if not link in results[provider]: results[provider][link] = {"ipv4":[ipv4s[0]],"ipv6":ipv6s}

with open(os.getcwd()+'/data/looking.json', 'w') as f:
    json.dump(results, f, indent=4)

Core = Base()
print("Merging files")
list = Core.merge()

print("Updating Readme")
readme = Core.readme(list)

print("Saving Readme")
with open(os.getcwd()+"/README.md", 'w') as f:
    f.write(readme)

print(f"Saving everything.json")
with open(os.getcwd()+'/data/everything.json', 'w') as f:
    json.dump(list, f, indent=4)
