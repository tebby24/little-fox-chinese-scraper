from utils import Downloader, Converter


if __name__ == "__main__":
    output_directory = 'subtitles'
    urls_json = 'data/urls.json'

    # download the xml subtitles
    downloader = Downloader(urls_json, output_directory)
    downloader.download_xml_subtitles(20)

    # convert xml subs to srt and txt
    converter = Converter(output_directory)
    converter.xml_to_srt()
    converter.srt_to_txt()