# from typing import List, Dict
from pymongo.collection import Collection
from metadata.extractTopics import extractTopicsFromText, prepareWords, preparePattern, getVectors


def prepareList(vorhabeninv_col: Collection, pattern_col: Collection, badlist_col: Collection):
    # if "vorhaben_inv" in collist:
        # vorhabeninv_col = mydb["vorhaben_inv"]
    vorhabeninv: dict = vorhabeninv_col.find_one()
    wvi: dict[str, list[str]] = {}
    wvi = vorhabeninv["words"]
        # v: Dict[str,List[str]] = vorhabeninv["words"]
        # for wor in v:
        #     wvi[wor] = v[wor]

    words, wordlist = prepareWords(wvi)
    categories: list[str] = []
        # if "categories" in collist:
        #     cat_col = mydb["categories"]
        #     catobj = cat_col.find_one()
        #     for cat in catobj:
        #         if cat != '_id':
        #             categories.append(cat)

    patternjs: list[str] = []
        # if "pattern" in collist:
            # pattern_col = mydb["pattern"]
    pattern = pattern_col.find()
    for v in pattern:
        patternjs.append(v["paragraph"])
    plist: list[dict[str, str]] = preparePattern(patternjs)

    badlistjs: list[str] = []
        # if "badlist" in collist:
        #     badlist_col = mydb["badlist"]
    badlist = badlist_col.find()
    for v in badlist:
        badlistjs.append(v["paragraph"])

    return words, wordlist, categories, plist, badlistjs


def extractTopics(col: Collection, pattern_topic: str, pattern_place: str, pattern_place_alt: str,
                  wordcache: dict[str, dict[str, any]],
                  ontology: dict[str, list[str]],
                  categories: list[str],
                  pattern: list[str], badlist: list[str],
                  bparagraphs: bool):
    tlist: list[dict] = []
    all_matches: dict[str, dict] = {}
    no_matches: dict[str, int] = {}
    spacywords=getVectors(wordcache)

    # dlist = []
    # for doc in col.find():
    #     dlist.append(doc)
    i = 0
    dlist = []
    for doc in col.find():
        dlist.append(doc)

    for doc in dlist:
        i = i+1
        text = doc["text"]
        lt = len(text)
        if i > 0 and lt > 10:
            t: dict = extractTopicsFromText(doc["file"], pattern_topic, pattern_place, pattern_place_alt,
                                            spacywords, wordcache, ontology, categories, pattern, badlist, bparagraphs, text, all_matches, no_matches)
            if t != {}:
                print(i, " " ,doc["file"], t["keywords"])
                col.update_one({"_id": doc["_id"]}, {"$set": {"topic": t}})

                # tlist.append(t)

    return tlist, all_matches, no_matches


def extractintents(metadata: Collection, vorhabeninv_col: Collection, pattern_col: Collection, 
                   badlist_col: Collection, all_col: Collection,no_col: Collection):

    words, wordlist, categories, plist, badlistjs = prepareList(vorhabeninv_col, pattern_col, badlist_col)

    bparagraph = True

    # metadata = mydb["metadata"]
    res, all_matches, no_matches = extractTopics(
        metadata, "Vorhaben:", "Grundstück:", "Grundstücke:",
        words, wordlist, categories, plist, badlistjs, bparagraph)

    # topics_col = mydb["topics"]
    # topics_col.delete_many({})
    # topics_col.insert_many(res)

    # all_col = mydb["emblist"]
    all_col.delete_many({})
    all_col.insert_one(all_matches)

    # no_col = mydb["noemblist"]
    no_col.delete_many({})
    no_col.insert_one(no_matches)

    # with open('C:\\Data\\test\\topics4b.json', 'w', encoding='utf-8') as json_file:
    #             json.dump(res, json_file, indent=4, ensure_ascii=False)
    # with open('C:\\Data\\test\\all_matches.json', 'w', encoding='utf-8') as json_file:
    #             json.dump(all_matches, json_file, indent=4, ensure_ascii=False)
    # with open('C:\\Data\\test\\no_matches.json', 'w', encoding='utf-8') as json_file:
    #             json.dump(no_matches, json_file, indent=4, ensure_ascii=False)

    return res, all_matches, no_matches

