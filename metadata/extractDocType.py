# coding: utf-8
import re
# from test_app.service import pattern

# Check regex: https://pythex.org/

# def compiler(patList,notPatList):
#     #########positive matching elements
#     pattern='.*$'
#     for pat in patList:
#         pattern='(?=.*('+pat+'))'+pattern
#     #########negativ matching elements'
#     temp_notPattern=''
#     for pat in notPatList:
#         pattern='^(?!.*'+pat+')'+pattern
#         temp_notPattern=temp_notPattern+pat+'|'
#     notPattern='(?=.*('+temp_notPattern+'kjcebjkw'+'))'+'.*$'
#     ########compile
#     compiling = re.compile(pattern)
#     notCompiling = re.compile(notPattern)
#     #compiling: berücksichtigt Schlüsselwörter, die zu einem Treffer führen, aber auch Schlüsselwörter die zu einem Ausschluss führen
#     #notCompiling: zeigt welche Schlüsselwörter zu einem Ausschluss geführt haben
#     return compiling,notCompiling


def compiler(patList):
    pattern = '.*$'
    for pat in patList:
        pattern = '(?=.*('+pat+'))'+pattern
    compiling = re.compile(pattern)
    return compiling


def notcompiler(notPatList):
    # positive matching elements
    pattern = '.*$'
    temp_notPattern = ''
    for pat in notPatList:
        pattern = '^(?!.*'+pat+')'+pattern
        temp_notPattern = temp_notPattern+pat+'|'
    notPattern = '(?=.*('+temp_notPattern+'kjcebjkw'+'))'+'.*$'
    notCompiling = re.compile(notPattern)
    return notCompiling


def findAll(patList, txt):
    # positive matching elements
    find = []
    for pat in patList:
        match = re.findall(pat, txt)
        if match:
            if type(match[0]) == tuple:
                find.extend(list(match))
            else:
                find.append(match[0])
    return list(filter(None, find))


document_pattern = {}
# d = '[denkmal]*[schutz]*[gerechten]*[geschützen]*[rechtliche[rn]*]*'
# no = '(?<!nicht)\s'
# # Treffer
# g_patList = [d+'\sGenehmigung|[§]\s*11|Paragraph\s*11|Genehmigung|Bescheid|Maßnahme|Instandsetzung|Auflage[n]*[^\w]|keiner\s'+d+'\sGenehmigung|keine\s'+d+'\sGenehmigung.+nötig', 'keiner\s'+d +
#              '\sGenehmigung|keine\s'+d+'\sGenehmigung.+nötig|'+no+'[zZ]u[ge]*stim[^ ]*|'+no+'[bB]+estäti[^ ]*|'+no+'erteil[^ ]*|'+no+'angenommen|'+no+'annehmen|'+no+'genehmig[t]*[en]*|'+no+'[zu\s]*gewähr[t]*[en]*']

