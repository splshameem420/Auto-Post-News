def publish_post(service, blog_id, title, content, image_url=None, labels=[]):
    """
    Blogger API v3 ব্যবহার করে ব্লগে নতুন পোস্ট পাবলিশ করার ফাংশন।
    """
    body_html = ""
    if image_url:
        body_html += (
            f'<div style="text-align:center; margin-bottom:15px;">'
            f'<img src="{image_url}" style="max-width:100%; height:auto; border-radius:8px;"/>'
            f'</div>'
        )
    
    # f-string এর বাইরে \n কে <br> তে রূপান্তর করা হয়েছে
    formatted_content = content.replace("\n", "<br>")
    body_html += f'<div>{formatted_content}</div>'

    # Blogger API-এর জন্য ট্যাগ পরিশোধন
    clean_labels = []
    if isinstance(labels, list):
        for label in labels:
            cleaned = str(label).strip()
            if cleaned:
                clean_labels.append(cleaned)
    elif isinstance(labels, str):
        clean_labels = [tag.strip() for tag in labels.split(',') if tag.strip()]

    post_body = {
        'kind': 'blogger#post',
        'title': title,
        'content': body_html,
        'labels': clean_labels
    }
    
    request = service.posts().insert(blogId=blog_id, body=post_body)
    return request.execute()
