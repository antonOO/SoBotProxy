from django.shortcuts import render
import requests
import json
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_protect

#returns document score
#def bm25(query, document):


def get_answer(request):

    question = request.GET['question']
    entities = eval(request.GET['entities'])
    intent = request.GET['intent']
    confidence = request.GET['confidence']


    url_query = (settings.SO_CUSTOM_FILTER % {"query" : question})
    response = requests.get(url_query)
    json_search_data = json.loads(response.text)

    question_string = "Cannot find question ..."
    answer_string = "Cannot find an answer ..."
    max_score = 0

    for item in json_search_data["items"]:
        #question_string = item["body"]
        for answer in item["answers"]:
            if answer["is_accepted"] and answer["score"] > max_score:
                answer_string = answer["body"]

    return HttpResponse(answer_string)
