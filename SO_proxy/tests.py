from django.test import TestCase
from .answer_processor import AnswerPocessor
from .answer_query_scaler import AnswerQueryScaler
from . import views

class AnswerPocessorTests(TestCase):

    def setUp(self):
        self.scores = [1,2]
        self.divergent_flag = False
        self.answer_processor = AnswerPocessor(self.divergent_flag, self.scores)
        self.docs = [{
                        'score' : 1,
                        'view_count' : 1,
                        'link': "link1",
                        'answers' : [{
                                        'body': "abody1-1",
                                        'score' : 1,
                                        'is_accepted' : True,
                                        'answer_id' : 1
                                    },
                                    {
                                        'body' : "abody1-2",
                                        'score' : 2,
                                        'is_accepted' : False,
                                        'answer_id' : 2
                                    }]
                    },
                    {
                        'score' : 1,
                        'view_count' : 1,
                        'link': "link1",
                        'answers' : [{
                                        'body' : "abody2-1",
                                        'score' : 1,
                                        'is_accepted' : True,
                                        'answer_id' : 3
                                    },
                                    {
                                        'body' : "abody2-2",
                                        'score' : 2,
                                        'is_accepted' : False,
                                        'answer_id' : 4
                                    }]
                    }]

    def test_extract_possible_answers_conseq_high_number(self):
        answers = self.answer_processor.extract_possible_answers_conseq(self.docs, 5)
        self.assertEquals(answers.pop()[-1], 4)
        self.assertEquals(answers.pop()[-1], 3)
        self.assertEquals(answers.pop()[-1], 2)
        self.assertEquals(answers.pop()[-1], 1)

    def test_extract_possible_answers_conseq_low_number(self):
        answers = self.answer_processor.extract_possible_answers_conseq(self.docs, 3)
        self.assertEquals(answers.pop()[-1], 3)
        self.assertEquals(answers.pop()[2], '1')

    def test_extract_possible_answers_diverg_high_number(self):
        answers = self.answer_processor.extract_possible_answers_diverg(self.docs, 5)
        self.assertEquals(answers.pop()[-1], 4)
        self.assertEquals(answers.pop()[-1], 2)
        self.assertEquals(answers.pop()[-1], 3)
        self.assertEquals(answers.pop()[-1], 1)

    def test_extract_possible_answers_diverg_low_number(self):
        answers = self.answer_processor.extract_possible_answers_diverg(self.docs, 3)
        self.assertEquals(answers.pop()[-1], 2)
        self.assertEquals(answers.pop()[2], '2')

    def test_extract_possible_answers(self):
        answers = self.answer_processor.extract_possible_answers(self.docs, 3)
        self.assertEquals(answers.pop()[-1], 3)
        self.scores = [1,2]
        self.divergent_flag = True
        self.answer_processor = AnswerPocessor(self.divergent_flag, self.scores)
        answers = self.answer_processor.extract_possible_answers(self.docs, 3)
        self.assertEquals(answers.pop()[-1], 2)


class AnswerQueryScalerTests(TestCase):

    def setUp(self):
        answer = "You can write a for-loop like this ``` for x in arr: ```"
        query = "write a for-loop"
        self.aqs = AnswerQueryScaler(answer, query, "programming_procedure")

    def test_get_exact_match(self):
        self.assertEquals(self.aqs.get_exact_match(), True)

    def test_term_overlap_over_length(self):
        score = 3/len(self.aqs.answer.split())
        self.assertEquals(self.aqs.term_overlap_over_length(), score)

    def test_tagme_relatednes(self):
        self.assertEquals(self.aqs.tagme_relatedness()>0, True)

    def test_intent_score(self):
        self.assertEquals(self.aqs.intent_score(), 2)


class ProxyTests(TestCase):

    def setUp(self):
        self.docs =[
                {
                    'title' : "Java arrays and loop",
                    'body' : """Arrays, while loop and for-loops, are common in Java.
                                Not only in java but in many other programming languages."""
                },
                {
                    'title' : "Python classes and OOP",
                    'body' : """Python is a language supporting class hierarchies.
                                OOP in python is a commong practice, even inheritence
                                is supported. Why isnt this working"""
                }
              ]


    def test_stip_text(self):
        self.assertEqual(views.strip_text("&.oss;Hi"), "hi")

    def test_get_bm25_ranking(self):
        scores = views.get_bm25_rankings(self.docs, "python classes", "body")
        self.assertEqual(len(scores), 2)

    def test_get_bm25_combined(self):
        scores = views.get_bm25_combined(self.docs, "python classes")
        self.assertEqual(len(scores), 2)
