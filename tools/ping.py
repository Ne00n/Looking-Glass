import dns.resolver, sys, os
sys.path.append(os.getcwd().replace("/tools",""))

from requests_html import HTMLSession
from Class.base import Base
import tldextract, requests, socket, json, re, os

if len(sys.argv) == 1:
    print("ping.py src/ping.txt output.json (optional)")
    sys.exit()

if len(sys.argv) == 3:
    default = sys.argv[2]
else:
     default = "default.json"
file = sys.argv[1]
data = {}
resolver = dns.resolver.Resolver()

with open(file, 'r') as f:
    text= f.read()
links = text.split()
for link in links:
    print(f"Checking {link}")
    ext = tldextract.extract(link)
    domain = ext.domain+"."+ext.suffix
    #IPv4
    try:
        v4s = resolver.resolve(link , "A")
    except Exception as e:
        print(e)
        continue
    #IPv6
    try:
        v6s = resolver.resolve(link , "AAAA")
    except Exception as e:
        print(e)
        v6s = []
    if not domain in data: data[domain] = {}
    if not link in data[domain]: data[domain][link] = {"ipv4":[],"ipv6":[]}
    #IPv4
    for v4 in v4s:
        if not v4.to_text() in data[domain][link]['ipv4']: data[domain][link]['ipv4'].append(v4.to_text())
    #IPv6
    for v6 in v6s:
        if not v6.to_text() in data[domain][link]['ipv6']: data[domain][link]['ipv6'].append(v6.to_text())


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
