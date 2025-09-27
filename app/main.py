from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path

from .api.endpoints import feed

from .database import engine, Base


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ReelPulse API",
    description="A deep learning-based recommendation system."
)


app.include_router(feed.router, prefix="/api/v1", tags=["Recommendations"])

@app.get("/", response_class=HTMLResponse)
def read_root():
    """
    Serves the main frontend HTML page.
    This function finds the index.html file, reads its content,
    and returns it as an HTML response that the browser can display.
    """
    html_file_path = Path(__file__).parent / "index.html"
    
    return html_file_path.read_text()

