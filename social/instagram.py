import requests
import os
import time

class InstagramPublisher:
    def __init__(self):
        self.access_token = os.getenv("IG_ACCESS_TOKEN")
        self.ig_user_id = os.getenv("IG_USER_ID")
        self.graph_url = "https://graph.facebook.com/v19.0"

    def is_configured(self):
        return bool(self.access_token and self.ig_user_id)

    def publish_post(self, image_url: str, caption: str) -> bool:
        if not self.is_configured():
            print("\n[!] Instagram API is not configured. Mocking success.")
            return True

        try:
            # 1. Create Media Container
            container_url = f"{self.graph_url}/{self.ig_user_id}/media"
            payload = {
                "image_url": image_url,
                "caption": caption,
                "access_token": self.access_token
            }
            res = requests.post(container_url, data=payload)
            res.raise_for_status()
            creation_id = res.json().get("id")

            # 2. Check if media is ready (Wait a few seconds)
            time.sleep(5)

            # 3. Publish Media
            publish_url = f"{self.graph_url}/{self.ig_user_id}/media_publish"
            publish_payload = {
                "creation_id": creation_id,
                "access_token": self.access_token
            }
            res_pub = requests.post(publish_url, data=publish_payload)
            res_pub.raise_for_status()
            
            return True
        except Exception as e:
            print(f"Error publishing to Instagram: {e}")
            return False
