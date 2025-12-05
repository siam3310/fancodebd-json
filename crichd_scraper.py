
import re
import urllib.request
import ssl

# --- Configuration ---
# List of channel pages to scrape. Add or remove URLs as needed.
CHANNELS = [
    # Cricket
    "https://v1.crichd.tv/sky-sports-cricket-live-stream-me-1",
    "https://v1.crichd.tv/willow-cricket-live-stream-play-01",
    "https://v1.crichd.tv/star-sports-1-live-stream-play-01",
    "https://v1.crichd.tv/ptv-sports-live-stream-play-01",
    "https://v1.crichd.tv/ten-sports-live-stream-play-01",
    "https://v1.crichd.tv/a-sports-hd-live-streaming-play-01",
    "https://v1.crichd.tv/fox-cricket-501-live-stream-play-01",
    "https://v1.crichd.tv/supersport-cricket-live-stream-play-01",
    
    # UK Sports
    "https://v1.crichd.tv/sky-sports-main-event-live-stream-play3",
    "https://v1.crichd.tv/sky-sports-premier-league-live-stream-play3",
    "https://v1.crichd.tv/sky-sports-football-live-stream-play3",
    "https://v1.crichd.tv/sky-sports-f1-live-streaming-f17",
    "https://v1.crichd.tv/tnt-sports-1-live-stream-uk-01",
    "https://v1.crichd.tv/tnt-sports-2-live-stream-uk-01",
    "https://v1.crichd.tv/tnt-sports-3-live-stream-uk-01",
    "https://v1.crichd.tv/tnt-sports-4-live-stream-uk-01",

    # US Sports
    "https://v1.crichd.tv/espn-us-live-stream-play",
    "https://v1.crichd.tv/espn-2-us-live-stream-play",
]

# --- SSL Configuration ---
# Disables SSL certificate verification. Use with caution.
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# --- Core Functions ---

def get_page_content(url, headers={}):
    """Fetches and returns the content of a given URL."""
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"    [!] Error fetching {url}: {e}")
        return None

def extract_stream_details(channel_url):
    """Follows the chain of pages to extract the final m3u8 link and title."""
    print(f"[1] Processing Channel: {channel_url}")
    
    # Step 1: Get the initial iframe from the main channel page
    main_content = get_page_content(channel_url)
    if not main_content:
        return None, None
        
    title_match = re.search(r'<h1.*?>(.*?)</h1>', main_content)
    title = title_match.group(1).strip() if title_match else channel_url.split('/')[-1]

    iframe_match = re.search(r'<iframe src="(//streamcrichd.com/[^"]+)"', main_content)
    if not iframe_match:
        print("    [!] Could not find streamcrichd.com iframe.")
        return None, title

    streamcrichd_url = "https:" + iframe_match.group(1)
    print(f"    [>] Found streamcrichd URL: {streamcrichd_url}")
    
    # Step 2: Get the 'fid' from the streamcrichd page
    streamcrichd_content = get_page_content(streamcrichd_url, headers={'Referer': 'https://v1.crichd.tv/'})
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
    profamouslife_content = get_page_content(profamouslife_url, headers={'Referer': 'https://streamcrichd.com/'})
    if not profamouslife_content:
        return None, title

    # Step 4: The Golden Regex - Extract the character array for the m3u8 link
    m3u8_parts_match = re.search(r'return\(\[([^\]]+)\]\.join', profamouslife_content)
    if not m3u8_parts_match:
        print("    [!] FATAL: Could not find the obfuscated m3u8 array.")
        return None, title

    url_parts_str = m3u8_parts_match.group(1)
    # Clean up the string and join the characters to form the final URL
    url_chars = [part.strip().replace('"', '').replace('\\/','/') for part in url_parts_str.split(',')]
    final_m3u8_url = "".join(url_chars)
    # A final cleanup to remove any extra slashes that sometimes appear
    final_m3u8_url = re.sub(r':/+', '://', final_m3u8_url)

    print(f"    [+] SUCCESS: Extracted M3U8 link: {final_m3u8_url}")
    return final_m3u8_url, title

def main():
    """Main function to generate the M3U playlist."""
    m3u_header = "#EXTM3U\n"
    playlist_entries = []

    print("--- Starting CricHD Channel Scraper ---")
    for channel_url in CHANNELS:
        m3u8_link, title = extract_stream_details(channel_url)
        if m3u8_link and title:
            entry = f'#EXTINF:-1 tvg-id="{title}" group-title="CricHD",{title}\n{m3u8_link}\n'
            playlist_entries.append(entry)
        print("-" * 30)

    if not playlist_entries:
        print("No stream links were found. The playlist will be empty.")
        final_playlist = m3u_header
    else:
        final_playlist = m3u_header + "\n".join(playlist_entries)

    try:
        with open("crichd_playlist.m3u", "w", encoding='utf-8') as f:
            f.write(final_playlist)
        print(f"--- Playlist Generation Complete! ---")
        print(f"Successfully wrote {len(playlist_entries)} channels to crichd_playlist.m3u")
    except IOError as e:
        print(f"[!] Error writing playlist to file: {e}")

if __name__ == "__main__":
    main()
