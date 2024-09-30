import json
import requests
from bs4 import BeautifulSoup
import os

class LFCSeriesScraper:
    homepage_url = 'https://chinese.littlefox.com/en/story'    

    def __init__(self, series_json):
        self.series_json = series_json
        with open(series_json, 'r') as f:
            self.series = json.load(f)

    def scrape_storys(self):
        """Adds the title, id and main url for each relevant story to the urls json

        Note: After scraping the stories, you should edit the 'single-stories' title to indicate which level
        they are. This information can't be scraped from the html.
        """
        response = requests.get(self.homepage_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        contents_divs = soup.find_all('div', class_='constents_wrap')

        for div in contents_divs:
            # We start at the 22nd series because the prior have fucked up subtitles and I don't want to parse them 
            id = div['data-smid']
            title = self.normalize_title(div.find('div', class_='thumb_titl').find('a').text)
            # main_url = os.path.join(self.homepage_url, 'contents_list', id)
        
            if id not in [entry['id'] for entry in self.series]:
                self.series.append({
                    'title': title,
                    'id': id,
                })
        
        self.write_series_json() 
         
    def normalize_title(self, title):
        return title.lower().strip().replace(' ', '-')

    def write_series_json(self):
        with open(self.series_json, 'w') as f:
            json.dump(self.series, f, indent=4)


class LFCURLScraper:
    def __init__(self, title, id, urls_json):
        self.title = title
        self.id = id
        self.urls_json = urls_json
        with open(urls_json, 'r') as f:
            self.urls = json.load(f)
        self.main_url = f"https://chinese.littlefox.com/en/story/contents_list/{id}"

    
    def setup_json(self):
        self.urls[self.title] = [] 

        titles = self.get_ep_titles()
        ids = self.get_ep_ids()

        for title, id in zip(titles, ids):
            self.urls[self.title].append({
                'title': title,
                'id': id
            })

        self.write_urls_json()

    def get_page_count(self):
        """
        Get the total number of pages for the series.
        
        :return: The maximum page number or None if not found.
        """
        try:
            response = requests.get(self.main_url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching main URL: {e}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        paging_div = soup.find('div', class_='lf_paging')

        if paging_div:
            page_numbers = [
                int(a_tag.text) for a_tag in paging_div.find_all('a') if a_tag.text.isdigit()
            ]
            if page_numbers:
                return max(page_numbers)
        return None

    def get_page_urls(self):
        """
        Generate a list of URLs for all pages in the series.
        
        :return: A list of page URLs or None if no pages are found.
        """
        max_page_count = self.get_page_count()
        if max_page_count:
            return [f'{self.main_url}?&page={page}' for page in range(1, max_page_count + 1)]
        else:
            print("No pages found")
            return None

    def get_ep_ids(self):
        """
        Extract episode IDs from all pages in the series.
        
        :return: A list of episode IDs.
        """
        print(f'Getting episode IDs for {self.title}')
        page_urls = self.get_page_urls()
        if not page_urls:
            return []

        ids = []
        for url in page_urls:
            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Error fetching page URL {url}: {e}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('div', class_='item')
            ids.extend(
                input_element.get('value')
                for item in items
                if (input_element := item.find('input', class_='LF_CHK s2 contentsCheck'))
            )
        return ids
    
    def get_ep_titles(self):
        '''
        Extract episode titles from all pages in the series.

        :return: A list of episode titles.
        '''
        print(f'Getting episode titles for {self.title}')
        page_urls = self.get_page_urls()
        if not page_urls:
            return []
    
        titles = []
        for url in page_urls:
            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Error fetching page URL {url}: {e}")
                continue
    
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('div', class_='item')
            titles.extend(
                item.find('span', class_='story_title_en').text.strip()
                for item in items
                if item.find('span', class_='story_title_en')
            )
        return titles

    def write_xml_urls(self):
        for i, ep in enumerate(self.urls[self.title]):
            xml_url = f'https://cdn.littlefox.co.kr/cn/captionxml/{ep['id']}.xml'
            self.urls[self.title][i]['xml_url'] = xml_url
        
        self.write_urls_json()


    def get_stream_urls(self):
        '''Get the urls for the .m3u8 stream files'''
        from selenium import webdriver 
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import re
        import time
    
        from dotenv import load_dotenv
        import os
    
        load_dotenv()
    
        username = os.getenv('LFC_USERNAME')
        password = os.getenv('LFC_PASSWORD')
    
        stream_urls = []        
    
        page_urls = self.get_page_urls()
        print(f"Page URLs: {page_urls}")
    
        driver = webdriver.Chrome()
    
        # sign in
        print("Navigating to login page...")
        driver.get("https://chinese.littlefox.com/en")
        driver.find_element(By.NAME, 'loginid').send_keys(username)
        driver.find_element(By.NAME, 'loginpw').send_keys(password)
        driver.find_element(By.CLASS_NAME, 'btn_login').click()
    
        time.sleep(3)
        print("Logged in successfully.")
    
        for page_url in page_urls:
            print(f"Navigating to page URL: {page_url}")
            driver.get(page_url)
        
            # Wait for the parent element to be present
            list_wrap = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'list_wrap'))
            )
            print("Found list_wrap element.")
    
            # Find the thumb_wrap elements within the list_wrap
            thumb_wraps = list_wrap.find_elements(By.CLASS_NAME, 'thumb_wrap')
            print(f"Found {len(thumb_wraps)} thumb_wrap elements.")
    
            # Loop through each element and click on it
            for i in range(len(thumb_wraps)):
                print(f"Processing thumb_wrap element {i+1}/{len(thumb_wraps)}")
                # Refetch the thumb_wrap elements
                list_wrap = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'list_wrap'))
                )
                thumb_wraps = list_wrap.find_elements(By.CLASS_NAME, 'thumb_wrap')
                
                # Wait for the specific element to be clickable
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(thumb_wraps[i])
                ).click()
                print(f"Clicked on thumb_wrap element {i+1}")
                time.sleep(5)  # Adjust the sleep time as needed to allow for page load or other actions
                driver.get("https://chinese.littlefox.com/en/player_h5/view")
                
                # Extract the page source
                page_source = driver.page_source
                
                # Use regex to find the stream.m3u8 URL
                match = re.search(r'video_url":"(\\/contents_5\\/cn\\/hls\\/1080\\/[^"]+\\/stream\.m3u8\?_[^"]+)"', page_source)
                if match:
                    stream_url = f'https://cdn.littlefox.co.kr/{match.group(1).replace('\\/', '/')}'
                    print(f"Found stream URL: {stream_url}")
                    stream_urls.append(stream_url)
                else:
                    print("Stream URL not found")
                    stream_urls.append(None)
                
                # Navigate back to the content list page
                driver.get(page_url)
                time.sleep(3)  # Adjust the sleep time as needed to allow for page load or other actions
    
        driver.quit()
        print("Closed the browser.")
    
        return stream_urls

    def write_stream_urls(self):
        # Check if all episodes already have a 'stream_url'
        all_have_stream_urls = all('stream_url' in ep for ep in self.urls[self.title])

        if not all_have_stream_urls:
            stream_urls = self.get_stream_urls()
            for i, url in enumerate(stream_urls):
                print(f"Updating URL for index {i}: {url}")
                self.urls[self.title][i]['stream_url'] = url

            self.write_urls_json()
            print("URLs written to JSON.")
        else:
            print("All episodes already have stream URLs.")

    def normalize_title(self, title):
        return title.lower().strip().replace(' ', '-')

    def write_urls_json(self):
        with open(self.urls_json, 'w') as f:
            json.dump(self.urls, f, indent=4)