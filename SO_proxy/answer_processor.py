
class AnswerPocessor():

    def __init__(self, divergent_flag):
        self.is_divergent = divergent_flag

    def extract_possible_answers_conseq(self, relevant_docs, num_answers):
        passages = []
        for doc in relevant_docs:
            for answer in doc['answers']:
                if len(passages) == num_answers:
                    return passages
                passages.append((answer['body'], doc['link']))
        return passages

    def extract_possible_answers_diverg(self, relevant_docs, num_answers):
        passages = []
        has_more_answers = True
        while has_more_answers:
            has_more_answers = False
            for doc in relevant_docs:
                if len(passages) == num_answers:
                    return passages
                elif len(doc['answers']) > 0:
                    answer = (doc['answers'].pop(0))['body']
                    passages.append((answer, doc['link']))
                    has_more_answers = True
        return passages

    def extract_possible_answers(self, relevant_docs, num_answers):
        if self.is_divergent:
            return self.extract_possible_answers_diverg(relevant_docs, num_answers)
        else:
            return self.extract_possible_answers_conseq(relevant_docs, num_answers)
