from flask import Flask, request, jsonify, render_template
import nltk
import ssl
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from collections import Counter
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import wordnet as wn
from nltk.sentiment import SentimentIntensityAnalyzer

# Set the NLTK data path
nltk.data.path.append("nltk_data")  # Ensure this points to your nltk_data directory

# Download the necessary NLTK data if not already downloaded
try:
    nltk.data.find("corpora/stopwords.zip")
    nltk.data.find("corpora/wordnet.zip")
    nltk.data.find("tokenizers/punkt.zip")
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    ssl._create_default_https_context = ssl._create_unverified_context
    nltk.download('stopwords', download_dir="nltk_data")
    nltk.download('wordnet', download_dir="nltk_data")
    nltk.download('punkt', download_dir="nltk_data")
    nltk.download('vader_lexicon', download_dir="nltk_data")

app = Flask(__name__)

def preprocess_answer(answer):
    answer = answer.lower()
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(answer)
    tokens_without_punctuation = [token for token in tokens if token not in string.punctuation]
    stop_words = set(stopwords.words('english'))
    tokens_without_stopwords = [token for token in tokens_without_punctuation if token not in stop_words]
    return tokens_without_stopwords

def extract_keywords(tokens):
    word_counts = Counter(tokens)
    keywords = word_counts.most_common(5)
    return [keyword for keyword, _ in keywords]

def calculate_cosine_similarity(student_answer, reference_answer):
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform([student_answer, reference_answer])
    similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
    return similarity

def calculate_keyword_matching(student_tokens, reference_tokens):
    common_keywords = set(student_tokens) & set(reference_tokens)
    matching_score = len(common_keywords) / len(reference_tokens) if reference_tokens else 0
    return matching_score

def calculate_semantic_similarity(student_tokens, reference_tokens):
    similarity_scores = []
    for token1 in student_tokens:
        max_similarity = -1
        for token2 in reference_tokens:
            synset1 = wn.synsets(token1)
            synset2 = wn.synsets(token2)
            if synset1 and synset2:
                similarity = max((s1.path_similarity(s2) or 0) for s1 in synset1 for s2 in synset2)
                if similarity is not None and similarity > max_similarity:
                    max_similarity = similarity
        if max_similarity != -1:
            similarity_scores.append(max_similarity)
    average_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
    return average_similarity

def calculate_sentiment_polarity(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_score = analyzer.polarity_scores(text)
    polarity = sentiment_score['compound']
    return polarity

def calculate_marks(scores, grading_criteria):
    max_score = sum(grading_criteria[measure]['weight'] for measure in grading_criteria)
    total_marks = sum(score * grading_criteria[measure]['weight'] for measure, score in scores.items())
    percentage = (total_marks / max_score) * 100
    return percentage

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    students = data['students']
    questions = data['questions']
    answers = data['answers']
    gpt_answers = data['gpt_answers']
    textbook_answers = data['textbook_answers']

    graded_answers = {}
    grading_criteria = {
        'Cosine Similarity': {'weight': 1},
        'Keyword Matching': {'weight': 1},
        'Semantic Similarity': {'weight': 1},
        'Contradiction Detection': {'weight': 1}
    }

    for question_index, (question, question_answers) in enumerate(zip(questions, answers)):
        gpt_answer = gpt_answers[question_index]
        gpt_tokens = preprocess_answer(gpt_answer)
        gpt_keywords = extract_keywords(gpt_tokens)

        textbook_answer = textbook_answers[question_index]
        textbook_tokens = preprocess_answer(textbook_answer)
        textbook_keywords = extract_keywords(textbook_tokens)

        answer_scores = {}
        for answer_index, answer in enumerate(question_answers):
            tokens = preprocess_answer(answer)
            keywords = extract_keywords(tokens)

            # GPT Scores
            gpt_cosine_similarity_score = calculate_cosine_similarity(answer, gpt_answer)
            gpt_keyword_matching_score = calculate_keyword_matching(tokens, gpt_tokens)
            gpt_semantic_similarity_score = calculate_semantic_similarity(tokens, gpt_tokens)
            gpt_contradiction_detection_score = 1 if calculate_sentiment_polarity(answer) * calculate_sentiment_polarity(gpt_answer) >= 0 else 0

            # Textbook Scores
            textbook_cosine_similarity_score = calculate_cosine_similarity(answer, textbook_answer)
            textbook_keyword_matching_score = calculate_keyword_matching(tokens, textbook_tokens)
            textbook_semantic_similarity_score = calculate_semantic_similarity(tokens, textbook_tokens)
            textbook_contradiction_detection_score = 1 if calculate_sentiment_polarity(answer) * calculate_sentiment_polarity(textbook_answer) >= 0 else 0

            gpt_scores = {
                'Cosine Similarity': gpt_cosine_similarity_score,
                'Keyword Matching': gpt_keyword_matching_score,
                'Semantic Similarity': gpt_semantic_similarity_score,
                'Contradiction Detection': gpt_contradiction_detection_score
            }

            textbook_scores = {
                'Cosine Similarity': textbook_cosine_similarity_score,
                'Keyword Matching': textbook_keyword_matching_score,
                'Semantic Similarity': textbook_semantic_similarity_score,
                'Contradiction Detection': textbook_contradiction_detection_score
            }

            gpt_marks = calculate_marks(gpt_scores, grading_criteria)
            textbook_marks = calculate_marks(textbook_scores, grading_criteria)

            answer_scores[f'Student {students[answer_index]}'] = {
                'GPT': gpt_marks,
                'TextBook': textbook_marks
            }

        graded_answers[question] = answer_scores

    return jsonify(graded_answers)

if __name__ == '__main__':
    app.run(debug=True)
