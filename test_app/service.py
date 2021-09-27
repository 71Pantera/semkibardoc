import os
from typing import Dict
from flask import Flask, json, Response, request, render_template, url_for, flash, redirect, jsonify
from flask.globals import session
from flask_cors import CORS
import pymongo

import numpy as np
import pandas as pd
from io import BytesIO
from flask import send_file

import datetime
from werkzeug.exceptions import abort
from bson.objectid import ObjectId

from markupsafe import Markup
from typing import Dict, Any, List
from dotenv import load_dotenv
import hashlib

from intent import extractTopicsAndPlaces, prepareWords, preparePattern, displacyText, spacytest

#  https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3
myapp = Flask(__name__, static_folder='client')
myapp.config['SECRET_KEY'] = 'your secret key'
CORS(myapp)

load_dotenv()
uri = os.getenv("MONGO_CONNECTION")
lib = os.getenv("DOCUMENT_URL")
tab = os.getenv("DOCUMENT_TABLE")
if uri == None:
    uri = "mongodb+srv://semtation:SemTalk3!@cluster0.pumvg.mongodb.net/kibardoc?retryWrites=true&w=majority"

# uri = "mongodb+srv://semtation:SemTalk3!@cluster0.pumvg.mongodb.net/kibardoc?retryWrites=true&w=majority"
uri = "mongodb://localhost:27017"

myclient = pymongo.MongoClient(uri,
                               maxPoolSize=50,
                               unicode_decode_error_handler='ignore')

mydb = myclient["kibardoc"]
collist = mydb.list_collection_names()

# metadatatable = "resolved"
metadatatable = "metadata"
if tab:
    metadatatable = tab


sha256 = hashlib.sha256()
sha256.update(str('123').encode("utf-8"))
hashPass = sha256.hexdigest()
usertable = "user"
usercol = mydb[usertable]
user = usercol.find_one({'username': "knowlogy"})
if user == None:
    usercol.insert_one({'username': "knowlogy", "password": hashPass})


@myapp.route("/createuser", methods=('GET', 'POST'))
def createuser(username: str, password: str):
    if 'username' in session:
        if request.method == 'POST':
            sha256 = hashlib.sha256()
            sha256.update(str(password).encode("utf-8"))
            hashPass = sha256.hexdigest()
            usertable = "user"
            usercol = mydb[usertable]
            user = usercol.find_one({'username': username})
            if user == None:
                usercol.insert_one(
                    {'username': "knowlogy", "password": hashPass})


@myapp.route("/services")
def index():
    return render_template('services.html')
    # return "Hello Flask, This is the KiBarDok Service. Try hida, intents, words, badlist, paragraph"

# Statics


@myapp.route('/')
def root():
    if 'username' in session:
        # s = ""
        # for arg in request.args:
        #     s = s + arg + "=" + request.args[arg] + "&"
        # if len(s) > 0:
        #     return myapp.send_static_file('index.html' + "?" + s[:len(s)])
        # else:
        return myapp.send_static_file('index.html')
    else:
        return redirect(url_for('login'))


@myapp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        uname = request.form["username"]
        password = request.form["password"]
        sha256 = hashlib.sha256()
        sha256.update(str(password).encode("utf-8"))
        hashPass = sha256.hexdigest()
        user = usercol.find_one({'username': uname, "password": hashPass})
        if user != None:
            session['username'] = uname
        return redirect(url_for('root'))

    return render_template('login.html')
    # return myapp.send_static_file('login.html')


@myapp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))
    # return myapp.send_static_file('login.html')


@myapp.route('/hidafacet')
def hidafacet():
    if user == None:
        return redirect(url_for('login'))
    return myapp.send_static_file('hida.html')


@myapp.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return myapp.send_static_file(path)


_allcategories: List[str] = []
_colors: Dict[str, str] = {}


def allcategories_and_colors():
    global _allcategories
    if _allcategories != []:
        return _allcategories, _colors
    vi: List[str] = []
    cat_col = mydb["categories"]
    catobj: Dict[str, Dict[str, str]] = cat_col.find_one()
    for cat in catobj:
        if cat != '_id':
            vi.append(cat)
            caobj = catobj[cat]
            _colors[caobj["label"]] = caobj["color"]

    # if "vorhaben_inv" in collist:
    #     vorhabeninv_col = mydb["vorhaben_inv"]
    #     vorhabeninv = vorhabeninv_col.find()
    #     for v in vorhabeninv:
    #         for wor in v["words"]:
    #             if len(v["words"][wor]) == 0:
    #                 vi.append(wor)

    _allcategories = vi
    return vi, _colors


