from langchain_core.tools import tool

from google_auth import get_google_credentials
from googleapiclient.discovery import build


# ============================================================
# CONFIG
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly"
]


# ============================================================
# SERVICE
# ============================================================

def get_youtube_service():
    credentials = get_google_credentials(SCOPES)

    service = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    return service


# ============================================================
# SEARCH VIDEOS
# ============================================================

@tool
def search_youtube(query: str, max_results: int = 10):
    """
    Search YouTube videos by keyword.
    """

    max_results = min(max(max_results, 1), 25)

    service = get_youtube_service()

    response = service.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=max_results
    ).execute()

    results = []

    for item in response.get("items", []):
        video_id = item["id"].get("videoId")

        snippet = item.get("snippet", {})

        results.append({
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt", "")
        })

    if not results:
        return "No YouTube videos found."

    return results


# ============================================================
# GET VIDEO
# ============================================================

@tool
def get_youtube_video(video_id: str):
    """
    Get information about a YouTube video using its video ID.
    """

    service = get_youtube_service()

    response = service.videos().list(
        part="snippet,contentDetails,statistics",
        id=video_id
    ).execute()

    items = response.get("items", [])

    if not items:
        return "YouTube video not found."

    video = items[0]

    snippet = video.get("snippet", {})
    statistics = video.get("statistics", {})
    content_details = video.get("contentDetails", {})

    return {
        "video_id": video.get("id"),
        "title": snippet.get("title", ""),
        "description": snippet.get("description", ""),
        "channel": snippet.get("channelTitle", ""),
        "published_at": snippet.get("publishedAt", ""),
        "duration": content_details.get("duration", ""),
        "views": statistics.get("viewCount", "0"),
        "likes": statistics.get("likeCount", "0"),
        "comments": statistics.get("commentCount", "0")
    }


# ============================================================
# GET MY CHANNEL
# ============================================================

@tool
def get_my_youtube_channel():
    """
    Get information about the authenticated user's YouTube channel.
    """

    service = get_youtube_service()

    response = service.channels().list(
        part="snippet,statistics,contentDetails",
        mine=True
    ).execute()

    items = response.get("items", [])

    if not items:
        return "No YouTube channel found for the authenticated account."

    channel = items[0]

    snippet = channel.get("snippet", {})
    statistics = channel.get("statistics", {})
    content_details = channel.get("contentDetails", {})

    return {
        "channel_id": channel.get("id"),
        "title": snippet.get("title", ""),
        "description": snippet.get("description", ""),
        "published_at": snippet.get("publishedAt", ""),
        "subscribers": statistics.get("subscriberCount", "0"),
        "views": statistics.get("viewCount", "0"),
        "videos": statistics.get("videoCount", "0"),
        "uploads_playlist": content_details
            .get("relatedPlaylists", {})
            .get("uploads")
    }


# ============================================================
# LIST MY UPLOADED VIDEOS
# ============================================================

@tool
def list_my_youtube_videos(max_results: int = 10):
    """
    List videos uploaded to the authenticated user's YouTube channel.
    """

    max_results = min(max(max_results, 1), 25)

    service = get_youtube_service()

    channel_response = service.channels().list(
        part="contentDetails",
        mine=True
    ).execute()

    channels = channel_response.get("items", [])

    if not channels:
        return "No YouTube channel found."

    uploads_playlist = (
        channels[0]
        .get("contentDetails", {})
        .get("relatedPlaylists", {})
        .get("uploads")
    )

    if not uploads_playlist:
        return "Uploads playlist not found."

    response = service.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=uploads_playlist,
        maxResults=max_results
    ).execute()

    results = []

    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        content_details = item.get("contentDetails", {})

        results.append({
            "video_id": content_details.get("videoId"),
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt", "")
        })

    if not results:
        return "No uploaded YouTube videos found."

    return results


# ============================================================
# TOOLS EXPORT
# ============================================================

youtube_tools = [
    search_youtube,
    get_youtube_video,
    get_my_youtube_channel,
    list_my_youtube_videos,
]
