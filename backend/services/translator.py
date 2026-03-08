import os
from openai import OpenAI


def translate_to_english(text: str, source_lang: str) -> str:
    """Translate text to English using OpenAI. If already English, returns as-is."""
    if source_lang.startswith("en"):
        return text

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Split into chunks to stay within token limits (~4000 chars each)
    max_chunk = 4000
    chunks = []
    current = ""

    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_chunk:
            chunks.append(current)
            current = line
        else:
            current = current + "\n" + line if current else line

    if current:
        chunks.append(current)

    translated_chunks = []
    for chunk in chunks:
        if not chunk.strip():
            translated_chunks.append("")
            continue

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Translate the following text to English. Return only the translation, no explanations.",
                },
                {"role": "user", "content": chunk},
            ],
            temperature=0.1,
        )
        translated_chunks.append(response.choices[0].message.content)

    return "\n".join(translated_chunks)
