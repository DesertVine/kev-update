# cisa_kev_rss_updater.py

import requests
import os
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree
import xml.etree.ElementTree as ET

# Constants
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
STATE_FILE = "last_release.txt"
RSS_FILE = "docs/rss.xml"
FEED_URL = "https://desertvine.github.io/kev-update/rss.xml"

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

# Helper: Create or update RSS feed with max 20 items and CVE summary
def create_rss(updated_date, kev_data):
    MAX_ITEMS = 20

    # Extract new CVEs based on matching dateAdded
    date_str = updated_date.split("T")[0]
    new_cves = [
        v["cveID"] for v in kev_data.get("vulnerabilities", [])
        if v.get("dateAdded") == date_str
    ]

    if new_cves:
        cve_summary = f"This update includes {len(new_cves)} new CVE(s): " + ", ".join(new_cves)
    else:
        cve_summary = "CISA updated the KEV catalog, but no specific CVEs matched the release date."

    new_item = {
        "title": f"KEV Catalog Updated: {date_str}",
        "link": KEV_URL,
        "description": f"CISA updated the KEV catalog on {date_str}. {cve_summary}",
        "guid": updated_date,
        "pubDate": datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    }

    items = []

    # Load existing items from RSS file
    if os.path.exists(RSS_FILE):
        try:
            tree = ET.parse(RSS_FILE)
            root = tree.getroot()
            for item in root.find('channel').findall('item'):
                i = {
                    "title": item.findtext("title"),
                    "link": item.findtext("link"),
                    "description": item.findtext("description"),
                    "guid": item.findtext("guid"),
                    "pubDate": item.findtext("pubDate")
                }
                items.append(i)
        except Exception as e:
            print(f"Error reading existing RSS: {e}")

    # Insert new item and limit to 20
    items.insert(0, new_item)
    items = items[:MAX_ITEMS]

    # Rebuild RSS feed
    rss = Element('rss', version='2.0')
    channel = SubElement(rss, 'channel')
    SubElement(channel, 'title').text = "CISA KEV Catalog Updates"
    SubElement(channel, 'link').text = FEED_URL
    SubElement(channel, 'description').text = "This feed notifies when CISA updates the KEV catalog."
    SubElement(channel, 'language').text = "en-us"

    for item in items:
        entry = SubElement(channel, 'item')
        SubElement(entry, 'title').text = item["title"]
        SubElement(entry, 'link').text = item["link"]
        SubElement(entry, 'description').text = item["description"]
        SubElement(entry, 'guid').text = item["guid"]
        SubElement(entry, 'pubDate').text = item["pubDate"]

    tree = ElementTree(rss)
    os.makedirs(os.path.dirname(RSS_FILE), exist_ok=True)
    tree.write(RSS_FILE, encoding='utf-8', xml_declaration=True)

# Main function
def main():
    try:
        response = requests.get(KEV_URL)
        response.raise_for_status()
        kev_data = response.json()
    except Exception as e:
        print(f"Error fetching KEV data: {e}")
        return

    current_release_date = kev_data.get("dateReleased", "")
    last_release_date = load_last_release()

    if current_release_date != last_release_date:
        print(f"New update detected: {current_release_date}")
        create_rss(current_release_date, kev_data)
        save_last_release(current_release_date)
    else:
        print("No new update.")

if __name__ == "__main__":
    main()
