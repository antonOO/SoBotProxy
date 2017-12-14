from django.shortcuts import render
import requests
import json
from django.http import HttpResponse
from django.conf import settings
import stackexchange
from django.views.decorators.csrf import csrf_protect

def get_answer(request):
    question = request.GET['question']
    #so = stackexchange.Site(stackexchange.StackOverflow, app_key=user_api_key, impose_throttling=True)
    so = stackexchange.StackOverflow()
    q = so.search(intitle = question, sort=stackexchange.Sort.Votes, order=stackexchange.DESC)
    qtitle = "Can't find that ..."
    if len(q) > 0 :
        qtitle = q[0].title
        print(qtitle)
    return HttpResponse(qtitle)
