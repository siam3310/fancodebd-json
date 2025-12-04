
import requests
import json

def transform_urls():
    """Fetches JSON data, transforms URLs, and saves it to a file."""
    try:
        response = requests.get("https://raw.githubusercontent.com/drmlive/fancode-live-events/refs/heads/main/fancode.json")
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        if "matches" in data and isinstance(data["matches"], list):
            for match in data["matches"]:
                if "adfree_url" in match and isinstance(match["adfree_url"], str) and match["adfree_url"].startswith("https://in-mc-fdlive.fancode.com/"):
                    match["adfree_url"] = match["adfree_url"].replace("https://in-mc-fdlive.fancode.com/", "https://bd-mc-fdlive.fancode.com/")

        with open("fancodebd_by_siam.json", "w") as f:
            json.dump(data, f, indent=4)

        print("Transformation complete. Check fancodebd_by_siam.json")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

if __name__ == "__main__":
    transform_urls()
