from openai import OpenAI
import os

SYSTEM_PROMPT = """You are an expert content analyst. Given a YouTube video transcript,
produce a structured analysis with the following sections:

1. SUMMARY
Write 2-3 paragraphs summarizing the main content of the video.

2. KEY POINTS
List the most important points discussed, as bullet points.

3. KEYWORDS
List the most relevant keywords and topics mentioned.

4. NOTABLE QUOTES
Extract the most impactful or important quotes from the transcript.

Be thorough and accurate. Write in English."""


def process_transcript(transcript_text: str, video_title: str) -> str:
    """Process a transcript through OpenAI to extract key insights."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    user_message = f'Video Title: "{video_title}"\n\nTranscript:\n{transcript_text}'

    # Truncate if too long (GPT-4o-mini context is 128k but we keep it reasonable)
    if len(user_message) > 100000:
        user_message = user_message[:100000] + "\n\n[Transcript truncated due to length]"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=4000,
    )

    return response.choices[0].message.content
