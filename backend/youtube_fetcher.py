# backend/youtube_fetcher.py
import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

def fetch_comments(video_id: str, max_results: int = 100):
    comments = []
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )
    while request and len(comments) < max_results:
        resp = request.execute()
        for item in resp.get("items", []):
            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(text)
            if len(comments) >= max_results:
                break
        request = youtube.commentThreads().list_next(request, resp)
    return comments

# Quick test
if __name__ == "__main__":
    print(fetch_comments("dQw4w9WgXcQ", max_results=5))
