import yt_dlp
from googleapiclient.discovery import build
from pymongo import MongoClient
import gridfs
import os
import pandas as pd
from bson import ObjectId

# MongoDB connection
client = MongoClient("mongodb+srv://{mongo_db_connection_string}")  # Replace with your MongoDB URL
db = client['exercise_videos']
fs = gridfs.GridFS(db)
YOUTUBE_API_KEY = "{youtbe_api_key}"

def search_youtube(query):
    """Search YouTube and return the first video link."""
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

        search_response = youtube.search().list(
            q=query,
            part="id",
            maxResults=1,
            type="video"
        ).execute()

        if search_response["items"]:
            video_id = search_response["items"][0]["id"]["videoId"]
            return f"https://www.youtube.com/watch?v={video_id}"
        else:
            print(f"No video found for query: {query}")
            return None

    except Exception as e:
        print(f"Error during YouTube search: {str(e)}")
        return None

def download_video(video_url, output_path="exercise_video.mp4"):
    """Download YouTube video and return metadata."""
    if not video_url:
        return None

    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)

        print("Video downloaded successfully!")

        # Return YouTube metadata
        return {
            "youtube_title": info.get("title", ""),
            "youtube_description": info.get("description", ""),
            "duration": info.get("duration", 0)
        }

    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return None

def upload_to_mongodb(file_path, metadata):
    """Upload video and metadata to MongoDB GridFS with MIME type"""
    with open(file_path, "rb") as f:
        # Explicitly set the contentType to "video/mp4"
        file_id = fs.put(f, filename=metadata["title"], contentType="video/mp4")

    # Store metadata along with GridFS file ID
    video_doc = {
        "title": metadata["title"],
        "description": metadata["description"],
        "body_part": metadata["body_part"],
        "equipment": metadata["equipment"],
        "type": metadata["type"],
        "youtube_title": metadata.get("youtube_title", ""),
        "youtube_description": metadata.get("youtube_description", ""),
        "duration": metadata.get("duration", 0),
        "file_id": str(file_id),   # Store as string for consistency
        "contentType": "video/mp4"  # Ensure MIME type is stored
    }

    db.video_metadata.insert_one(video_doc)
    print(f"Video uploaded with ID: {file_id}")
    os.remove(video_path)

if __name__ == "__main__":
    df = pd.read_csv('gym.csv')
    print(df.head())

    for i, title in enumerate(df['Title']):
        metadata = {
            "title": df['Title'][i],
            "description": df['Desc'][i],
            "body_part": df['BodyPart'][i],
            "equipment": df['Equipment'][i],
            "type": df['Type'][i]
        }

        # Search YouTube for the video
        video_url = search_youtube(metadata['title'])

        if video_url:
            video_path = f"exercise_video_{i}.mp4"

            # Download the video
            youtube_metadata = download_video(video_url, video_path)

            if youtube_metadata:
                # Merge metadata with YouTube info
                metadata.update(youtube_metadata)

                # Upload to MongoDB
                upload_to_mongodb(video_path, metadata)
            else:
                print(f"Skipping {metadata['title']} due to download error.")
        else:
            print(f"Skipping {metadata['title']} due to YouTube search error.")
        
