"""
StudyLock AI - Desktop Native Blocker Helper & Platform Adapter
Ref: StudyLock AI Architecture Specification Section 5.2 & Section 6.1 (Windows/macOS native adapter)
"""
import sys
import os
import time
import json
import logging
from typing import List, Dict, Any, Optional
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [StudyLock-DesktopHelper] %(message)s"
)
logger = logging.getLogger("DesktopHelper")

DEFAULT_PROCESS_BLOCKLIST = [
    "discord.exe",
    "steam.exe",
    "epicgameslauncher.exe",
    "spotify.exe",
    "battle.net.exe",
    "riotclientservices.exe"
]


class DesktopBlockerAdapter:
    def __init__(self, api_base_url: str = "http://127.0.0.1:8000/api/v1", token: Optional[str] = None):
        self.api_base_url = api_base_url
        self.token = token
        self.device_id: Optional[str] = None
        self.is_enforcing: bool = False
        self.blocked_processes: List[str] = list(DEFAULT_PROCESS_BLOCKLIST)
        self.platform_name = "windows" if sys.platform == "win32" else "macos"

    def register_device(self) -> bool:
        if not self.token:
            logger.info("Running in standalone local desktop mode (no cloud token provided).")
            return True

        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            resp = requests.post(
                f"{self.api_base_url}/devices",
                headers=headers,
                json={"platform": self.platform_name, "app_version": "1.0.0"},
                timeout=5
            )
            if resp.status_code in [200, 201]:
                self.device_id = resp.json().get("id")
                logger.info(f"Registered desktop device ID: {self.device_id}")
                return True
        except Exception as e:
            logger.warning(f"Device registration failed: {e}. Will operate in local offline mode.")
        return False

    def send_heartbeat(self):
        if not self.token or not self.device_id:
            return
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            requests.post(
                f"{self.api_base_url}/devices/{self.device_id}/heartbeat",
                headers=headers,
                json={"app_version": "1.0.0"},
                timeout=3
            )
        except Exception:
            pass

    def scan_and_restrict(self) -> List[str]:
        """
        Inspects running processes against active block rules.
        """
        restricted_found = []
        try:
            # Cross-platform check: on Windows tasklist / psutil
            import subprocess
            if sys.platform == "win32":
                output = subprocess.check_output("tasklist /FO CSV /NH", shell=True, text=True, errors="ignore")
                running = [line.split(",")[0].strip('"').lower() for line in output.splitlines() if line]
            else:
                output = subprocess.check_output("ps -e -o comm=", shell=True, text=True, errors="ignore")
                running = [line.strip().lower() for line in output.splitlines() if line]

            for proc in self.blocked_processes:
                if proc.lower() in running:
                    restricted_found.append(proc)

        except Exception as e:
            logger.error(f"Error scanning processes: {e}")

        return restricted_found

    def set_enforcement_mode(self, active: bool):
        self.is_enforcing = active
        status_str = "ACTIVE" if active else "INACTIVE"
        logger.info(f"Desktop restriction enforcement state updated to: {status_str}")

        if self.token and self.device_id:
            headers = {"Authorization": f"Bearer {self.token}"}
            try:
                requests.post(
                    f"{self.api_base_url}/devices/{self.device_id}/enforcement-report",
                    headers=headers,
                    json={
                        "enforcement_state": "ACTIVE" if active else "NOT_CONFIGURED",
                        "rule_ids_applied": self.blocked_processes if active else [],
                        "rule_ids_failed": []
                    },
                    timeout=3
                )
            except Exception:
                pass

    def run_loop(self, poll_interval: int = 5):
        logger.info(f"StudyLock Desktop Helper running on {self.platform_name}. Press Ctrl+C to stop.")
        self.register_device()
        self.set_enforcement_mode(True)

        try:
            while True:
                if self.is_enforcing:
                    found = self.scan_and_restrict()
                    if found:
                        logger.warning(f"Distraction processes detected running during focus: {found}")
                    self.send_heartbeat()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info("Emergency exit / shutdown requested by user. Clearing restrictions.")
            self.set_enforcement_mode(False)


if __name__ == "__main__":
    adapter = DesktopBlockerAdapter()
    adapter.run_loop(poll_interval=5)
