import requests
import re
import json
from django.conf import settings
import itertools

class AnswerQueryScaler():

    def __init__(self, answer, query):
        code_block = re.compile('```(?s).*```')
        m = code_block.search(answer)
        self.has_code = False
        if m:
            self.has_code = True
        self.answer = code_block.sub("", answer)
        self.query = query

    def __get_tagged_page_ids(self, part):
        tag_url = (settings.TAGME_TAG_URI % { "text" : part })
        response_tags = requests.get(tag_url)
        json_data = json.loads(response_tags.text)
        page_ids = []
        if 'annotations' in json_data:
            for annotation in json_data['annotations']:
                page_ids.append(annotation['id'])
        return page_ids


    def get_exact_match(self):
        return int(self.query in self.answer)

    def term_overlap_over_length(self):
        existent_terms_score = 0
        for word in self.query.split():
            if word in self.answer:
                existent_terms_score += 1
        return existent_terms_score/len(self.answer.split())

    def answer_length(self):
        return len(self.answer.split())

    def tagme_relatedness(self):
        query_ids = self.__get_tagged_page_ids(self.query)
        answer_ids = self.__get_tagged_page_ids(self.answer)

        ids_couple_str_arr = [("id=" + str(qid) + " " + str(aid)) for (qid, aid) in itertools.product(query_ids, answer_ids)]
        ids_couple_str = "&".join(ids_couple_str_arr)

        rel_url = (settings.TAGME_RELATEDNESS_URI % { 'ids' : ids_couple_str })
        response_data = requests.get(rel_url)
        json_relevancy_data = json.loads(response_data.text)

        score = 0
        couples_found = 0

        if 'result' in json_relevancy_data:
            for result in json_relevancy_data['result']:
                score += float(result['rel'])
                couples_found +=1

        if couples_found:
            return score/couples_found
        else:
            return 0
