import requests
import os
import sys
import subprocess
import time
import hashlib
import json
from pathlib import Path

from core.logging_config import get_logger

logger = get_logger("AppUpdater")


class SecurityError(Exception):
    """Erro de segurança durante atualização."""

    pass


class AppUpdater:
    """
    Gerenciador de atualizações com validação de segurança.
    Verifica checksums SHA256 antes de aplicar atualizações.
    """

    def __init__(
        self, current_version, repo_owner="eduardohotta", repo_name="omniTranslator"
    ):
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_url = (
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        )
        self._checksum_verified = False

    def check_for_updates(self):
        """
        Checks GitHub for a newer version.
        Returns (has_update, version_name, download_url, checksum_url)
        """
        try:
            logger.info(f"Checking for updates at {self.api_url}")
            response = requests.get(self.api_url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"GitHub API returned {response.status_code}")
                return False, None, None, None

            data = response.json()
            latest_version = data.get("tag_name", "").replace("v", "")

            if not latest_version:
                logger.warning("No version tag found in release")
                return False, None, None, None

            logger.info(
                f"Latest version: {latest_version}, Current: {self.current_version}"
            )

            # Simple version comparison (e.g., 1.1.0 > 1.0.0)
            if self._is_newer(latest_version, self.current_version):
                # Find the .exe asset and checksum
                assets = data.get("assets", [])
                download_url = None
                checksum_url = None

                for asset in assets:
                    name = asset.get("name", "")
                    if name.endswith(".exe"):
                        download_url = asset.get("browser_download_url")
                    elif name.endswith(".sha256") or name.endswith(".checksum"):
                        checksum_url = asset.get("browser_download_url")

                if download_url:
                    logger.info(f"Update available: {latest_version}")
                    return True, latest_version, download_url, checksum_url
                else:
                    logger.warning("No .exe asset found in release")

            return False, latest_version, None, None
        except Exception as e:
            logger.error(f"Update check failed: {e}")
            return False, None, None, None

    def _is_newer(self, latest, current):
        """Compare version strings (semantic versioning)."""
        try:
            v_latest = [int(x) for x in latest.split(".")]
            v_current = [int(x) for x in current.split(".")]
            return v_latest > v_current
        except:
            return latest > current

    def _download_checksum(self, checksum_url: str) -> str:
        """Download and parse checksum file."""
        try:
            response = requests.get(checksum_url, timeout=10)
            if response.status_code == 200:
                # SHA256 files usually contain: <hash> <filename>
                content = response.text.strip()
                parts = content.split()
                return parts[0] if parts else None
        except Exception as e:
            logger.warning(f"Could not download checksum: {e}")
        return None

    def _calculate_sha256(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _verify_checksum(self, file_path: str, expected_hash: str) -> bool:
        """Verify file integrity against expected hash."""
        if not expected_hash:
            logger.warning("No checksum available for verification")
            return False

        actual_hash = self._calculate_sha256(file_path)
        verified = actual_hash.lower() == expected_hash.lower()

        if verified:
            logger.info("✓ Checksum verification passed")
        else:
            logger.error(
                f"✗ Checksum mismatch! Expected: {expected_hash}, Got: {actual_hash}"
            )

        return verified

    def download_and_apply(
        self, download_url, checksum_url=None, progress_callback=None, skip_verify=False
    ):
        """
        Downloads the new exe with optional checksum verification.

        Args:
            download_url: URL do executável
            checksum_url: URL do arquivo de checksum (opcional)
            progress_callback: Função de callback para progresso
            skip_verify: Ignorar verificação de checksum (não recomendado)

        Returns:
            bool: True se download bem-sucedido e verificado
        """
        try:
            logger.info(f"Starting download from {download_url}")

            # Download checksum first if available
            expected_checksum = None
            if checksum_url and not skip_verify:
                expected_checksum = self._download_checksum(checksum_url)
                if expected_checksum:
                    logger.info("Checksum file downloaded")

            # Download the executable
            response = requests.get(download_url, stream=True, timeout=30)
            total_size = int(response.headers.get("content-length", 0))

            new_exe_path = "OmniTranslator_new.exe"
            downloaded = 0

            with open(new_exe_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(int(downloaded / total_size * 100))

            logger.info(f"Download completed: {downloaded} bytes")

            # Verify checksum
            if expected_checksum and not skip_verify:
                if not self._verify_checksum(new_exe_path, expected_checksum):
                    os.remove(new_exe_path)
                    raise SecurityError("Downloaded file checksum verification failed!")
                self._checksum_verified = True
            elif not skip_verify:
                logger.warning(
                    "No checksum available. Downloading without verification."
                )

            self._create_replacement_script()
            logger.info("Update ready to apply")
            return True

        except SecurityError:
            raise
        except Exception as e:
            logger.error(f"Download failed: {e}")
            # Cleanup on failure
            if os.path.exists("OmniTranslator_new.exe"):
                try:
                    os.remove("OmniTranslator_new.exe")
                except:
                    pass
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
