import pandas as pd
import re
from sentence_transformers import SentenceTransformer, util
from bs4 import BeautifulSoup
import urllib.request
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
from flask import Flask, request, jsonify
from flask_cors import CORS

model_name = 'paraphrase-MiniLM-L6-v2'  # Pre-trained model for sentence embeddings
model = SentenceTransformer(model_name)

def preprocess_text(text, remove_tags=False):
    if remove_tags:
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text()

    text = text.lower()
    tokens = text.split()
    stop_words = set(stopwords.words("english"))
    tokens = [word for word in tokens if word not in stop_words]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    processed_text = " ".join(tokens)
    return processed_text

def format_paragraphs(text, words_per_line=10):
    words = text.split()
    lines = [' '.join(words[i:i+words_per_line]) for i in range(0, len(words), words_per_line)]
    return '\n'.join(lines)

url = 'https://drive.google.com/u/0/uc?id=1tyy8KC1JCCBEJ22VMxeYNso8LKjP7Ta3&export=download'
csv_file_path = 'question_data.csv'
urllib.request.urlretrieve(url, csv_file_path)

question_data = pd.read_csv(csv_file_path)
question_texts = question_data['question_title'].apply(preprocess_text)

def encode_text(text):
    return model.encode([text])[0]

question_embeddings = question_texts.apply(encode_text)

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    user_input = data['query']
    user_input = preprocess_text(user_input)
    user_input_embedding = encode_text(user_input)
    similarities = question_embeddings.apply(lambda x: util.cos_sim(user_input_embedding, x))
    k = 5
    top_k_indices = similarities.argsort()[::-1][:k]
    results = []
    for i, index in enumerate(top_k_indices):
        if similarities[index] <= 0.55:
            break
        question_title = question_data.loc[index, 'question_title']
        question_body = format_paragraphs(preprocess_text(question_data.loc[index, 'question_body'], remove_tags=True))
        question_answer = format_paragraphs(preprocess_text(question_data.loc[index, 'answer_body'], remove_tags=True))

        result = {
            'question_title': question_title,
            'question_body': question_body,
            'question_answer': question_answer
        }
        results.append(result)

    return jsonify(results)

if __name__ == '__main__':
    app.run()
