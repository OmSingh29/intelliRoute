import json
import time
import requests
import os
from pathlib import Path

# Django Imports
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Hugging Face Imports
from huggingface_hub import InferenceClient

# Firebase Imports
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from google.cloud.firestore_v1.base_query import FieldFilter
import google.auth.exceptions


# --- HUGGING FACE API CONFIGURATION ---
MODEL_SUMMARIZATION = "sshleifer/distilbart-cnn-12-6"
MODEL_SENTIMENT = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
MODEL_ZERO_SHOT = "facebook/bart-large-mnli"
CLASSIFIER_LABELS = ["Urgent", "Billing", "Technical Support", "Bug Report", "Feature Request", "Praise", "General Feedback"]
# Define the strict priority order for custom sorting
PRIORITY_ORDER = ["Urgent", "Billing", "Technical Support", "Bug Report", "Feature Request", "Praise", "General Feedback"]
# Create a map for quick priority lookup (lower number is higher priority)
PRIORITY_MAP = {label: index for index, label in enumerate(PRIORITY_ORDER)}
# ----------------------------------------

# --- FIREBASE SETUP ---
db = None
try:
    # Use BASE_DIR to find the service account key
    key_path = settings.BASE_DIR / 'serviceAccountKey.json'
    
    if not key_path.exists():
        print("!!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"serviceAccountKey.json not found at {key_path}")
        print("The dashboard will not work until the file is placed correctly.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    
    cred = credentials.Certificate(str(key_path))
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase Admin SDK initialized successfully.")

except ValueError:
    # Catches the error if initialize_app() was already called
    print("Firebase Admin SDK already initialized.")
    db = firestore.client()
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    # db remains None if initialization fails
# ----------------------------------------

def index(request):
    """
    Renders the main HTML page (index.html).
    """
    return render(request, 'core/index.html')

def dashboard(request):
    """
    Renders the new dashboard HTML page.
    """
    return render(request, 'core/dashboard.html')


# Custom sorting function for business priority (used internally for rank lookup)
def sort_by_priority(tag_list):
    """
    Sorts a list of tags (strings) based on the predefined PRIORITY_ORDER.
    Tags not in the map are moved to the bottom.
    """
    return sorted(tag_list, key=lambda tag: PRIORITY_MAP.get(tag, 100))


@csrf_exempt
def analyze_feedback(request):
    """
    Receives text, calls the correct HF API endpoints, and returns analysis JSON.
    Also saves the result to Firestore.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    try:
        data = json.loads(request.body)
        text_input = data.get('text', '')
        if not text_input.strip():
            return JsonResponse({'error': 'Text input cannot be empty'}, status=400)

        # 1. Create ONE client
        client = InferenceClient(
            provider="hf-inference",
            api_key=settings.HF_API_TOKEN,
        )

        # --- API CALLS ---
        # 2. Call Summarization
        summary = client.summarization(
            text_input,
            model=MODEL_SUMMARIZATION,
        )

        # 3. Call Sentiment Analysis
        sentiment = client.text_classification(
            text_input,
            model=MODEL_SENTIMENT,
        )

        # 4. Call Zero-Shot Classification (Manual Requests Call - as per user instruction)
        # Using model-specific URL as defined by the user
        API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-mnli"
        headers = {
            "Authorization": f"Bearer {settings.HF_API_TOKEN}",
        }

        def query(payload):
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()

        tags_payload = {
            "inputs": text_input,
            "parameters": {"candidate_labels": CLASSIFIER_LABELS},
        }
        
        tags = query(tags_payload)

        # --- PROCESS RESULTS ---
        
        # 'summary' is a SummarizationOutput OBJECT.
        processed_summary = "Analysis failed."
        if summary and hasattr(summary, 'summary_text'):
            processed_summary = summary.summary_text

        # 'sentiment' is a LIST of TextClassificationOutputElement OBJECTS.
        processed_sentiment = "Neutral"
        if sentiment and isinstance(sentiment, list) and len(sentiment) > 0:
            top = max(sentiment, key=lambda x: x.score)
            processed_sentiment = top.label.title()
        
        # 'tags' is a LIST of DICTIONARIES (from the requests call)
        processed_tag = "General Feedback" # Default to lowest priority tag
        processed_rank = 100 # Default rank
        
        # Logic: Select tag based on MODEL CONFIDENCE (highest score)
        if tags and isinstance(tags, list) and len(tags) > 0 and isinstance(tags[0], dict):
            # Sort tags by confidence score first (highest score at tags[0])
            tags.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # Select the single, highest-scoring tag
            top_tag = tags[0].get('label')
            
            if top_tag:
                processed_tag = top_tag
                # Calculate priority rank of the SELECTED tag for dashboard sorting
                processed_rank = PRIORITY_MAP.get(processed_tag, 100)

        # Final response structure
        response_data = {
            'summary': processed_summary,
            'sentiment': processed_sentiment,
            # Store the single, highest-scoring tag
            'tags': [processed_tag], 
            # Store the priority rank for dashboard sorting
            'priority_rank': processed_rank, 
            'timestamp': firestore.SERVER_TIMESTAMP
        }

        # --- Save to Firestore ---
        # Strip the SERVER_TIMESTAMP before creating the JsonResponse
        response_data_for_json = response_data.copy()
        del response_data_for_json['timestamp'] 
        
        demo_user_id = "demo_user"
        try:
            if db:
                # Add the original response_data (with the SERVER_TIMESTAMP) to Firestore
                tickets_ref = db.collection('user_tickets').document(demo_user_id).collection('tickets')
                tickets_ref.add(response_data) 
            else:
                print("Firestore (db) is not initialized. Skipping save.")
        except Exception as e:
            print(f"Error saving to Firestore: {e}")
            pass

        return JsonResponse(response_data_for_json)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except requests.exceptions.HTTPError as e:
         # Capture specific API errors like 404, 401, 503 from the requests call
        return JsonResponse({'error': f'Hugging Face API Error: {e.response.status_code} - {e.response.text}'}, status=e.response.status_code)
    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)