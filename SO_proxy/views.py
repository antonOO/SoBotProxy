from django.shortcuts import render
import requests
import re
import json
from django.http import JsonResponse
from gensim.summarization.bm25 import BM25
from gensim import corpora
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from random import shuffle
from .answer_processor import *
from .answer_query_scaler import AnswerQueryScaler
from .models import TrainingData

'''
    Get the search data from SO

    params = specific search url (custom filter
             as defined in SO) String, array of
             Strings indicating tags -
             programming terms, a String value
             which appears in the retreaved
             answers

    return = data from SO
'''
def get_search_data(search_query, programming_terms, intitle = ""):
    url_query = (search_query % {"tags" : programming_terms, "intitle" : intitle})
    print(url_query)
    response = requests.get(url_query)
    return json.loads(response.text)

'''
    Remove unwanted symbols
    returned by SO

    params = String text

    return = stripped text
'''
def strip_text(text):
    text = text.lower()
    text = re.sub('&.{3,6};', "", text)
    return re.sub('[^0-9a-zA-Z ]+', "", text)

'''
    Check if ML extracted entities
    match coherently the question

    params = list String ents,
             question

    return = boolean flag
'''
def are_entities_legitimate(entities, question):
    for entity in entities:
        if not (entity[0] in question):
            return False
    return True

'''
    Get bm25 rankings between a SO
    question and a query, depending
    on a question corpora

    params = question corpora - array
            of SO tokenized docs, query
            String, question part
            indicating whether it is
            the question title or body

    return = an array of floats - scores,
            each index corresponding to
            the doc in the question
            corpora - its score
'''
def get_bm25_rankings(question_corpora, query_doc, question_part):
    parsed_query_doc = [word for word in query_doc.split()]
    parsed_qcorpora = [[word for word in strip_text(question[question_part]).split()] for question in question_corpora]
    dictionary = corpora.Dictionary(parsed_qcorpora)
    tokenized_qcorpora = [dictionary.doc2bow([word for word in strip_text(question[question_part]).split()]) for question in question_corpora]
    tokenized_query_doc = dictionary.doc2bow(parsed_query_doc)
    bm25 = BM25(tokenized_qcorpora)
    average_idf = sum(map(lambda k: float(bm25.idf[k]), bm25.idf.keys())) / len(bm25.idf.keys())
    return bm25.get_scores(tokenized_query_doc, average_idf)


'''
    A bm25 scorer of the title
    and the body of a question
    in SO

    params = question corpora, query

    return = scores
'''
def get_bm25_combined(question_corpora, query_doc):
    scores_body = get_bm25_rankings(question_corpora, query_doc, "body")
    scores_title = get_bm25_rankings(question_corpora, query_doc, "title")
    return [scores_body[i] + scores_title[i] for i in range(len(scores_body))]


'''
    Sort the array of documents
    based on their BM25 score

    params = the array of bm25 scores,
             the document corpora array

    return = the sorted document
             corpora array
'''
def get_relevancy_sorted_docs(rankings, documents):
    print(max(rankings))
    index_rank_array = [(index, rank) for index, rank in enumerate(rankings)]
    index_rank_array.sort(key=lambda index_rank: index_rank[1], reverse=True)
    return [documents[index_rank[0]] for index_rank in index_rank_array]


def get_answer(request):
    question = request.GET['question']
    entities = eval(request.GET['entities'])
    intent = request.GET['intent']
    confidence = request.GET['confidence']
    num_answers = int(request.GET['num_answers'])
    divergent_flag = eval(request.GET['divergent_flag'])

    '''
        The information extracted (entities) should be sufficient
        enough to formulate a generic_query. Also, the (entities)
        exctracted information should be relevant to the question.
    '''
    generic_query = " ".join(entity[0] for entity in entities)
    if (len(generic_query.split()) >= settings.MINIMAL_NUMBER_OF_ENTITIES) and not (are_entities_legitimate(entities, question)):
        generic_query = question
    programming_terms = "; ".join([entity[0] for entity in entities if "programming" in entity[1]])


    json_search_data = get_search_data(settings.SIMILAR_QUESTION_FILTER, programming_terms, generic_query)
    question_corpora = [item for item in json_search_data['items'] if "answers" in item and len(item['answers']) > 0 ]
    if len(json_search_data['items']) == 0 or len(question_corpora) == 0:
        json_answer_response = {
                                'passages' : "['Cannot find and answer']",
                                'query'    : str(generic_query)
        }
        return JsonResponse(json_answer_response)

    '''
        Perform question matching and append the answers
        based on question to question relevancy -
        answers from the most relevant questions are
        first in the array.
    '''
    scores = get_bm25_combined(question_corpora, generic_query)
    question_scores = get_bm25_combined(question_corpora, question)

    '''
        There might be more similar documents to the
        exact question itself, rather than the
        generic query.
    '''
    '''
    if max(question_scores) > max(scores):
        scores = question_scores
        generic_query = question
    '''

    relevant_docs = get_relevancy_sorted_docs(scores, question_corpora); print([doc["title"] for doc in relevant_docs])

    answer_proc = AnswerPocessor(divergent_flag)
    passages = answer_proc.extract_possible_answers(relevant_docs, num_answers)

    json_answer_response = {
                            'passages' : str(passages),
                            'query'    : str(generic_query)
    }

    return JsonResponse(json_answer_response)


def update_training_data_negative(request):
    query = request.GET['query']
    answer = request.GET['answer']
    print(query)
    aqs = AnswerQueryScaler(answer, query)
    print(aqs.has_code)
    print(aqs.tagme_relatedness())
    trainingData = TrainingData(exact_match = aqs.get_exact_match(), label = -1)
    trainingData.save()
    return HttpResponse("Successfull update!")

def update_training_data_positive(request):
    query = request.GET['query']
    answer = request.GET['answer']
    print(query)
    aqs = AnswerQueryScaler(answer, query)
    trainingData = TrainingData(exact_match = aqs.get_exact_match(), label = 1)
    trainingData.save()
    return HttpResponse("Successfull update!")
