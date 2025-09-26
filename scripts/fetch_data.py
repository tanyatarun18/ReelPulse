import os
import requests
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import sys

# Make sure we can import from the project's root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database import SessionLocal
from app.models import User, Post, Interaction

# Import our new fallback function from the other script
from scripts.generate_fake_data import create_and_populate_database

# Load environment variables from the .env file
load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL")
FLIC_TOKEN = os.getenv("FLIC_TOKEN")
HEADERS = {"Flic-Token": FLIC_TOKEN}

def fetch_paginated_data(endpoint: str, params: dict = None):
    """A helper function to fetch all pages of data from a given API endpoint."""
    if params is None:
        params = {}
    
    page = 1
    all_data = []
    
    while True:
        request_params = {"page": page, "page_size": 100, **params}
        print(f"Attempting to fetch page {page} from live API: {endpoint}...")
        
        # This will raise an exception if the connection fails (timeout, DNS error, etc.)
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
    """This function attempts to sync all required data from the live external API."""
    print("--- Starting Data Synchronization from Live API ---")
    
    # 1. Fetch and process all posts
    all_posts_data = fetch_paginated_data("posts/summary/get")
    for post_data in all_posts_data:
        if not post_data.get('id'): continue
        if not db.query(Post).filter(Post.external_id == post_data['id']).first():
            db.add(Post(external_id=post_data['id'], content_description=post_data.get('caption', '')))
    db.commit()
    print(f"Synced {len(all_posts_data)} posts.")

    # 2. Fetch and process 'like' interactions as positive signals for training
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
            db.commit() # Commit here to get the new user's ID
            
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
        # --- THIS IS THE "ATTEMPT, THEN FALLBACK" LOGIC ---
        try:
            # 1. We ATTEMPT to use the required live API first.
            sync_data_from_api(db)
        except requests.exceptions.RequestException as e:
            # 2. If it fails for ANY network reason...
            print("\n" + "="*60)
            print(f"CRITICAL: Could not connect to the live API. Reason: {e}")
            print("Executing fallback: Populating database with local fake data.")
            print("="*60 + "\n")
            # 3. ...we gracefully FALL BACK to our local data generator.
            create_and_populate_database(db)
    finally:
        db.close()

