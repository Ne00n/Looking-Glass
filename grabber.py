import multiprocessing, requests, json, time, sys, os, re
from tqdm.contrib.concurrent import process_map
from Class.grabber import Grabber
from requests_html import HTML
from functools import partial
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

print(f"Total folders {len(folders)}")
path = os.path.dirname(os.path.realpath(__file__))
crawler = Grabber(path)
files = crawler.findFiles(folders,folder)
results = process_map(crawler.fileToHtml, files, max_workers=4,chunksize=100)
links = []
for row in results: links.extend(row)
links = list(set(links)) 
results = process_map(crawler.filterUrls, links, max_workers=4,chunksize=100)
data = crawler.combine(results)
data['tagged'] = list(set(data['tagged']))
print("Direct Parsing")
domains = list(set(data['direct']))
func = partial(crawler.crawlParse, data=data, ignore=[], type="lg",direct=True)
results = process_map(func, domains, max_workers=8,chunksize=1)
links = []
for row in results:
    if row:
        for domain,block in row.items():
            for url,details in block.items():
                pool = multiprocessing.Pool(processes=4)
                func = partial(crawler.filterUrls, type="lg", domain=domain)
                results = pool.map(func, details['links'])
                data = crawler.combine(results,data)
print("Validating")
data = crawler.crawl(data)
print("Scrapping")
crawler.crawl(data,"scrap")

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