# document_pattern["Genehmigung"] = {
#     "file": ['geneh', 'zustim'],
#     "pos": g_patList,
#     "neg": ['[kK]eine[n]*\s[dD]+enkmal[en]*[schutz]*[gerechten]*[geschützen]*[rechtliche[n]*]*', 'Anhörung', 'Versagung', '[kK]eine\sGenehmigung', '[kK]eine\sZustimmung', '[kK]eine\s[bB]+estäti[^ ]*', 'versagt', 'versagen', 'abgelehnt', 'ablehnen', 'zurückgewiesen|zurückzuweisen', '§\s28\sVwVfG', '14\sTagen|zwei\sWochen|2\sWochen', 'Baugenehmigungsverfahren', '[Uu]nterlage[n]*[^.]*[nach]*[ein]*[zu]*reichen', 'fehlend[e]*[r]*[n]*\s[Uu]nterlage[n]*', 'nicht\sausreichend[e]*[r]*[n]*\s[Uu]nterlage[n]*', '[Uu]nterlage[n]*[^.]+nicht\sausreichend', 'unvollständig[e]*[r]*[n]*\s[Uu]+nterlage[n]*', 'bauordnungsrechtlich', 'Kein\sRechtsbehelfsbelehrung', 'FORMCHECKBOX', 'Prüfung\smit\sMitzeichnung\sdurch\sLDA']
# }
# document_pattern["Nachforderung"] = {
#     "file": [],
#     "pos": ['[Uu]nterlage[n]*[^.]*[un]*[nach]*[ein]*[zu]*reich[^.]*|fehlend[e]*[r]*[n]*\s[Uu]nterlage[n]*|unvollständig[e]*[r]*[n]*\s[Uu]nterlage[n]*|nicht\sausreichend[e]*[r]*[n]*\s[Uu]nterlage[n]*|[Uu]nterlage[n]*[^.]+nicht\sausreichend|Ergänz[^.]*[Uu]nterlage[n]*|\sum[^.]*Stellung[nahme]*|[Uu]nterlage[^.]*vervollständ[^ ]*|vervollständ[^.]*[uU]nterlage[n]*'],
#     "neg": ['Baugenehmigungsverfahren', '[bB]auordnungsrechtlich', '[kK]ein[e]*\sRechtsbehelfsbelehrung', 'Prüfung\smit\sMitzeichnung\sdurch\sLDA', 'Versagung', 'Anhörung']
# }
# document_pattern["Eingang"] = {
#     "file": [],
#     "pos": ['bestätig[^.]+Eingang|Eingangsbestätigung'],
#     "neg": ['Baugenehmigungsverfahren', '[bB]auordnungsrechtlich', '[kK]ein[e]*\sRechtsbehelfsbelehrung', 'Prüfung\smit\sMitzeichnung\sdurch\sLDA', 'Versagung', 'Anhörung', 'Unterlage[n]*[^.][nach]*[ein]*[zu]*reichen', 'fehlend[e]*[r]*[n]*\sUnterlage[n]*', 'nicht\sausreichend[e]*[r]*[n]*\sUnterlage[n]*', '[Unterlage[n]*]*[^.]+nicht\sausreichend']
# }
# document_pattern["Anhörung"] = {
#     "file": ['anhö', 'anhoe', 'anhorung'],
#     "pos": ['Anhörung\svor\sVersagung|Anhörung|§\s*28\s*VwVfG|14\sTage|zwei\sWochen|2\sWochen', '14\sTage|zwei\sWochen|2\sWochen|Versagung|Ablehnung|[kK]eine\sZustim[^ ]*|nicht\sgenehmig[^ ]*|nicht\san[ge]*n[^ ]*|nicht\s[zu ]*gewähr[^ ]*|anhören|versag[^ ]*|ab[ge]*lehn[^ ]*|entgegensteh[^ ]*|nicht\serteil[^ ]*|nicht\szu[ge]*stimm[^ ]*'],
#     "neg": ['Baugenehmigungsverfahren', '[bB]auordnungsrechtlich', '[kK]ein[e]*\sRechtsbehelfsbelehrung', 'FORMCHECKBOX', 'Prüfung\smit\sMitzeichnung\sdurch\sLDA', 'Anhörung[^.]*vom']
# }
# document_pattern["Versagung"] = {
#     "file": ['versag', 'versg', 'negativ'],
#     "pos": ['[dD]+enkmal[en]*[schutz]*[gerechten]*[geschützen]*[rechtliche[rn]*]*\sVersagung|Begründung\sder\sVersagung|Versagung|Ablehnung|[kK]eine\sZustim[^ ]*|kein[en]*\s[dD]+enkmal[en]*[schutz]*[gerechten]*[geschützen]*[rechtliche[rn]*]*|nicht\sgenehmig[^ ]*|nicht\szu\sgewähren|Wider[^ ]*[^.]*zurück[^ ]*', 'Wider[^ ]*[^.]*zurück[^ ]*|nicht\sgenehmig[^ ]*|nicht\s[zu ]*gewähren|versag[^ ]*|ab[ge]*lehn[^ ]*|entgegensteh[^ ]*|nicht\serteil[^ ]*|nicht\szugestim[^ ]*|nicht\san[ge]*n[^ ]*'],
#     "neg": ['Anhörung(?!\svom)|Anhörung\s[zur]*[der]*[\s]*Versagung(?!\svom)', 'Auflage[n]*[^\w]', '14\sTage|zwei\sWochen|2\sWochen', 'Baugenehmigungsverfahren', 'bauordnungsrechtlich', '[kK]ein\sRechtsbehelfsbelehrung', 'FORMCHECKBOX', 'Prüfung\smit\sMitzeichnung\sdurch\sLDA']
# }
# document_pattern["Bauverfahren"] = {
#     "file": [],
#     "pos": ['Bau[genehmigungs]*verfahren|Bauvorhaben|Bauvorlage|Bauabnahme|Bauausführung|Bauherr|[bB]auordnungsrechtlich[en]*|Genehmigungsverfahren|Anlage\szur\sBaugenehmigung[sverfahren]*|[kK]ein[e]*\sRechtsbehelfsbelehrung|Anlage\szur\sGenehmigung'],
#     "neg": ['Anhörung', '14\sTage|zwei\sWochen|2\sWochen', 'Versagung', 'FORMCHECKBOX', 'Prüfung\smit\sMitzeichnung\sdurch\sLDA']
# }
# document_pattern["Antrag"] = {
#     "file": [],
#     "pos": ['FORMCHECKBOX|Prüfung\smit\sMitzeichnung\sdurch\sLDA'],
#     "neg": ['never_ever']
# }
# document_pattern["Anfrage"] = {
#     "file": ["anfr"],
#     "pos": ['[Be]*[aA]+ntwort[ung]*[^.]*[fF]+rage|Anfrage|Frage[:]|Antwort[:]'],
#     "neg": ['never_ever']
# }
# document_pattern["Stellungnahme"] = {
#     "file": ["stellung"],
#     "pos": ['never_ever'],
#     "neg": ['never_ever']
# }
# document_pattern["Kein Denkmal"] = {
#     "file": ["kein denkmal"],
#     "pos": ['never_ever'],
#     "neg": ['never_ever']
# }


