import os
import requests
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database import SessionLocal
from app.models import User, Post, Interaction

from scripts.generate_fake_data import create_and_populate_database

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL")
FLIC_TOKEN = os.getenv("FLIC_TOKEN")
HEADERS = {"Flic-Token": FLIC_TOKEN}

def fetch_paginated_data(endpoint: str, params: dict = None):
    if params is None:
        params = {}
    
    page = 1
    all_data = []
    
    while True:
        request_params = {"page": page, "page_size": 100, **params}
        print(f"Attempting to fetch page {page} from live API: {endpoint}...")
        
        response = requests.get(f"{API_BASE_URL}/{endpoint}", headers=HEADERS, params=request_params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        content = data.get("data", data)
        
        if not content:
            break
            
        all_data.extend(content)
        page += 1
        
    return all_data

def sync_data_from_api(db: Session):
    print("--- Starting Data Synchronization from Live API ---")
    
    all_posts_data = fetch_paginated_data("posts/summary/get")
    for post_data in all_posts_data:
        if not post_data.get('id'): continue
        if not db.query(Post).filter(Post.external_id == post_data['id']).first():
            db.add(Post(external_id=post_data['id'], content_description=post_data.get('caption', '')))
    db.commit()
    print(f"Synced {len(all_posts_data)} posts.")

    liked_interactions = fetch_paginated_data(
        "posts/like", 
        {"resonance_algorithm": "resonance_algorithm_cjsvervb7dbhss8bdrj89s44jfjdbsjd0xnjkbvuire8zcjwerui3njfbvsujc5if"}
    )
    for interaction in liked_interactions:
        username, post_id = interaction.get('username'), interaction.get('post_id')
        if not (username and post_id): continue
        
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(username=username)
            db.add(user)
            db.commit() 
            
        post = db.query(Post).filter(Post.external_id == post_id).first()
        if user and post:
            exists = db.query(Interaction).filter_by(user_id=user.id, post_id=post.id, interaction_type='like').first()
            if not exists:
                db.add(Interaction(user_id=user.id, post_id=post.id, interaction_type='like'))
    db.commit()
    print("--- Live API Synchronization Complete ---")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        try:
            sync_data_from_api(db)
        except requests.exceptions.RequestException as e:
            print("\n" + "="*60)
            print(f"CRITICAL: Could not connect to the live API. Reason: {e}")
            print("Executing fallback: Populating database with local fake data.")
            print("="*60 + "\n")
            create_and_populate_database(db)
    finally:
        db.close()

