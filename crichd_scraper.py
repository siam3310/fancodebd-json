
import requests
import re
import json
import urllib3

# --- Configuration ---
CHANNELS = [
    "https://v1.crichd.tv/sky-sports-cricket-live-stream-me-1",
]

# Define a standard browser User-Agent
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

# --- Core Functions ---
def get_page_content(url, referer=None):
    """Fetches content from a URL with a browser-like User-Agent and optional referer."""
    try:
        # Add referer to the main headers if it exists
        request_headers = HEADERS.copy()
        if referer:
            request_headers['Referer'] = referer

        # Disabling SSL verification as the JS version did
        response = requests.get(url, headers=request_headers, timeout=20, verify=False)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"    [!] Error fetching {url}: {e}")
        return None

# ... (The rest of the script remains the same) ...

def extract_stream_details(channel_url):
    """Extracts the M3U8 link and title from a CricHD channel page."""
    print(f"[1] Processing Channel: {channel_url}")

    # Step 1: Get title and the initial iframe from the main channel page
    main_content = get_page_content(channel_url)
    if not main_content:
        return None, None

    title_match = re.search(r'<h1.*?>(.*?)</h1>', main_content)
    title = title_match.group(1).strip() if title_match else "Unknown Channel"

    iframe_match = re.search(r'<iframe src="(//streamcrichd.com/[^"]+)"', main_content)
    if not iframe_match:
        print("    [!] Could not find streamcrichd.com iframe.")
        return None, title

    streamcrichd_url = "https:" + iframe_match.group(1)
    print(f"    [>] Found streamcrichd URL: {streamcrichd_url}")

    # Step 2: Get the 'fid' from the streamcrichd page
    streamcrichd_content = get_page_content(streamcrichd_url, referer="https://v1.crichd.tv/")
    if not streamcrichd_content:
        return None, title

    fid_match = re.search(r'fid="([^"]+)"', streamcrichd_content)
    if not fid_match:
        print("    [!] Could not find 'fid' on streamcrichd page.")
        return None, title
    
    fid = fid_match.group(1)
    print(f"    [>] Found fid: {fid}")

    # Step 3: Get the final obfuscated script from the profamouslife page
    profamouslife_url = f"https://profamouslife.com/premium.php?player=desktop&live={fid}"
    profamouslife_content = get_page_content(profamouslife_url, referer="https://streamcrichd.com/")
    if not profamouslife_content:
        return None, title

    # Step 4: The Golden Regex - Extract and decode the m3u8 link
    m3u8_parts_match = re.search(r'return\(\[([^\]]+)\]\.join', profamouslife_content)
    if not m3u8_parts_match:
        print("    [!] FATAL: Could not find the obfuscated m3u8 array.")
        return None, title

    url_parts_str = f'[{m3u8_parts_match.group(1)}]'
    
    try:
        url_chars = json.loads(url_parts_str)
        final_m3u8_url = "".join(url_chars)
        final_m3u8_url = re.sub(r':/+', '://', final_m3u8_url)
        print(f"    [+] SUCCESS: Extracted M3U8 link.")
        return final_m3u8_url, title
    except json.JSONDecodeError as e:
        print(f"    [!] FATAL: Could not decode the m3u8 array parts. Error: {e}")
        return None, title

def main():
    """Main function to scrape channels and create the M3U playlist."""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    m3u_header = "#EXTM3U"
    playlist_entries = []

    print("--- Starting CricHD Channel Scraper (Python) ---")

    for channel_url in CHANNELS:
        m3u8_link, title = extract_stream_details(channel_url)
        if m3u8_link and title:
            entry = f'#EXTINF:-1 tvg-id="{title}" group-title="CricHD",{title}\n{m3u8_link}'
            playlist_entries.append(entry)
        print("-" * 40)

    final_playlist = m3u_header
    if not playlist_entries:
        print("No stream links were found. The playlist will be empty.")
    else:
        final_playlist += "\n\n" + "\n\n".join(playlist_entries)

    try:
        with open("crichd_playlist.m3u", "w", encoding='utf-8') as f:
            f.write(final_playlist)
        print(f"--- Playlist Generation Complete! ---")
        print(f"Successfully wrote {len(playlist_entries)} channel(s) to crichd_playlist.m3u")
    except IOError as e:
        print(f"[!] Error writing playlist to file: {e}")

if __name__ == "__main__":
    main()
