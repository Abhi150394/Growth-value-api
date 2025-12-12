# lightspeed_auth.py
import base64
import hashlib
import json
import os
import re
import time
import threading
import logging
from typing import Optional, Tuple, Dict, Any, Iterable
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from django.conf import settings

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


class LightspeedAuth:
    """
    Lightspeed PKCE + token manager that supports multiple locations.

    Tokens are stored in a JSON file with top-level keys == location names:
        {
            "location_a": {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 3600,
                "timestamp": 169...,   # unix epoch when token was obtained
                ...
            },
            "location_b": { ... }
        }
    """

    def __init__(
        self,
        token_file: Optional[str] = None,
        token_expiry_buffer: int = 60,
        max_workers: int = 8,
    ) -> None:
        """
        :param token_file: Absolute path to JSON file for storing tokens. Defaults to
                           <BASE_DIR>/lightspeed_tokens.json
        :param token_expiry_buffer: seconds to subtract from expiry to proactively refresh
        :param max_workers: default parallelism for concurrent operations
        """
        self.token_file = (
            token_file
            if token_file
            else os.path.join(settings.BASE_DIR, "lightspeed_tokens.json")
        )
        self._file_lock = threading.Lock()
        self.token_expiry_buffer = int(token_expiry_buffer)
        self.max_workers = int(max_workers)

    # ----------------------
    # PKCE helpers
    # ----------------------
    @staticmethod
    def generate_code_verifier_and_challenge() -> Tuple[str, str]:
        """Return (verifier, challenge)."""
        verifier = (
            base64.urlsafe_b64encode(os.urandom(40)).rstrip(b"=").decode("utf-8")
        )
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("utf-8")).digest()
        ).rstrip(b"=").decode("utf-8")
        return verifier, challenge

    # ----------------------
    # File I/O (thread-safe)
    # ----------------------
    def _read_tokens(self) -> Dict[str, Any]:
        """Read the token file; return empty dict if not present."""
        with self._file_lock:
            try:
                with open(self.token_file, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    if isinstance(data, dict):
                        return data
                    logger.warning("Token file malformed: expected top-level dict.")
                    return {}
            except FileNotFoundError:
                return {}
            except json.JSONDecodeError:
                logger.exception("Token file JSON decode error; returning empty dict.")
                return {}

    def _write_tokens(self, data: Dict[str, Any]) -> None:
        """
        Atomically write tokens to the token file. Uses a temp file + os.replace.
        """
        dirname = os.path.dirname(self.token_file) or "."
        os.makedirs(dirname, exist_ok=True)
        tmp = f"{self.token_file}.tmp"
        with self._file_lock:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.token_file)

    # ----------------------
    # Authorization / Exchange
    # ----------------------
    def get_authorization_code(self, location: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Simulate login + consent for a given location and return (auth_code, code_verifier).
        If the final redirect raises a ConnectionError containing the code (localhost flow),
        this extracts it as before.
        """
        verifier, challenge = self.generate_code_verifier_and_challenge()

        auth_url = (
            f"{settings.LIGHTSPEED['AUTHORIZE_URL']}"
            f"?response_type=code"
            f"&client_id={settings.LIGHTSPEED['CLIENT_ID']}"
            f"&redirect_uri={settings.LIGHTSPEED['REDIRECT_URI']}"
            f"&code_challenge_method={settings.LIGHTSPEED['CODE_CHALLENGE_METHOD']}"
            f"&code_challenge={challenge}"
        )

        session = requests.Session()
        resp = session.get(auth_url)
        soup = BeautifulSoup(resp.text, "html.parser")
        form = soup.find("form")

        if not form:
            logger.error("No auth form found on authorize page. URL: %s", resp.url)
            raise RuntimeError("Lightspeed authorization form not found.")

        action_url = urljoin(resp.url, form.get("action"))
        payload = {
            i.get("name"): i.get("value", "")
            for i in form.find_all("input")
            if i.get("name")
        }

        creds = settings.LIGHTSPEED["LOGIN_CREDENTIALS"].get(location)
        if not creds:
            raise KeyError(f"No credentials configured for location '{location}'.")

        payload["userId"] = creds["id"]
        payload["password"] = creds["password"]

        login_resp = session.post(action_url, data=payload, allow_redirects=True)
        soup = BeautifulSoup(login_resp.text, "html.parser")
 
        # consent form
        form = soup.find("form")
        if not form:
            # Possibly redirect with code in URL or other flow
            # try to find code in current URL
            match = re.search(r"[?&]code=([^&\s]+)", login_resp.url)
            if match:
                return match.group(1), verifier
            raise RuntimeError("Consent form not found after login.")

        action_url = urljoin(login_resp.url, form.get("action"))
        payload = {
            i.get("name"): i.get("value", "")
            for i in form.find_all("input")
            if i.get("name")
        }
        payload["consent"] = "true"

        try:
            allow_resp = session.post(action_url, data=payload, allow_redirects=True)
            # If flow redirects to redirect_uri (and fails because of localhost), we
            # can still extract code from the final URL
            match = re.search(r"[?&]code=([^&\s]+)", allow_resp.url)
            if match:
                return match.group(1), verifier
            # otherwise maybe the server responded with a redirect error we can catch
            return None, verifier
        except requests.exceptions.ConnectionError as exc:
            # older approach: code in exception string
            match = re.search(r"[?&]code=([^&\s]+)", str(exc))
            if match:
                return match.group(1), verifier
            raise

    def exchange_token_for_location(
        self, location: str, auth_code: str, code_verifier: str
    ) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for tokens and save under the given location key.
        Returns the token dict or None on failure.
        """
        payload = {
            "grant_type": "authorization_code",
            "client_id": settings.LIGHTSPEED["CLIENT_ID"],
            "client_secret": settings.LIGHTSPEED["CLIENT_SECRET"],
            "redirect_uri": settings.LIGHTSPEED["REDIRECT_URI"],
            "code_verifier": code_verifier,
            "code": auth_code,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = requests.post(settings.LIGHTSPEED["TOKEN_URL"], data=payload, headers=headers)

        if resp.status_code != 200:
            logger.error(
                "Exchange token failed for %s: %s %s", location, resp.status_code, resp.text
            )
            return None

        token_data = resp.json()
        token_data["timestamp"] = int(time.time())

        all_tokens = self._read_tokens()
        all_tokens[location] = token_data
        self._write_tokens(all_tokens)
        logger.info("Stored token for location '%s'.", location)
        return token_data

    # ----------------------
    # Refresh
    # ----------------------
    def refresh_token_for_location(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Refresh the access token for a specific location using the stored refresh_token.
        On success, stores the updated token data in the file.
        """
        all_tokens = self._read_tokens()
        saved = all_tokens.get(location)
        if not saved:
            logger.warning("No saved token for location '%s'.", location)
            return None

        refresh_token = saved.get("refresh_token")
        if not refresh_token:
            logger.warning("No refresh_token for location '%s'.", location)
            return None

        payload = {
            "grant_type": "refresh_token",
            "client_id": settings.LIGHTSPEED["CLIENT_ID"],
            "client_secret": settings.LIGHTSPEED["CLIENT_SECRET"],
            "refresh_token": refresh_token,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = requests.post(settings.LIGHTSPEED["TOKEN_URL"], data=payload, headers=headers)

        if resp.status_code != 200:
            logger.error(
                "Failed to refresh for %s: %s %s", location, resp.status_code, resp.text
            )
            return None

        new_token = resp.json()
        new_token["timestamp"] = int(time.time())

        all_tokens[location] = new_token
        self._write_tokens(all_tokens)
        logger.info("Refreshed token for location '%s'.", location)
        return new_token

    # ----------------------
    # Helpers for expiry and retrieval
    # ----------------------
    def _is_expired(self, token_payload: Dict[str, Any]) -> bool:
        """
        Return True if token is considered expired or about to expire (buffered).
        Requires 'expires_in' and 'timestamp' in payload.
        """
        if not token_payload:
            return True
        expires_in = token_payload.get("expires_in")
        ts = token_payload.get("timestamp")
        if not expires_in or not ts:
            return True
        expiry_time = int(ts) + int(expires_in) - int(self.token_expiry_buffer)
        return time.time() >= expiry_time

    def get_valid_access_token(self, location: str) -> Optional[str]:
        """
        Ensure the access token for location is valid. Refresh if needed.
        Returns the access token string or None on failure.
        """
        all_tokens = self._read_tokens()
        token_payload = all_tokens.get(location)

        if token_payload and not self._is_expired(token_payload):
            return token_payload.get("access_token")

        # token missing/expired -> try refresh
        refreshed = self.refresh_token_for_location(location)
        if refreshed and not self._is_expired(refreshed):
            return refreshed.get("access_token")
        # final fallback: no token available
        logger.warning("No valid access token for '%s' after refresh attempt.", location)
        return None

    # ----------------------
    # Bulk / concurrent helpers
    # ----------------------
    def refresh_all_tokens(self, locations: Optional[Iterable[str]] = None) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Refresh tokens for provided locations concurrently.
        If locations is None, refresh for every location present in token file.
        Returns a mapping location -> refreshed_token_dict or None if refresh failed.
        """
        all_tokens = self._read_tokens()
        target_locations = list(locations) if locations is not None else list(all_tokens.keys())
        results: Dict[str, Optional[Dict[str, Any]]] = {}

        if not target_locations:
            logger.info("No locations to refresh.")
            return results

        with ThreadPoolExecutor(max_workers=self.max_workers) as exe:
            future_to_loc = {
                exe.submit(self.refresh_token_for_location, loc): loc for loc in target_locations
            }
            for fut in as_completed(future_to_loc):
                loc = future_to_loc[fut]
                try:
                    results[loc] = fut.result()
                except Exception:
                    logger.exception("Exception while refreshing token for %s", loc)
                    results[loc] = None
        return results

    def obtain_tokens_for_locations_concurrent(self, locations: Iterable[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        High-level helper: for each location, run get_authorization_code() + exchange.
        NOTE: get_authorization_code() may require interaction depending on Lightspeed flow.
        Use carefully — concurrent login flows might be limited by the provider.
        Returns mapping location -> token_dict or None on failure.
        """
        results: Dict[str, Optional[Dict[str, Any]]] = {}

        def _flow(loc: str) -> Optional[Dict[str, Any]]:
            try:
                auth_code, verifier = self.get_authorization_code(loc)
                if not auth_code:
                    logger.error("No auth_code for %s", loc)
                    return None
                return self.exchange_token_for_location(loc, auth_code, verifier)
            except Exception:
                logger.exception("Auth flow failed for %s", loc)
                return None

        with ThreadPoolExecutor(max_workers=self.max_workers) as exe:
            future_to_loc = {exe.submit(_flow, loc): loc for loc in locations}
            for fut in as_completed(future_to_loc):
                loc = future_to_loc[fut]
                try:
                    results[loc] = fut.result()
                except Exception:
                    logger.exception("Exception during obtain flow for %s", loc)
                    results[loc] = None
        return results
