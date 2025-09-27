import random
from sqlalchemy.orm import Session

from app.models import User, Post, Interaction


NUM_USERS = 200
NUM_POSTS = 500
NUM_INTERACTIONS = 5000

def create_and_populate_database(db: Session):
    
    print("--- RUNNING FALLBACK: Generating fake local data. ---")

   
    if db.query(User).count() > 0:
        print("Database already contains data. Skipping generation.")
        return

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

    print(f"Generating {NUM_USERS} fake users...")
    users = [User(username=f"user_{i+1}") for i in range(NUM_USERS)]
    db.add_all(users)
    db.commit()
    print("Users created successfully.")

    print(f"Generating {NUM_INTERACTIONS} fake interactions...")
    user_ids = [u.id for u in db.query(User.id).all()]
    post_ids = [p.id for p in db.query(Post.id).all()]
    
    interactions = [
        Interaction(
            user_id=random.choice(user_ids),
            post_id=random.choice(post_ids),
            interaction_type='like' 
        ) for _ in range(NUM_INTERACTIONS)
    ]
    db.add_all(interactions)
    db.commit()
    print("Interactions created successfully.")

    print("--- Fallback data generation complete. ---")

