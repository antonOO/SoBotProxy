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
from .logging_initializer import *


initialize_logger()

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
    in SO; title is 1.5 more
    relevant

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
    index_rank_array = [(index, rank) for index, rank in enumerate(rankings)]
    index_rank_array.sort(key=lambda index_rank: index_rank[1], reverse=True)
    return [index_rank[1] for index_rank in index_rank_array],[documents[index_rank[0]] for index_rank in index_rank_array]


'''
    Prepares the answer response

    params = answer texts with their links as
             an array to string, query to string,
             intent string

    return = the json encapsulation of data above
'''
def prepare_response(passage_link_tuples, query, intent):
    json_answer_response = {
                            'passages' : passage_link_tuples,
                            'query'    : query,
                            'intent'   : intent
    }

    return json_answer_response

def get_answer(request):
    question = request.GET['question']
    entities = eval(request.GET['entities'])
    intent = request.GET['intent']
    confidence = request.GET['confidence']
    num_answers = int(request.GET['num_answers'])
    divergent_flag = eval(request.GET['divergent_flag'])
    direct_search_flag = eval(request.GET['direct_search_flag'])

    print(question)


    '''
        The information extracted (entities) should be sufficient
        enough to formulate a generic_query. Also, the (entities)
        exctracted information should be relevant to the question.
    '''
    generic_query = " ".join(entity[0] for entity in entities)
    print(generic_query)

    if ((len(generic_query.split()) < settings.MINIMAL_NUMBER_OF_ENTITIES) or #not (are_entities_legitimate(entities, question)
        settings.MINIMUM_INFORMATION_ACQUIRED >= float(len(generic_query.split())/len(question.split())) or
        direct_search_flag):
        generic_query = question
        logging.warning("Matching against stopword removed question!")
    programming_terms = "; ".join([entity[0] for entity in entities if "programming" in entity[1]])


    json_search_data = get_search_data(settings.SIMILAR_QUESTION_FILTER, programming_terms, generic_query)

    if 'items' not in json_search_data:
        return JsonResponse(prepare_response("['Cannot find an answer']", str(generic_query), intent))

    question_corpora = [item for item in json_search_data['items'] if "answers" in item and len(item['answers']) > 0 ]
    if len(json_search_data['items']) == 0 or len(question_corpora) == 0:
        return JsonResponse(prepare_response("['Cannot find an answer']", str(generic_query), intent))

    '''
        Perform question matching and append the answers
        based on question to question relevancy -
        answers from the most relevant questions are
        first in the array.
    '''

    scores = get_bm25_combined(question_corpora, generic_query)
    if question != generic_query and len(question.split()) == len(generic_query.split()):
        question_scores = get_bm25_combined(question_corpora, question)

        print(str(max(scores)) + " " + str(max(question_scores)))

        '''
            There might be more similar documents to the
            exact question itself, rather than the
            generic query.
        '''

        if max(question_scores) > max(scores):
            scores = question_scores
            generic_query = question
            logging.warning("Matching against stopword removed query - more similar questions to parsed question!")

    relevant_docs = question_corpora
    if not direct_search_flag:
        scores, relevant_docs = get_relevancy_sorted_docs(scores, question_corpora)

    print([doc["title"] for doc in relevant_docs])
    answer_proc = AnswerPocessor(divergent_flag, scores)
    passages = answer_proc.extract_possible_answers(relevant_docs, num_answers)

    return JsonResponse(prepare_response(str(passages), str(generic_query), intent))


def update_training_data_negative(request):
    query = request.GET['query']
    answer = request.GET['answer']
    intent = request.GET['intent']
    bm25_score = request.GET['bm25_score']
    qscore = request.GET['qscore']
    ascore = request.GET['ascore']
    view_count = request.GET['view_count']
    is_accepted = request.GET['is_accepted']

    aqs = AnswerQueryScaler(answer, query, intent)
    print(aqs.intent_score())
    trainingData = TrainingData(exact_match = aqs.get_exact_match(),
                                term_overlap = aqs.term_overlap_over_length(),
                                answer_length = aqs.answer_length(),
                                semantic_score = aqs.tagme_relatedness(),
                                has_code = aqs.has_code,
                                bm25_qrelevance = float(bm25_score),
                                intent = aqs.intent_score(),
                                qscore = qscore,
                                ascore = ascore,
                                view_count = view_count,
                                is_accepted_answer = int(eval(is_accepted)),
                                label = -1)
    trainingData.save()
    return HttpResponse("Successfull update!")

def update_training_data_positive(request):
    query = request.GET['query']
    answer = request.GET['answer']
    intent = request.GET['intent']
    bm25_score = request.GET['bm25_score']
    qscore = request.GET['qscore']
    ascore = request.GET['ascore']
    view_count = request.GET['view_count']
    is_accepted = request.GET['is_accepted']

    aqs = AnswerQueryScaler(answer, query, intent)

    trainingData = TrainingData(exact_match = aqs.get_exact_match(),
                                term_overlap = aqs.term_overlap_over_length(),
                                answer_length = aqs.answer_length(),
                                semantic_score = aqs.tagme_relatedness(),
                                has_code = aqs.has_code,
                                bm25_qrelevance = float(bm25_score),
                                intent = aqs.intent_score(),
                                qscore = qscore,
                                ascore = ascore,
                                view_count = view_count,
                                is_accepted_answer = int(eval(is_accepted)),
                                label = 1)
    trainingData.save()
    return HttpResponse("Successfull update!")