###########################################################
# pattern for "Genehmigung"
# d='[denkmal]*[schutz]*[gerechten]*[geschützen]*[rechtliche[rn]*]*'
# no='(?<!nicht)\s'
# Treffer
# g_patList = [d+'\sGenehmigung|[§]\s*11|Paragraph\s*11|Genehmigung|Bescheid|Maßnahme|Instandsetzung|Auflage[n]*[^\w]|keiner\s'+d+'\sGenehmigung|keine\s'+d+'\sGenehmigung.+nötig','keiner\s'+d+'\sGenehmigung|keine\s'+d+'\sGenehmigung.+nötig|'+no+'[zZ]u[ge]*stim[^ ]*|'+no+'[bB]+estäti[^ ]*|'+no+'erteil[^ ]*|'+no+'angenommen|'+no+'annehmen|'+no+'genehmig[t]*[en]*|'+no+'[zu\s]*gewähr[t]*[en]*']

# g_patList = ['[denkmal]*[schutz]*[gerechten]*[geschützen]*[rechtliche[rn]*]*\sGenehmigung|[§]\s*11|Paragraph\s*11|Genehmigung|Bescheid|Maßnahme|Instandsetzung|Auflage[n]*[^\w]|keiner\s[denkmal]*[schutz]*[gerechten]*[geschützen]*[rechtliche[rn]*]*\sGenehmigung|keine\s[denkmal]*[schutz]*[gerechten]*[geschützen]*[rechtliche[rn]*]*\sGenehmigung.+nötig','keiner\s[denkmal]*[schutz]*[gerechten]*[geschützen]*[rechtliche[rn]*]*\sGenehmigung|keine\s[denkmal]*[schutz]*[gerechten]*[geschützen]*[rechtliche[rn]*]*\sGenehmigung.+nötig|(?<!nicht)\s[zZ]u[ge]*stim[^ ]*|(?<!nicht)\s[bB]+estäti[^ ]*|(?<!nicht)\serteil[^ ]*|(?<!nicht)\sangenommen|(?<!nicht)\sannehmen|(?<!nicht)\sgenehmig[t]*[en]*|(?<!nicht)\s[zu\s]*gewähr[t]*[en]*']

