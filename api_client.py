import requests

class AnalyticsAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def get_areas(self):
        resp = requests.get(f"{self.base_url}/api/areas")
        resp.raise_for_status()
        return resp.json().get("data", [])

    def get_price_indices(self, area_ids=None, start_date=None, end_date=None, granularity="quarterly", provisional="all"):
        params = {"granularity": granularity, "provisional": provisional}
        if area_ids:
            params["areaIds"] = ",".join(area_ids) if isinstance(area_ids, list) else area_ids
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        resp = requests.get(f"{self.base_url}/api/price-indices", params=params)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def get_metrics_summary(self, area_ids=None, start_date=None, end_date=None):
        params = {}
        if area_ids:
            params["areaIds"] = ",".join(area_ids) if isinstance(area_ids, list) else area_ids
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        resp = requests.get(f"{self.base_url}/api/metrics/summary", params=params)
        resp.raise_for_status()
        return resp.json().get("data", {})

    def get_statistics(self, area_ids=None, start_date=None, end_date=None):
        params = {}
        if area_ids:
            params["areaIds"] = ",".join(area_ids) if isinstance(area_ids, list) else area_ids
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        resp = requests.get(f"{self.base_url}/api/statistics", params=params)
        resp.raise_for_status()
        return resp.json().get("data", {})

    def get_resources(self):
        resp = requests.get(f"{self.base_url}/api/resources")
        resp.raise_for_status()
        return resp.json().get("data", {})
