class AnswerPocessor():

    def __init__(self, divergent_flag, scores):
        self.is_divergent = divergent_flag
        self.scores = scores

    def extract_possible_answers_conseq(self, relevant_docs, num_answers):
        passages = []
        for doc in relevant_docs:

            index = relevant_docs.index(doc)
            qscore = doc['score']
            view_count = doc['view_count']

            for answer in doc['answers']:
                if len(passages) == num_answers:
                    return passages

                ascore = answer['score']
                is_accepted = answer['is_accepted']

                passages.append((answer['body'], doc['link'], str(self.scores[index]), qscore, view_count, ascore, is_accepted))
        return passages

    def extract_possible_answers_diverg(self, relevant_docs, num_answers):
        passages = []
        has_more_answers = True
        while has_more_answers:
            has_more_answers = False
            for doc in relevant_docs:

                index = relevant_docs.index(doc)
                qscore = doc['score']
                view_count = doc['view_count']

                if len(passages) == num_answers:
                    return passages
                elif len(doc['answers']) > 0:

                    answer = (doc['answers'].pop(0))
                    answer_body = answer['body']
                    ascore = answer['score']
                    is_accepted = answer['is_accepted']

                    passages.append((answer_body, doc['link'], str(self.scores[index]), qscore, view_count, ascore, is_accepted))
                    has_more_answers = True
        return passages

    def extract_possible_answers(self, relevant_docs, num_answers):
        if self.is_divergent:
            return self.extract_possible_answers_diverg(relevant_docs, num_answers)
        else:
            return self.extract_possible_answers_conseq(relevant_docs, num_answers)