# #Ausschluss
# g_not_patList=['[kK]eine[n]*\s[dD]+enkmal[en]*[schutz]*[gerechten]*[geschützen]*[rechtliche[n]*]*','Anhörung', 'Versagung', '[kK]eine\sGenehmigung','[kK]eine\sZustimmung','[kK]eine\s[bB]+estäti[^ ]*','versagt','versagen','abgelehnt','ablehnen','zurückgewiesen|zurückzuweisen','§\s28\sVwVfG','14\sTagen|zwei\sWochen|2\sWochen','Baugenehmigungsverfahren','[Uu]nterlage[n]*[^.]*[nach]*[ein]*[zu]*reichen','fehlend[e]*[r]*[n]*\s[Uu]nterlage[n]*','nicht\sausreichend[e]*[r]*[n]*\s[Uu]nterlage[n]*','[Uu]nterlage[n]*[^.]+nicht\sausreichend','unvollständig[e]*[r]*[n]*\s[Uu]+nterlage[n]*','bauordnungsrechtlich','Kein\sRechtsbehelfsbelehrung','FORMCHECKBOX','Prüfung\smit\sMitzeichnung\sdurch\sLDA']
# genehmigung=compiler(g_patList,g_not_patList)[0]
# notGenehmigung=compiler(g_patList,g_not_patList)[1]
# ####################################pattern for 'Nachforderung'
# n_patList=['[Uu]nterlage[n]*[^.]*[un]*[nach]*[ein]*[zu]*reich[^.]*|fehlend[e]*[r]*[n]*\s[Uu]nterlage[n]*|unvollständig[e]*[r]*[n]*\s[Uu]nterlage[n]*|nicht\sausreichend[e]*[r]*[n]*\s[Uu]nterlage[n]*|[Uu]nterlage[n]*[^.]+nicht\sausreichend|Ergänz[^.]*[Uu]nterlage[n]*|\sum[^.]*Stellung[nahme]*|[Uu]nterlage[^.]*vervollständ[^ ]*|vervollständ[^.]*[uU]nterlage[n]*']
# n_not_patList=['Baugenehmigungsverfahren','[bB]auordnungsrechtlich','[kK]ein[e]*\sRechtsbehelfsbelehrung','Prüfung\smit\sMitzeichnung\sdurch\sLDA','Versagung', 'Anhörung']
# nachforderung=compiler(n_patList,n_not_patList)[0]
# notNachforderung=compiler(n_patList,n_not_patList)[1]
# ####################################pattern for 'Eingangbestaetigung'
# e_patList=['bestätig[^.]+Eingang|Eingangsbestätigung']
# e_not_patList=['Baugenehmigungsverfahren','[bB]auordnungsrechtlich','[kK]ein[e]*\sRechtsbehelfsbelehrung','Prüfung\smit\sMitzeichnung\sdurch\sLDA','Versagung', 'Anhörung','Unterlage[n]*[^.][nach]*[ein]*[zu]*reichen','fehlend[e]*[r]*[n]*\sUnterlage[n]*','nicht\sausreichend[e]*[r]*[n]*\sUnterlage[n]*','[Unterlage[n]*]*[^.]+nicht\sausreichend']
# eingang=compiler(e_patList,e_not_patList)[0]
# notEingang=compiler(e_patList,e_not_patList)[1]
# ####################################pattern for 'Anhoerung'
# a_patList=['Anhörung\svor\sVersagung|Anhörung|§\s*28\s*VwVfG|14\sTage|zwei\sWochen|2\sWochen','14\sTage|zwei\sWochen|2\sWochen|Versagung|Ablehnung|[kK]eine\sZustim[^ ]*|nicht\sgenehmig[^ ]*|nicht\san[ge]*n[^ ]*|nicht\s[zu ]*gewähr[^ ]*|anhören|versag[^ ]*|ab[ge]*lehn[^ ]*|entgegensteh[^ ]*|nicht\serteil[^ ]*|nicht\szu[ge]*stimm[^ ]*']
# a_not_patList=['Baugenehmigungsverfahren','[bB]auordnungsrechtlich','[kK]ein[e]*\sRechtsbehelfsbelehrung','FORMCHECKBOX','Prüfung\smit\sMitzeichnung\sdurch\sLDA','Anhörung[^.]*vom']
# anhoerung=compiler(a_patList,a_not_patList)[0]
# notAnhoerung=compiler(a_patList,a_not_patList)[1]
# ####################################pattern for 'Versagung'
# v_patList=['[dD]+enkmal[en]*[schutz]*[gerechten]*[geschützen]*[rechtliche[rn]*]*\sVersagung|Begründung\sder\sVersagung|Versagung|Ablehnung|[kK]eine\sZustim[^ ]*|kein[en]*\s[dD]+enkmal[en]*[schutz]*[gerechten]*[geschützen]*[rechtliche[rn]*]*|nicht\sgenehmig[^ ]*|nicht\szu\sgewähren|Wider[^ ]*[^.]*zurück[^ ]*','Wider[^ ]*[^.]*zurück[^ ]*|nicht\sgenehmig[^ ]*|nicht\s[zu ]*gewähren|versag[^ ]*|ab[ge]*lehn[^ ]*|entgegensteh[^ ]*|nicht\serteil[^ ]*|nicht\szugestim[^ ]*|nicht\san[ge]*n[^ ]*']
# v_not_patList=['Anhörung(?!\svom)|Anhörung\s[zur]*[der]*[\s]*Versagung(?!\svom)','Auflage[n]*[^\w]','14\sTage|zwei\sWochen|2\sWochen','Baugenehmigungsverfahren', 'bauordnungsrechtlich','[kK]ein\sRechtsbehelfsbelehrung','FORMCHECKBOX','Prüfung\smit\sMitzeichnung\sdurch\sLDA']
# versagung=compiler(v_patList,v_not_patList)[0]
# notVersagung=compiler(v_patList,v_not_patList)[1]
# ####################################pattern for 'Baugenehmigungsverfahren'
# b_patList=['Bau[genehmigungs]*verfahren|Bauvorhaben|Bauvorlage|Bauabnahme|Bauausführung|Bauherr|[bB]auordnungsrechtlich[en]*|Genehmigungsverfahren|Anlage\szur\sBaugenehmigung[sverfahren]*|[kK]ein[e]*\sRechtsbehelfsbelehrung|Anlage\szur\sGenehmigung']
# b_not_patList=['Anhörung','14\sTage|zwei\sWochen|2\sWochen','Versagung','FORMCHECKBOX','Prüfung\smit\sMitzeichnung\sdurch\sLDA']
# bauverfahren=compiler(b_patList,b_not_patList)[0]
# notBauverfahren=compiler(b_patList,b_not_patList)[1]
# ####################################pattern for Antrag
# at_patList=['FORMCHECKBOX|Prüfung\smit\sMitzeichnung\sdurch\sLDA']
# at_not_patList=['kwfjdwe']
# antrag=compiler(at_patList,at_not_patList)[0]
# notAntrag=compiler(at_patList,at_not_patList)[1]
# ####################################pattern for 'Anfrage'
# af_patList=['[Be]*[aA]+ntwort[ung]*[^.]*[fF]+rage|Anfrage|Frage[:]|Antwort[:]']
# af_not_patList=['ksvkajv']
# anfrage=compiler(af_patList,af_not_patList)[0]
# notAnfrage=compiler(af_patList,af_not_patList)[1]
# ###########################################################

