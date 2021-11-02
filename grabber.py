from requests_html import HTML
import json, time, sys, os, re
import tldextract, requests


def parse(file):
    with open(file, 'r') as f:
        file = f.read()
    parseUrls(file)

def parseUrls(html,type="lg"):
    global data,direct
    matches = re.findall("([\w\d.-]+)?(lg|looking)([\w\d-]+)?(\.[\w\d-]+)(\.[\w\d.]+)",html, re.MULTILINE | re.DOTALL)
    if matches:
        for match in matches:
            result = "".join(match)
            domain = tldextract.extract(result).registered_domain
            if not domain in direct: direct.append(domain)
            if domain == "": continue
            if result.endswith("."): result = result[:len(result) -2]
            if not domain in data[type]: data[type][domain] = {}
            if not result in data[type][domain]: data[type][domain][result] = []
            if match[0]: data[type][domain][result.replace(match[0],"")] = []

def parseLinks(html,domain,type="lg"):
    global data
    html = HTML(html=html)
    tags = ['datacenters','data-centers','datacenter']
    if html.links:
        for link in html.links:
            if any(element in link  for element in tags):
                if not domain in data[type]: data[type][domain] = {}
                if domain in link:
                    url = link
                else:
                    if link.startswith("/"):
                        url = domain + link
                    else:
                        url = domain + "/" + link
                if not link in data[type][domain]: data[type][domain][url.replace("https://","").replace("http://","")] = []
                print("Found",url)

def isPrivate(ip):
    #Source https://stackoverflow.com/questions/691045/how-do-you-determine-if-an-ip-address-is-private-in-python
     priv_lo = re.compile("^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
     priv_24 = re.compile("^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
     priv_20 = re.compile("^192\.168\.\d{1,3}.\d{1,3}$")
     priv_16 = re.compile("^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{1,3}.[0-9]{1,3}$")
     return (priv_lo.match(ip) or priv_24.match(ip) or priv_20.match(ip) or priv_16.match(ip))

def parseIPs(ip,html):
    ipv4s = re.findall("([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s*(<|\")",html, re.MULTILINE | re.DOTALL)
    yourIP = re.findall("(Your IP Address|My IP):.*?>([\d.]+)<",html, re.MULTILINE | re.DOTALL)
    response = {"ipv4":[]}
    for entry in ipv4s:
        if yourIP and yourIP[0][1] == entry[0]: continue
        if isPrivate(entry[0]): continue
        if entry[0] == ip: continue
        response['ipv4'].append(entry[0])
    response['ipv4'] = list(set(response['ipv4']))
    return response

def get(url,domain):
    for run in range(4):
        try:
            if run > 1: time.sleep(0.5)
            prefix = "https://" if run % 2 == 0 else "http://"
            request = requests.get(prefix+url,allow_redirects=True,timeout=3)
            if domain not in request.url:
                print(f"Got redirected to different domain {url} vs {request.url}")
                continue
            parseUrls(request.text,"scrap")
            if (request.status_code == 200):
                if len(request.text) < 90:
                    print(f"HTML to short {len(request.text)}, dropping {request.url}")
                    continue
                if "window.location.replace" in request.text:
                    print(f"Found Javascript redirect, dropping {request.url}")
                    return False
                print(f"Got {request.status_code} keeping {request.url}")
                return request.text
            else:
                print(f"Got {request.status_code} dropping {request.url}")
                continue
        except requests.ConnectionError:
            print(f"Retrying {request.url} got connection error")
        except Exception as e:
            print(f"Retrying {request.url} got {e}")
    return False

if len(sys.argv) == 1:
    print("grabber.py /data/path output.json (optional)")
    sys.exit()

if len(sys.argv) == 3:
    default = sys.argv[2]
else:
     default = "default.json"
folder = sys.argv[1]
folders = os.listdir(folder)
data,direct = {"lg":{},"scrap":{}},[]

print("Getting current IP")
request = requests.get('https://ip.seeip.org/',allow_redirects=False,timeout=5)
if request.status_code == 200:
    ip = request.text
else:
    exit("Could not fetch IP")

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
for domain in direct:
    response = get(domain,domain)
    if response:
        parseUrls(response)
        parseLinks(response,domain)

for domain in data['lg']:
    for url in list(data['lg'][domain]):
        response = get(url,domain)
        if response:
            parseUrls(response,"scrap")
            ips = parseIPs(ip,response)
            if ips: data['lg'][domain][url] = ips
            continue
        del data['lg'][domain][url]

print("Scrapping")
for domain in list(data['scrap']):
    for url in list(data['scrap'][domain]):
        if not domain in data['lg']: data['lg'][domain] = {}
        if url in data['lg'][domain]: continue
        response = get(url,domain)
        if response:
            data['lg'][domain][url] = []
            ips = parseIPs(ip,response)
            if ips: data['lg'][domain][url] = ips
            continue

for domain,details in list(data['lg'].items()):
    if not details: del data['lg'][domain]

print("Filter double IP's")
for domain, details in data['lg'].items():
    once = []
    for url,ips in list(details.items()):
        for ip in list(ips['ipv4']):
            if ip in once:
                del data['lg'][domain][url]
                continue
            once.append(ip)

print(f"Saving {default}")
with open(os.getcwd()+'/data/'+default, 'w') as f:
    json.dump(data['lg'], f, indent=4)

print("Updating Readme")
readme = "# Looking-Glass\n"
list = {}
files = os.listdir(os.getcwd()+"/data/")
for file in files:
    if file.endswith(".json") and not "everything" in file:
        with open(os.getcwd()+"/data/"+file) as handle:
            file = json.loads(handle.read())
        list = dict(list, **file)

for element,urls in list.items():
    if len(urls) > 0:
        readme += "### "+element+"\n"
        for url in urls:
            readme += "* ["+url+"](http://"+url+")\n"

print(f"Saving everything.json")
with open(os.getcwd()+'/data/everything.json', 'w') as f:
    json.dump(list, f, indent=4)

with open(os.getcwd()+"/README.md", 'w') as f:
    f.write(readme)
