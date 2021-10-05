import requests
# from requests.api import request
import os
from pymongo.collection import Collection

def extract_text(file_path, tika_url):
    d = open(file_path, 'rb')
    r = requests.put(tika_url + "/tika", data=d)
    r.encoding = r.apparent_encoding
    result = r.text
    return result


def extract_meta(file_path, tika_url):
    file_name = str.split(file_path, '\\')[-1]
    response = requests.put(tika_url + "/meta", data=open(file_path,
                            'rb'),  headers={"Accept": "application/json"})
    try:
        result = response.json()
    except:
        result = {}
    result['file_name'] = file_name
    return result

def extractText(district: str, path: str, col: Collection, tika_url: str):
    i = 0
    # i = 100000
    m = 0
    col.delete_many({})
    for root, d_names, f_names in os.walk(path):
        for f in f_names:
            if not f.endswith(".xml"):
                i = i+1
                if i > 0:
                    ff = os.path.join(root, f)
                    ext = os.path.splitext(ff)[1]
                    
                    if ext != ".jpg" and ext != ".JPG" and ext != ".tif" and ext != ".wmf" and ext != ".gif":
                        txt = extract_text(ff, tika_url)
                    else:
                        continue
                        # txt = ""
                    print(i, " ", os.path.join(root, ff))
                    # met = extract_meta(ff, tika_url)
                    met = {}
                    try:
                        res = col.find_one_and_update({"file": f, "ext": ext, "path": root}, 
                            { "$set": {"meta": met, "text": txt, "district": district}})
                        if res == None:
                            # this is only needed if new documents are added:
                            # m = col.find().sort({"docid":-1}).limit(1)+1
                            m += 1
                            col.insert_one(
                                {"docid": m, "district": district, "file": f, "ext": ext, "path": root, "meta": met, "text": txt})
                    except:
                        print("TIKA Problem: ", ff)
                        pass
