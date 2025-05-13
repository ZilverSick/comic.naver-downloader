import requests
import asyncio
import aiohttp
import httpx
from bs4 import BeautifulSoup
import re
import os
from pathlib import Path
import argparse

dl: list[str] = []
sp: list[str] = []

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

async def fetch_url(client, url):
    response = await client.get(url)
    if response.status_code == 200:
        return response.text
    return None

async def fetch_download_image(client, url, fp):
    attempt = 0
    retries = 999  # Reduced the number of retries for efficiency
    while attempt < retries:
        try:
            async with client.get(url, headers=headers) as response:
                if response.status == 200:
                    image = await response.read()
                    with open(fp, 'wb') as f:
                        f.write(image)
                        print(f"DONE {fp}")
                        return
                else:
                    print(f"Failed to fetch image from {url}: Status code {response.status}")
        except Exception as e:
            print(f"Error fetching image from {url}: {e}")
        attempt += 1
        print(f"Retrying... ({attempt}/{retries})")
    print(f"Failed to fetch image from {url} after {retries} attempts")

async def download():
    async with aiohttp.ClientSession() as client:
        tasks = [fetch_download_image(client, url, fp) for url, fp in zip(dl, sp)]
        await asyncio.gather(*tasks)

async def set_path(comic_id, start, end, full_path):
    global dl
    urls = [f"https://comic.naver.com/webtoon/detail?titleId={comic_id}&no={cur}" for cur in range(start, end)]
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(*[fetch_url(client, url) for url in urls])
        for cur, content in zip(range(start, end), responses):
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                div = soup.select_one('body > div:nth-of-type(1) > div:nth-of-type(3) > div:nth-of-type(1)')
                if div:
                    img_tags = div.find_all('img')
                    img_links = [img['src'] for img in img_tags if 'src' in img.attrs]
                    dl.extend(img_links)
                    img_folder = os.path.join(full_path, str(cur))
                    if not os.path.exists(img_folder):
                        os.makedirs(img_folder)
                    save_paths = [os.path.join(img_folder, f'{e}.jpg') for e in range(len(img_links))]
                    sp.extend(save_paths)

def downloader(comic_id, start, end, outpath):
    outpath = Path(outpath)
    name_url = f"https://comic.naver.com/webtoon/list?titleId={comic_id}"
    response = requests.get(name_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        meta_tag = soup.find('meta', attrs={'property': 'og:title'})
        title_content = meta_tag.get('content')
        folder_name = re.sub(r'[<>:"/\\|?*]', '-', title_content)
        full_path = os.path.join(outpath, folder_name)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        asyncio.run(set_path(comic_id, start, end + 1, full_path))
        asyncio.run(download())
        print("FINISHED")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Naver Webtoons")
    parser.add_argument("comic_id", type=int, help="Comic ID from Naver Webtoon")
    parser.add_argument("start", type=int, help="Start episode number")
    parser.add_argument("end", type=int, help="End episode number")
    parser.add_argument("outpath", type=str, help="Output directory for download")

    args = parser.parse_args()

    downloader(args.comic_id, args.start, args.end, args.outpath)