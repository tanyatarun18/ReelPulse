import os
import pandas as pd
import numpy as np
import tensorflow as tf
import tensorflow_recommenders as tfrs
from sqlalchemy import create_engine
import sys

# Add the project root to the Python path to allow importing from the 'app' module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database import DATABASE_URL

def load_data_from_db():
    """Loads positive user-post interaction data from the database."""
    print("Loading data from database...")
    engine = create_engine(DATABASE_URL)
    # Select all 'like' or 'swipe_right' interactions as positive signals for training
    query = """
    SELECT u.username, p.external_id FROM interactions i
    JOIN users u ON i.user_id = u.id JOIN posts p ON i.post_id = p.id
    WHERE i.interaction_type IN ('like', 'swipe_right')
    """
    df = pd.read_sql(query, engine)
    print(f"Loaded {len(df)} interactions.")
    return df

class RecommenderModel(tfrs.Model):
    """The main Two-Tower model for learning user and post representations."""
    def __init__(self, user_ids, post_ids):
        super().__init__()
        embedding_dimension = 32
        
        # User Tower: Learns a "taste profile" for each user
        self.user_model = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=user_ids, mask_token=None),
            tf.keras.layers.Embedding(len(user_ids) + 1, embedding_dimension)
        ])
        
        # Post Tower: Learns a "vibe profile" for each post
        self.post_model = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=post_ids, mask_token=None),
            tf.keras.layers.Embedding(len(post_ids) + 1, embedding_dimension)
        ])
        
        # The Retrieval task computes the loss and metrics for our model
        self.task = tfrs.tasks.Retrieval(
            metrics=tfrs.metrics.FactorizedTopK(
                candidates=tf.data.Dataset.from_tensor_slices(post_ids).batch(128).map(self.post_model)
            )
        )

    def compute_loss(self, data, training=False):
        """Defines how the model learns during training."""
        user_embeddings = self.user_model(data["username"])
        post_embeddings = self.post_model(data["external_id"])
        return self.task(user_embeddings, post_embeddings, compute_metrics=not training)

def run_training():
    """Main function to orchestrate loading, training, and saving."""
    df = load_data_from_db()
    if df.empty:
        print("No interaction data to train on. Exiting.")
        return

    # Get unique IDs for users and posts to define our vocabulary
    user_ids = df["username"].unique().astype(str)
    post_ids = df["external_id"].unique().astype(str)
    
    # Create the training dataset
    interactions_ds = tf.data.Dataset.from_tensor_slices({
        "username": tf.constant(df["username"].values, dtype=tf.string),
        "external_id": tf.constant(df["external_id"].values, dtype=tf.string)
    }).shuffle(len(df)).batch(8192).cache()
    
    print("Building and compiling the model...")
    model = RecommenderModel(user_ids, post_ids)
    model.compile(optimizer=tf.keras.optimizers.Adagrad(learning_rate=0.1))
    
    print("Starting model training...")
    model.fit(interactions_ds, epochs=5)
    print("Training complete.")
    
    print("Exporting model components for serving...")
    os.makedirs("exported_model", exist_ok=True)
    
    # --- THIS IS THE NEW, RELIABLE SAVING METHOD ---
    
    # 1. Save the trained user model.
    model.user_model.save("exported_model/user_model")
    
    # 2. Use the trained post model to get the "vibe profile" (embedding) for every post.
    all_post_embeddings = model.post_model(post_ids)
    # Save these embeddings to a file.
    np.save("exported_model/post_embeddings.npy", all_post_embeddings)
    
    # 3. Save the actual list of post IDs, so we know which embedding corresponds to which post.
    np.save("exported_model/post_ids.npy", post_ids)
    
    print("Model components exported successfully to 'exported_model/'.")

if __name__ == "__main__":
    run_training()

