from old_utils import LFCSeriesScraper
import requests
from bs4 import BeautifulSoup

homepage_url = 'https://chinese.littlefox.com/en/story'
try:
    response = requests.get(homepage_url)
    response.raise_for_status()
except requests.RequestException as e:
    print(f"Error fetching main URL: {e}")

soup = BeautifulSoup(response.text, 'html.parser')
contents_divs = soup.find_all('div', class_='constents_wrap')
series_scrapers = []

for div in contents_divs[22:23]:
    # We start at the 22nd series because the prior have fucked up subtitles and I don't want to parse them 
    id = div['data-smid']
    title = div.find('div', class_='thumb_titl').find('a').text
    print(id, title)
    # series_scrapers.append(LFCSeriesScraper(title, id, 'output'))


# Adjust names of 'Single Stories' series as to differentiate them.
# series_scrapers[0].series_title = "Single Stories 3"
# series_scrapers[9].series_title = "Single Stories 4"
# series_scrapers[16].series_title = "Single Stories 5"

# for scraper in series_scrapers:
#     print(scraper.ep_infos)