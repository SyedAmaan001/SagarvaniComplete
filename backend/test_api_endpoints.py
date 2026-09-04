"""
Comprehensive API & Endpoint Integration Test Suite for Sagarvani Backend
"""
import sys
# pyrefly: ignore [missing-import]
import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

def test_all_endpoints():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    results = []

    endpoints_to_test = [
        ("GET", "/", None),
        ("GET", "/api/status", None),
        ("GET", "/api/languages", None),
        ("POST", "/api/orca/interpret", {"query": "Can I go fishing tomorrow from Malpe?"}),
        ("POST", "/api/orca/query", {"query": "Is high tide expected near Mangalore?"}),
        ("GET", "/api/gateway/normalized?lat=13.35&lon=74.70", None),
        ("GET", "/api/pfz/candidates?lat=13.35&lon=74.70", None),
        ("GET", "/api/geofence/restricted-zones", None),
        ("POST", "/api/orchestrate", {"query": "Weather near Goa?"}),
        ("GET", "/api/ocean-currents", None),
        ("GET", "/api/ocean-currents/point?lat=13.35&lon=74.70", None),
        ("GET", "/api/ocean-currents/all", None),
        ("GET", "/api/coastal-summary", None),
        ("GET", "/api/coastal-latest", None),
        ("GET", "/api/weather/13.35/74.70", None),
        ("GET", "/api/weather/marine/13.35/74.70", None),
        ("GET", "/api/risk/point?lat=13.35&lon=74.70", None),
        ("GET", "/api/risk-zones", None),
        ("GET", "/api/cyclone-track", None),
        ("GET", "/api/cyclone/impact?lat=13.35&lon=74.70", None),
        ("GET", "/api/imd/cyclones", None),
        ("GET", "/api/imd/warning?region=west_coast", None),
        ("GET", "/api/imd/fishing-zones", None),
        ("GET", "/api/copernicus/status", None),
        ("GET", "/api/copernicus/ocean-data?lat=13.35&lon=74.70", None),
        ("GET", "/api/advisory?lat=13.35&lon=74.70", None),
        ("GET", "/api/advisory/quick?lat=13.35&lon=74.70", None),
        ("POST", "/api/send-alert", {"to_number": "+919035195941", "message": "Test alert", "channel": "whatsapp"}),
        ("POST", "/api/send-bulk-alert", {"phone_numbers": ["+919035195941"], "message": "Test bulk alert"}),
        ("GET", "/api/message-status/SM123456", None),
        ("GET", "/api/tide/predict?lat=13.35&lon=74.70", None),
        ("GET", "/api/tide/stations", None),
        ("GET", "/api/vessel/sva?lat=13.35&lon=74.70", None),
        ("GET", "/api/vessel/sva/all", None),
        ("GET", "/api/satellite/composite?lat=13.35&lon=74.70", None),
        ("GET", "/api/erddap/dataset?dataset_id=incois_wave", None),
        ("GET", "/api/maritime/limits?lat=13.35&lon=74.70", None),
    ]

    print(f"Running automated API tests on {len(endpoints_to_test)} endpoints...\n")

    passed = 0
    failed = 0

    for item in endpoints_to_test:
        method = item[0]
        path = item[1]
        payload = item[2]

        try:
            if method == "GET":
                resp = client.get(path)
            elif method == "POST":
                resp = client.post(path, json=payload)

            status = resp.status_code
            if status < 400:
                results.append((method, path, status, "SUCCESS"))
                passed += 1
            else:
                results.append((method, path, status, f"FAILED ({resp.text[:100]})"))
                failed += 1
        except Exception as e:
            results.append((method, path, 500, f"EXCEPT: {str(e)}"))
            failed += 1

    print(f"{'METHOD':<8} | {'PATH':<45} | {'STATUS':<6} | RESULT")
    print("-" * 80)
    for res in results:
        print(f"{res[0]:<8} | {res[1]:<45} | {res[2]:<6} | {res[3]}")

    print("\nSummary:")
    print(f"Total: {len(endpoints_to_test)} | Passed: {passed} | Failed: {failed}")

if __name__ == "__main__":
    test_all_endpoints()
