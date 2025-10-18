from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import json
import os
from .Vector import upsert_pdf_to_pinecone, retrieve_relevant_chunks, generate_answer_with_gemini, differentiators

@csrf_exempt
def upload(request):
    if request.method == 'POST':
        # Handle S3 URL or file upload
        s3_url = request.POST.get('s3_url')
        if s3_url:
            upsert_pdf_to_pinecone(s3_url, differentiators)
            return JsonResponse({'message': 'S3 PDF processed successfully'})
        
        # Handle file upload
        file = request.FILES['file']
        filename = default_storage.save(file.name, file)
        filepath = default_storage.path(filename)
        
        upsert_pdf_to_pinecone(filepath, differentiators)
        os.remove(filepath)
        
        return JsonResponse({'message': 'PDF uploaded to Pinecone successfully'})

@csrf_exempt
def retrieve(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data['query']
        context = retrieve_relevant_chunks(query, differentiators) #will fetch data from pinecone
        answer = generate_answer_with_gemini(query, context)
        
        return JsonResponse({'answer': answer, 'context': context})

@csrf_exempt
def generate(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data['query']
        context = data['context']
        answer = generate_answer_with_gemini(query, context)
        
        return JsonResponse({'answer': answer})