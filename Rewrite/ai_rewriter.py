import json
import time


def rewrite_article(ai_client, title, text):
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
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = ai_client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt
            )
            
            clean_json = response.text.strip().replace('```json', '').replace('```', '')
            data = json.loads(clean_json)

            if not isinstance(data.get('tags'), list):
                data['tags'] = ["News"]

            return data
            
        except Exception as e:  # noqa: BLE001
            if "503" in str(e) and attempt < max_retries - 1:
                print(f"⚠️ Gemini API ব্যস্ত, {attempt + 1} নম্বর পুনরায় চেষ্টা করা হচ্ছে...")
                time.sleep(5)
            else:
                print("⚠️ AI Rewrite ত্রুটি:", e)
                return {
                    "title": title, 
                    "content": text,
                    "tags": ["News"]
                }