import requests
import os
import sys
import subprocess
import time

class AppUpdater:
    def __init__(self, current_version, repo_owner="Hotta", repo_name="OmniTranslator"):
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        
    def check_for_updates(self):
        """Checks GitHub for a newer version. Returns (has_update, version_name, download_url)"""
        try:
            response = requests.get(self.api_url, timeout=10)
            if response.status_code != 200:
                return False, None, None
            
            data = response.json()
            latest_version = data.get("tag_name", "").replace("v", "")
            
            if not latest_version:
                return False, None, None
                
            # Simple version comparison (e.g., 1.1.0 > 1.0.0)
            if self._is_newer(latest_version, self.current_version):
                # Find the .exe asset
                assets = data.get("assets", [])
                for asset in assets:
                    if asset.get("name", "").endswith(".exe"):
                        return True, latest_version, asset.get("browser_download_url")
            
            return False, latest_version, None
        except Exception as e:
            print(f"Update check failed: {e}")
            return False, None, None

    def _is_newer(self, latest, current):
        try:
            v_latest = [int(x) for x in latest.split(".")]
            v_current = [int(x) for x in current.split(".")]
            return v_latest > v_current
        except:
            return latest > current

    def download_and_apply(self, download_url, progress_callback=None):
        """Downloads the new exe and triggers the replacement script"""
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            
            new_exe_path = "OmniTranslator_new.exe"
            downloaded = 0
            
            with open(new_exe_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(int(downloaded / total_size * 100))
            
            self._create_replacement_script()
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            return False

    def _create_replacement_script(self):
        """Creates a .bat script to replace the current exe with the new one"""
        current_exe = os.path.basename(sys.executable)
        # If running as script, sys.executable is python.exe. We need to handle that.
        # But in production, it will be OmniTranslator.exe
        if not current_exe.endswith(".exe"):
            current_exe = "OmniTranslator.exe"

        bat_content = f"""@echo off
timeout /t 1 /nobreak > nul
del "{current_exe}"
rename "OmniTranslator_new.exe" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
        with open("apply_update.bat", "w") as f:
            f.write(bat_content)
            
    def restart_and_update(self):
        """Closes the app and runs the replacement script"""
        if os.path.exists("apply_update.bat"):
            subprocess.Popen(["apply_update.bat"], shell=True)
            sys.exit(0)
