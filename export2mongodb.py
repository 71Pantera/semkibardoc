# import spacy
import pymongo
import json
import os
# import requests

from pymongo.collection import Collection

import random
# from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

from metadata.extractText import extractText
from metadata.support import initSupport, initDocumentPattern
from metadata.extractAddress import findAddresses
from metadata.findMonuments import findMonuments, folderAddress
from metadata.findDocType import findDocType
from metadata.extractDates import findDates
from metadata.extractProject import findProject
from metadata.extractIntents import extractintents

# from tmtest import tm_test, tm_test2


load_dotenv()

# uri = "mongodb://localhost:27017"
# uri =  os.getenv("MONGO_CONNECTION_ATLAS")
# uri =  os.getenv("MONGO_CONNECTION_KLS")
uri =  os.getenv("MONGO_CONNECTION_AZURE")

myclient = pymongo.MongoClient(uri)
# myclient._topology_settings

mydb = myclient["kibardoc"]
collist = mydb.list_collection_names()


def color_generator(number_of_colors):
    color = ["#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
             for i in range(number_of_colors)]
    return color


def loadArrayCollection(filename: str, colname: str):
    col: Collection = mydb[colname]
    items: any = []
    with open(filename, encoding='utf-8') as f:
        items = json.loads(f.read())
    col.delete_many({})
    col.insert_many(items)


def loadDictCollection(filename: str, colname: str):
    col: Collection = mydb[colname]
    item: any = {}
    with open(filename, encoding='utf-8') as f:
        item = json.loads(f.read())
    col.delete_many({})
    col.insert_one(item)


def patchHida(filename: str, hidaname: str):
    with open(filename, encoding='utf-8') as f:
        hida0: dict = json.loads(f.read())
        monuments = []
        for hid in hida0:
            monument = hida0[hid]
            # if "K-Begründung" in monument:
            #     del monument["K-Begründung"]
            if "AdresseDict" in monument:
                adict = monument["AdresseDict"]
                keys = [x for x in adict]
                for str in keys:
                    if "." in str:
                        str2 = str.replace(".", "")
                        adict[str2] = adict[str]
                        del adict[str]
                        continue
            monuments.append(monument)
        hida_col = mydb[hidaname]
        hida_col.delete_many({})
        hida_col.insert_many(monuments)


def patchResolved(resolvedname: str, filename: str, hidaname: str):
    hida_col = mydb[hidaname]
    resolved_col = mydb[resolvedname]
    with open(filename, encoding='utf-8') as f:
        resolvedjs = json.loads(f.read())
        resolved = []
        for directory in resolvedjs:
            el = resolvedjs[directory]
            if "datei" in el:
                filesjs = el["datei"]
                for file in filesjs:
                    # print(directory, file)
                    obj = filesjs[file]
                    vorhaben = obj["vorhaben"]
                    if len(vorhaben) == 1:
                        if vorhaben[0] == "Errichtung einer Mega-Light-Werbeanlage":
                            vorhaben = []
                    vorgang = obj["vorgang"]
                    objnr = obj["objnr"]
                    hida = {}
                    if "method" in objnr:
                        meth = objnr["method"]
                        if len(meth) > 0:
                            for o in objnr:
                                if o != "method" and o != "behoerde" and o != "hausnummer":
                                    if meth == 'inhalt_direct' and o == "treffer":
                                        treflist = objnr["treffer"][meth]
                                        tref = treflist[0]
                                        hidaid = tref[0]
                                        hidaobj = hida_col.find_one(
                                            {"OBJ-Dok-Nr": hidaid})
                                        listentext = hidaobj["Listentext"]
                                        denkmalname = hidaobj["Denkmalname"]
                                        denkmalart = hidaobj["Denkmalart"]
                                        sachbegriff = hidaobj["Sachbegriff"]
                                        hida[hidaid] = {
                                            "hidaid": hidaid,
                                            "Listentext": listentext,
                                            "Denkmalart": denkmalart,
                                            "Denkmalname": denkmalname,
                                            "Sachbegriff": sachbegriff}
                                        #     if isinstance(hidaobjl, list):
                                        #         for hidaid in hidaobjl:
                                        #             hida[hidaid]= { "hidaid": hidaid, "treffer": objnr["treffer"]}
                                        #     else:
                                        #             hida[hidaid]= { "hidaid": hidaobjl, "treffer": objnr["treffer"]}
                                    else:
                                        denkmal = objnr[o]
                                        # print(denkmal)
                                        for hidaobj in denkmal["treffer"][meth]:
                                            hidaid = hidaobj[0]
                                            hidaobj = hida_col.find_one(
                                                {"OBJ-Dok-Nr": hidaid})
                                            listentext = hidaobj["Listentext"]
                                            denkmalname = hidaobj["Denkmalname"]
                                            denkmalart = hidaobj["Denkmalart"]
                                            sachbegriff = hidaobj["Sachbegriff"]
                                            hida[hidaid] = {
                                                "hidaid": hidaid,
                                                "Listentext": listentext,
                                                "Denkmalart": denkmalart,
                                                "Denkmalname": denkmalname,
                                                "Sachbegriff": sachbegriff}

                    resolved.append({"file": file, "dir": directory,
                                     "vorgang": vorgang,
                                     "vorhaben": vorhaben,
                                     "hida": hida,
                                     "obj": obj})
        resolved_col.delete_many({})
        resolved_col.insert_many(resolved)
        # print(resolved)


