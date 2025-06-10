import json
import re
import queue
import threading
import time
import requests

from typing import Optional, Any, Dict, Tuple, Callable
from sal.logger import PluginLogger
from sal.constants import HttpClientTimers


class SalRequest:
    """
    Encapsulates a request for the HttpClient.
    This class holds the URL, payload, headers, and an optional callback function
    to be invoked upon completion of the request.
    """
    def __init__(self, url: str, payload: dict, headers: dict, callback: Optional[Callable] = None):
        self.url = url
        self.payload = payload
        self.headers = headers
        self.callback = callback


    def __str__(self):
        return f"SalRequest(URL='{self.url}')"



class HttpClient:
    """
    Handles asynchronous HTTP POST requests with JSON payloads.
    This class manages a queue of requests and processes them in a dedicated worker thread.
    It supports sending JSON POST requests with optional API keys and callbacks,
    as well as synchronous GET requests.
    """
    def __init__(self, plugin_name: str, plugin_version: str):
        PluginLogger.logger.info(f"Initializing HttpClient for {plugin_name} v{plugin_version}...")
        self.user_agent = f"{plugin_name}/{plugin_version}"
        self._request_queue = queue.Queue()
        self._worker_thread = None
        self._shutdown_event = threading.Event()

        # Regex for URL validation (Contribution: adapted from BGS-Tally's requestmanager.py)
        self._url_validator = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)


    # Starts the HTTP client's worker thread if it is not already running.
    def start(self):
        """Starts the HTTP client's worker thread."""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._shutdown_event.clear()
            self._worker_thread = threading.Thread(target=self._worker, name="SAL-HttpClientWorker")
            self._worker_thread.daemon = True
            self._worker_thread.start()
            PluginLogger.logger.info("start: HttpClient worker thread started.")
        else:
            PluginLogger.logger.info("start: HttpClient worker thread already running.")


    # Stops the HTTP client's worker thread and cleans up resources.
    def stop(self):
        """Stops the HTTP client's worker thread."""
        PluginLogger.logger.info("stop: Attempting to stop HttpClient worker thread...")
        self._shutdown_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            try:
                self._request_queue.put_nowait(None)
            except queue.Full:
                pass

            self._worker_thread.join(timeout=HttpClientTimers.REQUEST_TIMEOUT_S + HttpClientTimers.WORKER_SLEEP_S + 1)
            if self._worker_thread.is_alive():
                PluginLogger.logger.warning("stop: HttpClient worker thread did not stop in the allocated time.")
            else:
                PluginLogger.logger.info("stop: HttpClient worker thread stopped successfully.")
        else:
            PluginLogger.logger.info("stop: HttpClient worker thread was not running or already stopped.")
        self._worker_thread = None


    # Validates the URL using a regex pattern.
    def _is_url_valid(self, url_string: str) -> bool:
        """Validates the provided URL string."""
        if not url_string or not isinstance(url_string, str):
            return False
        return self._url_validator.match(url_string) is not None


    # Sends a JSON POST request to the specified URL with the given payload and headers.
    def send_json_post_request(self, url: str, payload: dict, api_key: Optional[str] = None, callback: Optional[Callable[[bool, Optional[dict], Optional[int]], None]] = None):
        """Queues a JSON POST request."""
        if not self._is_url_valid(url):
            PluginLogger.logger.error(f"send_json_post_request: Invalid URL for POST request: '{url}'")
            if callback:
                callback(False, {"error_origin": "URLValidation", "error": "Invalid URL provided"}, None)
            return

        # Headers for the request, including User-Agent and Content-Type.
        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/json"
        }

        # If an API key is provided, add it to the headers.
        if api_key:
            headers["x-api-key"] = api_key

        request_item = SalRequest(url, payload, headers, callback)
        self._request_queue.put(request_item)
        PluginLogger.logger.debug(f"send_json_post_request: Queued {request_item}")


    # Sends a synchronous GET request.
    def send_get_request_sync(self, url: str, params: Optional[Dict[str, Any]] = None, custom_headers: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Any], Optional[int], Optional[str]]:
        """Sends a synchronous GET request and returns the response data, status code, and error message."""
        if not self._is_url_valid(url):
            PluginLogger.logger.error(f"send_get_request_sync: Invalid URL for GET request: '{url}'")
            return None, None, "Invalid URL provided"
        
        req_headers = {
            "User-Agent": self.user_agent
        }
        if custom_headers:
            req_headers.update(custom_headers)
        
        PluginLogger.logger.info(f"send_get_request_sync: Sending synchronous GET request to {url} with params {params} and headers {req_headers}")
        try:
            response = requests.get(
                url,
                params=params,
                headers=req_headers,
                timeout=HttpClientTimers.REQUEST_TIMEOUT_S
            )
            response.raise_for_status()
            response_data = None
            try:
                response_data = response.json()
            except ValueError:
                PluginLogger.logger.warning(f"send_get_request_sync: Response from {url} was not valid JSON, returning text. Body: {response.text[:500]}")
                response_data = response.text
            
            return response_data, response.status_code, None
        
        except requests.exceptions.HTTPError as e:
            PluginLogger.logger.error(f"send_get_request_sync: HTTP error for {url}: {e}", exc_info=True)
            return None, e.response.status_code if e.response else None, str(e)
        except requests.exceptions.Timeout as e:
            PluginLogger.logger.error(f"send_get_request_sync: Request timed out for {url}: {e}", exc_info=True)
            return None, None, "Request timed out"
        except requests.exceptions.RequestException as e:
            PluginLogger.logger.error(f"send_get_request_sync: Request failed for {url}: {e}", exc_info=True)
            return None, None, str(e)
        except Exception as e:
            PluginLogger.logger.critical(f"Unexpected error in send_get_request_sync: {e}", exc_info=True)
            return None, None, "Unexpected error occurred"


    # Worker method that processes requests from the queue.
    def _worker(self):
        while not self._shutdown_event.is_set():
            try:
                request_item = self._request_queue.get(timeout=HttpClientTimers.WORKER_SLEEP_S)

                if request_item is None or self._shutdown_event.is_set():
                    if request_item: self._request_queue.task_done()
                    break

                response = None
                try:
                    response = requests.post(
                        request_item.url,
                        json=[request_item.payload],
                        headers=request_item.headers,
                        timeout=HttpClientTimers.REQUEST_TIMEOUT_S
                    )
                    response.raise_for_status()
                    
                    PluginLogger.logger.debug(f"_worker: Request to {request_item.url} successful (Status: {response.status_code}).")
                    response_data = None
                    try:
                        response_data = response.json()
                    except ValueError:
                        PluginLogger.logger.warning(f"_worker: Response from {request_item.url} was not valid JSON, returning text. Body: {response.text[:500]}")
                        response_data = response.text

                    if request_item.callback:
                        PluginLogger.logger.debug(f"_worker: Invoking callback for {request_item.url} with success=True")
                        request_item.callback(True, response_data, response.status_code)

                except requests.exceptions.HTTPError as e:
                    PluginLogger.logger.error(
                        f"Caught HTTPError in _worker. Type: {type(e).__name__}. Exception: {str(e)}. Has response attribute: {hasattr(e, 'response')}. Response object: {e.response}. Callback present: {request_item.callback is not None}",
                        exc_info=True
                    )

                    original_err_msg = f"HTTP error for {request_item.url}: {e.response.status_code if e.response else 'N/A'}"
                    PluginLogger.logger.debug(f"_worker: Original format log would be: {original_err_msg} - Response: {e.response.text if e.response else 'No response text'}") 
                    
                    if request_item.callback:
                        PluginLogger.logger.debug(f"_worker: Invoking callback for {request_item.url} with success=False due to HTTPError. Callback: {request_item.callback}")
                        error_payload_http = {
                            "error_origin": "HTTPError_Block",
                            "exception_type": type(e).__name__,
                            "exception_message": str(e),
                            "response_attr_is_none": e.response is None,
                            "response_status_code_on_exception_obj": e.response.status_code if e.response else "N/A (e.response was None/False)",
                            "response_text_on_exception_obj": e.response.text if e.response else "N/A (e.response was None/False)"
                        }
                        request_item.callback(False, error_payload_http, e.response.status_code if e.response else None)
                
                except requests.exceptions.Timeout as e:
                    PluginLogger.logger.error(f"_worker: Request timed out for {request_item.url}. Type: {type(e).__name__}. Exception: {str(e)}. Callback present: {request_item.callback is not None}", exc_info=True)
                    if request_item.callback:
                        PluginLogger.logger.debug(f"_worker: Invoking callback for {request_item.url} with success=False due to Timeout. Callback: {request_item.callback}")
                        request_item.callback(False, {"error_origin": "Timeout_Block", "error": "Request timed out", "exception_type": type(e).__name__, "exception_message": str(e)}, None)
                
                except requests.exceptions.RequestException as e:
                    PluginLogger.logger.error(f"_worker: Request failed for {request_item.url}. Type: {type(e).__name__}. Exception: {str(e)}. Callback present: {request_item.callback is not None}", exc_info=True)
                    if request_item.callback:
                        PluginLogger.logger.debug(f"_worker: Invoking callback for {request_item.url} with success=False due to RequestException. Callback: {request_item.callback}")
                        error_payload_req = {
                            "error_origin": "RequestException_Block",
                            "exception_type": type(e).__name__,
                            "exception_message": str(e)
                        }
                        request_item.callback(False, error_payload_req, None)
                
                finally:
                    self._request_queue.task_done()
                    PluginLogger.logger.debug(f"_worker: Finished processing {request_item}. task_done() called.")

            except queue.Empty:
                continue
            except Exception as e:
                PluginLogger.logger.critical(f"_worker: Unexpected critical error in HttpClient worker: {e}", exc_info=True)
                time.sleep(HttpClientTimers.WORKER_SLEEP_S * 5)

        PluginLogger.logger.info("HttpClient worker finished processing queue and is shutting down.")