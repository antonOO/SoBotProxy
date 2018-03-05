from django.test import TestCase
from .answer_processor import AnswerPocessor
from .answer_query_scaler import AnswerQueryScaler
from . import views
from django.core.urlresolvers import reverse


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
                    'body' : """Python is a language supporting classes and hierarchies.
                                OOP in python is a commong practice, even inheritence
                                is supported. Why isnt this working"""
                },
                {
                    'title' : "Unikernels are the new trend",
                    'body' : """Unikernels are minimalistic virtual machines,
                                which are perfect for microservices, ultra secure,
                                easy to deploy and are super fast. Consider them."""
                }
              ]

        self.update_training_data = {
                                        'query' : "query",
                                        'answer' : "answer",
                                        'intent' : "programming_procedure",
                                        'bm25_score' : "5",
                                        'qscore' : "6",
                                        'ascore' : "7",
                                        'view_count' : "8",
                                        'is_accepted' : "True",
                                        'uid' : "123"
                                    }


    def test_stip_text(self):
        self.assertEqual(views.strip_text("&.oss;Hi"), "hi")

    def test_get_bm25_ranking(self):
        scores = views.get_bm25_rankings(self.docs, "python classes", "body")
        self.assertEqual(len(scores), 3)
        self.assertEqual(scores[1] > scores[0] and scores[1] > scores[2], True)

    def test_get_bm25_combined(self):
        scores = views.get_bm25_combined(self.docs, "python classes")
        self.assertEqual(len(scores), 3)
        self.assertEqual(scores[1] > scores[0] and scores[1] > scores[2], True)

    def test_relevancy_sorted_docs(self):
        scores = views.get_bm25_combined(self.docs, "python classes")
        scores, docs = views.get_relevancy_sorted_docs(scores, self.docs)
        self.assertEqual(docs[0]['title'], "Python classes and OOP")
        self.assertEqual(scores[0] > scores[1] and scores[0] > scores[2], True)

    def test_update_training_data_positive(self):
        response = self.client.get(reverse('update_training_data_positive'), self.update_training_data)
        self.assertEqual("Successfull" in str(response.content), True)
        response = self.client.get(reverse('update_training_data_positive'), self.update_training_data)
        self.assertEqual("already exists" in str(response.content), True)

    def test_update_training_data_negative(self):
        response = self.client.get(reverse('update_training_data_negative'), self.update_training_data)
        self.assertEqual("Successfull" in str(response.content), True)
        response = self.client.get(reverse('update_training_data_negative'), self.update_training_data)
        self.assertEqual("already exists" in str(response.content), True)

    def test_poll_data_csv(self):
        response = self.client.get(reverse('poll_data_csv'))
        self.assertEqual("Successfull" in str(response.content), True)

    def test_get_answer(self):
        response = self.client.get(reverse('get_answer'))
        self.assertEqual("Wrong input" in str(response.content), True)
