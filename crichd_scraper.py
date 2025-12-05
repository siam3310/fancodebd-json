
import urllib.request
import re
import http.client
import ssl

# Disable SSL certificate verification (useful for some sites, but use with caution)
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Python < 2.7.9 / 3.4.3 doesn't support this
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

def get_page_content(url, headers={}):
    """Fetches the content of a URL."""
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def get_main_page_links():
    """Fetches all match and channel links from the crichd main page."""
    main_url = "https://v1.crichd.tv/web"
    print("Fetching main page...")
    content = get_page_content(main_url)
    
    if not content:
        print("Failed to fetch main page content.")
        return []

    links = re.findall(r'<a href="([^"]+)"[^>]*class="[^"]*event[^"]*"', content)
    channel_links = re.findall(r'<div class="channels">\\s*<a href="([^"]+)"', content)
    
    all_links = links + channel_links
    
    unique_links = sorted(list(set(all_links)))
    
    print(f"Found {len(unique_links)} unique links.")
    return unique_links

def get_stream_details(page_url):
    """Finds the stream details from a match/channel page."""
    print(f"Fetching page: {page_url}")
    content = get_page_content(page_url)
    if not content:
        return None, None

    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
    title = title_match.group(1).strip() if title_match else page_url.split('/')[-1].replace('-', ' ').title()

    # First, look for the 'embeds' array pattern
    embeds_match = re.search(r'embeds\\[\\d+\\]\\s*=\\s*\\\'<iframe src="([^"]+)"', content)
    if embeds_match:
        iframe_src = embeds_match.group(1)
        if 'streamcrichd.com' in iframe_src:
            return "https:" + iframe_src, title
            
    # If not found, look for direct crichdplayer.com links
    player_link_match = re.search(r'href="(https://crichdplayer.com/[^"]+)"', content)
    if player_link_match:
        return player_link_match.group(1), title
        
    print(f"No stream details found on {page_url}")
    return None, None

def get_final_m3u8_from_stream_page(stream_url):
    """Gets the final m3u8 link from any of the intermediate stream pages."""
    print(f"Fetching stream page: {stream_url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://v1.crichd.tv/' 
    }
    content = get_page_content(stream_url, headers=headers)
    if not content:
        return None

    # The golden regex to find the obfuscated URL array
    url_parts_match = re.search(r'return\\(\\[(\\"[^\\\]]+\\")\\]\\.join', content)
    
    if url_parts_match:
        url_parts_str = url_parts_match.group(1)
        url_chars = [part.strip() for part in url_parts_str.replace('"', '').split(',')]
        final_url = "".join(url_chars)
        print(f"SUCCESS! Found m3u8 link: {final_url}")
        return final_url
        
    # If the first pattern fails, lets try to find the 'fid' and follow the 'profamouslife' path
    fid_match = re.search(r'fid="([^"]+)"', content)
    if fid_match:
        fid = fid_match.group(1)
        premium_php_url = f"https://profamouslife.com/premium.php?player=desktop&live={fid}"
        print(f"Found fid, constructed premium.php URL: {premium_php_url}")
        return get_final_m3u8_from_stream_page(premium_php_url) # Recursive call

    print(f"Could not find m3u8 link on {stream_url}")
    return None

def generate_m3u_playlist():
    """The main function to generate the M3U playlist."""
    
    page_links = get_main_page_links()
    if not page_links:
        print("Could not retrieve any links from the main page. Aborting.")
        return

    m3u_content = "#EXTM3U\\n"
    
    for link in page_links:
        stream_url, title = get_stream_details(link)
        if not stream_url:
            continue
            
        final_link = get_final_m3u8_from_stream_page(stream_url)
            
        if final_link:
            m3u_content += f'#EXTINF:-1 tvg-name="{title}",{title}\\n'
            m3u_content += f'{final_link}\\n'
        
        print("-" * 20)

    try:
        with open("crichd_playlist.m3u", "w", encoding='utf-8') as f:
            f.write(m3u_content)
        print("Playlist 'crichd_playlist.m3u' generated successfully!")
    except IOError as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    generate_m3u_playlist()
