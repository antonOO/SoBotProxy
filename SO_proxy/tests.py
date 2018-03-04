from django.test import TestCase
from .answer_processor import AnswerPocessor

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