def projectMetaDataHida(metadataname: str, hidaname: str):
    hida_col = mydb[hidaname]
    metadata_col = mydb[metadataname]
    for doc in metadata_col.find():
        if "hidas" in doc:
            hida = {}
            sachbegriff = set([])
            denkmalart = set([])
            denkmalname = set([])
            for hidaid in doc["hidas"]:
                hidaobj = hida_col.find_one(
                    {"OBJ-Dok-Nr": hidaid})
                if not hidaobj:
                    hidaobj = hida_col.find_one(
                        {"Teil-Obj-Dok-Nr": hidaid})
                if "Denkmalname" in hidaobj:
                    s = hidaobj["Denkmalname"]
                    denkmalname.update(s)

                if "Denkmalart" in hidaobj:
                    s: str = hidaobj["Denkmalart"]
                    denkmalart.add(s)

                sachbegriffh = hidaobj["Sachbegriff"]
                sachbegriff.update(sachbegriffh)

                hida[hidaid] = hidaobj
            metadata_col.update_one(
                {"_id": doc["_id"]}, {
                    "$set": {
                        # "hida": hida,
                        "Sachbegriff": list(sachbegriff),
                        "Denkmalart": list(denkmalart),
                        "Denkmalname": list(denkmalname)}
                })
        else:
            # hida = {}
            sachbegriff = set([])
            denkmalart = set([])
            denkmalname = set([])
            metadata_col.update_one(
                {"_id": doc["_id"]}, {
                    "$set": {
                        # "hida": hida,
                        "Sachbegriff": list(sachbegriff),
                        "Denkmalart": list(denkmalart),
                        "Denkmalname": list(denkmalname)}
                })


def setMetaDataDistrict(metadataname: str, district: str):
    metadata_col = mydb[metadataname]
    for doc in metadata_col.find():
        if not "district" in doc:
            metadata_col.update_one(
                {"_id": doc["_id"]}, {
                    "$set": {"district": district}
                })


def patchDir(resolvedname: str, folders: str, path: str):
    folders_col = mydb[folders]
    resolved_col = mydb[resolvedname]
    for folder in folders_col.find():
        for file in folder["files"]:
            dir = folder["dir"]
            dir = dir.replace(path, "")
            f = file
            if f.endswith(".doc"):
                f = f.replace(".doc", ".docx")
            if f.endswith(".docx"):
                print(dir, f)
                resolved_col.update_many(
                    {"file": f}, {"$set": {"dir": dir}})


def patchKeywords(resolvedname: str, topicsname: str):
    topics_col = mydb[topicsname]
    resolved_col = mydb[resolvedname]
    for topic in topics_col.find():
        # print(topic["file"])
        hidas = []
        sachbegriff = []
        denkmalart = []
        denkmalname = []
        if "hida" in topic:
            for hida0 in topic["hida"]:
                hidas.append(hida0)
                # ????? weder hidas noch die attributaggregation wird weiter verwendet....
                sachbegriff += hida0["Sachbegriff"]
                denkmalart += hida0["Denkmalart"]
                denkmalname += hida0["Denkmalname"]

        for theme in topic["keywords"]:
            resolved_col.update_many(
                {"file": topic["file"]}, {"$set": {
                    theme: topic["keywords"][theme]
                }})
        # resolved_col.update_many(
        #     {"file": topic["file"]}, {"$set": {
        #         "html": topic["html"]
        #     }})


