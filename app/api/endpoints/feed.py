from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import numpy as np
from typing import Optional

# Import the database session dependency
from app.database import get_db
# Import the recommendation service functions
from app.services import recommendation_service as rs
# Import the database models
from app import models

# Create a new router object. This helps organize the API endpoints.
router = APIRouter()


@router.on_event("startup")
def startup_event():
    """
    This function runs once when the FastAPI server starts.
    It pre-loads the AI model into memory so that it's ready for requests.
    """
    rs.load_model()


@router.get("/feed/{username}")
def get_personalized_feed(username: str, project_code: Optional[str] = None, db: Session = Depends(get_db)):
    """
    This is the main recommendation endpoint. It handles all three cases:
    1. Personalized feed for a known user.
    2. Generic cold start feed for a new user.
    3. Mood-based cold start feed for a new user who provides a project_code.
    """
    # Check if the user exists in our database.
    user = db.query(models.User).filter(models.User.username == username).first()

    # --- THIS IS THE UPDATED COLD START LOGIC ---
    if not user:
        # If a project_code (mood) is provided by a new user...
        if project_code:
            # ...call the new function to get recommendations for that specific category.
            recommendations = rs.get_category_recommendations(project_code)
            return {"username": username, "type": f"cold_start_category: {project_code}",
                    "recommendations": recommendations}
        else:
            # Otherwise, use the original cold start logic for a generic feed.
            recommendations = rs.get_cold_start_recommendations()
            return {"username": username, "type": "cold_start", "recommendations": recommendations}

    # If the user is known, get their personalized feed from the AI model.
    recommendations = rs.get_recommendations_for_user(username)
    return {"username": username, "type": "personalized", "recommendations": recommendations}


@router.get("/discover/{username}")
def get_discovery_feed(username: str):
    """
    Provides a shuffled list of recommendations for the interactive
    "Tinder for Videos" swipe mode.
    """
    recs = rs.get_recommendations_for_user(username, top_k=50)
    np.random.shuffle(recs)
    return {"username": username, "discover_queue": recs[:20]}


@router.post("/discover/swipe")
def record_swipe(username: str, post_external_id: str, liked: bool, db: Session = Depends(get_db)):
    """
    Records a user's swipe action (like or dislike) in the database.
    This new data can be used the next time the model is trained.
    """
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")

    post = db.query(models.Post).filter(models.Post.external_id == post_external_id).first()
    if not post: raise HTTPException(status_code=404, detail="Post not found")

    interaction_type = "swipe_right" if liked else "swipe_left"

    new_interaction = models.Interaction(user_id=user.id, post_id=post.id, interaction_type=interaction_type)
    db.add(new_interaction)
    db.commit()

    return {"status": "success", "message": f"Recorded '{interaction_type}' for {username} on {post_external_id}"}
