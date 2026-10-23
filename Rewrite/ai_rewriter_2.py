import json
import re
import time

from google.genai import types

GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "allam-2-7b",
]

GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash"
]

MAX_RETRIES = 2
MAX_INPUT_CHARS = 6000
GROQ_MAX_TOKENS = 4096

RETRYABLE_HINTS = (
    "429", "rate", "quota", "timeout", "timed out",
    "503", "502", "500", "overloaded", "unavailable", "connection",
)


def is_retryable(error):
    msg = str(error).lower()
    return any(hint in msg for hint in RETRYABLE_HINTS)


def parse_ai_json(raw):
    if not raw:
        raise ValueError("empty response")

    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    raw = raw.strip()

    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found")
    raw = raw[start:end + 1]

    data = json.loads(raw)

    title = str(data.get("title", "")).strip()
    content = str(data.get("content", "")).strip()
    if not title or not content:
        raise ValueError("title/content missing")

    tags = data.get("tags")
    if not isinstance(tags, list) or not tags:
        tags = ["News"]
    tags = [str(t).strip() for t in tags if str(t).strip()]

    return {"title": title, "content": content, "tags": tags}


def failed_result(title, text):
    return {
        "title": title,
        "content": text,
        "tags": ["News"],
        "failed": True,
    }


def summarize_errors(all_errors):
    unique_errors = list(dict.fromkeys(all_errors))
    return " | ".join(unique_errors) if unique_errors else "unknown error"


def rewrite_with_groq(groq_client, title, text):
    ai_name = "Groq"
    all_errors = []
    print(f"AI Name: {ai_name}")

    text = text[:MAX_INPUT_CHARS]

    system_prompt = (
        "You are an expert news editor for a leading Bengali news portal."
        "Rewrite or translate the following news article into fluent, standard Bengali. "
        "Do not add any information, numbers, or names on your own. "
        "Create an engaging Bengali headline and a detailed news report."
        "Respond only in JSON format; do not write anything outside the JSON: "
        '{"title": "...", "content": "...", "tags": ["...", "..."]}'
    )
    user_prompt = f"Main Title: {title}\n\nNews:\n{text}"

    for model in GROQ_MODELS:
        print(f"Current Model: {model}")
        last_model_error = None

        for attempt in range(MAX_RETRIES):
            try:
                completion = groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=GROQ_MAX_TOKENS,
                )
                return parse_ai_json(completion.choices[0].message.content)

            except Exception as e:  # noqa: BLE001
                last_model_error = e
                all_errors.append(str(e))
                retryable = is_retryable(e) or isinstance(e, (ValueError, json.JSONDecodeError))
                if not retryable:
                    break
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2)

        print(f"({model}) failed: {last_model_error}\n")

    print(f"{ai_name} all models failed: {summarize_errors(all_errors)}\n")
    return failed_result(title, text)


def rewrite_article(gemini_client, groq_client, title, text):
    text = text[:MAX_INPUT_CHARS]

    prompt = f"""
    You are an expert news editor for a leading Bengali news portal.
    Rewrite or translate the following news article into fluent, standard Bengali.

    Instructions:
    - If the input is in English, translate and rewrite it into compelling standard Bengali.
    - If the input is already in Bengali, rewrite it to make it unique and engaging.
    - Do not add any fact, number or name that is not in the original.
    - Create an attractive Bengali headline (title).
    - Provide a detailed news article in Bengali (minimum 250-300 words).
    - Include 3-5 relevant Bengali/English tags.

    Return the output ONLY in JSON format like this:
    {{
        "title": "...",
        "content": "...",
        "tags": ["...", "..."]
    }}

    Original Title: {title}
    Original Text: {text}
    """

    ai_name = "Gemini"
    all_errors = []
    print(f"AI Name: {ai_name}")

    for model in GEMINI_MODELS:
        print(f"Current Model: {model}")
        last_model_error = None
        hit_rate_limit = False

        for attempt in range(MAX_RETRIES):
            try:
                response = gemini_client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    ),
                )
                return parse_ai_json(response.text)

            except Exception as e:  # noqa: BLE001
                last_model_error = e
                all_errors.append(str(e))
                
                error_msg = str(e).lower()
                if "429" in error_msg or "rate" in error_msg or "quota" in error_msg:
                    hit_rate_limit = True
                    break
                retryable = is_retryable(e) or isinstance(e, (ValueError, json.JSONDecodeError))
                if not retryable:
                    break
                if attempt < MAX_RETRIES - 1:
                    time.sleep(5)

        print(f"({model}) failed: {last_model_error}\n")
        if hit_rate_limit:
            print(f" ({ai_name} API rate limit hit, retrying with next model...\n")
            break

    print(f"{ai_name} all models failed: {summarize_errors(all_errors)}\n")

    return rewrite_with_groq(groq_client, title, text)
