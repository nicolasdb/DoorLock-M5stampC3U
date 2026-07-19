import urequests
import time
import _thread
import os
import ubinascii
import uhashlib
import door_control
import credentials


def _hmac_sha256(key, msg):
    """Minimal HMAC-SHA256, since MicroPython has no `hmac` module."""
    block_size = 64
    if len(key) > block_size:
        key = uhashlib.sha256(key).digest()
    key = key + b"\x00" * (block_size - len(key))
    o_key_pad = bytes(b ^ 0x5C for b in key)
    i_key_pad = bytes(b ^ 0x36 for b in key)
    inner = uhashlib.sha256(i_key_pad + msg).digest()
    return uhashlib.sha256(o_key_pad + inner).digest()


class URLClient:
    def __init__(
        self,
        server_url=credentials.DOOR_SERVER_URL + "/check",
        device_id=credentials.DEVICE_ID,
        device_secret=credentials.DEVICE_SECRET,
        check_interval=1,
        timeout=5,
    ):
        """
        Poll the backend for door status.

        Every poll is authenticated in both directions: the request carries
        this device's id, and the response must carry an HMAC-SHA256 (keyed
        with the shared DEVICE_SECRET) over a nonce this device just picked.
        A bare HTTP 200 is no longer sufficient to open the door - only a
        response signed by the paired backend is trusted. This closes the
        gap where anything that could get a 200 back to the device (a
        spoofed DNS answer, a MITM'd AP, a misconfigured proxy) could pop
        the lock, since MicroPython's TLS stack does not verify certificates
        by default.
        """
        self.server_url = server_url
        self.device_id = device_id
        self.device_secret = device_secret
        self.check_interval = check_interval
        self.timeout = timeout
        self.running = False

    def _make_nonce(self):
        return ubinascii.hexlify(os.urandom(8)).decode()

    def _verify(self, nonce, data):
        try:
            status = data.get("status")
            sig = data.get("sig")
            if status not in ("open", "closed") or not sig:
                return False
            expected = ubinascii.hexlify(
                _hmac_sha256(
                    self.device_secret.encode(),
                    "{}:{}".format(nonce, status).encode(),
                )
            ).decode()
            if expected != sig:
                print("[URLClient] Signature mismatch - rejecting response")
                return False
            return status == "open"
        except Exception as e:
            print(f"[URLClient] Signature verification error: {e}")
            return False

    def check_server_status(self):
        """
        Poll the backend and open the door only if it returns a response
        signed with our shared secret.

        :return: True if the door was opened, False otherwise
        """
        nonce = self._make_nonce()
        url = "{}?device_id={}&nonce={}".format(
            self.server_url, self.device_id, nonce
        )
        try:
            print(f"[URLClient] Checking server status: {url}")
            response = urequests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": "CHB Door (ESP32-C3)"},
            )
            status_code = response.status_code
            try:
                data = response.json()
            except Exception:
                data = None
            response.close()

            if status_code == 200 and data and self._verify(nonce, data):
                print("[URLClient] Verified open signal. Opening door.")
                door_control.open_door()
                return True

            if status_code == 200 and not data:
                # An unpaired backend or a legacy plaintext responder. Do
                # NOT open the door on this - it means the response can't
                # be authenticated as coming from our paired backend.
                print(
                    "[URLClient] WARNING: got HTTP 200 without a valid "
                    "signature - ignoring (unpaired backend or possible "
                    "spoofing)"
                )

            return False

        except Exception as e:
            print(f"[URLClient] Server check error: {e}")
            return False

    def start_background_check(self):
        """
        Start background thread for periodic server checks
        """
        if not self.running:
            self.running = True
            _thread.start_new_thread(self._background_check, ())
            print("[URLClient] Background server check started")

    def stop_background_check(self):
        """
        Stop background server checks
        """
        self.running = False
        print("[URLClient] Background server check stopped")

    def _background_check(self):
        """
        Internal method for continuous server checking
        """
        while self.running:
            try:
                self.check_server_status()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"[URLClient] Background check error: {e}")
                time.sleep(self.check_interval)


# Create a global URLClient instance
url_client = URLClient()
