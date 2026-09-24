from langchain_core.tools import tool

from google_auth import get_google_credentials
from googleapiclient.discovery import build


# ============================================================
# CONFIG
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]


# ============================================================
# SERVICE
# ============================================================

def get_youtube_analytics_service():
    credentials = get_google_credentials(SCOPES)

    service = build(
        "youtubeAnalytics",
        "v2",
        credentials=credentials
    )

    return service


# ============================================================
# CHANNEL OVERVIEW
# ============================================================

@tool
def get_youtube_channel_analytics(
    start_date: str,
    end_date: str
):
    """
    Get YouTube channel analytics for a date range.

    Dates must use YYYY-MM-DD format.
    """

    service = get_youtube_analytics_service()

    response = service.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics="views,estimatedMinutesWatched,averageViewDuration,likes,comments,subscribersGained,subscribersLost",
        dimensions="day",
        sort="day"
    ).execute()

    rows = response.get("rows", [])

    if not rows:
        return "No YouTube analytics data found for this date range."

    headers = [
        column["name"]
        for column in response.get("columnHeaders", [])
    ]

    results = []

    for row in rows:
        results.append(
            dict(zip(headers, row))
        )

    return results


# ============================================================
# VIDEO ANALYTICS
# ============================================================

@tool
def get_youtube_video_analytics(
    video_id: str,
    start_date: str,
    end_date: str
):
    """
    Get analytics for a specific YouTube video.

    Dates must use YYYY-MM-DD format.
    """

    service = get_youtube_analytics_service()

    response = service.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics="views,estimatedMinutesWatched,averageViewDuration,likes,comments",
        filters=f"video=={video_id}"
    ).execute()

    rows = response.get("rows", [])

    if not rows:
        return "No analytics data found for this video and date range."

    headers = [
        column["name"]
        for column in response.get("columnHeaders", [])
    ]

    return dict(zip(headers, rows[0]))


# ============================================================
# TRAFFIC SOURCES
# ============================================================

@tool
def get_youtube_traffic_sources(
    start_date: str,
    end_date: str
):
    """
    Get YouTube channel traffic sources for a date range.

    Dates must use YYYY-MM-DD format.
    """

    service = get_youtube_analytics_service()

    response = service.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics="views,estimatedMinutesWatched",
        dimensions="insightTrafficSourceType",
        sort="-views"
    ).execute()

    rows = response.get("rows", [])

    if not rows:
        return "No traffic source analytics found."

    headers = [
        column["name"]
        for column in response.get("columnHeaders", [])
    ]

    results = []

    for row in rows:
        results.append(
            dict(zip(headers, row))
        )

    return results


# ============================================================
# TOP VIDEOS
# ============================================================

@tool
def get_top_youtube_videos(
    start_date: str,
    end_date: str,
    max_results: int = 10
):
    """
    Get the top videos on the authenticated YouTube channel
    based on views.

    Dates must use YYYY-MM-DD format.
    """

    max_results = min(max(max_results, 1), 25)

    service = get_youtube_analytics_service()

    response = service.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics="views,estimatedMinutesWatched,likes,comments",
        dimensions="video",
        sort="-views",
        maxResults=max_results
    ).execute()

    rows = response.get("rows", [])

    if not rows:
        return "No video analytics data found."

    headers = [
        column["name"]
        for column in response.get("columnHeaders", [])
    ]

    results = []

    for row in rows:
        results.append(
            dict(zip(headers, row))
        )

    return results


# ============================================================
# SUBSCRIBER CHANGE
# ============================================================

@tool
def get_youtube_subscriber_analytics(
    start_date: str,
    end_date: str
):
    """
    Get daily subscriber gains and losses for a date range.

    Dates must use YYYY-MM-DD format.
    """

    service = get_youtube_analytics_service()

    response = service.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics="subscribersGained,subscribersLost",
        dimensions="day",
        sort="day"
    ).execute()

    rows = response.get("rows", [])

    if not rows:
        return "No subscriber analytics found."

    headers = [
        column["name"]
        for column in response.get("columnHeaders", [])
    ]

    results = []

    for row in rows:
        results.append(
            dict(zip(headers, row))
        )

    return results


# ============================================================
# TOOLS EXPORT
# ============================================================

youtube_analytics_tools = [
    get_youtube_channel_analytics,
    get_youtube_video_analytics,
    get_youtube_traffic_sources,
    get_top_youtube_videos,
    get_youtube_subscriber_analytics,
]