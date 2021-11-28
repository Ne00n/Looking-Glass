import sys, os
sys.path.append(os.getcwd().replace("/tools",""))

from requests_html import HTMLSession
from Class.base import Base
import json, re, os

html = HTMLSession()
urls = ['http://ec2-reachability.amazonaws.com','http://ipv6.ec2-reachability.amazonaws.com/']

results = {"aws":{}}
for url in urls:
    response = html.get(url)
    rows = response.html.find('tr > td')

    count,block,once = 1,False,[]
    if not url in results["aws"]: results["aws"][url] = {"ipv4":[],"ipv6":[]}
    for row in rows:
        if count == 1:
            if row.text in once or "gov" in row.text:
                block = True
            else:
                once.append(row.text)
        if count == 3 and not block:
            print(row.text)
            if "ipv6" in url:
                results["aws"][url]["ipv6"].append(row.text)
            else:
                results["aws"][url]["ipv4"].append(row.text)
        if count == 4:
            count = 1
            block = False
        else:
            count += 1

with open(os.getcwd()+'/data/aws.json', 'w') as f:
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
