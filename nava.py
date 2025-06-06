#!/usr/bin/env python3
"""
High-tech Naver Webtoon Downloader with Smart Environment Management
Features:
- Auto virtual environment creation
- Smart module management with fallback
- Cache system to avoid redundant operations
- Progress tracking and retry mechanisms
"""

import subprocess
import sys
import os
import json
import hashlib
from pathlib import Path
import venv
import importlib.util
from typing import List, Dict, Optional, Tuple
import argparse
import time
import asyncio

class SmartEnvironmentManager:
    def __init__(self, project_name: str = "webtoon_downloader"):
        self.project_name = project_name
        self.cache_file = Path("cache.txt")
        self.env_path = Path(f".venv_{project_name}")
        self.requirements = {
            'aiohttp': '3.11.11',
            'beautifulsoup4': '4.13.4', 
            'httpx': '0.28.1',
            'requests': '2.32.3'
        }
        self.cache_data = self._load_cache()
        self._analysis_done = False
        self._needs_venv = False
        self._missing_external = []
        self._available_external = []
    
    def _get_import_name(self, package_name: str) -> str:
        """Get the actual import name for a package (some packages have different import names)"""
        import_mapping = {
            'beautifulsoup4': 'bs4',
            'aiohttp': 'aiohttp',
            'httpx': 'httpx', 
            'requests': 'requests',
            'pathlib': 'pathlib',  # Built-in module
            'asyncio': 'asyncio',  # Built-in module
            're': 're',            # Built-in module
            'time': 'time',        # Built-in module
            'json': 'json',        # Built-in module
            'os': 'os',            # Built-in module
            'sys': 'sys',          # Built-in module
            'subprocess': 'subprocess',  # Built-in module
            'hashlib': 'hashlib',  # Built-in module
            'venv': 'venv',        # Built-in module
            'importlib': 'importlib',  # Built-in module
            'argparse': 'argparse'  # Built-in module
        }
        return import_mapping.get(package_name, package_name)
        
    def _load_cache(self) -> Dict:
        """Load cache data from file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache data to file"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
    
    def _get_cache_key(self, operation: str, data: str = "") -> str:
        """Generate cache key for operation"""
        return hashlib.md5(f"{operation}_{data}".encode()).hexdigest()
    
    def _is_module_available(self, module_name: str, base_env: bool = True) -> bool:
        """Check if module is available and functional"""
        cache_key = self._get_cache_key("module_check", f"{module_name}_{base_env}")
        
        if cache_key in self.cache_data:
            print(f"📋 Cache: {module_name} status from cache")
            return self.cache_data[cache_key]
        
        try:
            if base_env:
                # Check in base environment
                import_name = self._get_import_name(module_name)
                spec = importlib.util.find_spec(import_name)
                if spec is not None:
                    # Test actual import functionality
                    module = importlib.import_module(import_name)
                    result = True
                else:
                    result = False
            else:
                # Check in virtual environment
                venv_python = self._get_venv_python()
                import_name = self._get_import_name(module_name)
                
                result = subprocess.run([
                    venv_python, "-c", f"import {import_name}"
                ], capture_output=True, text=True).returncode == 0
            
            self.cache_data[cache_key] = result
            self._save_cache()
            return result
            
        except Exception as e:
            print(f"❌ Error checking module {module_name}: {e}")
            return False
    
    def _create_virtual_env(self):
        """Create new virtual environment"""
        cache_key = self._get_cache_key("venv_creation", str(self.env_path))
        
        if cache_key in self.cache_data and self.env_path.exists():
            print(f"📋 Virtual environment already exists: {self.env_path}")
            return
        
        print(f"🔧 Creating virtual environment: {self.env_path}")
        try:
            venv.create(self.env_path, with_pip=True)
            self.cache_data[cache_key] = True
            self._save_cache()
            print(f"✅ Virtual environment created successfully")
        except Exception as e:
            print(f"❌ Failed to create virtual environment: {e}")
            raise
    
    def _get_venv_python(self) -> str:
        """Get path to Python executable in virtual environment"""
        if os.name == 'nt':  # Windows
            return str(self.env_path / "Scripts" / "python.exe")
        else:  # Unix/Linux/macOS
            return str(self.env_path / "bin" / "python")
    
    def _install_module(self, module_name: str, version: str = None):
        """Install module in virtual environment"""
        package = f"{module_name}=={version}" if version else module_name
        cache_key = self._get_cache_key("module_install", package)
        
        if cache_key in self.cache_data:
            print(f"📋 Cache: {package} already installed")
            return
        
        print(f"📦 Installing {package}...")
        venv_python = self._get_venv_python()
        
        try:
            result = subprocess.run([
                venv_python, "-m", "pip", "install", package
            ], capture_output=True, text=True, check=True)
            
            self.cache_data[cache_key] = True
            self._save_cache()
            print(f"✅ Successfully installed {package}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e.stderr}")
            raise
    
    def analyze_required_modules(self):
        """Analyze which modules are actually needed and check availability"""
        if self._analysis_done:
            return self._missing_external, self._available_external
            
        print("🔍 Analyzing required modules...")
        
        # Only external packages that need installation
        external_packages = {
            'aiohttp': '3.11.11',
            'beautifulsoup4': '4.13.4', 
            'httpx': '0.28.1',
            'requests': '2.32.3'
        }
        
        # Built-in modules (just check, don't install)
        builtin_modules = [
            'asyncio', 'pathlib', 're', 'time', 'json', 'os', 'sys',
            'subprocess', 'hashlib', 'venv', 'importlib', 'argparse'
        ]
        
        missing_external = []
        available_external = []
        missing_builtin = []
        
        # Check external packages
        for module_name, version in external_packages.items():
            if self._is_module_available(module_name, base_env=True):
                available_external.append(module_name)
                print(f"✅ {module_name} - Available in base")
            else:
                missing_external.append((module_name, version))
                print(f"❌ {module_name} - Missing (will install)")
        
        # Check built-in modules
        for module_name in builtin_modules:
            if self._is_module_available(module_name, base_env=True):
                print(f"✅ {module_name} - Built-in available")
            else:
                missing_builtin.append(module_name)
                print(f"⚠️  {module_name} - Built-in missing (unusual)")
        
        if missing_builtin:
            print(f"⚠️  Warning: Missing built-in modules: {missing_builtin}")
        
        # Cache results
        self._analysis_done = True
        self._missing_external = missing_external
        self._available_external = available_external
        self._needs_venv = len(missing_external) > 0
        
        return missing_external, available_external
    
    def setup_environment(self):
        """Setup environment and manage all modules"""
        print("🚀 Starting High-tech Environment Setup...")
        
        # Step 1: Analyze what external packages are needed vs available
        missing_external, available_external = self.analyze_required_modules()
        
        # Step 2: Only create venv if we actually need to install external packages
        if missing_external:
            print(f"\n📦 Need to install {len(missing_external)} external packages: {[m[0] for m in missing_external]}")
            self._create_virtual_env()
            
            # Step 3: Install missing external packages
            for module_name, version in missing_external:
                print(f"\n📦 Installing {module_name}...")
                self._install_module(module_name, version)
                
                # Wait a moment for installation to complete
                time.sleep(1)
                
                # Verify installation in venv
                if not self._is_module_available(module_name, base_env=False):
                    print(f"⚠️  Retrying verification for {module_name}...")
                    time.sleep(2)  # Wait a bit more
                    if not self._is_module_available(module_name, base_env=False):
                        print(f"❌ Failed to verify {module_name} installation")
                        print(f"⚠️  Continuing anyway - module might still work")
                    else:
                        print(f"✅ {module_name} verified after retry")
        else:
            print(f"\n🎉 All required external packages are available in base environment!")
            print("✨ No virtual environment needed - using base Python!")
        
        print(f"\n📊 Module Summary:")
        print(f"✅ Available external packages: {len(available_external)}")
        if missing_external:
            print(f"📦 Installed external packages: {len(missing_external)}")
        print("\n🎉 Environment setup completed successfully!")
    
    def get_python_executable(self) -> str:
        """Get path to Python executable that should be used"""
        if not self._analysis_done:
            raise RuntimeError("setup_environment() must be called before get_python_executable()")
        
        if not self._needs_venv:
            print("🐍 Using base Python environment (all external packages available)")
            return sys.executable
        else:
            print(f"🐍 Using virtual environment (missing: {[m[0] for m in self._missing_external]})")
            return self._get_venv_python()

class HighTechWebtoonDownloader:
    def __init__(self):
        self.dl: List[str] = []
        self.sp: List[str] = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session_stats = {
            'images_downloaded': 0,
            'images_skipped': 0,
            'failed_downloads': 0,
            'start_time': time.time()
        }
    
    async def fetch_url(self, client, url):
        """Fetch data from URL"""
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
        return None
    
    async def fetch_download_image(self, client, url, fp):
        """Download image with intelligent retry system and duplicate prevention"""
        file_path = Path(fp)
        
        # Check if file already exists and has reasonable size
        if file_path.exists():
            file_size = file_path.stat().st_size
            if file_size > 1024:  # File exists and is larger than 1KB (not empty/corrupted)
                print(f"⏭️  Skipped (exists): {file_path.name}")
                self.session_stats['images_downloaded'] += 1  # Count as successful
                return True
            else:
                print(f"🔄 Replacing corrupted file: {file_path.name} (size: {file_size} bytes)")
        
        attempt = 0
        max_retries = 5
        
        while attempt < max_retries:
            try:
                async with client.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        image = await response.read()
                        
                        # Ensure directory exists
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Write to temporary file first, then rename (atomic operation)
                        temp_path = file_path.with_suffix('.tmp')
                        with open(temp_path, 'wb') as f:
                            f.write(image)
                        
                        # Only replace if download was successful and file is not empty
                        if temp_path.stat().st_size > 1024:  # At least 1KB
                            temp_path.rename(file_path)
                            self.session_stats['images_downloaded'] += 1
                            print(f"✅ Downloaded: {file_path.name} ({len(image):,} bytes)")
                            return True
                        else:
                            temp_path.unlink()  # Delete empty/corrupted temp file
                            print(f"⚠️  Downloaded file too small, retrying...")
                    else:
                        print(f"⚠️  HTTP {response.status} for {url}")
            except Exception as e:
                print(f"❌ Error downloading {url}: {e}")
            
            attempt += 1
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"🔄 Retrying in {wait_time}s... ({attempt}/{max_retries})")
                await asyncio.sleep(wait_time)
        
        self.session_stats['failed_downloads'] += 1
        print(f"💥 Failed to download {url} after {max_retries} attempts")
        return False
    
    async def download_all_images(self):
        """Download all images concurrently"""
        print(f"🚀 Starting download of {len(self.dl)} images...")
        
        import aiohttp
        
        async with aiohttp.ClientSession() as client:
            tasks = [
                self.fetch_download_image(client, url, fp) 
                for url, fp in zip(self.dl, self.sp)
            ]
            await asyncio.gather(*tasks)
    
    async def extract_episode_data(self, comic_id, start, end, full_path):
        """Extract episode data"""
        import httpx
        from bs4 import BeautifulSoup
        
        print(f"📖 Extracting episodes {start}-{end-1}...")
        urls = [
            f"https://comic.naver.com/webtoon/detail?titleId={comic_id}&no={cur}" 
            for cur in range(start, end)
        ]
        
        async with httpx.AsyncClient() as client:
            responses = await asyncio.gather(*[
                self.fetch_url(client, url) for url in urls
            ])
            
            for cur, content in zip(range(start, end), responses):
                if content:
                    soup = BeautifulSoup(content, 'html.parser')
                    div = soup.select_one('body > div:nth-of-type(1) > div:nth-of-type(3) > div:nth-of-type(1)')
                    
                    if div:
                        img_tags = div.find_all('img')
                        img_links = [img['src'] for img in img_tags if 'src' in img.attrs]
                        self.dl.extend(img_links)
                        
                        img_folder = Path(full_path) / str(cur)
                        img_folder.mkdir(exist_ok=True)
                        
                        save_paths = [
                            str(img_folder / f'{e}.jpg') 
                            for e in range(len(img_links))
                        ]
                        self.sp.extend(save_paths)
                        
                        print(f"📄 Episode {cur}: {len(img_links)} images found")
    
    def get_comic_title(self, comic_id):
        """Get comic title"""
        import requests
        from bs4 import BeautifulSoup
        import re
        
        name_url = f"https://comic.naver.com/webtoon/list?titleId={comic_id}"
        response = requests.get(name_url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            meta_tag = soup.find('meta', attrs={'property': 'og:title'})
            if meta_tag:
                title_content = meta_tag.get('content')
                return re.sub(r'[<>:"/\\|?*]', '-', title_content)
        
        return f"comic_{comic_id}"
    
    def print_stats(self):
        """Display download statistics"""
        elapsed = time.time() - self.session_stats['start_time']
        total_processed = self.session_stats['images_downloaded'] + self.session_stats['failed_downloads']
        print(f"\n📊 Download Statistics:")
        print(f"✅ Successfully downloaded: {self.session_stats['images_downloaded']}")
        print(f"⏭️  Skipped (already exists): {self.session_stats.get('images_skipped', 0)}")
        print(f"❌ Failed downloads: {self.session_stats['failed_downloads']}")
        print(f"📁 Total processed: {total_processed}")
        print(f"⏱️  Total time: {elapsed:.2f} seconds")
        if self.session_stats['images_downloaded'] > 0:
            print(f"⚡ Download speed: {self.session_stats['images_downloaded']/elapsed:.2f} images/sec")

async def main_download_process(comic_id, start, end, outpath):
    """Main download process"""
    downloader = HighTechWebtoonDownloader()
    
    # Create main folder
    title = downloader.get_comic_title(comic_id)
    full_path = Path(outpath) / title
    full_path.mkdir(parents=True, exist_ok=True)
    
    print(f"📚 Comic: {title}")
    print(f"📁 Output: {full_path}")
    
    # Extract episode data
    await downloader.extract_episode_data(comic_id, start, end + 1, full_path)
    
    # Download all images
    await downloader.download_all_images()
    
    # Show statistics
    downloader.print_stats()
    print("🎉 FINISHED!")

def main():
    """Main function"""
    print("🌟 High-tech Naver Webtoon Downloader v2.0")
    print("=" * 50)
    
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="High-tech Naver Webtoon Downloader with Smart Environment Management"
    )
    parser.add_argument("comic_id", type=int, help="Comic ID from Naver Webtoon")
    parser.add_argument("start", type=int, help="Start episode number")
    parser.add_argument("end", type=int, help="End episode number")
    parser.add_argument("outpath", type=str, help="Output directory for download")
    parser.add_argument("--skip-env-setup", action="store_true", 
                       help="Skip environment setup (use existing)")
    
    args = parser.parse_args()
    
    try:
        # Setup environment
        if not args.skip_env_setup:
            env_manager = SmartEnvironmentManager()
            env_manager.setup_environment()
            python_exe = env_manager.get_python_executable()
            
            # If need to use venv, rerun script in venv
            if python_exe != sys.executable:
                print(f"🔄 Switching to virtual environment...")
                subprocess.run([
                    python_exe, __file__,
                    str(args.comic_id), str(args.start), str(args.end), args.outpath,
                    "--skip-env-setup"
                ])
                return
        
        # Run download process
        print("\n" + "="*50)
        print("🚀 Starting Download Process...")
        asyncio.run(main_download_process(
            args.comic_id, args.start, args.end, args.outpath
        ))
        
    except KeyboardInterrupt:
        print("\n⚠️  Download interrupted by user")
    except Exception as e:
        print(f"\n💥 Error: {e}")
        raise

if __name__ == "__main__":
    main()