def projectMetaDataKeywords(metadataname: str):
    col = mydb[metadataname]
    for doc in col.find():
        if "topic" in doc:
            topic = doc["topic"]
            for theme in topic["keywords"]:
                col.update_many(
                    {"_id": doc["_id"]}, {"$set": {
                        theme: topic["keywords"][theme]
                    }})
        # resolved_col.update_many(
        #     {"file": topic["file"]}, {"$set": {
        #         "html": topic["html"]
        #     }})


def updateID(metadataname: str):
    col = mydb[metadataname]
    i = 0
    for doc in col.find():
        i += 1
        col.update_many(
            {"_id": doc["_id"]}, {"$set": {
                "docid": i
            }})


def unprojectMetaDataKeywords(metadataname: str):
    col = mydb[metadataname]
    for doc in col.find():
        if "topic" in doc:
            topic = doc["topic"]
            for theme in topic["keywords"]:
                col.update_one({"_id": doc["_id"]}, {"$unset": {theme: None}})


def patchText(resolvedname: str, textname: str):
    text_col = mydb[textname]
    resolved_col = mydb[resolvedname]
    for text in text_col.find():
        f = text["file"]
        t = text["text"]
        t = t.replace('\n', ' ')
        t = t.replace('\u2002', ' ')
        print(text["file"])
        resolved_col.update_many(
            {"file": f}, {"$set": {
                "text": t
            }})


def projectHida(resolvedname: str):
    resolved_col = mydb[resolvedname]
    for reso0 in resolved_col.find():
        print(reso0["file"])
        hidas = []
        sachbegriff = []
        denkmalart = []
        denkmalname = []
        if "hida" in reso0:
            for hida0 in reso0["hida"]:
                hidas.append(hida0)
                if reso0["hida"][hida0]["Sachbegriff"]:
                    sachbegriff += reso0["hida"][hida0]["Sachbegriff"]
                if reso0["hida"][hida0]["Denkmalart"]:
                    denkmalart.append(reso0["hida"][hida0]["Denkmalart"])
                if reso0["hida"][hida0]["Denkmalname"]:
                    denkmalname += reso0["hida"][hida0]["Denkmalname"]
            resolved_col.update_one(
                {"file": reso0["file"]}, {
                    "$set": {"hidas": hidas, "Sachbegriff": list(set(sachbegriff)),
                             "Denkmalart": list(set(denkmalart)),
                             "Denkmalname": list(set(denkmalname))}
                })


def patchVorhaben(resolvedname: str):
    resolved_col = mydb[resolvedname]
    for reso1 in resolved_col.find():
        if "vorhaben" in reso1 and len(reso1["vorhaben"]) == 1 and reso1["vorhaben"][0] == 'Errichtung einer Mega-Light-Werbeanlage':
            print(reso1["file"])
            resolved_col.update_one(
                {"file": reso1["file"]}, {
                    "$set": {"vorhaben": []}
                })


def patchCategories(words: str, categoriesname: str):
    categories = []
    if words in collist:
        vorhabeninv_col = mydb[words]
        vorhabeninv = vorhabeninv_col.find()
        for v in vorhabeninv:
            for wor in v["words"]:
                if len(v["words"][wor]) == 0:
                    categories.append(wor)
    catcolors = {}
    color = color_generator(len(categories))
    for i in range(len(categories)):
        catcolors[categories[i]] = {
            "color": color[i], "label": categories[i].upper()}

    cat_col = mydb[categoriesname]
    cat_col.delete_many({})
    cat_col.insert_one(catcolors)


def loadEmbddings(filename: str, colname: str):
    col: Collection = mydb[colname]
    items: any = []
    with open(filename, encoding='utf-8') as f:
        mlist = json.loads(f.read())
        for m in mlist:
            items.append({"word": m, "match": mlist[m], "correct": True})
    col.delete_many({})
    col.insert_many(items)


def loadNoMatches(filename: str, colname: str):
    col: Collection = mydb[colname]
    items: any = []
    with open(filename, encoding='utf-8') as f:
        mlist = json.loads(f.read())
        for m in mlist:
            items.append({"word": m, "count": mlist[m]})
    col.delete_many({})
    col.insert_many(items)


