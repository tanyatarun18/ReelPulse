import tensorflow as tf
import numpy as np
import os
from typing import List, Dict
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal

USER_MODEL = None
POST_EMBEDDINGS = None
POST_IDS = None

def load_model():
    global USER_MODEL, POST_EMBEDDINGS, POST_IDS
    user_model_path = "exported_model/user_model"
    post_embeddings_path = "exported_model/post_embeddings.npy"
    post_ids_path = "exported_model/post_ids.npy"

    if all(os.path.exists(p) for p in [user_model_path, post_embeddings_path, post_ids_path]):
        print("Loading model components from disk...")
        USER_MODEL = tf.keras.models.load_model(user_model_path)
        POST_EMBEDDINGS = np.load(post_embeddings_path)
        POST_IDS = np.load(post_ids_path, allow_pickle=True)
        print("Model components loaded successfully.")
    else:
        print("WARNING: Model components not found. Recommendations will be generic.")

def _get_posts_details(post_ids: List[str]) -> List[Dict]:
    
    if not post_ids:
        return []
    
    db = SessionLocal()
    try:
        posts = db.query(models.Post).filter(models.Post.external_id.in_(post_ids)).all()
        
        posts_dict = {post.external_id: post for post in posts}
        
        return [
            {
                "id": post_id,
                "description": posts_dict[post_id].content_description,
                "category": posts_dict[post_id].category
            }
            for post_id in post_ids if post_id in posts_dict
        ]
    finally:
        db.close()

def get_recommendations_for_user(username: str, top_k: int = 20) -> List[Dict]:
    """Generates personalized recommendations with full details."""
    if any(x is None for x in [USER_MODEL, POST_EMBEDDINGS, POST_IDS]):
        return get_cold_start_recommendations(top_k)

    user_tensor = tf.constant([username])
    user_embedding = USER_MODEL(user_tensor).numpy()

    scores = np.dot(user_embedding, POST_EMBEDDINGS.T).flatten()

    top_indices = np.argsort(-scores)[:top_k]
    recommended_ids = POST_IDS[top_indices].tolist()
    
    return _get_posts_details(recommended_ids)

def get_cold_start_recommendations(top_k: int = 20) -> List[Dict]:
    """Returns a random list of posts with full details for new users."""
    if POST_IDS is not None and len(POST_IDS) > 0:
        random_ids = np.random.choice(POST_IDS, size=min(top_k, len(POST_IDS)), replace=False).tolist()
        return _get_posts_details(random_ids)
    return []

def get_category_recommendations(category: str, top_k: int = 20) -> List[Dict]:
    """Returns posts from a specific category with full details."""
    db = SessionLocal()
    try:
        posts = db.query(models.Post).filter(models.Post.category == category).limit(top_k).all()
        
        if not posts:
            return get_cold_start_recommendations(top_k)
        
        return [
            {
                "id": post.external_id,
                "description": post.content_description,
                "category": post.category
            }
            for post in posts
        ]
    finally:
        db.close()
