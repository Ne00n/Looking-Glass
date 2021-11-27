import sys, os
sys.path.append(os.getcwd().replace("/tools",""))

from requests_html import HTMLSession
from Class.base import Base
import tldextract, requests, socket, json, re, os

if len(sys.argv) == 1:
    print("ping.py /data/path output.json (optional)")
    sys.exit()

if len(sys.argv) == 3:
    default = sys.argv[2]
else:
     default = "default.json"
folder = sys.argv[1]
files = os.listdir(folder)

print("Getting current IP")
request = requests.get('https://ip.seeip.org/',allow_redirects=False,timeout=5)
if request.status_code == 200:
    ip = request.text
else:
    exit("Could not fetch IP")

with open(os.getcwd()+"/tools/countries.json") as handle:
    countriesRaw = json.loads(handle.read())

countries = []
for iso,country in countriesRaw.items():
    countries.append(f"{iso.lower()}.")

data = {}
tags = ['speedtest','proof','lg','icmp']
ignore = ['friendhosting']
html = HTMLSession()
for file in files:
    with open(folder+"/"+file, 'r') as f:
        text= f.read()
    links = text.split()
    for link in links:
        response = html.get(link)
        for target in response.html.absolute_links:
            print(f"Checking {target}")
            if any(element in target for element in tags) or ( not any(element in target for element in ignore) and  any(target.replace("https://","").startswith(element) for element in countries)):
                ext = tldextract.extract(target)
                domain = ext.domain+"."+ext.suffix
                url = '.'.join(ext[:3])
                try:
                    target = socket.gethostbyname(url)
                except Exception as e:
                    print(f"Could not resolve {url}")
                    continue
                if ip == target: continue
                if not domain in data: data[domain] = {}
                if not url in data[domain]: data[domain][url] = {"ipv4":[],"ipv6":[]}
                if not target in data[domain][url]['ipv4']: data[domain][url]['ipv4'].append(target)

print(f"Saving {default}")
with open(os.getcwd()+'/data/'+default, 'w') as f:
    json.dump(data, f, indent=4)

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
