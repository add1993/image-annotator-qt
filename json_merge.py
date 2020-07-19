import os, sys
import json

files = ['set2_caption.txt', 'set2v1_darknet.txt']

dict1, dict2 = {}, {}
with open(files[0], 'r+') as json_file:
    dict1 = json.load(json_file)

with open(files[1], 'r+') as json_file:
    dict2 = json.load(json_file)

rdict = {}
rdict['name'] = 'combined_json'
rdict['samples'] = []

for i in range(len(dict1['samples'])):
    rdict['samples'].append(dict1['samples'][i])
    rdict['samples'][i]['instances'].extend(dict2['samples'][i]['instances'])

with open('set2_combined_json.json', 'w') as outfile:
    json.dump(rdict, outfile, indent=4)



