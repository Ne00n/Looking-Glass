from tqdm.contrib.concurrent import process_map
from Class.grabber import Grabber
from requests_html import HTML
import multiprocessing, requests, json, time, sys, os, re
from Class.base import Base

if len(sys.argv) == 1:
    print("grabber.py /data/path output.json (optional)")
    sys.exit()

if len(sys.argv) == 3:
    default = sys.argv[2]
else:
     default = "default.json"
folder = sys.argv[1]
if os.path.isdir(folder): 
    folders = os.listdir(folder)
else:
    folders = folder

print("Getting current IPv4")
request = requests.get('https://ip4.seeip.org/',allow_redirects=False,timeout=5)
if request.status_code == 200:
    ipv4 = request.text
else:
    exit("Could not fetch IPv4")

print("Getting current IPv6")
request = requests.get('https://ip6.seeip.org/',allow_redirects=False,timeout=5)
if request.status_code == 200:
    ipv6 = request.text
else:
    exit("Could not fetch IPv6")

print(f"Total folders {len(folders)}")
crawler = Grabber()
files = crawler.findFiles(folders,folder)
results = process_map(crawler.fileToHtml, files, max_workers=4,chunksize=100)
links = []
for row in results: links.extend(row)
links = list(set(links)) 
results = process_map(crawler.filterUrls, links, max_workers=4,chunksize=100)
data = crawler.combine(results)
data['tagged'] = list(set(data['tagged']))
print("Validating")
data = crawler.crawl(data,ipv4,ipv6)
print("Scrapping")
data = crawler.crawl(data,ipv4,ipv6,"scrap")
print("Direct Parsing")
for domain in list(set(data['direct'])):
    response,workingURL = crawler.get(domain,domain)
    if response:
        links = crawler.getLinks(response)
        pool = multiprocessing.Pool(processes=4)
        results = pool.map(crawler.filterUrlsScrap, links)
        data = crawler.combine(results,data)

print("Scrapping")
crawler.crawl(data,ipv4,ipv6,"scrap")

print(f"Saving {default}")
with open(os.getcwd()+'/data/'+default, 'w') as f:
    json.dump(data['lg'], f, indent=4)

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
