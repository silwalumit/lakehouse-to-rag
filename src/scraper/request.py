import requests.adapters
from urllib3 import Retry


class RetryingSession:
    def __init__(
        self,
        max_retries: int = 3,
        user_agent: str = "Mozilla/5.0",
    ) -> None:
        self.session = requests.Session()
        self._configure_adapter(max_retries)
        self._set_headers(user_agent)

    def _configure_adapter(self, max_retries: int) -> None:
        """Create a requests session with retry logic"""

        # Configure retry strategy
        retry = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=0.5,
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _set_headers(self, user_agent: str) -> None:
        """Create a requests session with proper headers."""
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )

    def get(self, url: str, **kwargs) -> requests.Response:
        """Send a GET request."""
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response

    def close(self):
        self.session.close()
