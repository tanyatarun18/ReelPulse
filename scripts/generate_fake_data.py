import random
from sqlalchemy.orm import Session

# We need to import the database models to create new records
from app.models import User, Post, Interaction

# --- Configuration for Fake Data ---
# These constants define how much data will be generated if the fallback is triggered.
NUM_USERS = 200
NUM_POSTS = 500
NUM_INTERACTIONS = 5000

def create_and_populate_database(db: Session):
    """
    Generates and saves fake users, posts, and interactions into the database.
    This function is called by fetch_data.py as a fallback when the live API is down.
    """
    print("--- RUNNING FALLBACK: Generating fake local data. ---")

    # First, check if the database already contains data. This prevents
    # accidentally re-running the generation and creating duplicate entries.
    if db.query(User).count() > 0:
        print("Database already contains data. Skipping generation.")
        return

    # 1. Generate Fake Posts with categories for mood-based recommendations
    print(f"Generating {NUM_POSTS} fake posts...")
    moods = ['motivational', 'educational', 'funny', 'inspirational']
    posts = [
        Post(
            external_id=f"post_{i+1}",
            content_description=f"This is a sample description for video number {i+1}.",
            category=random.choice(moods)
        ) for i in range(NUM_POSTS)
    ]
    db.add_all(posts)
    db.commit()
    print("Posts created successfully.")

    # 2. Generate Fake Users
    print(f"Generating {NUM_USERS} fake users...")
    users = [User(username=f"user_{i+1}") for i in range(NUM_USERS)]
    db.add_all(users)
    db.commit()
    print("Users created successfully.")

    # 3. Generate Fake Interactions (e.g., 'likes') between users and posts
    print(f"Generating {NUM_INTERACTIONS} fake interactions...")
    # Get all user and post IDs from the database now that they exist
    user_ids = [u.id for u in db.query(User.id).all()]
    post_ids = [p.id for p in db.query(Post.id).all()]
    
    interactions = [
        Interaction(
            user_id=random.choice(user_ids),
            post_id=random.choice(post_ids),
            interaction_type='like'  # This is the positive signal for our AI
        ) for _ in range(NUM_INTERACTIONS)
    ]
    db.add_all(interactions)
    db.commit()
    print("Interactions created successfully.")

    print("--- Fallback data generation complete. ---")

