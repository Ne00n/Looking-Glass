import urllib.request, subprocess, json, sys, re, os

sys.path.append(os.getcwd().replace("/tools",""))
from Class.base import Base

urls = {"gcore":"https://lg.gcorelabs.com","ovh":"https://lg.ovh.net","meerfarbig":"https://meerblick.io"}

def fetch(url):
    try:
        print(f"Getting {url}")
        request = urllib.request.urlopen(url, timeout=20)
        if (request.getcode() == 200):
            return request.read().decode('utf-8')
    except:
        return False

def cmd(command):
    p = subprocess.run(f"{command}", stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return p.stdout.decode('utf-8')

def fingPingable(ip):
    ip = ip.split('.')[:3]
    ip = ".".join(ip) 
    for run in range(1,10):
        dest = f"{ip}.{run}"
        resp = cmd(f"fping {dest}")
        if "is alive" in resp: return dest

results = {}
for provider,url in urls.items():
    html = fetch(url)
    if html is False: continue
    locations = re.findall('class="hosts"><a id="([a-zA-Z0-9]+)"',html, re.MULTILINE | re.DOTALL)
    locations = set(locations)
    for location in locations:
        html = fetch(f"{url}/traceroute/{location}/ipv4?q=one.one.one.one")
        ips = re.findall('<br>.*?"whois">([0-9.]+)<',html, re.MULTILINE)
        if not provider in results: results[provider] = {}
        if not url in results[provider]: results[provider][url] = {"ipv4":[],"ipv6":[]}
        ip = fingPingable(ips[0])
        results[provider][url]["ipv4"].append(ip)
    
with open(os.getcwd()+'/data/bird.json', 'w') as f:
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