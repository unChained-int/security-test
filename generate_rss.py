#!/usr/bin/env python3
import feedparser
import requests
from datetime import datetime, timezone
from dateutil import parser as date_parser
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time

RSS_FEEDS = [
    # IT-Security
    "https://feeds.feedburner.com/TheHackersNews?format=xml",
    "https://krebsonsecurity.com/feed/",
    "https://www.darkreading.com/rss.xml",
    "https://www.welivesecurity.com/en/rss/feed/",
    "https://www.infosecurity-magazine.com/rss/news/",
    "https://www.nist.gov/blogs/cybersecurity-insights/rss.xml",
    "https://www.techrepublic.com/rssfeeds/topic/cybersecurity/",
    "https://www.proofpoint.com/us/rss.xml",
    "https://www.upguard.com/blog/rss.xml",
    "https://blog.pcisecuritystandards.org/rss.xml",
    "https://www.securityweek.com/feed",
    "https://threatpost.com/feed/",
    "https://www.schneier.com/feed/atom/",
    # Datenschutz / Privacy
    "https://privacyinternational.org/rss/news",
    "https://edps.europa.eu/press-publications/press-news/rss_en",
    "https://www.enforceprivacy.com/feed/",
    "https://www.dlapiperdataprotection.com/feed/",
    # IT-Security Policy / Cyber Policy
    "https://www.enisa.europa.eu/news/feed",
    "https://www.enisa.europa.eu/newsroom/rss",
    "https://www.bsi.bund.de/SharedDocs/RSS/DE/rss.xml",
    "https://www.cisa.gov/news-events/rss.xml",
    "https://www.techpolicy.com/feed/"
]

def fetch_feed(url):
    """Holt einen RSS-Feed von einer URL"""
    try:
        print(f"Fetching: {url}")
        response = requests.get(url, timeout=10, headers={'User-Agent': 'RSS-Aggregator/1.0'})
        feed = feedparser.parse(response.content)
        return feed
    except Exception as e:
        print(f"Fehler beim Abrufen von {url}: {e}")
        return None

def parse_date(entry):
    """Konvertiert verschiedene Datumsformate in datetime"""
    from datetime import timezone
    
    date_fields = ['published', 'updated', 'created']
    
    for field in date_fields:
        if hasattr(entry, field):
            try:
                parsed_date = date_parser.parse(getattr(entry, field))
                # Stelle sicher, dass alle Datumsangaben timezone-aware sind
                if parsed_date.tzinfo is None:
                    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                return parsed_date
            except:
                pass
    
    # Fallback auf aktuelles Datum (timezone-aware)
    return datetime.now(timezone.utc)

def sanitize_text(text):
    """Bereinigt Text für XML"""
    if not text:
        return ""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')

def create_rss_feed(entries, max_entries=100):
    """Erstellt einen RSS 2.0 Feed aus den gesammelten Einträgen"""
    
    # Root Element
    rss = ET.Element('rss', version='2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    rss.set('xmlns:dc', 'http://purl.org/dc/elements/1.1/')
    
    channel = ET.SubElement(rss, 'channel')
    
    # Feed Metadaten
    ET.SubElement(channel, 'title').text = 'IT-Security & Privacy News Aggregator'
    ET.SubElement(channel, 'link').text = 'https://github.com/unChained-int/security-test'
    ET.SubElement(channel, 'description').text = 'Aggregierter RSS-Feed aus führenden IT-Security, Privacy und Cyber Policy Quellen'
    ET.SubElement(channel, 'language').text = 'de'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
    ET.SubElement(channel, 'generator').text = 'RSS-Aggregator Script'
    
    # Atom Self-Link
    atom_link = ET.SubElement(channel, 'atom:link')
    atom_link.set('href', 'https://raw.githubusercontent.com/unChained-int/security-test/main/feed.xml')
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    # Sortiere Einträge nach Datum (neueste zuerst)
    entries.sort(key=lambda x: x['date'], reverse=True)
    
    # Füge Items hinzu (begrenzt auf max_entries)
    for entry_data in entries[:max_entries]:
        item = ET.SubElement(channel, 'item')
        
        ET.SubElement(item, 'title').text = entry_data['title']
        ET.SubElement(item, 'link').text = entry_data['link']
        ET.SubElement(item, 'description').text = entry_data['description']
        ET.SubElement(item, 'pubDate').text = entry_data['date'].strftime('%a, %d %b %Y %H:%M:%S %z')
        ET.SubElement(item, 'guid', isPermaLink='true').text = entry_data['link']
        
        if entry_data.get('author'):
            ET.SubElement(item, 'dc:creator').text = entry_data['author']
        
        if entry_data.get('source'):
            source = ET.SubElement(item, 'source', url=entry_data['source'])
            source.text = entry_data['source_name']
        
        # Kategorien/Tags
        for category in entry_data.get('categories', []):
            ET.SubElement(item, 'category').text = category
    
    return rss

def prettify_xml(elem):
    """Formatiert XML schön"""
    rough_string = ET.tostring(elem, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='utf-8')

def main():
    print("Starte RSS-Aggregation...")
    all_entries = []
    
    for feed_url in RSS_FEEDS:
        feed = fetch_feed(feed_url)
        
        if not feed or not hasattr(feed, 'entries'):
            continue
        
        # Extrahiere Feed-Informationen
        feed_title = getattr(feed.feed, 'title', 'Unknown Source')
        
        for entry in feed.entries:
            # Extrahiere Entry-Daten
            entry_data = {
                'title': sanitize_text(getattr(entry, 'title', 'Kein Titel')),
                'link': getattr(entry, 'link', ''),
                'description': sanitize_text(getattr(entry, 'summary', getattr(entry, 'description', ''))),
                'date': parse_date(entry),
                'author': sanitize_text(getattr(entry, 'author', '')),
                'source': feed_url,
                'source_name': sanitize_text(feed_title),
                'categories': [sanitize_text(tag.term) for tag in getattr(entry, 'tags', [])]
            }
            
            all_entries.append(entry_data)
        
        # Kleine Pause zwischen Requests
        time.sleep(0.5)
    
    print(f"\nInsgesamt {len(all_entries)} Einträge gesammelt")
    
    # Erstelle RSS Feed
    rss_feed = create_rss_feed(all_entries, max_entries=100)
    
    # Schreibe in Datei
    xml_content = prettify_xml(rss_feed)
    
    with open('feed.xml', 'wb') as f:
        f.write(xml_content)
    
    print("RSS Feed erfolgreich erstellt: feed.xml")

if __name__ == '__main__':
    main()