document_type = {}
not_document_type = {}

# for dt in document_pattern:
#     document_type[dt] = compiler(document_pattern[dt]["pos"])
#     not_document_type[dt] = notcompiler(document_pattern[dt]["neg"])

def setDocTypePattern(pattern: dict): 
    global document_pattern
    global document_type
    global not_document_type
    document_pattern = pattern
    for dt in document_pattern:
        document_type[dt] = compiler(document_pattern[dt]["pos"])
        not_document_type[dt] = notcompiler(document_pattern[dt]["neg"])

# document_type = {
#   "Genehmigung"           : genehmigung,
#   "Anhörung"              : anhoerung,
#   "Versagung"             : versagung,
#   "Bauverfahren"          : bauverfahren,
#   "Antrag"                : antrag,
#   "Anfrage"               : anfrage,
#   "Nachforderung"         : nachforderung,
#   "Eingang"               : eingang
# }

# not_document_type = {
#     'Nicht-Genehmigung'   : notGenehmigung,
#     'Nicht-Anhörung'      : notAnhoerung,
#     'Nicht-Versagung'     : notVersagung,
#     'Nicht-Bauverfahren'  : notBauverfahren,
#     'Nicht-Antrag'        : notAntrag,
#     'Nicht-Anfrage'       : notAnfrage,
#     "Nicht-Nachforderung" : notNachforderung,
#     "Nicht-Eingang"       : notEingang
# }

