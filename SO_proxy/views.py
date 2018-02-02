from django.shortcuts import render
import requests
import re
import json
from gensim.summarization.bm25 import BM25
from gensim import corpora
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
    print(url_query)
    response = requests.get(url_query)
    return json.loads(response.text)

def strip_text(text):
    text = text.lower()
    text = re.sub('&.{3,6};', "", text)
    return re.sub('[^0-9a-zA-Z ]+', "", text)


def get_bm25_rankings(question_corpora, query_doc, question_part):
    parsed_query_doc = [word for word in query_doc.split()]
    parsed_qcorpora = [[word for word in strip_text(question[question_part]).split()] for question in question_corpora]
    dictionary = corpora.Dictionary(parsed_qcorpora)
    tokenized_qcorpora = [dictionary.doc2bow([word for word in strip_text(question[question_part]).split()]) for question in question_corpora]
    tokenized_query_doc = dictionary.doc2bow(parsed_query_doc)
    bm25 = BM25(tokenized_qcorpora)
    average_idf = sum(map(lambda k: float(bm25.idf[k]), bm25.idf.keys())) / len(bm25.idf.keys())
    return bm25.get_scores(tokenized_query_doc, average_idf)

def get_bm25_combined(question_corpora, query_doc):
    scores_body = get_bm25_rankings(question_corpora, query_doc, "body")
    scores_title = get_bm25_rankings(question_corpora, query_doc, "title")
    return [scores_body[i] + scores_title[i] for i in range(len(scores_body))]

def get_most_relevant_docs(rankings, documents):
    max_rank = max(rankings)
    highest_rank_indecies = [index for index, rank in enumerate(rankings) if rank == max_rank]
    return [documents[i] for i in highest_rank_indecies]


def extract_possible_answers(relevant_docs):
    passages = []
    for doc in relevant_docs:
        for answer in doc["answers"]:
            passages.append(split_to_passages(answer["body"]))
    #shuffle(passages)
    return passages

def are_entities_legitimate(entities, question):
    for entity in entities:
        if not (entity[0] in question):
            return False
    return True

def get_answer(request):
    question = request.GET['question']
    entities = eval(request.GET['entities'])
    intent = request.GET['intent']
    confidence = request.GET['confidence']
    num_answers = int(request.get['num_answers'])

    print(entities)
    '''
        The information extracted should be sufficient
        enough to formulate a generic_query. Also, the
        exctracted information should be relevant to
        the question.
    '''
    generic_query = " ".join(entity[0] for entity in entities)
    if (len(generic_query.split()) >= settings.MINIMAL_NUMBER_OF_ENTITIES) and not (are_entities_legitimate(entities, question)):
        generic_query = question
    programming_terms = "; ".join([entity[0] for entity in entities if "programming" in entity[1]])

    ''' '''
    json_search_data = get_search_data(settings.SIMILAR_QUESTION_FILTER, programming_terms, generic_query)
    if len(json_search_data['items']) == 0:
        return HttpResponse("Cannot find an answer ...")

    max_score = 0

    passages = []
    question_corpora = []

    for item in json_search_data['items']:
        if "answers" in item and len(item['answers']) > 0:
            question_corpora.append(item)
                                                 #question
    scores = get_bm25_combined(question_corpora, generic_query)
    print(scores)
    relevant_docs = get_most_relevant_docs(scores, question_corpora)
    print(len(relevant_docs))
    print([doc["title"] for doc in relevant_docs])
    passages = extract_possible_answers(relevant_docs)
    print(len(passages))
    return HttpResponse(passages[0])
