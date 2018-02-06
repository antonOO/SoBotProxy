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


'''

'''
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
Get bm25 rankings between a SO
question and a query, depending
on a question corpora

params = question corpora - array
        of tokenized docs, query
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


def extract_possible_answers(relevant_docs, num_answers):
    passages = []
    for doc in relevant_docs:
        for answer in doc["answers"]:
            if len(passages) == num_answers:
                return passages
            passages = passages + split_to_passages(answer["body"])

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
    num_answers = int(request.GET['num_answers'])

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
    print(len(json_search_data['items']))
    if len(json_search_data['items']) == 0:
        json_answer_response = {
                                'passages' : "['Cannot find and answer']",
                                'query'    : str(generic_query)
        }
        return JsonResponse(json_answer_response)

    max_score = 0

    passages = []
    question_corpora = []

    for item in json_search_data['items']:
        if "answers" in item and len(item['answers']) > 0:
            question_corpora.append(item)


                                                 #question
    scores = get_bm25_combined(question_corpora, generic_query)
    print(scores)
    relevant_docs = get_relevancy_sorted_docs(scores, question_corpora)
    print(len(relevant_docs))
    print([doc["title"] for doc in relevant_docs])
    passages = extract_possible_answers(relevant_docs, num_answers)

    json_answer_response = {
                            'passages' : str(passages),
                            'query'    : str(generic_query)
    }

    return JsonResponse(json_answer_response)


def update_training_data(request):
    return HttpResponse("Successfully updated")
