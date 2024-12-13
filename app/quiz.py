class Answer:
    def __init__(self, text: str, correct: bool) -> None:
        self.text = text
        self.correct = correct

class Question:
    def __init__(self, text: str, answers: list[Answer], cost: int) -> None:
        self.text = text
        self.answers = answers
        self.cost = cost



