import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter


def extract_video_id(url: str) -> str:
    patterns = [
        r'(?:v=|/v/)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
        r'(?:shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def get_video_title(video_id: str) -> str:
    """Get video title using a simple HTTP request to YouTube's oembed API."""
    import urllib.request
    import json
    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("title", video_id)
    except Exception:
        return video_id


def fetch_transcript(video_id: str) -> dict:
    """Fetch transcript for a YouTube video. Returns dict with text, language, and title."""
    title = get_video_title(video_id)

    ytt_api = YouTubeTranscriptApi()
    transcript_list = ytt_api.list(video_id)

    # Try English first
    try:
        transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
        snippets = transcript.fetch()
        formatter = TextFormatter()
        text = formatter.format_transcript(snippets)
        return {"text": text, "language": "en", "title": title}
    except Exception:
        pass

    # Fall back to any available transcript
    for transcript in transcript_list:
        snippets = transcript.fetch()
        formatter = TextFormatter()
        text = formatter.format_transcript(snippets)
        return {"text": text, "language": transcript.language_code, "title": title}

    raise Exception(f"No transcript available for video {video_id}")