def patchInvTaxo(resolvedname: str, invtaxo: str):
    resolved_col = mydb[resolvedname]
    resol = resolved_col.find()
    for reso2 in resol:
        invtaxo_col = mydb[invtaxo]
        sblist = []
        if "Sachbegriff" in reso2:
            sblist = reso2["Sachbegriff"]
        if len(sblist) > 0:
            sl = sblist
            for sb in sblist:
                for plist in invtaxo_col.find({"name": sb}):
                    for pa in plist["parents"]:
                        if pa != "ARCHITEKTUR" and pa != "FUNKTION" and pa != "BAUAUFGABE" and not pa in sl:
                            sl.append(pa)
            resolved_col.update_one({"_id": reso2["_id"]}, {
                                    "$set": {"Sachbegriff": sl}})


def projectHidaInvTaxo(hidaname: str, invtaxo: str):
    hida_col = mydb[hidaname]
    invtaxo_col = mydb[invtaxo]
    hidal = hida_col.find()
    for hida in hidal:
        invtaxo_col = mydb["invtaxo"]
        sblist = hida["Sachbegriff"]
        if len(sblist) > 0:
            sl = sblist
            for sb in sblist:
                for plist in invtaxo_col.find({"name": sb}):
                    for pa in plist["parents"]:
                        if pa != "ARCHITEKTUR" and pa != "FUNKTION" and pa != "BAUAUFGABE" and not pa in sl:
                            sl.append(pa)
            hida_col.update_one({"_id": hida["_id"]}, {
                                "$set": {"Sachbegriff": sl}})


def mongoExport(metadataname="metadata", hidaname="hida",
                ispattern=False, ishida=False, isresolved=False,
                ismetadatahida=False,
                isfolders=False, isbadlist=False,
                isvorhaben=False, isvorhabeninv=False,
                istaxo=False, istopics=False,
                ispatch_dir=False, iskeywords=False,
                ismetadatakeywords=False,
                ismetadatanokeywords=False,
                isupdatehida=False, isupdatevorhaben=False,
                istext=False, isupdatetext=False,
                iscategories=False,
                isemblist=False, isnoemblist=False,
                isinvtaxo=False, isupdatetaxo=False,
                isupdatehidataxo=False):

    # metadata = mydb[metadataname]

    # hida = mydb[hidaname]

    if ispattern:
        loadArrayCollection(r".\static\pattern.json", "pattern")

    if ishida:
        patchHida(r".\static\hida.json", hidaname)

    if isresolved:
        patchResolved(metadataname, "resolved.json", hidaname)

    if ismetadatahida:
        projectMetaDataHida(metadataname, hidaname)

    if isfolders:
        loadArrayCollection("files.json", "folders")
        loadArrayCollection("koepnick_files.json", "koepnick_folders")
        # loadArrayCollection("files.json", "folders")

    if isbadlist:
        loadArrayCollection(r".\static\badlist.json", "badlist")

    if isvorhaben:
        loadArrayCollection(r".\static\vorhaben.json", "vorhaben")

    if isvorhabeninv:
        loadDictCollection(r".\static\vorhaben_inv.json", "vorhaben_inv")

    if istaxo:
        loadArrayCollection(r".\static\taxo.json", "taxo")

    if istopics:
        loadArrayCollection("topics3a.json", "topics")

    if ispatch_dir or isresolved:
        patchDir(metadataname, "folders", r"C:\Data\test\KIbarDok")

    if isresolved or istopics or iskeywords:
        patchKeywords(metadataname, "topics")

    if ismetadatakeywords:
        projectMetaDataKeywords(metadataname)

    if ismetadatanokeywords:
        unprojectMetaDataKeywords(metadataname)
    # if istext:
    #     loadArrayCollection(r"..\static\text3.json", "text")

    # if isresolved or isupdatetext:
    #     patchText("resolved", "text")

    if isresolved or isupdatehida:
        projectHida(metadataname)

    if isresolved or isupdatevorhaben:
        patchVorhaben(metadataname)

    if iscategories or isvorhabeninv:
        patchCategories(r".\static\vorhaben_inv", "categories")

    if isemblist:
        loadEmbddings(r".\static\all_matches.json", "emblist")

    if isnoemblist:
        loadNoMatches(r".\static\no_matches.json", "noemblist")

    if isinvtaxo:
        loadArrayCollection(r".\static\taxo_inv.json", "invtaxo")

    if isresolved or isupdatetaxo or ismetadatahida:
        patchInvTaxo(metadataname, "invtaxo")

    if ishida or isupdatehidataxo:
        projectHidaInvTaxo(hidaname, "invtaxo")

