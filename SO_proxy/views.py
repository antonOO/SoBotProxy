from django.shortcuts import render
import requests
import re
import json
from gensim.summarization.bm25 import BM25
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_protect

'''
def split_to_passages(text):
    passages = []
    while(True):
        m = re.search('<code>(.+?)</code>')
        if m:
            passages.append(m.group(1))
            text = text.replace(m.group(1), "")
        else:
            break
    passages.append(text.splitlines())
    return passages '''

def get_search_data(programming_terms):
    url_query = (settings.SO_CUSTOM_FILTER % {"query" : programming_terms})
    response = requests.get(url_query)
    return json.loads(response.text)


def get_bm25_rankings(question_corpora, query_doc):
    parsed_query_doc = [word for word in query_doc.split()]
    tokenized_qcorpora = [[word for word in question.split()] for question in question_corpora]
    bm25 = BM25(tokenized_qcorpora)
    average_idf = sum(map(lambda k: float(bm25.idf[k]), bm25.idf.keys())) / len(bm25.idf.keys())
    return bm25.get_scores(parsed_query_doc, average_idf)



def get_answer(request):
    question = request.GET['question']
    entities = eval(request.GET['entities'])
    intent = request.GET['intent']
    confidence = request.GET['confidence']

    print(str(entities))

    similarity_terms = " ".join(entity[0] for entity in entities)
    programming_terms = "; ".join([entity[0] for entity in entities if "programming" in entity[1]])
    json_search_data = get_search_data(programming_terms)

    question_string = "Cannot find question ..."
    answer_string = "Cannot find an answer ..."

    max_score = 0

    passages = []
    question_corpora = []

    for item in json_search_data["items"]:
        question_corpora.append(item["title"])

        '''for answer in item["answers"]:
            if answer["is_accepted"] and answer["score"] > max_score:
                answer_string = answer["body"]'''

    scores = get_bm25_rankings(question_corpora, similarity_terms)
    return HttpResponse(str(scores))
