import os
import json

# path = "C:\\Data\\test\\KIbarDok\\Treptow"
path = "E:\\2_Köpenick"

ents = []

# for root, d_names, f_names in os.walk(path):
#     ents.append({ 'dir': root, 'files': f_names} )
# s= json.dumps(ents, indent = 4, ensure_ascii = False)
# print(s)
with open('C:\\Data\\test\\KIbarDok\\koepnick_files.json', 'w') as fp:
    for root, d_names, f_names in os.walk(path):
       r =  root.replace('\uf028','').replace('\uf022','').replace('\u0308','')
       fl = []
       for f in f_names:
           fl.append(f.replace('\uf025','').replace('\u0308',''))
       ents.append({ 'dir': r, 'files': fl} )
    json.dump(ents, fp, indent = 4, ensure_ascii = False)
