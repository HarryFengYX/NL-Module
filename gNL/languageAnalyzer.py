# Imports the Google Cloud client library
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
import sys, os
import json
import datetime
import logging

NSUBJ = 28
ROOT = 54
CONJ = 12
PREP = 43
POBJ = 36
VERB = 11
DOBJ = 18
DET = 16
POSS = 37
AMOD = 5
NN = 26

pos = {
    0: "unknown",
    1: "",
    6: "noun",
}

pos = ["unknown", 'adj', 'adp', 'adv', 'conj', 'det', 'noun', 'num', 'pron', 'prt', 'punct', 'verb', 'x', 'affix']

text2conditionDBLocation = "text2conditionDB.json"

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/Harry/Desktop/af/gNL/My_NL.json"

class AnalyzedSentence:
    def __init__(self, ):
        self.root = ""
        self.mvList = []

    def addRoot(self, rootToken):
        self.root = rootToken
        self.mvList.append(self.root)

    def addMV(self, mvToken):
        self.mvList.append(mvToken)

    def __str__(self, ):
        return 

def findRoots(analyzed):
    rootList = []
    for t in analyzed.tokens:
        if t.dependency_edge.label == ROOT and t.part_of_speech.tag == VERB:
            rootList.append(t)
    return rootList

def findConjs(analyzed, tokenList):
    conjList = [[token] for token in tokenList] # main verb list
    for t in analyzed.tokens:
        if t.dependency_edge.label == CONJ:
            for i in range(len(conjList)):
                if conjList[i] == [None]:
                    break
                if analyzed.tokens[t.dependency_edge.head_token_index] == tokenList[i]:
                    conjList[i].append(t)
    return conjList

def findNsubjs(analyzed, rootList):
    return findDependent(analyzed, rootList, NSUBJ, unique=True)

def findDependent(analyzed, depList, label=None, unique=False, notLabels=None):
    #find elements that both depend on elements of dep and have certain kind of label
    foundList = []
    for dep in depList:
        found = False
        foundDepList = []
        for t in analyzed.tokens:
            logics = [True]
            if label != None:
                logics.append(t.dependency_edge.label == label)
            elif notLabels != None:
                logics.append(t.dependency_edge.label not in notLabels)
            if set(logics) == {True}:
                if analyzed.tokens[t.dependency_edge.head_token_index] == dep:
                    found = True
                    foundDepList.append(t)
        if found == False:
            foundDepList.append(None)
        if unique:
            foundList.append(foundDepList[0])
        else:
            foundList.append(foundDepList)
    return foundList

def findConditions(analyzed, mainVerbs):
    # main verbs are all the main verbs in a sentence
    mvDictList = []
    conditions = findDependent(analyzed, mainVerbs, notLabels=[NSUBJ, ROOT])
    for i in range(len(mainVerbs)):
        mvDictList.append({"lemma": mainVerbs[i].lemma, "conditions": [analyzeCondition(analyzed, c) for c in conditions[i]]})
    return mvDictList

def analyzeCondition(analyzed, condition):
    # i guess the purpose is to find out what is the object and what is time and such
    conditionDict = {}
    if condition.dependency_edge.label == DOBJ:
        # conditionDict["object"] = condition.lemma
        conditionDict["object"] = {"lemma": condition.lemma, "description": findDescriptions(analyzed, condition)}
    elif condition.dependency_edge.label == PREP:
        # conditionDict["other"] = condition.lemma
        conditionDict["other"] = {"lemma": condition.lemma, "description": completePrep(analyzed, condition)}
    else:
        conditionDict["unknown"] = condition.lemma
        conditionDict["label"] = condition.dependency_edge.label
    return conditionDict

def findDescriptions(analyzed, noun):
    return token2info(analyzed, noun, [NSUBJ, DET])

def completePrep(analyzed, prep):
    return token2info(analyzed, prep, [NSUBJ, DET])

