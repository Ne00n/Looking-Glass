import tldextract, requests, time, sys, os, re
from requests_html import HTML
from functools import partial
import multiprocessing

class Grabber():

    lookingRegex = re.compile("([\w\d.-]+)?(lg|looking)([\w\d-]+)?(\.[\w\d-]+)(\.[\w\d.]+)")
    tags = ['datacenters','data-center','data-centers','datacenter','looking-glass','looking_glass','lookingglass','looking','lg','speedtest','icmp','ping']
    ipRegex = re.compile('([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s*(<|\")')
    ip6Regex = re.compile('([\da-f]{4}:[\da-f]{1,4}:[\d\w:]{1,})')
    priv_lo = re.compile("^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    priv_24 = re.compile("^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    priv_20 = re.compile("^192\.168\.\d{1,3}.\d{1,3}$")
    priv_16 = re.compile("^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{1,3}.[0-9]{1,3}$")
    skip = ['/dashboard/message/','/plugin/thankfor/','entry/signin','/entry/register','/entry/signout','/profile/','/discussion/','lowendtalk.com','lowendbox.com','speedtest.net','youtube.com','geekbench.com','github.com','facebook.com','lafibre.info',
        'linkedin.com','archive.org','reddit.com','ebay','google','wikipedia','twitter','smokeping','#comment-','xing.com','microsoft.com','github.com','github.io','pinterest.com','flipboard.com','tomshardware.com','servethehome.com','t.me','telegram.org','udemy',
        'hostingchecker.com','ndtv.com','thedailybeast.com','nvidia.com','vice.com','reuters.com','serverfault.com','vpsboard.com','dnstools.ws','kiloroot','check-host.net','instagram','t-online.de','vancouversun.com','4players.de','myip.ms','silive.com','pingdom',
        'foxbusiness.com','helgeklein.com','dailymail.co.uk','variety.com','bitnodes.io','helloacm.com','datacenterknowledge.com','flipkart.com','techspot.com','yahoo.com','stacksocial.com','stackcommerce.com','videocardz.com','cnbc.com','arstechnica.com',
        'ovhcloud.com','comm2ig.dk']

    def __init__(self):
        sys.setrecursionlimit(1500)
        blacklists = ['https://raw.githubusercontent.com/olbat/ut1-blacklists/master/blacklists/shopping/domains','https://raw.githubusercontent.com/olbat/ut1-blacklists/master/blacklists/games/domains',
        'https://raw.githubusercontent.com/olbat/ut1-blacklists/master/blacklists/social_networks/domains']
        for link in blacklists:
            print(f"Downloading Blacklist {link}")
            request = requests.get(link,allow_redirects=False,timeout=6)
            if (request.status_code == 200):
                links = request.text.split()
                for url in links:
                    self.skip.append(url)

    def findFiles(self,folders,folder):
        htmls = []
        if os.path.isfile(folder): return [folder]
        print(f"Checking {folder}")
        for index, element in enumerate(folders):
            if element.endswith(".html") or element.endswith(".json"):
                htmls.append(folder+"/"+element)
            else:
                files = os.listdir(folder+"/"+element)
                for findex, file in enumerate(files):
                    if file.endswith(".html") or file.endswith(".json"):
                        htmls.append(folder+"/"+element+"/"+file)
                        print(f"Done {findex} of {len(files)}")
            print(f"Done {index} of {len(folders)}")
        return htmls

    def fileToHtml(self,file):
        with open(file, 'r') as f:
            html = f.read()
        return self.getLinks(html)

    def getLinks(self,html):
        try:
            parse = HTML(html=html)
            return parse.links
        except Exception as e:
            print(f"Failed to parse HTML {e}")
            return []

    def isPrivate(self,ip):
        #Source https://stackoverflow.com/questions/691045/how-do-you-determine-if-an-ip-address-is-private-in-python
        return (self.priv_lo.match(ip) or self.priv_24.match(ip) or self.priv_20.match(ip) or self.priv_16.match(ip))

    def parseIPs(self,ipv4,ipv6,html):
        ipv4s = self.ipRegex.findall(html, re.DOTALL)
        ipv6s = self.ip6Regex.findall(html, re.DOTALL)
        yourIP = re.findall("(Your IP Address|My IP):.*?([\d.]+)\s?<",html, re.MULTILINE | re.DOTALL)
        yourIPv6 = re.findall("(Your IP Address|My IP):.*?([\da-f]{4}:[\da-f]{1,4}:[\d\w:]{1,})\s?<",html, re.IGNORECASE | re.DOTALL)
        response = {"ipv4":[],"ipv6":[]}
        for entry in ipv4s:
            if len(ipv4s) > 30: break
            if yourIP and yourIP[0][1] == entry[0]: continue
            if self.isPrivate(entry[0]): continue
            if entry[0] == ipv4: continue
            response['ipv4'].append(entry[0])
        for entry in ipv6s:
            if yourIPv6 and yourIPv6[0][1] == entry: continue
            if entry == ipv6: continue
            if len(ipv6s) > 30: break
            response['ipv6'].append(entry)
        response['ipv4'] = list(set(response['ipv4']))
        response['ipv6'] = list(set(response['ipv6']))
        return response

    def combine(self,results,data={"lg":{},"scrap":{},"direct":[],"tagged":[],"ignore":[]}):
        for result in results:
            if result:
                data['direct'].extend(result['direct'])
                data['tagged'].extend(result['tagged'])
                data['ignore'].extend(result['ignore'])
                for domain,urls in result['data']['lg'].items():
                    if not domain in data['lg']: data['lg'][domain] = {}
                    for url in urls:
                        if not url in data['lg'][domain]: data['lg'][domain][url] = []
                for domain,urls in result['data']['scrap'].items():
                    if not domain in data['scrap']: data['scrap'][domain] = {}
                    for url in urls:
                        if not url in data['scrap'][domain]: data['scrap'][domain][url] = []
        return data

    def crawl(self,data,ipv4,ipv6,type="lg"):
        for domain in list(data[type]):
            for url in list(data[type][domain]):
                if any(url in s for s in data['ignore']): continue
                data['ignore'].append(url)
                if type == "scrap":
                    if not domain in data['lg']: data['lg'][domain] = {}
                    if url in data['lg'][domain]: continue 
                response,workingURL = self.get(url,domain)
                if response:
                    if type == "scrap" and url not in data['lg'][domain]: data['lg'][domain][url] = []
                    links = self.getLinks(response)
                    for link in list(links):
                        if link in data['ignore']: links.remove(link)
                    pool = multiprocessing.Pool(processes=4)
                    func = partial(self.filterUrls, type="scrap", domain=domain)
                    results = pool.map(func, links)
                    data = self.combine(results,data)
                    ips = self.parseIPs(ipv4,ipv6,response)
                    current = url
                    if url != workingURL:
                        print(f"Replacing {url} with {workingURL}")
                        current = workingURL
                        del data['lg'][domain][url]
                        data['lg'][domain][current] = {}
                    if ips['ipv4'] or ips['ipv6']:
                        data['lg'][domain][current] = ips
                    elif url in data['tagged']:
                        if current in data['lg'][domain]: 
                            del data['lg'][domain][current]
                            data['tagged'].remove(url)
                    continue
                del data[type][domain][url]
        return data

    def filterUrls(self,link,type="lg",domain=""):
        data,direct,tagged,ignore = {"lg":{},"scrap":{},"ignore":[]},[],[],[]
        onlyDirect = ['cart','order','billing','ovz','openvz','kvm','lxc','vps','server','vserver','virtual','vm','cloud','compute','dedicated','ryzen','epyc','xeon','intel','amd']
        if domain and not domain in link and not "http" in link:
            if link.startswith("//"):
                return False
            elif link.startswith("/"):
                link = domain + link
            else:
                link = domain + "/" + link
        #extension filter
        whitelist = ['.php','.html','.htm']
        extension = re.findall("[a-z]\/.*?(\.[a-zA-Z]+)$",link.lower())
        if extension and not extension[0] in whitelist:
            print(f"Skipping {link} not in whitelist")
            return False
        #additional filter
        if link.lower().endswith(("1g","10g","lua",'test-10mb','test-100mb','test-1000mb')): 
            print(f"Skipping {link}")
            return False
        if any(tag in link for tag in self.skip): return False
        domain = tldextract.extract(link).registered_domain
        if not domain: return False
        if any(element in link  for element in onlyDirect):
            if not domain in direct: direct.append(domain)
        #in link but should not be in domain
        if any(element in link  for element in self.tags) and not any(element in domain for element in self.tags):
            if not domain in data[type]: data[type][domain] = {}
            if not link in data[type][domain]: data[type][domain][link] = []
            tagged.append(link)
        matches = self.lookingRegex.findall(link, re.DOTALL)
        if matches:
            for match in matches:
                result = "".join(match)
                domain = tldextract.extract(result).registered_domain
                if not domain: return False
                if not domain in direct: direct.append(domain)
                if result.endswith("."): result = result[:len(result) -2]
                if not domain in data[type]: data[type][domain] = {}
                if not result in data[type][domain]: data[type][domain][result] = []
                if match[0]: data[type][domain][result.replace(match[0],"")] = []
        return {"data":data,"direct":direct,"tagged":tagged,"ignore":ignore}

    def get(self,url,domain):
        for run in range(3):
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
                    if prefix:
                        continue
                    else:
                        return False,""
                if (request.status_code == 200):
                    if len(request.text) < 90:
                        print(f"HTML to short {len(request.text)}, dropping {request.url}")
                        continue
                    print(f"Got {request.status_code} keeping {request.url}")
                    return request.text,request.url
                else:
                    print(f"Got {request.status_code} dropping {request.url}")
                    if prefix:
                        continue
                    else:
                        return False,""
            except requests.ConnectionError:
                print(f"Retrying {prefix+url} got connection error")
            except Exception as e:
                print(f"Retrying {prefix+url} error {e}")
        return False,""