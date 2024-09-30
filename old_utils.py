import requests
from bs4 import BeautifulSoup
import srt
from datetime import timedelta
import os

class LFCSeriesScraper:
    def __init__(self, series_title, series_id, output_directory):
        """
        Initialize the Series class with the given series ID.
        
        :param series_id: The ID of the series.
        """
        self.series_title = series_title
        self.series_id = series_id
        self.main_url = f'https://chinese.littlefox.com/en/story/contents_list/{self.series_id}'
        self.output_subdirectory = os.path.join(output_directory, self.normalize_title(self.series_title))

        self.ep_infos = self.collect_ep_infos()

    def __repr__(self) -> str:
        return f"Series(title={self.series_title}, id={self.series_id})"

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

        driver = webdriver.Chrome()

        # sign in
        driver.get("https://chinese.littlefox.com/en")
        driver.find_element(By.NAME, 'loginid').send_keys(username)
        driver.find_element(By.NAME, 'loginpw').send_keys(password)
        driver.find_element(By.CLASS_NAME, 'btn_login').click()

        time.sleep(3)

        for page_url in page_urls:
            driver.get(page_url)
        
            # Wait for the parent element to be present
            list_wrap = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'list_wrap'))
            )
            # Find the thumb_wrap elements within the list_wrap
            thumb_wraps = list_wrap.find_elements(By.CLASS_NAME, 'thumb_wrap')

            # Loop through each element and click on it
            for i in range(len(thumb_wraps)):
                # Refetch the thumb_wrap elements
                list_wrap = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'list_wrap'))
                )
                thumb_wraps = list_wrap.find_elements(By.CLASS_NAME, 'thumb_wrap')
                
                # Wait for the specific element to be clickable
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(thumb_wraps[i])
                ).click()
                time.sleep(5)  # Adjust the sleep time as needed to allow for page load or other actions
                driver.get("https://chinese.littlefox.com/en/player_h5/view")
                
                # Extract the page source
                page_source = driver.page_source
                
                # Use regex to find the stream.m3u8 URL
                match = re.search(r'video_url":"(\\/contents_5\\/cn\\/hls\\/1080\\/[^"]+\\/stream\.m3u8\?_[^"]+)"', page_source)
                if match:
                    stream_url = os.path.join('https://cdn.littlefox.co.kr', match.group(1).replace('\\/', '/'))
                    print(f"Found stream URL: {stream_url}")
                    stream_urls.append(stream_url)
                else:
                    print("Stream URL not found")
                    stream_urls.append(None)
                
                # Navigate back to the content list page
                driver.get(page_url)
                time.sleep(3)  # Adjust the sleep time as needed to allow for page load or other actions

            driver.quit()

    def collect_ep_infos(self):
        '''
        Collect episode information for all episodes in the series. 
        '''
        infos = []
        ep_ids = self.get_ep_ids()
        ep_titles = self.get_ep_titles()
        stream_urls = self.get_stream_urls()
        for i in range(len(ep_ids)):
            dic = {}
            dic['id'] = ep_ids[i]
            dic['title'] = ep_titles[i]
            dic['subdirectory_path'] = os.path.join(self.output_subdirectory, f'{i+1}_{ep_titles[i]}')
            os.makedirs(dic['subdirectory_path'], exist_ok=True) # create the folder for each episode
            dic['xml_path'] = os.path.join(dic['subdirectory_path'], f'{i+1}_{ep_titles[i]}.xml')
            dic['xml_url'] = f'https://cdn.littlefox.co.kr/cn/captionxml/{ep_ids[i]}.xml'
            dic['srt_path'] = os.path.join(dic['subdirectory_path'], f'{i+1}_{ep_titles[i]}.srt')
            dic['txt_path'] = os.path.join(dic['subdirectory_path'], f'{i+1}_{ep_titles[i]}.txt')
            dic['stream_url'] = stream_urls[i]
            dic['stream_path'] = os.path.join(dic['subdirectory_path'], f'{i+1}_{ep_titles[i]}.m3u8')
            dic['mp4_path'] = os.path.join(dic['subdirectory_path'], f'{i+1}_{ep_titles[i]}.mp4')
            infos.append(dic)
        return infos

    def download_xml_subtitles(self):
        paths = [ep_info['xml_path'] for ep_info in self.ep_infos]
        urls = [ep_info['xml_url'] for ep_info in self.ep_infos]

        for path, url in zip(paths, urls):
            response = requests.get(url)
            if response.status_code == 200:
                with open(path, 'wb') as file:
                    file.write(response.content)
                print(f"File downloaded successfully: {path}")
            else:
                print(f"Failed to download file from {url}: {response.status_code}")

    def convert_xml_to_srt(self):
        '''The subtitles on Little Fox Chinese are in XML format. We need to convert them to SRT format.'''
        def ms_to_timedelta(ms):
            return timedelta(milliseconds=int(ms))

        xml_paths = [ep_info['xml_path'] for ep_info in self.ep_infos]
        srt_paths = [ep_info['srt_path'] for ep_info in self.ep_infos]

        for xml_path, srt_path in zip(xml_paths, srt_paths):
            with open(xml_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'xml')

            subtitles = []

            paragraphs = soup.find_all('Paragraph')
            for paragraph in paragraphs:
                # Extract the subtitle number, start time, end time, and text
                start = ms_to_timedelta(paragraph.find('StartMilliseconds').text)
                end = ms_to_timedelta(paragraph.find('EndMilliseconds').text)
                text = paragraph.find('Text').text
                subtitles.append(srt.Subtitle(index=len(subtitles) + 1, start=start, end=end, content=text))

            with open(srt_path, 'w', encoding='utf-8') as file: 
                file.write(srt.compose(subtitles))

            print(f"File converted successfully: {srt_path}")

    def save_subtitles(self):
        '''Download the xml subtitles and then convert them to srt format'''
        self.download_xml_subtitles()
        self.convert_xml_to_srt()



    def normalize_title(self, title):
        return title.lower().strip().replace(' ', '-')