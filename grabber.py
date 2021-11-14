from requests_html import HTML
from Class.base import Base
import json, time, sys, os, re
import tldextract, requests

tags = ['datacenters','data-centers','datacenter','looking-glass','looking','lg','speedtest','icmp','ping']
lookingRegex = re.compile("([\w\d.-]+)?(lg|looking)([\w\d-]+)?(\.[\w\d-]+)(\.[\w\d.]+)")
ipRegex = re.compile('([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s*(<|\")')
ip6Regex = re.compile('([\da-f]{4}:[\da-f]{1,4}:[\d\w:]{1,})')
priv_lo = re.compile("^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
priv_24 = re.compile("^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
priv_20 = re.compile("^192\.168\.\d{1,3}.\d{1,3}$")
priv_16 = re.compile("^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{1,3}.[0-9]{1,3}$")

def parse(file):
    with open(file, 'r') as f:
        file = f.read()
    parseUrls(file)

def scrap():
    global data
    print("Scrapping")
    for domain in list(data['scrap']):
        for url in list(data['scrap'][domain]):
            if not domain in data['lg']: data['lg'][domain] = {}
            if url in data['lg'][domain]: continue
            response = get(url,domain)
            if response:
                data['lg'][domain][url] = []
                ips = parseIPs(ip,response)
                if ips['ipv4']:
                    data['lg'][domain][url] = ips
                elif url in tagged:
                    del data['lg'][domain][url]
                continue
            del data['scrap'][domain][url]

def parseUrls(html,type="lg"):
    global lookingRegex, ignore, direct, data, tags
    skip = ['entry/register','entry/signin','/discussion/','/profile/','lowendtalk.com','lowendbox.com','speedtest.net','youtube.com','geekbench.com','github.com','facebook.com',
    'twitter.com','linkedin.com']
    onlyDirect = ['cart','order','billing','ovz','openvz','kvm','lxc','vps','server','virtual','cloud','compute','dedicated','ryzen']
    parse = HTML(html=html)
    if parse.links:
        for link in parse.links:
            if link in ignore: continue
            if link == "/": continue
            if any(tag in link for tag in skip): continue
            ignore.append(link)
            domain = tldextract.extract(link).registered_domain
            if domain == "": continue
            if any(element in link  for element in onlyDirect):
                if not domain in direct: direct.append(domain)
            #in link but should not be in domain
            if any(element in link  for element in tags) and not any(element in domain  for element in tags):
                if not domain in data[type]: data[type][domain] = {}
                if not link in data[type][domain]: data[type][domain][link] = []
                tagged.append(link)
    matches = lookingRegex.findall(html, re.DOTALL)
    if matches:
        for match in matches:
            result = "".join(match)
            if result in ignore: continue
            domain = tldextract.extract(result).registered_domain
            if domain == "": continue
            if not domain in direct: direct.append(domain)
            if domain == "": continue
            if result.endswith("."): result = result[:len(result) -2]
            if not domain in data[type]: data[type][domain] = {}
            if not result in data[type][domain]: data[type][domain][result] = []
            ignore.append(result)
            if match[0]: data[type][domain][result.replace(match[0],"")] = []

def parseLinks(html,domain,type="lg"):
    global data,tagged,tags
    html = HTML(html=html)
    ignore = ['foxbusiness.com']
    if html.links:
        for link in html.links:
            if link in ignore: continue
            if any(element in link  for element in tags):
                if not domain in data[type]: data[type][domain] = {}
                if domain in link or "http" in link:
                    url = link
                else:
                    if link.startswith("/"):
                        url = domain + link
                    else:
                        url = domain + "/" + link
                if not link in data[type][domain]:
                    data[type][domain][url] = []
                    tagged.append(url)
                print("Found",url)

def isPrivate(ip):
    global priv_lo,priv_16,priv_20,priv_24
    #Source https://stackoverflow.com/questions/691045/how-do-you-determine-if-an-ip-address-is-private-in-python
    return (priv_lo.match(ip) or priv_24.match(ip) or priv_20.match(ip) or priv_16.match(ip))

def parseIPs(ip,html):
    global ipRegex
    ipv4s = ipRegex.findall(html, re.DOTALL)
    ipv6s = ip6Regex.findall(html, re.DOTALL)
    yourIP = re.findall("(Your IP Address|My IP):.*?([\d.]+)\s?<",html, re.MULTILINE | re.DOTALL)
    yourIPv6 = re.findall("(Your IP Address|My IP):.*?([\da-f]{4}:[\da-f]{1,4}:[\d\w:]{1,})\s?<",html, re.IGNORECASE | re.DOTALL)
    response = {"ipv4":[],"ipv6":[]}
    for entry in ipv4s:
        if len(ipv4s) > 30: break
        if yourIP and yourIP[0][1] == entry[0]: continue
        if isPrivate(entry[0]): continue
        if entry[0] == ip: continue
        response['ipv4'].append(entry[0])
    for entry in ipv6s:
        if yourIPv6 and yourIPv6[0][1] == entry: continue
        if len(ipv6s) > 30: break
        response['ipv6'].append(entry)
    response['ipv4'] = list(set(response['ipv4']))
    response['ipv6'] = list(set(response['ipv6']))
    return response

def get(url,domain):
    if url.lower().endswith((".test", ".zip", ".bin",".png",".jpg",".dat",".pdf",".gz",".data",".img",".mb",".db")): return False
    for run in range(4):
        try:
            if run > 1: time.sleep(0.5)
            if url.startswith("//"): url = url.replace("//","")
            if not "http" in url:
                prefix = "https://" if run % 2 == 0 else "http://"
            else:
                prefix = ""
            print(f"Getting {prefix+url}")
            request = requests.get(prefix+url,allow_redirects=True,timeout=6)
            if domain.lower() not in request.url.lower():
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
            print(f"Retrying {prefix+url} got connection error")
        except Exception as e:
            print(f"Retrying {prefix+url} got {e}")
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
data,direct,ignore,tagged = {"lg":{},"scrap":{}},[],[],[]

print("Getting current IP")
request = requests.get('https://ip.seeip.org/',allow_redirects=False,timeout=5)
if request.status_code == 200:
    ip = request.text
else:
    exit("Could not fetch IP")

print(f"Total folders {len(folders)}")
print(f"Parsing {folder}")
for index, element in enumerate(folders):
    if element.endswith(".html") or element.endswith(".json"):
        parse(folder+"/"+element)
    else:
        files = os.listdir(folder+"/"+element)
        for findex, file in enumerate(files):
            if file.endswith(".html") or file.endswith(".json"):
                parse(folder+"/"+element+"/"+file)
                print(f"Done {findex} of {len(files)}")
    print(f"Done {index} of {len(folders)}")

print("Validating")
for domain in data['lg']:
    for url in list(data['lg'][domain]):
        response = get(url,domain)
        if response:
            parseUrls(response,"scrap")
            ips = parseIPs(ip,response)
            if ips['ipv4']:
                data['lg'][domain][url] = ips
            elif url in tagged:
                del data['lg'][domain][url]
            continue
        del data['lg'][domain][url]

scrap()

for domain in direct:
    response = get(domain,domain)
    if response:
        parseUrls(response,"scrap")
        parseLinks(response,domain,"scrap")
        continue

scrap()

print(f"Saving {default}")
with open(os.getcwd()+'/data/'+default, 'w') as f:
    json.dump(data['lg'], f, indent=4)

print("Merging files")
list = Base.merge()

print("Updating Readme")
readme = Base.readme(list)

print("Saving Readme")
with open(os.getcwd()+"/README.md", 'w') as f:
    f.write(readme)

print(f"Saving everything.json")
with open(os.getcwd()+'/data/everything.json', 'w') as f:
    json.dump(list, f, indent=4)
