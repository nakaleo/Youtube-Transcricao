from openai import OpenAI
import os

SYSTEM_PROMPT = """You will receive a transcript or text related to Vedic astrology.
Your task is to extract information strictly from the text and categorize it into the structure below.
Rules:
* Do not add any information that is not explicitly mentioned in the text.
* Only extract keywords or short phrases that appear in the text.
* Do not explain anything.
* Do not write full sentences.
* Use concise keywords separated by commas.
* If there is no information for a category, write "No info".
* You MUST include ALL lines below in your response. Do NOT skip or omit any line.
* Every single category MUST appear in your output, even if the value is "No info".
* Keep the response exactly in the format shown below.
Output format:
Main Subject: <fill>
Meaning: <fill>
People representation: <fill>
Places representation: <fill>
Objects representation: <fill>
Attributes: <fill>
Positive Aspects: <fill>
Negative Aspects: <fill>
Emotions: <fill>
Skills: <fill>
Other information: <fill>"""


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
