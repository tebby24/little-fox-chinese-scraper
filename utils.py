import json
import glob
import requests
from bs4 import BeautifulSoup
from datetime import timedelta
import srt
import re
import os
import concurrent.futures


def normalize_title(title):
    return title.lower().strip().replace(' ', '-')


class SeriesScraper:
    """
    This class is used to scrape information about the series on LFC.
    All the information is already stored in the file data/series.json, so you don't need to use this class. 
    """
    homepage_url = 'https://chinese.littlefox.com/en/story'    

    def __init__(self, series_json):
        self.series_json = series_json
        with open(series_json, 'r') as f:
            self.series = json.load(f)

    def scrape_series(self):
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
            title = normalize_title(div.find('div', class_='thumb_titl').find('a').text)
            # main_url = os.path.join(self.homepage_url, 'contents_list', id)
        
            if id not in [entry['id'] for entry in self.series]:
                self.series.append({
                    'title': title,
                    'id': id,
                })
        
        self.write_series_json() 
         
    def write_series_json(self):
        with open(self.series_json, 'w') as f:
            json.dump(self.series, f, indent=4)


class URLScraper:
    '''
    This class is used to scrape all the relevant urls from LFC.
    This includes .xml subtitle files and .m3u8 stream files.
    The urls are already stored in data/urls.json, so you do not need to use this class. 
    '''
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


    def write_urls_json(self):
        with open(self.urls_json, 'w') as f:
            json.dump(self.urls, f, indent=4)



class Downloader:
    '''This class is used to download the content written to the urls.json file
    '''
    def __init__(self, urls_json, output_directory):
        self.urls_json = urls_json
        self.output_directory = output_directory

        with open(urls_json, 'r') as f:
            self.urls = json.load(f)

        self.content_dictionary = self.build_content_dictionary()
        self.setup_output_directory()

    def build_content_dictionary(self):
        '''I think the only reason I'm doing this is because I didn't think ahead while building the urls json
           and I don't want to build it again cuz I had to let it run overnight...
        '''
        content_dic = {}
        for elem in self.urls:
            series_dic = {}
            ep_cnt = 1
            for info in self.urls[elem]:
                ep_name = f'{ep_cnt}_{normalize_title(info['title'])}'
                series_dic[ep_name] = {
                    'xml_url': info['xml_url'],
                    'stream_url': info['stream_url']
                }
                ep_cnt += 1

            content_dic[elem] = series_dic
        
        return content_dic

    def setup_output_directory(self):
        # make sure output directory exists
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)
        
        # make sure series directories exist
        for series in self.content_dictionary:
            series_dir = os.path.join(self.output_directory, series)
            if not os.path.exists(series_dir):
                os.makedirs(series_dir)

            # make sure each episode directory exists
            for ep in self.content_dictionary[series]:
                ep_dir = os.path.join(series_dir, ep)
                if not os.path.exists(ep_dir):
                    os.makedirs(ep_dir)

    def download_xml_subtitles(self, max_threads):
        tasks = []
        for series in self.content_dictionary:
            print(f"Processing series: {series}")
            for ep in self.content_dictionary[series]:
                xml_url = self.content_dictionary[series][ep]['xml_url']
                xml_path = os.path.join(self.output_directory, series, ep, f'{ep}.xml')
                
                if os.path.exists(xml_path):
                    print(f"XML for episode {ep} already exists. Skipping download.")
                    continue
    
                print(f"Queueing download for XML of episode: {ep} from {xml_url}")
                tasks.append((xml_url, xml_path))
    
        def download_task(xml_url, xml_path):
            print(f"Downloading XML for episode from {xml_url}")
            try:
                response = requests.get(xml_url)
                response.raise_for_status()  # Raise an HTTPError for bad responses
                xml_content = response.text
                with open(xml_path, 'w') as f:
                    f.write(xml_content)
                print(f"Successfully downloaded and saved XML for episode from {xml_url}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to download {xml_url}: {e}")
    
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(download_task, url, path) for url, path in tasks]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error downloading file: {e}")

    def download_stream_files(self):
        for series in self.content_dictionary:
            print(f"Processing series: {series}")
            for ep in self.content_dictionary[series]:
                stream_url = self.content_dictionary[series][ep]['stream_url']
                stream_path = os.path.join(self.output_directory, series, ep, f'{ep}.m3u8')
                
                if os.path.exists(stream_path):
                    print(f"Stream for episode {ep} already exists. Skipping download.")
                    continue

                print(f"Downloading stream for episode: {ep} from {stream_url}")
                try:
                    response = requests.get(stream_url)
                    response.raise_for_status()  # Raise an HTTPError for bad responses
                    stream_content = response.text
                    with open(stream_path, 'w') as f:
                        f.write(stream_content)
                    print(f"Successfully downloaded and saved stream for episode: {ep}")
                except requests.exceptions.RequestException as e:
                    print(f"Failed to download {stream_url}: {e}")

    def download_ep_mp4(self, m3u8_url, output_path):
        """Download the mp4 file from the m3u8 URL using ffmpeg"""
        import subprocess
        import os

        print(f"Starting download for {output_path} from {m3u8_url}")

        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
            print(f"Created directory {os.path.dirname(output_path)}")

        # ffmpeg command to download the mp4 file from the m3u8 URL
        command = [
            "ffmpeg",
            "-loglevel", "error",  # Suppress all but error messages
            "-i", m3u8_url,        # Input URL (.m3u8)
            "-c", "copy",          # Copy codec (avoid re-encoding)
            "-bsf:a", "aac_adtstoasc",  # Bitstream filter for audio
            output_path            # Output file (.mp4)
        ]

        # Run the command using subprocess
        try:
            subprocess.run(command, check=True)
            print(f"Successfully downloaded {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to download {output_path}: {e}")

    def download_mp4s(self, max_threads):
        """Make sure you have ffmpeg on your computer"""
        tasks = []
        for series in self.content_dictionary:
            print(f"Processing series: {series}")
            for ep in self.content_dictionary[series]:
                stream_url = self.content_dictionary[series][ep]['stream_url']
                mp4_path = os.path.join(self.output_directory, series, ep, f'{ep}.mp4')

                if os.path.exists(mp4_path):
                    print(f"MP4 for episode {ep} already exists. Skipping download.")
                    continue

                print(f"Queueing download for {mp4_path} from {stream_url}")
                tasks.append((stream_url, mp4_path))

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(self.download_ep_mp4, url, path) for url, path in tasks]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error downloading file: {e}")

