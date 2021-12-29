import subprocess, pyasn, json, sys, os

sys.path.append(os.getcwd().replace("/tools",""))
from Class.base import Base

print("Loading asn")
reader = pyasn.pyasn(os.getcwd()+'/asn.dat')

targets = {"OneProvider.com":136258,"Online.net":12876}

def cmd(command):
    p = subprocess.run(f"{command}", stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return p.stdout.decode('utf-8')

def findPingable(subnet):
    ip = subnet.split('/')[0].split(".")[:3]
    ip = ".".join(ip)
    for run in range(1,15):
        dest = f"{ip}.{run}"
        resp = cmd(f"fping {dest}")
        if "is alive" in resp: return dest

results = {}
for provider,asn in targets.items():
    subnets = reader.get_as_prefixes(asn)
    for subnet in subnets:
        print(f"Looking up {subnet}")
        ip = findPingable(subnet)
        if not provider in results: results[provider] = {}
        if not provider in results[provider]: results[provider][provider] = {"ipv4":[],"ipv6":[]}
        results[provider][provider]["ipv4"].append(ip)
    
with open(os.getcwd()+'/data/asn.json', 'w') as f:
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