# mongoExport(ispattern=True,ishida=True,isresolved=True,isfolders=True,isbadlist=True,isvorhaben=True,
        #    isvorhabeninv=True, istaxo=True,istopics=True, ispatch_dir=True, iskeywords=True)
# mongoExport(iskeywords=True)
# mongoExport(isresolved=True)
# mongoExport(istext=True)
# mongoExport(isupdatetext=True)
# mongoExport(istopics=True)
# mongoExport(isfolders=True)
# mongoExport(isfolders=True,isbadlist=True,iscategories=True,isvorhaben=True)
# mongoExport(isupdatevorhaben=True)
# mongoExport(isvorhabeninv=True)
# mongoExport(isemblist=True)
# mongoExport(isnoemblist=True)
# mongoExport(isinvtaxo=True)
# mongoExport(isupdatetaxo=True)
# mongoExport(isupdatehidataxo=True)
# mongoExport(iscategories=True)
# mongoExport(ispatch_dir=True)
# mongoExport(ismetadatakeywords=True)

# def lookupAddress(district: str, path: str):
#     r = requests.get("http://www.google.de/maps/place/" + "Berlin Treptow " + path, allow_redirects=True)
#     print(r.url)

# lookupAddress("Berlin Treptow", "moosdorfstrasse  7-9")


def extractMetaData(name: str, metadataname: str, district: str, path: str, folders: str, tika: str):
    istaxo = (not "taxo" in collist)
    isinvtaxo = (not "invtaxo" in collist)
    isvorhaben = (not "vorhaben" in collist)
    isvorhaben_inv = (not "vorhaben_inv" in collist)
    ispattern = (not "pattern" in collist)
    isbadlist = (not "badlist" in collist)
    mongoExport(
        istaxo=istaxo,
        isinvtaxo=isinvtaxo,
        isbadlist=isbadlist,
        isvorhaben=isvorhaben,
        isvorhabeninv=isvorhaben_inv,
        ispattern=ispattern)

    if not "hida" in collist:
        mongoExport(ishida=True)
        mongoExport(isupdatehidataxo=True)
    hida = mydb["hida"]
    support = mydb["support"]

    metadata = mydb[metadataname]
    extractText(name, path, metadata, tika)
    initSupport(support, hida, district)

    findAddresses(metadata, support, "de")
    folders = mydb[folders]
    folderAddress(folders, hida, path, support, "de", district)
    findMonuments(metadata, hida, support, folders, "de", district)
    mongoExport(metadataname=metadataname, ismetadatahida=True)

    doctypes = mydb["doctypes"]
    initDocumentPattern(doctypes)
    findDocType(metadata, doctypes)
    findDates(metadata)
    findProject(metadata)

    vorhabeninv_col = mydb["vorhaben_inv"]
    pattern_col = mydb["pattern"]
    badlist_col = mydb["badlist"]
    all_col = mydb["emblist"]
    no_col = mydb["noemblist"]
    extractintents(metadata, vorhabeninv_col, pattern_col,
                   badlist_col, all_col, no_col)
    mongoExport(metadataname=metadataname, ismetadatakeywords=True)


# extractMetaData("Lichtenberg", "lichtenberg", "Lichtenberg",
#                 "E:\\Lichtenberg\\Dokumentationen",
#                 "lichtenberg_folders", "http://localhost:9998")
extractMetaData("Treptow", "treptow", "Treptow-Köpenick",
                "C:\\Data\\test\\KIbarDok\\Treptow\\1_Treptow",
                "folders", "http://localhost:9998")
# extractMetaData("Köpenick", "koepenick", "Treptow-Köpenick",
#                "E:\\2_Köpenick", 
#                 "koepnick_folders", "http://localhost:9998")

# updateID("metadata2")
# setMetaDataDistrict("treptow","Treptow-Köpenick")
# mongoExport(ismetadatanokeywords=True)