#
#         text = text.replace("\n", " ")


def matchFileName(fname: str):
    for dt in document_pattern:
        for pt in document_pattern[dt]["file"]:
            if fname.find(pt) > -1:
                return {dt: ['Dateiname']}
    return []


def allPositiveDocTypes(text: str):
    text = text.replace(u"\n", " ")
    text = text.replace(u"\t", " ")
    text = ' '.join(text.split())
    allList = {}
    for dt in document_pattern:
        allList[dt] = document_type[dt].findall(text)
    return allList

    # #######################################
    # self.genehmigung=genehmigung.findall(self.text)
    # self.allGenehmigung=findAll(g_patList,self.text)
    # # self.notGenehmigung=notGenehmigung.findall(self.text)
    # # self.allNotGenehmigung=findAll(g_not_patList,self.text)
    # #######################################
    # self.anhoerung=anhoerung.findall(self.text)
    # self.allAnhoerung=findAll(a_patList,self.text)
    # # self.notAnhoerung=notAnhoerung.findall(self.text)
    # # self.allNotAnhoerung=findAll(a_not_patList,self.text)
    # #######################################
    # self.versagung=versagung.findall(self.text)
    # self.allVersagung=findAll(v_patList,self.text)
    # # self.notVersagung=notVersagung.findall(self.text)
    # # self.allNotVersagung=findAll(v_not_patList,self.text)
    # #######################################
    # self.bauverfahren=bauverfahren.findall(self.text)
    # self.allBauverfahren=findAll(b_patList,self.text)
    # # self.notBauverfahren=notBauverfahren.findall(self.text)
    # # self.allNotBauverfahren=findAll(b_not_patList,self.text)
    # #######################################
    # self.antrag=antrag.findall(self.text)
    # self.allAntrag=findAll(at_patList,self.text)
    # # self.notAntrag=notAntrag.findall(self.text)
    # # self.allNotAntrag=findAll(at_not_patList,self.text)
    # #######################################
    # self.anfrage=anfrage.findall(self.text)
    # self.allAnfrage=findAll(af_patList,self.text)
    # # self.notAnfrage=notAntrag.findall(self.text)
    # # self.allNotAnfrage=findAll(af_not_patList,self.text)
    # #######################################
    # self.nachforderung=nachforderung.findall(self.text)
    # self.allNachforderung=findAll(n_patList,self.text)
    # # self.notNachforderung=notNachforderung.findall(self.text)
    # # self.allNotNachforderung=findAll(n_not_patList,self.text)
    # #######################################
    # self.eingang=eingang.findall(self.text)
    # self.allEingang=findAll(e_patList,self.text)
    # # self.notEingang=notEingang.findall(self.text)
    # # self.allNotEingang=findAll(e_not_patList,self.text)
    # #######################################
    # self.allList={
    #     'Genehmigung':self.allGenehmigung,
    #     'Anhoerung':self.allAnhoerung,
    #     'Versagung':self.allVersagung,
    #     'Bauverfahren':self.allBauverfahren,
    #     'Antrag':self.allAntrag,
    #     'Anfrage':self.allAnfrage,
    #     'Nachforderung':self.allNachforderung,
    #     'Eingang':self.allEingang
    # }
    #######################################


def allPositiveMatches(text):
    text = text.replace(u"\n", " ")
    text = text.replace(u"\t", " ")
    text = ' '.join(text.split())
    _all = {}
    for k, v in list(document_type.items()):
        match = v.findall(text)
        if match:
            if type(match[0]) == tuple:
                _all[k] = list(filter(None, list(match[0])))
            else:
                _all[k] = [match[0]]
    return _all


def allNegativeMatches(text):
    _all = {}
    for k, v in list(not_document_type.items()):
        match = v.findall(text)
        if match:
            if type(match[0]) == tuple:
                _all[k] = list(filter(None, list(match[0])))
            else:
                _all[k] = [match[0]]
    return _all
    #######################################