class Converter:
    def __init__(self, output_directory):
        self.output_directory = output_directory
    
    def xml_to_srt(self):
        '''Convert XML subtitle files to SRT format.'''
        def ms_to_timedelta(ms):
            return timedelta(milliseconds=int(ms))
    
        for root, _, _ in os.walk(self.output_directory):
            for file in glob.glob(os.path.join(root, '*.xml')):
                xml_path = file
                srt_path = os.path.splitext(xml_path)[0] + '.srt'
    
                with open(xml_path, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'xml')
    
                subtitles = []
    
                paragraphs = soup.find_all('Paragraph')
                for paragraph in paragraphs:
                    start = ms_to_timedelta(paragraph.find('StartMilliseconds').text)
                    end = ms_to_timedelta(paragraph.find('EndMilliseconds').text)
                    text = paragraph.find('Text').text

                    subtitles.append(srt.Subtitle(index=len(subtitles) + 1, start=start, end=end, content=text))
    
                word_by_word = False
                for subtitle in subtitles:
                    if "[@" in subtitle.content:
                        word_by_word = True
                        break

                if word_by_word:
                    subtitles = self.correct_word_by_word_subtitles(subtitles)

                with open(srt_path, 'w', encoding='utf-8') as file: 
                    file.write(srt.compose(subtitles))
    
                print(f"File converted successfully: {srt_path}")
            
    def correct_word_by_word_subtitles(self, subtitles):
        if not subtitles:
            return []
    
        for subtitle in subtitles:
            subtitle.content = re.sub(r'\[@|\@\]', '', subtitle.content)
                
        new_subtitles = []
        prev = None
        start = subtitles[0].start
    
        for subtitle in subtitles:
            if prev is None:
                prev = subtitle
                continue
            if subtitle.content != prev.content:
                end = prev.end                
                new_subtitles.append(srt.Subtitle(index=len(new_subtitles) + 1, start=start, end=end, content=prev.content))
                start = subtitle.start
            prev = subtitle
    
        # Add the last subtitle
        if prev is not None:
            new_subtitles.append(srt.Subtitle(index=len(new_subtitles) + 1, start=start, end=prev.end, content=prev.content))
    
        # remove the pinyin lines
        for subtitle in new_subtitles:
            subtitle.content = self.remove_pinyin_line(subtitle.content)

        return new_subtitles

    def remove_pinyin_line(self, content):
        # Regex pattern to match pinyin tone marks
        tone_pattern = re.compile(r'[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]')
        new_content = ""
        for line in content.split("\n"):
            if not tone_pattern.search(line):
                new_content += line + "\n"
        return new_content.strip()

    def srt_to_txt(self):
        '''Convert SRT subtitle files to plain text.'''
        for root, _, _ in os.walk(self.output_directory):
            for file in glob.glob(os.path.join(root, '*.srt')):
                srt_path = file
                txt_path = os.path.splitext(srt_path)[0] + '.txt'
    
                with open(srt_path, 'r', encoding='utf-8') as file:
                    srt_content = file.read()

                subtitles = list(srt.parse(srt_content))

                with open(txt_path, 'w', encoding='utf-8') as file:
                    for subtitle in subtitles:
                        file.write(subtitle.content + '\n')