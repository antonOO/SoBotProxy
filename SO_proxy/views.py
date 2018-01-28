from django.shortcuts import render
import requests
import re
import json
from gensim.summarization.bm25 import BM25
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from random import shuffle


def split_to_passages(text):
    '''passages = []
    while(True):
        m = re.search('<code>(.+?)</code>', text)
        if m:
            passages.append(m.group(1))
            text = text.replace(m.group(1), "")
        else:
            break
    passages.append(text.splitlines())'''
    passages = []
    passages.append(text)
    return passages

def get_search_data(search_query, programming_terms, intitle = ""):
    url_query = (search_query % {"tags" : programming_terms, "intitle" : intitle})
    response = requests.get(url_query)
    return json.loads(response.text)


def get_bm25_rankings(question_corpora, query_doc):
    parsed_query_doc = [word for word in query_doc.split()]
    tokenized_qcorpora = [[word for word in question['title'].split()] for question in question_corpora]
    bm25 = BM25(tokenized_qcorpora)
    average_idf = sum(map(lambda k: float(bm25.idf[k]), bm25.idf.keys())) / len(bm25.idf.keys())
    return bm25.get_scores(parsed_query_doc, average_idf)


def get_most_relevant_docs(rankings, documents):
    max_rank = max(rankings)
    highest_rank_indecies = [index for index, rank in enumerate(rankings) if rank == max_rank]
    return [documents[i] for i in highest_rank_indecies]


def extract_possible_answers(relevant_docs):
    passages = []
    for doc in relevant_docs:
        for answer in doc["answers"]:
            passages.append(split_to_passages(answer["body"]))
    shuffle(passages)
    return passages


def get_answer(request):
    question = request.GET['question']
    entities = eval(request.GET['entities'])
    intent = request.GET['intent']
    confidence = request.GET['confidence']

    print(str(entities))

    similarity_terms = " ".join(word for word in question)
    programming_terms = "; ".join([entity[0] for entity in entities if "programming" in entity[1]])

    #Query SO for similar information to the question.
    json_search_data = get_search_data(settings.SIMILAR_QUESTION_FILTER, programming_terms, question)
    if len(json_search_data['items']) == 0:
        return HttpResponse("Cannot find an answer ...")

    max_score = 0

    passages = []
    question_corpora = []

    for item in json_search_data['items']:
        if "answers" in item and len(item['answers']) > 0:
            question_corpora.append(item)

    scores = get_bm25_rankings(question_corpora, similarity_terms)
    relevant_docs = get_most_relevant_docs(scores, question_corpora)

    passages = extract_possible_answers(relevant_docs)
    print(len(passages))
    return HttpResponse(passages[0])