# def posAllList(self):
#         _posAllList = {'all':[]}
#         for k,v in list(self.allList.items()):
#             if v:
#                 _posAllList[k]=v
#                 _posAllList['all'].extend(v)
#         _posAllList['all']=list(set(list(self.posAllList['all'])))
#         return _posAllList
#     ######################################

# def allNegativeDocTypes(text: str):
#         text=' '.join(text.split())
#         allList={}
#         for dt in document_pattern:
#             allList[dt]=not_document_type[dt].findall(text)
#         return allList

# class findNotVorgang:
#     def __init__(self, text=""):
#         #######################################remove unecessary spaces
#         text = text.replace("\n", " ")
#         text=' '.join(text.split())
#         self.text = text
#         #######################################
#         # self.genehmigung=genehmigung.findall(self.text)
#         # self.allGenehmigung=findAll(g_patList,self.text)
#         self.notGenehmigung=notGenehmigung.findall(self.text)
#         self.allNotGenehmigung=findAll(g_not_patList,self.text)
#         #######################################
#         # self.anhoerung=anhoerung.findall(self.text)
#         # self.allAnhoerung=findAll(a_patList,self.text)
#         self.notAnhoerung=notAnhoerung.findall(self.text)
#         self.allNotAnhoerung=findAll(a_not_patList,self.text)
#         #######################################
#         # self.versagung=versagung.findall(self.text)
#         # self.allVersagung=findAll(v_patList,self.text)
#         self.notVersagung=notVersagung.findall(self.text)
#         self.allNotVersagung=findAll(v_not_patList,self.text)
#         #######################################
#         # self.bauverfahren=bauverfahren.findall(self.text)
#         # self.allBauverfahren=findAll(b_patList,self.text)
#         self.notBauverfahren=notBauverfahren.findall(self.text)
#         self.allNotBauverfahren=findAll(b_not_patList,self.text)
#         #######################################
#         # self.antrag=antrag.findall(self.text)
#         # self.allAntrag=findAll(at_patList,self.text)
#         self.notAntrag=notAntrag.findall(self.text)
#         self.allNotAntrag=findAll(at_not_patList,self.text)
#         #######################################
#         # self.anfrage=anfrage.findall(self.text)
#         # self.allAnfrage=findAll(af_patList,self.text)
#         self.notAnfrage=notAntrag.findall(self.text)
#         self.allNotAnfrage=findAll(af_not_patList,self.text)
#         #######################################
#         # self.nachforderung=nachforderung.findall(self.text)
#         # self.allNachforderung=findAll(n_patList,self.text)
#         self.notNachforderung=notNachforderung.findall(self.text)
#         self.allNotNachforderung=findAll(n_not_patList,self.text)
#         #######################################
#         # self.eingang=eingang.findall(self.text)
#         # self.allEingang=findAll(e_patList,self.text)
#         self.notEingang=notEingang.findall(self.text)
#         self.allNotEingang=findAll(e_not_patList,self.text)
#         #######################################
#         self.allNotList={
#             'Nicht-Genehmigung':self.allNotGenehmigung,
#             'Nicht-Anhoerung':self.allNotAnhoerung,
#             'Nicht-Versagung':self.allNotVersagung,
#             'Nicht-Bauverfahren':self.allNotBauverfahren,
#             'Nicht-Antrag':self.allNotAntrag,
#             'Nicht-Anfrage':self.allNotAnfrage,
#             'Nicht-Nachforderung':self.allNotNachforderung,
#             'Nicht-Eingang':self.allNotEingang
#         }
#     #######################################
#     def negativAll(self):
#         self.negativAll = {}
#         for k, v in list(not_document_type.items()):
#             match=v.findall(self.text)
#             if match:
#                 if type(match[0])==tuple:
#                     self.negativAll[k]=list(filter(None, list(match[0])))
#                 else:
#                     self.negativAll[k]=[match[0]]
#         return self.negativAll

#     #######################################
#     def negativAllList(self):
#         self.negativAllList = {'all':[]}
#         for k,v in list(self.allNotList.items()):
#             if v:
#                 self.negativAllList[k]=v
#                 self.negativAllList['all'].extend(v)
#         self.negativAllList['all']=list(set(list(self.negativAllList['all'])))
#         return self.negativAllList
#     #######################################
