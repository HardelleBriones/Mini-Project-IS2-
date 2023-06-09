import pandas as pd
import numpy as np
import os
from sentence_transformers import SentenceTransformer, util
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
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

csv_file_path = 'question_data.csv'

question_data = pd.read_csv(csv_file_path)
question_data = question_data.dropna()  # Drop rows with missing values
question_texts = question_data['question_title'].apply(preprocess_text)

def encode_text(text):
    return model.encode([text])[0]

question_embeddings = question_texts.apply(encode_text)

# Check if precomputed embeddings exist
embeddings_file_path = 'question_embeddings.npy'
if os.path.isfile(embeddings_file_path):
    question_embeddings = np.load(embeddings_file_path, allow_pickle=True)
else:
    question_embeddings = np.array([model.encode(question) for question in question_texts])
    np.save(embeddings_file_path, question_embeddings)


# Convert the question_embeddings to a DataFrame
question_embeddings = pd.DataFrame(question_embeddings)

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    if 'query' not in data:
        return jsonify({'error': 'Missing query parameter'})

    user_input = data['query']
    user_input = preprocess_text(user_input)
    user_input_embedding = encode_text(user_input)
    # Convert user_input_embedding to a DataFrame
    user_input_embedding = pd.DataFrame([user_input_embedding])
    similarities = question_embeddings.apply(lambda x: util.cos_sim(user_input_embedding.values[0], x.values), axis=1)

    k = 5
    top_k_indices = similarities.argsort()[::-1][:k]
    results = []
    for i, index in enumerate(top_k_indices):
        if similarities[index] <= 0.55:
            break
        question_title = question_data.loc[index, 'question_title']
        question_body = question_data.loc[index, 'question_body']
        question_answer = question_data.loc[index, 'answer_body']

        result = {
            'question_title': question_title,
            'question_body': question_body,
            'question_answer': question_answer
        }
        results.append(result)

    return jsonify(results)

if __name__ == '__main__':
    app.run()
