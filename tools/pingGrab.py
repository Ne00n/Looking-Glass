import dns.resolver, sys, os
sys.path.append(os.getcwd().replace("/tools",""))

from requests_html import HTMLSession
from Class.base import Base
from pathlib import Path 
import tldextract, requests, socket, json, re, os

if len(sys.argv) == 1:
    print("ping.py /data/path output.json (optional)")
    sys.exit()

if len(sys.argv) == 3:
    default = sys.argv[2]
else:
     default = "default.json"
folder = sys.argv[1]
if os.path.isdir(folder):
    files = os.listdir(folder)
else:
    files = []
    files.append(Path(folder).name)
    folder = folder.replace(Path(folder).name,"")

with open(os.getcwd()+"/tools/countries.json") as handle:
    countriesRaw = json.loads(handle.read())

countries = []
for iso,country in countriesRaw.items():
    countries.append(f"{iso.lower()}.")

data = {}
tags = ['speedtest','proof','lg','icmp']
ignore = ['friendhosting','starrydns','frantech']
resolver = dns.resolver.Resolver()
html = HTMLSession()
for file in files:
    print(f"Loading file {file}")
    with open(folder+"/"+file, 'r') as f:
        text = f.read()
    links = text.split()
    for link in links:
        response = html.get(link)
        for target in response.html.absolute_links:
            print(f"Checking {target}")
            if any(element in target for element in tags) or ( not any(element in target for element in ignore) and  any(target.replace("https://","").startswith(element) for element in countries)):
                ext = tldextract.extract(target)
                domain = ext.domain+"."+ext.suffix
                url = '.'.join(ext[:3])
                sub = url.replace("https://","").replace("http://","")
                #IPv4
                try:
                    v4s = resolver.resolve(sub , "A")
                except Exception as e:
                    print(e)
                    continue
                #IPv6
                try:
                    v6s = resolver.resolve(sub , "AAAA")
                except Exception as e:
                    print(e)
                    v6s = []
                if not domain in data: data[domain] = {}
                if not url in data[domain]: data[domain][url] = {"ipv4":[],"ipv6":[]}
                #IPv4
                for v4 in v4s:
                    if not v4.to_text() in data[domain][url]['ipv4']: data[domain][url]['ipv4'].append(v4.to_text())
                #IPv6
                for v6 in v6s:
                    if not v6.to_text() in data[domain][url]['ipv6']: data[domain][url]['ipv6'].append(v6.to_text())


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
