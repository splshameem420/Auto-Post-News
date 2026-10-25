from googleapiclient.errors import HttpError


def publish_post(service, blog_id, title, content, image_url=None, labels=[]):  # noqa: B006
    body_html = ""
    if image_url:
        body_html += (
            f'<div style="text-align:center; margin-bottom:15px;">'
            f'<img src="{image_url}" style="max-width:100%; height:auto; border-radius:8px;"/>'
            f'</div>'
        )
    
    formatted_content = content.replace("\n", "<br>")
    body_html += f'<div>{formatted_content}</div>'

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
    try:
        request = service.posts().insert(blogId=blog_id, body=post_body)
        response = request.execute()
        return response
    except HttpError as e:
        print(f"An error occurred: {e}")
        return None
    
    except Exception as e:  # noqa: BLE001
        print(f"An unexpected error occurred: {e}")
        return None
