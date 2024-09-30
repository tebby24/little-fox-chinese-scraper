import json
from utils import LFCSeriesScraper, LFCURLScraper


if __name__ == "__main__":
    # initialize scraper
    scraper = LFCSeriesScraper('series.json')

    # scrape the story titles, ids, and main urls
    # ! manually adjust the stories.json file to add the level number to the 'single-stories' titles
    scraper.scrape_storys()

    with open('series.json', 'r') as f:
        series = json.load(f)

    for s in series:
        url_scraper = LFCURLScraper(s['title'], s['id'], 'urls.json')

        # setup the json with episode title and ids
        # url_scraper.setup_json()

        # generate and write the subtitle .xml urls for each episode 
        # url_scraper.write_xml_urls()

        # scrape the stream.m3u8 urls
        while True:
            try:
                url_scraper.write_stream_urls()
                break  # Exit loop if successful
            except Exception as e:
                print(f"Attempt failed: {e}")
                # Optionally, add a delay before retrying
                # time.sleep(1)

