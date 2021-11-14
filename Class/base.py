import json, os

class Base():

    def merge():
        ignore = ["8.8.8.8"]
        list,once = {},{}
        files = os.listdir(os.getcwd()+"/data/")
        for file in files:
            if file.endswith(".json") and not "everything" in file:
                with open(os.getcwd()+"/data/"+file) as handle:
                    file = json.loads(handle.read())
                for domain,details in file.items():
                    if not domain in list: list[domain] = {}
                    if not domain in once: once[domain] = []
                    for url,ips in details.items():
                        if not url in list[domain]: list[domain][url] = {"ipv4":[],"ipv6":[]}
                        if ips:
                            for ip in ips['ipv4']:
                                if ip in once[domain]: continue
                                if ip in ignore: continue
                                if not ip in list[domain][url]['ipv4']: list[domain][url]['ipv4'].append(ip)
                                once[domain].append(ip)
                            for ip in ips['ipv6']:
                                if ip in once[domain]: continue
                                if ip in ignore: continue
                                if not ip in list[domain][url]['ipv6']: list[domain][url]['ipv6'].append(ip)
                                once[domain].append(ip)
                            if not list[domain][url]['ipv4'] and not list[domain][url]['ipv6']:
                                del list[domain][url]
        return list

    def readme(list):
        readme = "# Looking-Glass\n"
        for element,urls in list.items():
            if len(urls) > 0:
                readme += "### "+element+"\n"
                for url in urls:
                    readme += "* ["+url+"](http://"+url+")\n"
        return readme