def token2info(analyzed, token, notLabels=None, recursive=False):
    tokenDictList = []
    deps = findDependent(analyzed, [token], notLabels=notLabels)[0]
    try:
        if set(deps) == {None}:
            return None
    except TypeError:
        pass
    for d in deps:
        if d.dependency_edge.label == POSS:
            condition = "whose"
        elif d.dependency_edge.label in [POBJ, DOBJ]:
            condition = text2condition(d.lemma.encode())
            if condition == None: condition = "object"
        elif d.dependency_edge.label == AMOD:
            # condition = "adjective"
            condition = "description"
        elif d.dependency_edge.label == PREP:
            condition = "prep"
        elif d.dependency_edge.label == NN:
            condition = "description"
        else:
            condition = "dependency"
        if recursive:
            nextDeps = token2info(analyzed, d, notLabels, recursive)
            if nextDeps != None:
                tokenDictList.append({"lemma": d.lemma, "condition": condition, "dependencies": nextDeps, "pos tag": pos[d.part_of_speech.tag]})
            else:
                tokenDictList.append({"lemma": d.lemma, "condition": condition, "pos tag": pos[d.part_of_speech.tag]})
        else:
            tokenDictList.append({"lemma": d.lemma, "condition": condition, "pos tag": pos[d.part_of_speech.tag]})
    return tokenDictList

def findAll(analyzed):
    # get main verbs
    rootList = findRoots(analyzed)
    # as there are conjunctions like a is blah, and b is blah, it is better to treat them
    # as two sentences and the main verb for the not first will be subroot
    # the grammar rules aren't clear to me so far, but i think it should be find ", conj", then find the verbs depend on the root
    mvList = findConjs(analyzed, rootList)
    # get main subjects
    nsubjList = findNsubjs(analyzed, rootList)
    msList = findConjs(analyzed, nsubjList)
    # get conditions
    sentenceList = []
    for i in range(len(rootList)):
        sentence = {
            'root': tokenText(rootList[i]),
            'main verbs': listInfo(analyzed, mvList[i], notLabels=[DET, NSUBJ, ROOT]),
            'nsubj': tokenText(nsubjList[i]),
            'main subjects': listInfo(analyzed, msList[i], notLabels=[DET]),
        }
        sentenceList.append(sentence)

    return sentenceList

def tokenText(token):
    if token != None:
        return token.text.content.encode()
    else:
        return "None"

def tokenLemma(token):
    if token != None:
        return token.lemma.encode()
    else:
        return None

def tokenListText(tokenList):
    return [tokenText(t) for t in tokenList]

def listInfo(analyzed, tokenList, notLabels=None):
    tokenInfoList = []
    for token in tokenList:
        if token != None:
            dep = token2info(analyzed, token, notLabels=notLabels, recursive=True)
            if dep != None:
                tokenInfoList.append({"lemma": token.lemma, "dependencies": token2info(analyzed, token, notLabels=notLabels, recursive=True)})
            else:
                tokenInfoList.append({"lemma": token.lemma})
        else:
            tokenInfoList.append(None)
    return tokenInfoList

def text2condition(text, ):
    if text in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
        return "day"
    elif text in ["breakfast", "brunch", "lunch", "dinner", ]:
        return "meal"
    else:
        return None

# Instantiates a client
client = language.LanguageServiceClient()

logging.basicConfig(filename='lang.log', level=logging.DEBUG, format='%(asctime)-15s %(message)s')

# The text to analyze
if len(sys.argv) < 3:
    logging.info("running by myself")
    text = u'Google and Andy, headquartered in Mountain View, unveiled and uncovered the new Android phone at the Consumer Electronic Show.  Sundar Pichai said in his keynote that users love their new Android phones.'
    text = u"it is lunch time. find the dinning menu"
    outputFile = "output.json"
else:
    logging.info("running by other")
    text = sys.argv[1].decode('utf-8')
    outputFile = sys.argv[2]
    os.chdir(os.path.dirname(sys.argv[0]))

document = types.Document(
    content=text,
    type=enums.Document.Type.PLAIN_TEXT)

# Detects the sentiment of the text
analyzed = client.analyze_syntax(document=document)

sentenceList = findAll(analyzed)
with open(outputFile, "w+") as fp:
    fp.write(json.dumps(sentenceList))