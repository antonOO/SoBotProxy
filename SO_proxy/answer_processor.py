def extract_possible_answers(relevant_docs, num_answers):
    passages = []
    for doc in relevant_docs:
        for answer in doc["answers"]:
            if len(passages) == num_answers:
                return passages
            passages.append(answer["body"])

    #shuffle(passages)
    return passages
