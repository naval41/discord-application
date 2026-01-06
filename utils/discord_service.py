import requests
import json
import os

class DiscordSender:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, "r") as f:
            self.config = json.load(f)
        
        self.token = self.config.get("discord_token")
        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }

    def send_message(self, channel_id, content=None, embed=None):
        """
        Sends a message to a Discord channel. 
        Supports content text and/or an embed dictionary.
        """
        if not self.token:
            print("Error: No Discord token found in config.")
            return None

        url = f"{self.base_url}/channels/{channel_id}/messages"
        payload = {}
        if content:
            payload["content"] = content
        if embed:
            payload["embeds"] = [embed]
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"Failed to send Discord message: {e}")
            if e.response is not None:
                print(f"Response: {e.response.text}")
            return None
        except Exception as e:
            print(f"Error sending Discord message: {e}")
            return None
