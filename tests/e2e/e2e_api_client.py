import requests


class E2EAPIClient:
    """Wrapper for making HTTP requests to the API"""

    def __init__(self, endpoint, headers):
        self.endpoint = endpoint
        self.headers = headers

    def post(self, path, data, headers=None):
        """Make POST request"""
        url = f"{self.endpoint}{path}"
        h = self.headers.copy()
        if headers:
            h.update(headers)
        response = requests.post(url, json=data, headers=h)
        return response

    def get(self, path, params=None, headers=None):
        """Make GET request"""
        url = f"{self.endpoint}{path}"
        h = self.headers.copy()
        if headers:
            h.update(headers)
        response = requests.get(url, params=params, headers=h)
        return response

    def delete(self, path, params=None, headers=None):
        """Make DELETE request"""
        url = f"{self.endpoint}{path}"
        h = self.headers.copy()
        if headers:
            h.update(headers)
        response = requests.delete(url, params=params, headers=h)
        return response