@ myapp.route("/categories")
def categories():
    vi, col = allcategories_and_colors()
    json_string = json.dumps(vi, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@myapp.route("/documents")
def documents():
    if user == None:
        return redirect(url_for('login'))
    # print(request.args)
    query = request.args
    vi = []
    if metadatatable in collist:
        col = mydb[metadatatable]
        resolved = col.find(query)
        for v in resolved:
            v1 = {}
            # for a in v:
            #     if a != "_id" and a != "obj":
            #         v1[a] = v[a]
            # vi.append(v1)
            if "topic" in v:
                item: Dict = v["topic"]
                if item != None:
                    vi.append(item)
    json_string = json.dumps(vi, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route('/document/<docid>/edit', methods=('GET', 'POST'))
def editdocument(docid):
    if user == None:
        return redirect(url_for('login'))
    item = get_document(metadatatable, docid)
    if request.method == 'POST':
        qs = {}
        qs["qscomment"] = request.form['qscomment']
        qs["qsrelation"] = request.form["qsrelation"]
        qs["qsdoctype"] = request.form["qsdoctype"]
        if "qsobjnrInvalid" in request.form:
            qs["qsobjnrInvalid"] = True
        else:
            qs["qsobjnrInvalid"] = False
        qs["qsobjnummer"] = request.form["qsobjnummer"]
        qs["qsvorhaben"] = request.form["qsvorhaben"]
        qs["qscomment"] = request.form["qscomment"]
        col = mydb[metadatatable]
        col.update_one(
            {'docid': int(docid)}, {'$set': {'qs': qs}})
        return redirect(url_for('showdocument', docid=docid))
    else:
        comment = ""
        if "comment" in item:
            comment = item["comment"]
        vorhaben = ""
        if "vorhaben" in item:
            vorhaben = item["vorhaben"]
        p = item["path"].replace("C:\\Data\\test\\KIbarDok\\Treptow\\", "")
        p = p.replace("\\", "/")
        pdfurl = lib + p + "/" + item["file"]

        qs = {"docid": item["docid"],
              "qsdoctype": item["doctype"],
              "qsobjnrInvalid": False,
              "qsobjnummer": "",
              "qsvorhaben": vorhaben,
              "qscomment": comment
              }
        if "qs" in item:
            qs = item["qs"]
        qs["file"] = item["file"]
        qs["pdfurl"] = pdfurl
        do_monument = True
        if "qs" in item:
            if "qsrelation" in item["qs"] and not item["qs"]["qsrelation"] == "Denkmalschutz":
                do_monument = False

        qs["qsmonumentchecked"] = 'checked' if do_monument else ''
        qs["qsdistancechecked"] = '' if do_monument else 'checked'
        return render_template('edit_document.html', **qs) # , debug=myapp.debug


@myapp.route("/showdocuments")
def showdocuments():
    if user == None:
        return redirect(url_for('login'))
    vi = []
    if metadatatable in collist:
        col = mydb[metadatatable]
        query = request.args
        metadata = col.find(query)
        for v in metadata:
            v1 = {}
            v1["docid"] = v["docid"]
            v1["file"] = v["file"]
            v1["path"] = v["path"]
            if not "comment" in v:
                v1["comment"] = ""
            else:
                v1["comment"] = v["comment"]
            if "doctype" in v:
                v1["doctype"] = v["doctype"]
            else:
                v1["doctype"] = ""

            if "hida" in v:
                v1["hida"] = v["hida"]
            else:
                v1["hida"] = []

            if "vorhaben" in v:
                v1["vorhaben"] = v["vorhaben"]
            else:
                v1["vorhaben"] = []
            vi.append(v1)
    return render_template('show_documents.html', documents=vi)


@myapp.route("/showdocument")
def showdocument():
    if user == None:
        return redirect(url_for('login'))
    if metadatatable in collist:

        catlist, colors = allcategories_and_colors()
        options = {"ents": catlist, "colors": colors}
        res_col = mydb[metadatatable]
        # list_col = mydb["topics"]
        query = request.args
        query1 = query.copy()
        query1["docid"] = int(query1["docid"])
        metadata = res_col.find(query1)
        for v in metadata:
            # item: Dict = list_col.find_one({"file": v["file"]})
            if not "comment" in v:
                v["comment"] = ""
            paragraphs: List[Dict] = []
            kw = {}
            if "topic" in v:
                item: Dict = v["topic"]
                if item != None:
                    for i in item["intents"]:
                        pt: str = i["paragraph"]
                        ents: List[Any] = i["entities"]
                        html: Markup = displacyText(pt, ents, options)
                        paragraphs.append({"html": html})
                for c in catlist:
                    if c in v:
                        kw[c] = v[c]
            v["keywords"] = kw
            return render_template('show_document.html', res=v, paragraphs=paragraphs)


@myapp.route("/hida")
def allhida():
    # print(request.args)
    query = request.args
    vi = []
    if "hida" in collist:
        hida_col = mydb["hida"]
        hida = hida_col.find(query)
        for v in hida:
            v1 = {}
            if 'OBJ-Dok-Nr' in v:
                v1['OBJ-Dok-Nr'] = v['OBJ-Dok-Nr']
            if 'Teil-Obj-Dok-Nr' in v:
                v1['Teil-Obj-Dok-Nr'] = v['Teil-Obj-Dok-Nr']
            # for a in v:
            #     if a != "_id":
            #         v1[a]=v[a]
            # vi.append(v1)

            # mname=""
            if 'Listentext' in v:
                v1['Listentext'] = v['Listentext']
            if 'Denkmalname' in v:
                v1['Denkmalname'] = v['Denkmalname']
            if 'Sachbegriff' in v:
                v1['Sachbegriff'] = v['Sachbegriff']
            if 'Denkmalart' in v:
                v1['Denkmalart'] = v['Denkmalart']

            # elif 'Denkmalname' in v:
            #     mname= v['Denkmalname']
            # sb = []
            # if 'Sachbegriff' in v:
            #     sb= v['Sachbegriff']
            # if 'OBJ-Dok-Nr' in v:
            #     vi.append({ 'OBJ-Dok-Nr': v['OBJ-Dok-Nr'], 'Listentext': mname, 'Sachbegriff':sb})
            if 'OBJ-Dok-Nr' in v1:
                vi.append(v1)
            else:
                print(v)

    json_string = json.dumps(vi, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route("/hida/<id>")
def hida(id=""):
    collist = mydb.list_collection_names()
    vi = {}
    if "hida" in collist:
        hida_col = mydb["hida"]
        hida = hida_col.find({'OBJ-Dok-Nr': id})
        # if hida.retrieved == 0:
        #     hida = hida_col.find({'Teil-Obj-Dok-Nr': id})
        for v in hida:
            response = Response(
                str(v), content_type="application/json; charset=utf-8")
            return response
        hida = hida_col.find({'Teil-Obj-Dok-Nr': id})
        for v in hida:
            response = Response(
                str(v), content_type="application/json; charset=utf-8")
            return response
    json_string = json.dumps(vi, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route("/showhida/<id>")
def showhida(id=""):
    collist = mydb.list_collection_names()
    if "hida" in collist:
        hida_col = mydb["hida"]
        hida = hida_col.find({'OBJ-Dok-Nr': id})
        # if hida.retrieved == 0:
        #     hida = hida_col.find({'Teil-Obj-Dok-Nr': id})
        res = {}
        for v in hida:
            for at in v:
                if at != "_id" and at != "Objekt-Type":
                    va = v[at]
                    if isinstance(va, list):
                        va = ', '.join(va)
                    res[at] = va
            return render_template('show_monument.html', res=res, title="Denkmal")
        hida = hida_col.find({'Teil-Obj-Dok-Nr': id})
        for v in hida:
            for at in v:
                if at != "_id" and at != "Objekt-Type":
                    va = v[at]
                    if isinstance(va, list):
                        va = ', '.join(va)
                    res[at] = va
            return render_template('show_monument.html', res=res, title="Denkmal")


@ myapp.route("/monuments")
def monuments():
    vi = []
    if "hida" in collist:
        hida_col = mydb["hida"]
        query = request.args
        hida = hida_col.find(query)
        for v in hida:
            mname = ""
            if 'Listentext' in v:
                mname = v['Listentext']
            elif 'Denkmalname' in v:
                mname = v['Denkmalname']
            sb = []
            if 'Sachbegriff' in v:
                sb = v['Sachbegriff']
            if 'OBJ-Dok-Nr' in v:
                vi.append(
                    {'OBJ-Dok-Nr': v['OBJ-Dok-Nr'], 'Listentext': mname, 'Sachbegriff': sb})
    return render_template('show_monuments.html', monuments=vi)


@ myapp.route("/taxo")
def alltaxo():
    query = request.args
    collist = mydb.list_collection_names()
    vi = []
    if "taxo" in collist:
        taxo_col = mydb["taxo"]
        taxo = taxo_col.find(query)
        for v in taxo:
            v1 = {}
            for a in v:
                if a != "_id":
                    v1[a] = v[a]
            vi.append(v1)

    json_string = json.dumps(vi, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route("/showtaxo")
def showtaxo():
    query = request.args
    vi = []
    if "taxo" in collist:
        taxo_col = mydb["taxo"]
        taxo = taxo_col.find(query)
        for v in taxo:
            vi.append(v)
    return render_template('show_taxo.html', taxo=vi, title="Sachbegriffe")


@ myapp.route("/intents")
def allintents():
    if user == None:
        return redirect(url_for('login'))
    collist = mydb.list_collection_names()
    vi = {}
    if "vorhaben_inv" in collist:
        vorhabeninv_col = mydb["vorhaben_inv"]
        vorhabeninv = vorhabeninv_col.find()
        for v in vorhabeninv:
            for intent in v["intents"]:
                vi[intent] = v["intents"][intent]
    json_string = json.dumps(vi, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route("/intents/<intent>")
def intents(intent=""):
    if user == None:
        return redirect(url_for('login'))
    # uri = os.getenv("MONGO_CONNECTION")
    # myclient = pymongo.MongoClient(uri)
    # mydb = myclient["kibardoc"]
    # collist = mydb.list_collection_names()
    vi = {}
    if "vorhaben_inv" in collist:
        vorhabeninv_col = mydb["vorhaben_inv"]
        vorhabeninv = vorhabeninv_col.find()
        for v in vorhabeninv:
            if intent:
                if intent in v["intents"]:
                    vi = v["intents"][intent]
    json_string = json.dumps(vi, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route("/showintents")
def showintents():
    if user == None:
        return redirect(url_for('login'))
    vi = {}
    if "vorhaben_inv" in collist:
        vorhabeninv_col = mydb["vorhaben_inv"]
        vorhabeninv = vorhabeninv_col.find()
        for v in vorhabeninv:
            for intent in sorted(v["intents"]):
                vi[intent] = v["intents"][intent]
    return render_template('show_listdict.html', listdict=vi, title="Unterklassen")


@ myapp.route("/words")
def allwords():
    if user == None:
        return redirect(url_for('login'))
    query = request.args
    vi = {}
    if "vorhaben_inv" in collist:
        vorhabeninv_col = mydb["vorhaben_inv"]
        vorhabeninv = vorhabeninv_col.find(query)
        for v in vorhabeninv:
            for wor in v["words"]:
                vi[wor] = v["words"][wor]
    json_string = json.dumps(vi, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route("/words/<word>")
def words(word=""):
    if user == None:
        return redirect(url_for('login'))
    collist = mydb.list_collection_names()
    vi = {}
    query = request.args
    if "vorhaben_inv" in collist:
        vorhabeninv_col = mydb["vorhaben_inv"]
        vorhabeninv = vorhabeninv_col.find(query)
        for v in vorhabeninv:
            if word:
                if word in v["words"]:
                    vi = v["words"][word]
    json_string = json.dumps(vi, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route("/showwords")
def showwords():
    if user == None:
        return redirect(url_for('login'))
    vi = {}
    if "vorhaben_inv" in collist:
        vorhabeninv_col = mydb["vorhaben_inv"]
        vorhabeninv = vorhabeninv_col.find()
        for v in vorhabeninv:
            for wor in sorted(v["words"]):
                vi[wor] = v["words"][wor]
    return render_template('show_listdict.html', listdict=vi, title="Oberbegriffe")


def get_item(table: str, id: str):
    col = mydb[table]
    item = col.find_one({'_id': ObjectId(id)})
    if item is None:
        abort(404)
    return item


def get_document(table: str, docid: str):
    col = mydb[table]
    item = col.find_one({'docid': int(docid)})
    if item is None:
        abort(404)
    return item


@ myapp.route("/pattern")
def allpattern():
    if user == None:
        return redirect(url_for('login'))
    collist = mydb.list_collection_names()
    vi = []
    if "pattern" in collist:
        list_col = mydb["pattern"]
        list = list_col.find()
        for v in list:
            vi.append(v["paragraph"])
    json_string = json.dumps(vi, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route('/pattern/<id>')
def pattern(id):
    if user == None:
        return redirect(url_for('login'))
    item = get_item("pattern", id)
    return render_template('show_item.html', item=item)


@ myapp.route("/showpattern")
def showpattern():
    if user == None:
        return redirect(url_for('login'))
    vi = []
    if "pattern" in collist:
        list_col = mydb["pattern"]
        list = list_col.find()
        for v in list:
            vi.append(v)
    return render_template('show_list.html', list=sorted(vi, key=lambda p: p['paragraph']), title="Textbausteine", table="editpatternlist")


@ myapp.route('/pattern/<id>/edit', methods=('GET', 'POST'))
def editpatternlist(id):
    if user == None:
        return redirect(url_for('login'))
    item = get_item("pattern", id)
    if request.method == 'POST':
        paragraph = request.form['paragraph']
        typ = request.form['type']
        col = mydb["pattern"]
        col.update_one(
            {'_id': ObjectId(id)}, {'$set': {'paragraph': paragraph, 'type': typ}})
        return redirect(url_for('showpattern'))
    collist = mydb.list_collection_names()
    vi = [{ "name": ""}]
    if "doctypes" in collist:
        list_col = mydb["doctypes"]
    list = list_col.find()
    for v in list:
        v1 = {}
        for a in v:
            if a != "_id":
                v1[a] = v[a]
        vi.append(v1)
    return render_template('edit_item.html', item=item, types=vi, delete_item="deletepattern")


@ myapp.route('/pattern/<id>/delete', methods=('POST',))
def deletepattern(id):
    if user == None:
        return redirect(url_for('login'))
    # item = get_item("pattern", id)
    col = mydb["pattern"]
    col.remove({'_id': ObjectId(id)})
    flash('"{}" was successfully deleted!'.format('Item'))
    return redirect(url_for('showpattern'))

@ myapp.route("/doctypes")
def alldoctypes():
    if user == None:
        return redirect(url_for('login'))
    collist = mydb.list_collection_names()
    vi = []
    if "doctypes" in collist:
        list_col = mydb["doctypes"]
        list = list_col.find()
        for v in list:
            v1 = {}
            for a in v:
                if a != "_id":
                    v1[a] = v[a]
            vi.append(v1)
    json_string = json.dumps(vi, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response

@ myapp.route("/showdoctypes")
def showdoctypes():
    if user == None:
        return redirect(url_for('login'))
    vi = []
    if "doctypes" in collist:
        list_col = mydb["doctypes"]
        list = list_col.find()
        for v in list:
            vi.append(v)
    return render_template('show_document_types.html', documents=vi, title="Dokumenttypen")

@ myapp.route("/badlist")
def allbadlist():
    if user == None:
        return redirect(url_for('login'))
    collist = mydb.list_collection_names()
    vi = []
    if "badlist" in collist:
        list_col = mydb["badlist"]
        list = list_col.find()
        for v in list:
            vi.append(v["paragraph"])
    json_string = json.dumps(vi, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route("/showbadlist")
def showbadlist():
    if user == None:
        return redirect(url_for('login'))
    vi = []
    if "badlist" in collist:
        list_col = mydb["badlist"]
        list = list_col.find()
        for v in list:
            vi.append(v)
    return render_template('show_list.html', list=sorted(vi, key=lambda p: p['paragraph']), title="Badlist", table="editbadlist")


@ myapp.route('/badlist/<id>')
def badlist(id):
    if user == None:
        return redirect(url_for('login'))
    item = get_item("badlist", id)
    return render_template('show_item.html', item=item)


@ myapp.route('/badlist/<id>/edit', methods=('GET', 'POST'))
def editbadlist(id):
    if user == None:
        return redirect(url_for('login'))
    item = get_item("badlist", id)
    if request.method == 'POST':
        paragraph = request.form['paragraph']
        col = mydb["badlist"]
        col.update_one(
            {'_id': ObjectId(id)}, {'$set': {'paragraph': paragraph}})
        return redirect(url_for('showbadlist'))
    return render_template('edit_item.html', item=item, types=[], delete_item="deletebadlist")


@ myapp.route('/badlist/<id>/delete', methods=('POST',))
def deletebadlist(id):
    if user == None:
        return redirect(url_for('login'))
    # item = get_item("badlist", id)
    col = mydb["badlist"]
    col.remove({'_id': ObjectId(id)})
    flash('"{}" was successfully deleted!'.format('Item'))
    return redirect(url_for('showbadlist'))


@ myapp.route("/showemblist")
def showemblist():
    if user == None:
        return redirect(url_for('login'))
    vi = []
    if "emblist" in collist:
        list_col = mydb["emblist"]
        list = list_col.find_one()
        for v in list:
            if v != "_id":
                vi.append({"word": v, "match": list[v]})
    return render_template('show_emblist.html', list=vi, title="de_core_news_md", table="editemblist")


@ myapp.route('/emblist/<id>/edit', methods=('GET', 'POST'))
def editemblist(id):
    if user == None:
        return redirect(url_for('login'))
    # item = get_item("emblist", id)
    if request.method == 'POST':
        # paragraph = request.form['paragraph']
        # col = mydb["pattern"]
        # col.update_one(
        #     {'_id': ObjectId(id)}, {'$set': {'paragraph': paragraph}})
        return redirect(url_for('showemblist'))
    # return render_template('edit_embitem.html', item=item, delete_item="deleteemblist")
    return redirect(url_for('showemblist'))


@ myapp.route("/shownoemblist")
def shownoemblist():
    if user == None:
        return redirect(url_for('login'))
    vi = []
    if "noemblist" in collist:
        list_col = mydb["noemblist"]
        list = list_col.find_one()
        for v in list:
            if v != "_id":
                vi.append({"word": v, "count": list[v]})
    return render_template('show_noemblist.html', list=vi, title="Unmatched", table="editnoemblist")


@ myapp.route('/noemblist/<id>/edit', methods=('GET', 'POST'))
def editnoemblist(id):
    if user == None:
        return redirect(url_for('login'))

    # item = get_item("noemblist", id)
    if request.method == 'POST':
        # paragraph = request.form['paragraph']
        # col = mydb["pattern"]
        # col.update_one(
        #     {'_id': ObjectId(id)}, {'$set': {'paragraph': paragraph}})
        return redirect(url_for('shownoemblist'))
    # return render_template('edit_embitem.html', item=item, delete_item="deleteemblist")
    return redirect(url_for('shownoemblist'))


@ myapp.route("/keywords")
def keywords():
    if user == None:
        return redirect(url_for('login'))
    query = request.args
    collist: List = mydb.list_collection_names()
    vi: List[Dict[str, Any]] = []
    # if "topics" in collist:
    #     list_col = mydb["topics"]
    #     list = list_col.find(query)
    #     for v in list:
    #         vi.append({"file": v["file"], "path": v["path"],
    #                   "keywords": v["keywords"], "intents": v["intents"]})
    if metadatatable in collist:
        list_col = mydb[metadatatable]
        list = list_col.find(query)
        for v in list:
            kwor = []
            inte = []
            if "topic" in v:
                kwor = v["topic"]["keywords"]
                inte = v["topic"]["intents"]
            vi.append({"file": v["file"], "path": v["path"],
                      "keywords": kwor, "intents": inte})
    json_string = json.dumps(vi, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route("/allshowkeywords")
def allshowkeywords():
    if user == None:
        return redirect(url_for('login'))
    query = request.args
    collist = mydb.list_collection_names()
    vi: List[Dict[str, Any]] = []
    # if "topics" in collist:
    #     list_col = mydb["topics"]
    #     list: List[Dict[str, Any]] = list_col.find(query)
    #     for v in list:
    #         vi.append(v)
    if metadatatable in collist:
        list_col = mydb[metadatatable]
        list = list_col.find(query)
        for v in list:
            kwor = []
            inte = []
            if "topic" in v:
                kwor = v["topic"]["keywords"]
                inte = v["topic"]["intents"]
            vi.append({"docid": v["docid"], "file": v["file"], "path": v["path"],
                      "keywords": kwor, "intents": inte})
    return render_template('show_documents_keywords.html', documents=vi, title="Schlagworte", table="show_keywords")

    # if "categories" in collist:
    #     cat_col = mydb["categories"]
    #     catobj = cat_col.find_one()
    #     for cat in catobj:
    #         categories.append(cat)


@ myapp.route("/showkeywords/<docid>")
def showkeywords(docid=""):
    if user == None:
        return redirect(url_for('login'))
    collist = mydb.list_collection_names()
    # if "topics" in collist:
    if metadatatable in collist:
        catlist, colors = allcategories_and_colors()
        options: Dict(str, Any) = {"ents": catlist, "colors": colors}
        # item: Dict = get_item("topics", id)
        # doc: Dict = get_item(metadatatable, id)
        doc: Dict = get_document(metadatatable, docid)
        paragraphs: List[Dict[str, Any]] = []
        res = {}
        res["file"] = doc["file"]
        if "place" in doc:
            res["place"] = doc["place"]
        else:
            res["place"] = []
        res["keywords"] = []

        if "topic" in doc:
            item = doc["topic"]
            res["keywords"] = item["keywords"]
            for i in item["intents"]:
                pt: str = i["paragraph"]
                ents: List[Any] = i["entities"]
                html: Markup = displacyText(pt, ents, options)
                paragraphs.append({"words:": i["words"], "html": html})
        return render_template('show_extraction.html', res=res, title="Schlagworte", paragraphs=paragraphs)

# @ myapp.route("/showfilekeywords")
# def showfilekeywords(file=""):
#     collist=mydb.list_collection_names()
#     # if metadatatable in collist:
#     if "topics" in collist:
#         catlist, colors = allcategories_and_colors()
#         options = {"ents": catlist, "colors": colors}
#         list_col=mydb["topics"]
#         query=request.args
#         item: Dict= list_col.find_one(query)
#         paragraphs: List[Dict[str,Any]]=[]
#         for i in item["intents"]:
#             pt: str = i["paragraph"]
#             ents: List[Any] = i["entities"]
#             html: Markup = displacyText(pt, ents, options)
#             paragraphs.append({"words:": i["words"], "html": html})
#         return render_template('show_extraction.html', res=item, title="Keyword", paragraphs=paragraphs)


# #########################################

def _get_array_param(param: str) -> List[str]:
    if param == '':
        return []
    else:
        # return filter(None, param.split(","))
        return param.split(",")


def _get_group_pipeline(group_by: str):
    return [
        {
            '$group': {
                '_id': '$' + group_by,
                'count': {'$sum': 1},
            }
        },
        {
            '$project': {
                '_id': 0,
                'value': '$_id',
                'count': 1,
            }
        },
        {
            '$sort': {'count': -1}
        },
        {
            '$limit': 6,
        }
    ]


def getmatch(args, catlist: List[str]) -> Dict[str, str]:
    match: Dict[str, Any] = {}
    for cat in catlist:
        catvals = _get_array_param(args.get(cat, ''))
        if catvals:
            match[cat] = {'$in': catvals}
    return match


# resolved2()


def _get_facet_pipeline(facet, match):
    pipeline = []
    if match:
        if facet in match:
            matchc = match.copy();
            del matchc[facet]
        else:
            matchc = match
        pipeline = [
            {'$match': matchc}
        ] if match else []
    return pipeline + _get_group_pipeline(facet)


def _get_group_pipeline(group_by):
    return [
        {'$unwind': '$' + group_by},
        {
            '$group': {
                '_id': '$' + group_by,
                'count': {'$sum': 1},
            }
        },
        {
            '$project': {
                '_id': 0,
                'value': '$_id',
                'count': 1,
            }
        },
        {
            '$sort': {'count': -1}
        },
        {
            '$limit': 100,
        }
    ]


def _get_single_value_facet_pipeline(facet, match):
    pipeline = []
    if match:
        if facet in match:
            matchc = match.copy();
            del matchc[facet]
        else:
            matchc = match
        pipeline = [
            {'$match': matchc}
        ] if match else []
    return pipeline + _get_single_value_group_pipeline(facet)


def _get_single_value_group_pipeline(group_by):
    return [
        {
            '$group': {
                '_id': '$' + group_by,
                'count': {'$sum': 1},
            }
        },
        {
            '$project': {
                '_id': 0,
                'value': '$_id',
                'count': 1,
            }
        },
        {
            '$sort': {'count': -1}
        },
        {
            '$limit': 100,
        }
    ]


@ myapp.route("/search/resolved2_facets")
def resolved2_facets():
    if user == None:
        return redirect(url_for('login'))

    catlist, colors = allcategories_and_colors()
    match = getmatch(request.args, catlist)

    search = request.args.get('search', '')

    hidas = _get_array_param(request.args.get('hidas', ''))
    path = _get_array_param(request.args.get('path', ''))
    doctype = _get_array_param(request.args.get('doctype', ''))
    ext = _get_array_param(request.args.get('ext', ''))
    district = _get_array_param(request.args.get('district', ''))
    vorhaben = _get_array_param(request.args.get('vorhaben', ''))
    Sachbegriff = _get_array_param(request.args.get('Sachbegriff', ''))
    Denkmalart = _get_array_param(request.args.get('Denkmalart', ''))
    Denkmalname = _get_array_param(request.args.get('Denkmalname', ''))

    if path:
        match['path'] = {'$in': path}
    if hidas:
        match['hidas'] = {'$in': hidas}
    if doctype:
        match['doctype'] = {'$in': doctype}
    if ext:
        match['ext'] = {'$in': ext}
    if district:
        match['district'] = {'$in': district}
    if vorhaben:
        match['vorhaben'] = {'$in': vorhaben}
    if Sachbegriff:
        match['Sachbegriff'] = {'$in': Sachbegriff}
    if Denkmalart:
        match['Denkmalart'] = {'$in': Denkmalart}
    if Denkmalname:
        match['Denkmalname'] = {'$in': Denkmalname}
    pipeline = [{
        '$match': {'$text': {'$search': search}}
    }] if search else []

    facets = {
        'path':  _get_single_value_facet_pipeline('path', match),
        'path':  _get_single_value_facet_pipeline('path', match),
        'hidas':  _get_facet_pipeline('hidas', match),
        'doctype': _get_single_value_facet_pipeline('doctype', match),
        'ext': _get_single_value_facet_pipeline('ext', match),
        'district': _get_single_value_facet_pipeline('district', match),
        'vorhaben':  _get_single_value_facet_pipeline('vorhaben', match),
        'Sachbegriff':  _get_facet_pipeline('Sachbegriff', match),
        'Denkmalart':  _get_facet_pipeline('Denkmalart', match),
        'Denkmalname':  _get_facet_pipeline('Denkmalname', match),
    }
    for cat in catlist:
        facets[cat] = _get_facet_pipeline(cat, match)

    pipeline += [{'$facet': facets}]

    col = mydb[metadatatable]
    res = list(col.aggregate(pipeline))[0]

    json_string = json.dumps(res, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route("/search/resolved2")
def resolved2():
    if user == None:
        return redirect(url_for('login'))
    # pagination
    page = int(request.args.get('page', '0'))
    page_size = int(request.args.get('page_size', '50'))
    skip = page * page_size
    limit = min(page_size, 50)

    catlist, col = allcategories_and_colors()
    match = getmatch(request.args, catlist)

    search = request.args.get('search', '')

    hidas = _get_array_param(request.args.get('hidas', ''))
    path = _get_array_param(request.args.get('path', ''))
    doctype = _get_array_param(request.args.get('doctype', ''))
    ext = _get_array_param(request.args.get('ext', ''))
    district = _get_array_param(request.args.get('district', ''))
    vorhaben = _get_array_param(request.args.get('vorhaben', ''))
    Sachbegriff = _get_array_param(request.args.get('Sachbegriff', ''))
    Denkmalart = _get_array_param(request.args.get('Denkmalart', ''))
    Denkmalname = _get_array_param(request.args.get('Denkmalname', ''))

    if search and search != '':
        match['$text'] = {'$search': search}

    if path:
        match['path'] = {'$in': path}
    if hidas:
        match['hidas'] = {'$in': hidas}
    if doctype:
        match['doctype'] = {'$in': doctype}
    if ext:
        match['ext'] = {'$in': ext}
    if district:
        match['district'] = {'$in': district}
    if vorhaben:
        match['vorhaben'] = {'$in': vorhaben}
    if Sachbegriff:
        match['Sachbegriff'] = {'$in': Sachbegriff}
    if Denkmalart:
        match['Denkmalart'] = {'$in': Denkmalart}
    if Denkmalname:
        match['Denkmalname'] = {'$in': Denkmalname}

    pipeline = [{
        '$match': match
    }] if match else []

    pipeline += [{
        '$facet': {
            metadatatable: [
                {'$skip': skip},
                {'$limit': limit}
            ],
            'count': [
                {'$count': 'total'}
            ],
        }
    }]

    col = mydb[metadatatable]
    res = list(col.aggregate(pipeline))[0]
    print(res["count"])

    # remove _id, is an ObjectId and is not serializable
    # for resolved in res[metadatatable]:
    #     del resolved['_id']

    vi: Dict[str, Any] = []
    for v in res[metadatatable]:  # remove _id, is an ObjectId and is not serializable
        v1: Dict[str, Any] = {}
        for a in v:
            if a != "_id" and a != "obj" and a != "hida" and a != "meta" and a != "topic" and a != "adrDict" and a != "text":
                v1[a] = v[a]
        vi.append(v1)

    del res[metadatatable]
    res["metadata"] = vi
    res['count'] = res['count'][0]['total'] if res['count'] else 0

    # return jsonify(res)
    json_string = json.dumps(res, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@myapp.route('/excel/qs')
def excelqs2():
    if user == None:
        return redirect(url_for('login'))
    col = mydb[metadatatable]
    vi: Dict[str, Any] = []
    for row in col.find({"qs": {"$exists": True}}):
        v1: Dict[str, Any] = {}
        v1["docid"] = row["docid"]
        for a in row["qs"]:
            v1[a] = row["qs"][a]
        vi.append(v1)

    df_1 = pd.DataFrame(vi)

    # df_1 = pd.DataFrame(vi)
    # df_1 = pd.DataFrame(np.random.randint(0,10,size=(10, 4)), columns=list('ABCD'))

    # create an output stream
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # taken from the original question
    df_1.to_excel(writer, startrow=0, merge_cells=False, sheet_name="Sheet_1")
    workbook = writer.book
    worksheet = writer.sheets["Sheet_1"]
    writer.close()
    output.seek(0)
    return send_file(output, attachment_filename="qs.xlsx", as_attachment=True)


@myapp.route('/excel/resolved2')
def excelresolved2():
    if user == None:
        return redirect(url_for('login'))
    # pagination
    # page = int(request.args.get('page', '0'))
    page_size = int(request.args.get('page_size', '50'))
    # skip = page * page_size
    limit = min(page_size, 50)
    page = 0
    skip = 0
    # limit = 100

    catlist, col = allcategories_and_colors()
    match = getmatch(request.args, catlist)

    search = request.args.get('search', '')

    hidas = _get_array_param(request.args.get('hidas', ''))
    path = _get_array_param(request.args.get('path', ''))
    doctype = _get_array_param(request.args.get('doctype', ''))
    ext = _get_array_param(request.args.get('ext', ''))
    district = _get_array_param(request.args.get('district', ''))
    vorhaben = _get_array_param(request.args.get('vorhaben', ''))
    Sachbegriff = _get_array_param(request.args.get('Sachbegriff', ''))
    Denkmalart = _get_array_param(request.args.get('Denkmalart', ''))
    Denkmalname = _get_array_param(request.args.get('Denkmalname', ''))

    if search and search != '':
        match['$text'] = {'$search': search}

    if path:
        match['path'] = {'$in': path}
    if hidas:
        match['hidas'] = {'$in': hidas}
    if doctype:
        match['doctype'] = {'$in': doctype}
    if ext:
        match['ext'] = {'$in': ext}
    if district:
        match['district'] = {'$in': district}
    if vorhaben:
        match['vorhaben'] = {'$in': vorhaben}
    if Sachbegriff:
        match['Sachbegriff'] = {'$in': Sachbegriff}
    if Denkmalart:
        match['Denkmalart'] = {'$in': Denkmalart}
    if Denkmalname:
        match['Denkmalname'] = {'$in': Denkmalname}

    pipeline = [{
        '$match': match
    }] if match else []

    metaspec = [{'$skip': skip}, {'$limit': limit}]

    pipeline += [{
        '$facet': {
            metadatatable: metaspec,
            'count': [
                {'$count': 'total'}
            ],
        }
    }]

    col = mydb[metadatatable]
    res = list(col.aggregate(pipeline))[0]
    print(res["count"])

    # remove _id, is an ObjectId and is not serializable
    # for resolved in res[metadatatable]:
    #     del resolved['_id']

    vi: Dict[str, Any] = []
    for v in res[metadatatable]:  # remove _id, is an ObjectId and is not serializable
        v1: Dict[str, Any] = {}
        for a in v:
            if a != "_id" and a != "obj" and a != "hida" and a != "meta" and a != "topic" and a != "adrDict" and a != "text":
                v1[a] = v[a]
        vi.append(v1)

    # res[metadatatable] = vi
    res['count'] = res['count'][0]['total'] if res['count'] else 0

    cnt = res['count']
    while cnt > len(vi):
        page += 1
        skip = page * page_size
        metaspec[0] = {'$skip': skip}
        res = list(col.aggregate(pipeline))[0]
        for v in res[metadatatable]:  # remove _id, is an ObjectId and is not serializable
            v1: Dict[str, Any] = {}
            for a in v:
                if a != "_id" and a != "obj" and a != "hida" and a != "meta" and a != "topic" and a != "adrDict" and a != "text":
                    v1[a] = v[a]
            vi.append(v1)

    df_1 = pd.DataFrame(vi)

    # df_1 = pd.DataFrame(vi)
    # df_1 = pd.DataFrame(np.random.randint(0,10,size=(10, 4)), columns=list('ABCD'))

    # create an output stream
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # taken from the original question
    df_1.to_excel(writer, startrow=0, merge_cells=False, sheet_name="Sheet_1")
    workbook = writer.book
    worksheet = writer.sheets["Sheet_1"]
    # format = workbook.add_format()
    # format.set_bg_color('#eeeeee')
    # worksheet.set_column(0,9,28)

    # the writer has done its job
    writer.close()

    # go back to the beginning of the stream
    output.seek(0)

    # finally return the file
    return send_file(output, attachment_filename="testing.xlsx", as_attachment=True)


@ myapp.route("/search/doclib")
def doclib():
    res = {}
    res['doclib'] = lib

    # return jsonify(res)
    json_string = json.dumps(res, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route("/search/hida2_facets")
def hida2_facets():

    hcatlist = ["Sachbegriff",
                "Num-Dat",
                "Künstler-Rolle", "Künstler-Name", "Künstler-Funktion",
                "Sozietät-Art-Rolle", "Sozietät-Name", "Sozietät-ber-Funktion",
                "Ausw-Stelle"]

    match = getmatch(request.args, hcatlist)

    Bezirk = _get_array_param(request.args.get('Bezirk', ''))
    Ortsteil = _get_array_param(request.args.get('Ortsteil', ''))
    Denkmalart = _get_array_param(request.args.get('Denkmalart', ''))

    search = request.args.get('search', '')

    pipeline = [{
        '$match': {'$text': {'$search': search}}
    }] if search else []

    if Bezirk:
        match['Bezirk'] = {'$in': Bezirk}
    if Ortsteil:
        match['Ortsteil'] = {'$in': Ortsteil}
    if Denkmalart:
        match['Denkmalart'] = {'$in': Denkmalart}

    facets = {
        'Bezirk':  _get_single_value_facet_pipeline('Bezirk', match),
        'Ortsteil':  _get_single_value_facet_pipeline('Ortsteil', match),
        'Denkmalart':  _get_single_value_facet_pipeline('Denkmalart', match),
    }
    for cat in hcatlist:
        facets[cat] = _get_facet_pipeline(cat, match)

    pipeline += [{'$facet': facets}]

    col = mydb["hida"]
    res = list(col.aggregate(pipeline))[0]

    json_string = json.dumps(res, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route("/search/hida2")
def hida2():
    # pagination
    page = int(request.args.get('page', '0'))
    page_size = int(request.args.get('page-size', '50'))
    skip = page * page_size
    limit = min(page_size, 50)

    # "Bezirk", "Ortsteil", "Denkmalart", "Sachbegriff",
    hcatlist = ["Sachbegriff", "Num-Dat", "Künstler-Rolle", "Künstler-Name",
                "Künstler-Funktion",
                "Sozietät-Art-Rolle",
                "Sozietät-Name",
                "Sozietät-ber-Funktion"
                "Ausw-Stelle"]

    match = getmatch(request.args, hcatlist)

    Bezirk = _get_array_param(request.args.get('Bezirk', ''))
    Ortsteil = _get_array_param(request.args.get('Ortsteil', ''))
    Denkmalart = _get_array_param(request.args.get('Denkmalart', ''))

    search = request.args.get('search', '')

    if search and search != '':
        match['$text'] = {'$search': search}

    if Bezirk:
        match['Bezirk'] = {'$in': Bezirk}
    if Ortsteil:
        match['Ortsteil'] = {'$in': Ortsteil}
    if Denkmalart:
        match['Denkmalart'] = {'$in': Denkmalart}

    pipeline = [{
        '$match': match
    }] if match else []

    pipeline += [{
        '$facet': {
            'hida': [
                {'$skip': skip},
                {'$limit': limit}
            ],
            'count': [
                {'$count': 'total'}
            ],
        }
    }]

    col = mydb["hida"]
    res = list(col.aggregate(pipeline))[0]
    print(res["count"])

    vi: Dict[str, Any] = []
    for v in res['hida']:  # remove _id, is an ObjectId and is not serializable
        v1: Dict[str, Any] = {}
        for a in v:
            if a != "_id":
                v1[a] = v[a]
        vi.append(v1)

    res['hida'] = vi
    res['count'] = res['count'][0]['total'] if res['count'] else 0

    # return jsonify(res)
    json_string = json.dumps(res, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response

# #########################################


def prepareList():
    if "vorhaben_inv" in collist:
        vorhabeninv_col = mydb["vorhaben_inv"]
        vorhabeninv: Dict = vorhabeninv_col.find_one()
        wvi: Dict[str, List[str]] = {}
        wvi = vorhabeninv["words"]

        words, wordlist = prepareWords(wvi)
        categories: List[str] = []

        # if "categories" in collist:
        #     cat_col = mydb["categories"]
        #     catobj = cat_col.find_one()
        #     for cat in catobj:
        #         if cat != '_id':
        #             categories.append(cat)

        patternjs: List[str] = []
        if "pattern" in collist:
            pattern_col = mydb["pattern"]
            pattern = pattern_col.find()
            for v in pattern:
                patternjs.append(v["paragraph"])
        plist: List[Dict[str, str]] = preparePattern(patternjs)

        badlistjs: List[str] = []
        if "badlist" in collist:
            badlist_col = mydb["badlist"]
            badlist = badlist_col.find()
            for v in badlist:
                badlistjs.append(v["paragraph"])

    return words, wordlist, categories, plist, badlistjs


@ myapp.route("/extractintents", methods=('GET', 'POST'))
def extractintents():

    words, wordlist, categories, plist, badlistjs = prepareList()

    bparagraph = True

    res = extractTopicsAndPlaces(
        words, wordlist, categories, plist, badlistjs, bparagraph, "")

    print(res)
    json_string = json.dumps(res, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route('/create_extraction', methods=('GET', 'POST'))
def create_extraction():
    if request.method == 'POST':
        text = request.form['content']
        query = request.args

        bparagraph = True
        if "bparagraph" in query:
            bparagraph = query["bparagraph"]

        words, wordlist, categories, plist, badlistjs = prepareList()

        res = extractTopicsAndPlaces(
            words, wordlist, categories, plist, badlistjs, bparagraph, text)
        if len(res) > 0:
            catlist, colors = allcategories_and_colors()
            options = {"ents": catlist, "colors": colors}
            item: Dict = res
            paragraphs: List[Dict[str, Any]] = []
            for i in item["intents"]:
                pt: str = i["paragraph"]
                ents: List[Any] = i["entities"]
                html: Markup = displacyText(pt, ents, options)
                paragraphs.append({"words:": i["words"], "html": html})
            return render_template('show_extraction.html', res=item, title="Keyword", paragraphs=paragraphs)
        else:
            return render_template('index.html')

    return render_template('create_extraction.html')


@ myapp.route("/testprepare1")
def testprepare1():
    s = spacytest("Wollen wir die Fenster am Haus streichen?")
    json_string = json.dumps(s, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response


@ myapp.route("/testprepare2")
def testprepare2():
    collist = mydb.list_collection_names()
    wvi = {}
    if "vorhaben_inv" in collist:
        vorhabeninv_col = mydb["vorhaben_inv"]
        vorhabeninv = vorhabeninv_col.find()
        for v in vorhabeninv:
            for wor in v["words"]:
                wvi[wor] = v["words"][wor]
    words, wordlist = prepareWords(wvi)
    s = spacytest("Wollen wir die Fenster am Haus streichen?")
    json_string = json.dumps(s, ensure_ascii=False)
    response = Response(
        json_string, content_type="application/json; charset=utf-8")
    return response

# CRUD UI Demo ########################################################


if not "posts" in collist:
    posts_col = mydb["posts"]
    posts_col.insert_many([{'ID': 1, 'title': "TIT1", 'created': datetime.datetime.now(), 'content': 'cont1'},
                           {'ID': 2, 'title': "TIT2", 'created': datetime.datetime.now(), 'content': 'cont2'}])


def get_post(post_id):
    posts_col = mydb["posts"]
    post = posts_col.find_one({'ID': post_id})
    if post is None:
        abort(404)
    return post


@ myapp.route("/posts")
def posts():
    posts_col = mydb["posts"]
    posts = posts_col.find()
    # return "Hello Flask, This is the KiBarDok Service. Try hida, intents, words, badlist, paragraph"
    return render_template('posts.html', posts=posts)

###


@ myapp.route('/posts/<int:id>')
def show_post(id):
    post = get_post(id)
    return render_template('show_post.html', post=post)


@ myapp.route('/posts/create', methods=('GET', 'POST'))
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if not title:
            flash('Title is required!')
        else:
            posts_col = mydb["posts"]
            posts = posts_col.find()
            maxid = 0
            for p in posts:
                if p['ID'] > maxid:
                    maxid = p['ID']
            newid = maxid+1
            posts_col.insert({'ID': newid, 'title': title,
                             'created': datetime.datetime.now(), 'content': content})
            return redirect(url_for('posts'))
    return render_template('create_post.html')


@ myapp.route('/posts/<int:id>/edit', methods=('GET', 'POST'))
def edit_post(id):
    post = get_post(id)
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if not title:
            flash('Title is required!')
        else:
            posts_col = mydb["posts"]
            posts_col.update_one(
                {'ID': id}, {'$set': {'title': title, 'content': content}})
            return redirect(url_for('posts'))
    return render_template('edit_post.html', post=post)


@ myapp.route('/posts/<int:id>/delete', methods=('POST',))
def delete_post(id):
    post = get_post(id)
    posts_col = mydb["posts"]
    posts_col.remove({'ID': id})
    flash('"{}" was successfully deleted!'.format(post['title']))
    return redirect(url_for('posts'))
