import requests
from bs4 import BeautifulSoup
import srt
from datetime import timedelta
import os

class Series:
    def __init__(self, series_title, series_id):
        """
        Initialize the Series class with the given series ID.
        
        :param series_id: The ID of the series.
        """
        self.main_url = f'https://chinese.littlefox.com/en/story/contents_list/{series_id}'
        title_as_filepath = series_title.lower().replace(' ', '-')  
        self.xml_output_directory = f'output/xml/{title_as_filepath}'
        self.srt_output_directory = f'output/srt/{title_as_filepath}'

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
    
    def download_xml_subtitles(self):
            urls = [f'https://cdn.littlefox.co.kr/cn/captionxml/{id}.xml' for id in self.get_ep_ids()]
            paths = [os.path.join(self.xml_output_directory, f'{i}.xml') for i in range(1, len(urls) + 1)]

            # Ensure the output directory exists
            os.makedirs(self.xml_output_directory, exist_ok=True)

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

        for xml_file in os.listdir(self.xml_output_directory):
            if not xml_file.endswith('.xml'):
                continue

            xml_path = os.path.join(self.xml_output_directory, xml_file)
            srt_path = os.path.join(self.srt_output_directory, xml_file.replace('.xml', '.srt'))

            # Ensure the directory exists
            os.makedirs(os.path.dirname(xml_path), exist_ok=True)
            os.makedirs(os.path.dirname(srt_path), exist_ok=True)

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

    def normalize_srt(self):
        '''The little fox Chinese subtitles in the earlier Episodes include an individual title for each word. We don't want this, so we will combine the subtitles to have one for each individual line of text.'''
        for srt_file in os.listdir(self.srt_output_directory):
            if not srt_file.endswith('.srt'):
                continue

            srt_path = os.path.join(self.srt_output_directory, srt_file)

            with open(srt_path, 'r', encoding='utf-8') as file:
                srt_content = file.read()

            # Split the content into subtitles
            subtitles = list(srt.parse(srt_content))
            normalized_subtitles = []

            for sub in subtitles:
                sub.content = sub.content.replace('[@', '').replace('@]', '')
                if normalized_subtitles:
                    if sub.content != normalized_subtitles[-1].content:
                        normalized_subtitles.append(sub)
                    else:
                        normalized_subtitles[-1].end = sub.end
                else:
                    normalized_subtitles.append(sub)

            with open(srt_path, 'w', encoding='utf-8') as file:
                file.write(srt.compose(normalized_subtitles))