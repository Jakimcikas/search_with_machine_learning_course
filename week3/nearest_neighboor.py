import re
from nltk.stem import SnowballStemmer
import fasttext as ft

stemmer = SnowballStemmer("english")

def transform(name):
    cleaned = re.sub("[^0-9a-zA-Z]+", " ", name.replace("\n", " ")).lower()
    return " ".join([stemmer.stem(token) for token in cleaned.split()])


if __name__ == "__main__":
    tests = []
    with open("/workspace/search_with_machine_learning_course/week3/tests.txt") as f:
        test_cases = f.readlines()
        tests = [transform(tc) for tc in test_cases]

    model = ft.load_model('/workspace/datasets/fasttext/title_model.bin')

    for t in tests:
        prediction = model.get_nearest_neighbors(t)
        print(f"test case: {t}\n{prediction}")
