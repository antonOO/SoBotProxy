class AnswerQueryScaler():

    def __init__(self, answer, query):
        self.answer = answer
        self.query = query

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
