# cisa_kev_rss_updater.py

import requests
import json
import os
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree

# Constants
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
STATE_FILE = "last_release.txt"
RSS_FILE = "docs/rss.xml"
FEED_URL = "https://<your-username>.github.io/<your-repo>/rss.xml"

# Helper: Load previous release date
def load_last_release():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, 'r') as f:
        return f.read().strip()

# Helper: Save current release date
def save_last_release(date_str):
    with open(STATE_FILE, 'w') as f:
        f.write(date_str)

# Helper: Create RSS feed
def create_rss(updated_date):
    rss = Element('rss', version='2.0')
    channel = SubElement(rss, 'channel')

    SubElement(channel, 'title').text = "CISA KEV Catalog Updates"
    SubElement(channel, 'link').text = FEED_URL
    SubElement(channel, 'description').text = "This feed notifies when CISA updates the KEV catalog."
    SubElement(channel, 'language').text = "en-us"

    item = SubElement(channel, 'item')
    SubElement(item, 'title').text = f"KEV Catalog Updated: {updated_date}"
    SubElement(item, 'link').text = KEV_URL
    SubElement(item, 'guid').text = updated_date
    SubElement(item, 'pubDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    SubElement(item, 'description').text = f"CISA updated the KEV catalog on {updated_date}."

    tree = ElementTree(rss)
    os.makedirs(os.path.dirname(RSS_FILE), exist_ok=True)
    tree.write(RSS_FILE, encoding='utf-8', xml_declaration=True)

# Main function
def main():
    response = requests.get(KEV_URL)
    kev_data = response.json()
    current_release_date = kev_data.get("releaseDate", "")

    last_release_date = load_last_release()

    if current_release_date != last_release_date:
        print(f"New update detected: {current_release_date}")
        create_rss(current_release_date)
        save_last_release(current_release_date)
    else:
        print("No new update.")

if __name__ == "__main__":
    main()
