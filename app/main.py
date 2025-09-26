from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path

# Import the router from your endpoints file
from .api.endpoints import feed

# Import the database engine and Base from your database file
from .database import engine, Base

# This command tells SQLAlchemy to create all the database tables
# defined in your models.py file, but only if they don't already exist.
Base.metadata.create_all(bind=engine)

# Create the main FastAPI application instance
app = FastAPI(
    title="ReelPulse API",
    description="A deep learning-based recommendation system."
)

# This includes all the API routes (like /feed, /discover) from your feed.py file.
# They will be available under the /api/v1 prefix.
app.include_router(feed.router, prefix="/api/v1", tags=["Recommendations"])

# This defines what happens when a user visits the main homepage (the "/" URL).
@app.get("/", response_class=HTMLResponse)
def read_root():
    """
    Serves the main frontend HTML page.
    This function finds the index.html file, reads its content,
    and returns it as an HTML response that the browser can display.
    """
    # Create a path to the index.html file located in the same directory
    html_file_path = Path(__file__).parent / "index.html"
    
    # Read the content of the HTML file and return it
    return html_file_path.read_text()

