from requests_html import HTMLSession
import json, re, os

html = HTMLSession()
response = html.get('https://looking.house/points.php')
rows = response.html.find('tr > td > a')

results = {}
for index, row in enumerate(rows):
    if index % 2 == 0:
        provider = rows[index+1].text
        link = "looking.house" + list(row.links)[0]
        if not provider in results: results[provider] = {}
        ipv4s = re.findall("([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})",row.text, re.MULTILINE | re.DOTALL)
        if not link in results[provider]: results[provider][link] = {"ipv4":ipv4s[0]}

with open(os.getcwd()+'/data/looking.json', 'w') as f:
    json.dump(results, f, indent=4)

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

print(f"Saving everything.json")
with open(os.getcwd()+'/data/everything.json', 'w') as f:
    json.dump(list, f, indent=4)

with open(os.getcwd()+"/README.md", 'w') as f:
    f.write(readme)
