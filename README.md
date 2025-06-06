
**UPDATE 06/06/2025 **
+ Prevent duplicate image downloads
+ No need to install modules yourself, and no worries about your existing modules being overwritten or having to download different versions of existing modules


**INSTALLATION**

```bash
git clone https://github.com/ZilverSick/comic.naver-downloader.git
cd comic.naver-downloader
```

or

```ps1
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/kikunayar/comic.naver-downloader/main/nava.py" -OutFile nava.py
```

**USAGE EXAMPLE** 

Command line usage:

```bash
python nava.py 816614 1 40 .\webtoons
```

or you can use it in a python script:

```python
from nava import downloader

downloader(816614,1,40,r'.\webtoons')
```

- comic id = 816614
- start = 1
- end = 40
- directory = r'.\webtoons'

Since the numbering is sequential, you might need to offset the episode count if there is a prologue
