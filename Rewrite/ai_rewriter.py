import json
import time

GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "allam-2-7b",
]

GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash"
]

def rewrite_articale_groq(groq_client, title, text):
    """Gemini ফেইল করলে Groq দিয়ে রিরাইট করার ফলব্যাক ফাংশন"""
    system_prompt = (
        "আপনি একজন অভিজ্ঞ সংবাদ সম্পাদক। মূল সংবাদের তথ্য ও ভাবার্থ ঠিক রেখে "
        "সহজ, সাবলীল ও প্রচলিত সংবাদের ভাষায় বাংলায় রিরাইট করুন। "
        "নিজে থেকে কোনো তথ্য, সংখ্যা বা নাম যোগ করবেন না। "
        "আকর্ষণীয় বাংলা শিরোনাম এবং বিস্তারিত সংবাদ তৈরি করুন।"
    )
    user_prompt = f"মূল শিরোনাম: {title}\n\nখবর:\n{text}"

    for model in GROQ_MODELS:
        try:
            completion = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=2048,
            )
            
            rewritten_text = completion.choices[0].message.content.strip()
            
            return {
                "title": title,
                "content": rewritten_text,
                "tags": ["সংবাদ", "বাংলাদেশ", "খবর"]
            }
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ Groq মডেল '{model}' এ ত্রুটি: {e}")
            continue
            
    return {
        "title": title, 
        "content": text,
        "tags": ["News"]
    }

def rewrite_article(gemini_client, groq_client, title, text):
    prompt = f"""
    You are an expert news editor for a leading Bengali news portal. 
    Rewrite or translate the following news article into fluent, standard Bengali.
    
    Instructions:
    - If the input is in English, translate and rewrite it into compelling standard Bengali.
    - If the input is already in Bengali, rewrite it to make it unique and engaging.
    - Create an attractive Bengali headline (title).
    - Provide a detailed news article in Bengali (minimum 250-300 words).
    - Include 3-5 relevant Bengali/English tags.

    Return the output ONLY in JSON format like this:
    {{
        "title": "আপনার বাংলা শিরোনাম",
        "content": "বাংলা বিস্তারিত খবর...",
        "tags": ["জাতীয়", "আন্তর্জাতিক", "খবর"]
    }}

    Original Title: {title}
    Original Text: {text}
    """
    
    max_retries = 2
    for model in GEMINI_MODELS:
        for attempt in range(max_retries):
            try:
                response = gemini_client.models.generate_content(
                    model=model,
                    contents=prompt
                )
            
                clean_json = response.text.strip().replace('```json', '').replace('```', '')
                data = json.loads(clean_json)

                if not isinstance(data.get('tags'), list):
                    data['tags'] = ["News"]
                return data
            
            except Exception as e:  # noqa: BLE001
                if "503" in str(e) and attempt < max_retries - 1:
                    print(f"⚠️ Gemini API Failed, {attempt + 1} ...")
                    time.sleep(5)
                elif attempt == max_retries - 1:
                    print("⚠️ Gemini Fail Switch To Groq:", e)
                    return rewrite_articale_groq(groq_client, title, text)
                else:
                    return {
                        "title": title, 
                        "content": text,
                        "tags": ["News"]
                    }