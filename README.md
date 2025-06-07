
**UPDATE 06/06/2025 ** NO-Brain
+ Prevent duplicate image downloads
+ No need to install modules yourself, and no worries about your existing modules being overwritten


**INSTALLATION/USAGE**

for powershell window
```ps1
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/kikunayar/comic.naver-downloader/main/nava.py" -OutFile nava.py
python nava.py 816614 1 40 .\webtoons
```






- comic id = 816614
- start = 1
- end = 40
- directory = .\webtoons'





for github
```ps1
git clone https://github.com/ZilverSick/comic.naver-downloader.git
cd comic.naver-downloader
python nava.py 816614 1 40 .\webtoons
```





