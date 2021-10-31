import tldextract, requests
import json, sys, os, re

def parse(file):
    with open(file, 'r') as f:
        file = f.read()
    parseUrls(file)

def parseUrls(html,type="lg"):
    global data
    patterns = ["lg[\.|-][a-zA-Z0-9-.]*\.[a-zA-Z0-9]{2,15}","[a-zA-Z0-9-.]*[\.|-]lg[\.|-][a-zA-Z0-9-.]*\.[a-zA-Z0-9]{2,15}","lg[a-zA-Z0-9-.]*\.[a-zA-Z0-9-.]*\.[a-zA-Z0-9]{2,15}"]
    for regex in patterns:
        matches = re.findall(regex,html, re.MULTILINE | re.DOTALL)
        if matches:
            for match in matches:
                if len(match) > 5:
                    domain = tldextract.extract(match).registered_domain
                    if domain == "": continue
                    if not domain in data[type]: data[type][domain] = []
                    if not match in data[type][domain]: data[type][domain].append(match)

def get(url):
    try:
        request = requests.get(url,allow_redirects=False,timeout=5)
        parseUrls(request.text,"scrap")
        if (request.status_code == 200):
            if len(request.text) < 200:
                print(f"HTML to short {len(request.text)}, dropping {url}")
                return False
            print(f"Got {request.status_code} keeping {url}")
            return True
        else:
            print(f"Got {request.status_code} dropping {url}")
    except Exception as e: return False

if len(sys.argv) == 1:
    print("grabber.py /data/path output.json (optional)")
    sys.exit()

if len(sys.argv) == 3:
    default = sys.argv[2]
else:
     default = "default.json"
folder = sys.argv[1]
folders = os.listdir(folder)
data = {"lg":{},"scrap":{}}

print(f"Parsing {folder}")
for element in folders:
    if element.endswith(".html") or element.endswith(".json"):
        parse(folder+"/"+element)
    else:
        files = os.listdir(folder+"/"+element)
        for file in files:
            if file.endswith(".html") or file.endswith(".json"):
                parse(folder+"/"+element+"/"+file)

print("Validating")
for domain in data['lg']:
    for url in list(data['lg'][domain]):
        response = get("https://"+url)
        if response: continue
        response = get("http://"+url)
        if response: continue
        data['lg'][domain].remove(url)

print("Scrapping")
for domain in list(data['scrap']):
    for url in data['scrap'][domain]:
        if not domain in data['lg']: data['lg'][domain] = []
        if url in data['lg'][domain]: continue
        response = get("https://"+url)
        if response:
            data['lg'][domain].append(url)
            continue
        response = get("http://"+url)
        if response:
            data['lg'][domain].append(url)
            continue

print(f"Saving {default}")
with open(os.getcwd()+'/data/'+default, 'w') as f:
    json.dump(data['lg'], f, indent=4)

print("Updating Readme")
readme = "# Looking-Glass\n"
list = {}
files = os.listdir(os.getcwd()+"/data/")
for file in files:
    if file.endswith(".json"):
        with open(os.getcwd()+"/data/"+file) as handle:
            file = json.loads(handle.read())
        list = dict(list, **file)

for element,urls in list.items():
    if len(urls) > 0:
        readme += "### "+element+"\n"
        for url in urls:
            readme += "* ["+url+"](http://"+url+")\n"

with open(os.getcwd()+"/README.md", 'w') as f:
    f.write(readme)
