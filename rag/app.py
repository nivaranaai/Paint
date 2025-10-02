from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from Vector import upsert_pdf_to_pinecone, retrieve_relevant_chunks, generate_answer_with_gemini, differentiators

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload():
    # Handle S3 URL or file upload
    s3_url = request.form.get('s3_url')
    if s3_url:
        upsert_pdf_to_pinecone(s3_url, differentiators)
        return jsonify({'message': 'S3 PDF processed successfully'})
    
    # Handle file upload
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    upsert_pdf_to_pinecone(filepath, differentiators)
    os.remove(filepath)
    
    return jsonify({'message': 'PDF uploaded to Pinecone successfully'})

@app.route('/retrieve', methods=['POST'])
def retrieve():
    query = request.json['query']
    context = retrieve_relevant_chunks(query, differentiators)
    answer = generate_answer_with_gemini(query, context)
    
    return jsonify({'answer': answer, 'context': context})

@app.route('/generate', methods=['POST'])
def generate():
    query = request.json['query']
    context = request.json['context']
    answer = generate_answer_with_gemini(query, context)
    
    return jsonify({'answer': answer})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)