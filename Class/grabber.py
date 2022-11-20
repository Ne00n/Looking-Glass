from requests_html import HTML
import tldextract, os, re

class Grabber():

    lookingRegex = re.compile("([\w\d.-]+)?(lg|looking)([\w\d-]+)?(\.[\w\d-]+)(\.[\w\d.]+)")
    tags = ['datacenters','data-centers','datacenter','looking-glass','looking','lg','speedtest','icmp','ping']

    def findFiles(self,folders,folder):
        htmls = []
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
        if not html: return False
        parse = HTML(html=html)
        return parse.links

    def filterUrls(self,link,type="lg"):
        data,direct,tagged = {"lg":{},"scrap":{}},[],[]
        skip = ['/dashboard/message/','/plugin/thankfor/','entry/signin','/entry/register','/entry/signout','/profile/','/discussion/','lowendtalk.com','lowendbox.com','speedtest.net','youtube.com','geekbench.com','github.com','facebook.com','lafibre.info',
        'twitter.com','linkedin.com','smokeping?target=']
        onlyDirect = ['cart','order','billing','ovz','openvz','kvm','lxc','vps','server','virtual','cloud','compute','dedicated','ryzen']
        if link == "/": return False
        if any(tag in link for tag in skip): return False
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
                if domain == "": continue
                if not domain in direct: direct.append(domain)
                if domain == "": continue
                if result.endswith("."): result = result[:len(result) -2]
                if not domain in data[type]: data[type][domain] = {}
                if not result in data[type][domain]: data[type][domain][result] = []
                if match[0]: data[type][domain][result.replace(match[0],"")] = []
        return {"data":data,"direct":direct,"tagged":tagged}