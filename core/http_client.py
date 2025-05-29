import json
import re
import queue
import threading
import time
import requests

from .logger import logger

# Constants
REQUEST_TIMEOUT_S = 10
WORKER_SLEEP_S = 1

class SalRequest:
    """Encapsulates a request for the HttpClient."""
    def __init__(self, url: str, payload: dict, headers: dict, callback: callable = None):
        self.url = url
        self.payload = payload
        self.headers = headers
        self.callback = callback

    def __str__(self):
        return f"SalRequest(URL='{self.url}')"

class HttpClient:
    """Handles asynchronous HTTP POST requests with JSON payloads."""
    def __init__(self, plugin_name: str, plugin_version: str):
        logger.info(f"Initializing HttpClient for {plugin_name} v{plugin_version}...")
        self.user_agent = f"{plugin_name}/{plugin_version}"
        self._request_queue = queue.Queue()
        self._worker_thread = None
        self._shutdown_event = threading.Event()

        # Regex for URL validation (adapted from BGS-Tally's requestmanager.py)
        self._url_validator = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        logger.info("HttpClient initialized.")

    def start(self):
        """Starts the HTTP client's worker thread."""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._shutdown_event.clear()
            self._worker_thread = threading.Thread(target=self._worker, name="SAL-HttpClientWorker")
            self._worker_thread.daemon = True
            self._worker_thread.start()
            logger.info("HttpClient worker thread started.")
        else:
            logger.info("HttpClient worker thread already running.")

    def stop(self):
        """Stops the HTTP client's worker thread."""
        logger.info("Attempting to stop HttpClient worker thread...")
        self._shutdown_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            try:
                # Try to unblock the queue.get() if it's waiting
                self._request_queue.put_nowait(None)
            except queue.Full:
                pass # Worker will eventually pick something or notice shutdown event

            self._worker_thread.join(timeout=REQUEST_TIMEOUT_S + WORKER_SLEEP_S + 1) # Wait for worker
            if self._worker_thread.is_alive():
                logger.warning("HttpClient worker thread did not stop in the allocated time.")
            else:
                logger.info("HttpClient worker thread stopped successfully.")
        else:
            logger.info("HttpClient worker thread was not running or already stopped.")
        self._worker_thread = None


    def _is_url_valid(self, url_string: str) -> bool:
        if not url_string or not isinstance(url_string, str):
            return False
        return self._url_validator.match(url_string) is not None

    def send_json_post_request(self, url: str, payload: dict, api_key: str = None, callback: callable = None):
        """Queues a JSON POST request."""
        if not self._is_url_valid(url):
            logger.error(f"Invalid URL for POST request: '{url}'")
            if callback:
                # Args: success (bool), response_data (dict/str), status_code (int/None)
                callback(False, {"error": "Invalid URL provided"}, None)
            return

        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}" # Common practice

        request_item = SalRequest(url, payload, headers, callback)
        self._request_queue.put(request_item)
        logger.debug(f"Queued {request_item}")

    def _worker(self):
        logger.info("HttpClient worker started processing queue.")
        while not self._shutdown_event.is_set():
            try:
                request_item = self._request_queue.get(timeout=WORKER_SLEEP_S)

                if request_item is None or self._shutdown_event.is_set(): # Check for shutdown signal
                    if request_item: self._request_queue.task_done() # Mark dummy item as done
                    break

                logger.info(f"Processing {request_item}")
                response = None
                try:
                    response = requests.post(
                        request_item.url,
                        json=request_item.payload, # requests library handles json.dumps
                        headers=request_item.headers,
                        timeout=REQUEST_TIMEOUT_S
                    )
                    response.raise_for_status()  # Raises HTTPError for 4XX or 5XX status codes
                    
                    logger.info(f"Request to {request_item.url} successful (Status: {response.status_code}).")
                    response_data = None
                    try:
                        response_data = response.json()
                    except ValueError: # Handle cases where response is not JSON
                        logger.warning(f"Response from {request_item.url} was not valid JSON, returning text.")
                        response_data = response.text

                    if request_item.callback:
                        request_item.callback(True, response_data, response.status_code)

                except requests.exceptions.HTTPError as e:
                    err_msg = f"HTTP error for {request_item.url}: {e.response.status_code if e.response else 'N/A'}"
                    logger.error(err_msg + f" - Response: {e.response.text if e.response else 'No response text'}")
                    if request_item.callback:
                        request_item.callback(False, e.response.text if e.response else err_msg, e.response.status_code if e.response else None)
                except requests.exceptions.Timeout:
                    logger.error(f"Request timed out for {request_item.url}")
                    if request_item.callback:
                        request_item.callback(False, {"error": "Request timed out"}, None)
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request failed for {request_item.url}: {e}")
                    if request_item.callback:
                        request_item.callback(False, {"error": str(e)}, None)
                finally:
                    self._request_queue.task_done()

            except queue.Empty:
                # This is expected when the queue is empty, loop and check shutdown_event
                continue
            except Exception as e:
                logger.critical(f"Unexpected critical error in HttpClient worker: {e}", exc_info=True)
                # Avoid busy-looping on unexpected critical errors; sleep a bit longer
                time.sleep(WORKER_SLEEP_S * 5)

        logger.info("HttpClient worker finished processing queue and is shutting down.")

# Global instance of the HttpClient
# This will be None until plugin_start creates it via initialize_http_client.
http_client_instance = None

def initialize_http_client(plugin_name: str, plugin_version: str):
    """Creates and starts the global HttpClient instance."""
    global http_client_instance
    if http_client_instance is None:
        logger.info("Global HttpClient not found, creating new instance.")
        http_client_instance = HttpClient(plugin_name, plugin_version)
        http_client_instance.start()
    else:
        logger.info("Global HttpClient already initialized.")
    return http_client_instance

def stop_http_client():
    """Stops the global HttpClient instance."""
    global http_client_instance
    if http_client_instance:
        logger.info("Stopping global HttpClient instance.")
        http_client_instance.stop()
        http_client_instance = None # Clear the global instance
    else:
        logger.info("Global HttpClient instance not found or already stopped.")

