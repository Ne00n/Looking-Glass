import geoip2.database
import unicodedata
import ipaddress, json, os

class Base():

    def __init__(self):
        if os.path.exists(os.getcwd()+"/GeoLite2-City.mmdb"):
            print("Loading GeoLite2-City.mmdb")
            self.reader = geoip2.database.Reader(os.getcwd()+"/GeoLite2-City.mmdb")
        else:
            print("Could not find GeoLite2-City.mmdb")

    def merge(self):
        ignore = ["8.8.8.8","198.251.86.22","1.1.1.1","4.2.2.2"]
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
                        if not url in list[domain]: list[domain][url] = {"ipv4":{},"ipv6":{}}
                        if ips:
                            for ip in ips['ipv4']:
                                try:
                                    tmp = ipaddress.ip_address(ip)
                                except:
                                    print(f'Dropping {ip}')
                                    continue
                                if ip in once[domain]: continue
                                if ip in ignore: continue
                                geo = self.geo(ip)
                                if not ip in list[domain][url]['ipv4']: list[domain][url]['ipv4'][ip] = geo
                                once[domain].append(ip)
                                list[domain][url]['ipv4'] = {k: list[domain][url]['ipv4'][k] for k in sorted(list[domain][url]['ipv4'])}
                                list[domain] = {k: list[domain][k] for k in sorted(list[domain])}
                            for ip in ips['ipv6']:
                                if ip in once[domain]: continue
                                if ip in ignore: continue
                                geo = self.geo(ip)
                                if not ip in list[domain][url]['ipv6']: list[domain][url]['ipv6'][ip] = geo
                                once[domain].append(ip)
                            if not list[domain][url]['ipv4'] and not list[domain][url]['ipv6']:
                                del list[domain][url]
        return list

    def geo(self,ip):
        geo = "n/a"
        try:
            response = self.reader.city(ip)
            geo = f"{response.city.name}, {response.country.name}" if response.city.name else response.country.name
            geo = unicodedata.normalize('NFKD', geo).encode('ASCII', 'ignore').decode("utf-8") 
        except Exception as e:
            print(f"Skipping geo lookup on {ip}")
        return geo

    def readme(self,list):
        readme = "# Looking-Glass\n"
        for element,urls in list.items():
            if len(urls) > 0:
                readme += "### "+element+"\n"
                for url in urls:
                    readme += "* ["+url+"](http://"+url+")\n"
        return readme
