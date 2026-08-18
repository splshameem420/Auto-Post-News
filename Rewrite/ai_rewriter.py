import json
import time


def rewrite_article(ai_client, title, text):
    prompt = f"""
    You are an expert news editor. Rewrite the following news in standard fluent Bengali for a professional news portal.
    
    Structure:
    - Create an engaging Bengali headline.
    - Write a detailed article (minimum 250-300 words).
    - Provide 3-5 short tags in Bengali/English.

    Return the output ONLY in JSON format like this:
    {{
        "title": "আপনার বাংলা শিরোনাম",
        "content": "বাংলা বিস্তারিত খবর...",
        "tags": ["জাতীয়", "সংবাদ"]
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

            # নিশ্চিত করা যেন tags সর্বদা লিস্ট হয়
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