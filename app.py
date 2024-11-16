import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse
import subprocess
import os

def scrape_urls(base_url, filter_path):
    # Send a request to the webpage
    response = requests.get(base_url)
    response.raise_for_status()  # Check that the request was successful

    # Parse the webpage content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all hyperlink tags
    links = soup.find_all('a', href=True)

    # Parse the base URL to get the main domain
    parsed_base_url = urlparse(base_url)
    main_domain = f"{parsed_base_url.scheme}://{parsed_base_url.netloc}"

    # Filter and collect URLs
    filtered_urls = []
    for link in links:
        href = link['href']
        # Join the relative URLs with the base URL
        full_url = urljoin(base_url, href)
        # Filter URLs that start with the main domain and specific path
        if full_url.startswith(main_domain + filter_path):
            filtered_urls.append(full_url)

    return filtered_urls

def save_downloaded_url(url, file_path):
    with open(file_path, 'a') as file:
        file.write(url + '\n')

def read_downloaded_urls(file_path):
    if not os.path.exists(file_path):
        return set()
    with open(file_path, 'r') as file:
        return set(line.strip() for line in file)

def get_subdirectory_from_url(base_url):
    parsed_url = urlparse(base_url)
    path_parts = parsed_url.path.strip('/').split('/')
    if path_parts:
        return path_parts[-1]
    return 'video'

def download_with_yt_dlp(url, subdirectory=None):
    if subdirectory and not os.path.exists(subdirectory):
        os.makedirs(subdirectory)
    command = ['yt-dlp']
    if subdirectory:
        command.extend(['-P', subdirectory])
    command.append(url)
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"yt-dlp failed with error: {e}")
        return False
    return True

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Scrape a webpage for all URLs and download videos using yt-dlp.')
    parser.add_argument('--to_download_file', type=str, default='to_download.txt',
                        help='The file containing base URLs to start the scrape from (default: to_download.txt)')
    parser.add_argument('--filter_path', type=str, default='/categories/',
                        help='The path to filter URLs (default: /categories/)')
    parser.add_argument('--downloaded_file', type=str, default='downloaded.dat',
                        help='The file to save downloaded URLs (default: downloaded.dat)')
    args = parser.parse_args()

    # Read base URLs to download from file
    with open(args.to_download_file, 'r') as file:
        base_urls = [line.strip() for line in file]

    # Read previously downloaded URLs
    downloaded_urls = read_downloaded_urls(args.downloaded_file)

    for base_url in base_urls:
        # Scrape URLs and filter out already downloaded ones
        filtered_urls = scrape_urls(base_url, args.filter_path)
        new_urls = [url for url in filtered_urls if url not in downloaded_urls]

        subdirectory = get_subdirectory_from_url(base_url)

        for url in new_urls:
            if url in downloaded_urls:
                print(f"Skipping URL {url} as it has been previously downloaded.")
                continue

            print(f"Downloading URL: {url}")
            success = download_with_yt_dlp(url, subdirectory)
            if success:
                save_downloaded_url(url, args.downloaded_file)
            else:
                print(f"Failed to download {url}")

if __name__ == '__main__':
    main()
