import httpx

BASE = "http://127.0.0.1:8000"

# Use separate timeouts: quick endpoints get 15s, heavy ones get 60s
QUICK = httpx.Client(timeout=15)
HEAVY = httpx.Client(timeout=60)

endpoints = [
    # (method, path, heavy?)
    ("GET", "/", False),
    ("GET", "/api/status", False),
    ("GET", "/api/languages", False),
    ("GET", "/api/orca/query?lat=13.35&lon=74.7&vessel=motorized_craft&language=en&departure_time=Tomorrow+05:00+AM&max_range_km=35", True),
    ("GET", "/api/weather/marine/13.35/74.7", False),
    ("GET", "/api/risk/point?lat=13.35&lon=74.7", False),
    ("GET", "/api/risk-zones", True),
    ("GET", "/api/cyclone-track", False),
    ("GET", "/api/imd/cyclones", False),
    ("GET", "/api/imd/warning?lat=13.35&lon=74.7", False),
    ("GET", "/api/imd/fishing-zones", False),
    ("GET", "/api/tide/predict?station=Malpe&hours=24", False),
    ("GET", "/api/tide/stations", False),
    ("GET", "/api/vessel/sva/all?wave_m=1.5&wind_kmh=28", False),
    ("GET", "/api/erddap/dataset?lat=13.35&lon=74.7", False),
    ("GET", "/api/satellite/composite?lat=13.35&lon=74.7", False),
    ("GET", "/api/pfz/candidates?lat=13.35&lon=74.7", False),
    ("GET", "/api/geofence/restricted-zones", False),
    ("GET", "/api/copernicus/status", False),
    ("GET", "/api/ocean-currents", False),
    ("GET", "/api/coastal-summary", False),
    ("GET", "/api/cyclone/impact?lat=13.35&lon=74.7", False),
    ("GET", "/api/gateway/normalized?lat=13.35&lon=74.7", True),
    ("GET", "/api/advisory/quick?lat=13.35&lon=74.7&language=english", True),
]

print("=" * 62)
print("  SAGARVANI BACKEND - COMPREHENSIVE ENDPOINT TEST")
print("=" * 62)

passed = 0
failed = 0
timeouts = 0
results = []

for method, path, heavy in endpoints:
    client = HEAVY if heavy else QUICK
    try:
        r = client.get(BASE + path)
        status = r.status_code
        ok = status < 400
        if ok:
            passed += 1
            icon = "PASS"
        else:
            failed += 1
            icon = "FAIL"
        short = path[:54]
        print(f"[{icon}] {status}  {short}")
        if not ok:
            try:
                detail = r.json().get("detail", "")[:120]
                print(f"         Error: {detail}")
            except Exception:
                pass
        results.append((icon, status, path))
    except httpx.ReadTimeout:
        timeouts += 1
        failed += 1
        print(f"[TOUT] ---  {path[:54]}")
        print(f"         Timed out (endpoint is too slow or hanging)")
        results.append(("TOUT", 0, path))
    except Exception as e:
        failed += 1
        msg = str(e)[:100].encode("ascii", "replace").decode("ascii")
        print(f"[ERR ] ---  {path[:54]}")
        print(f"         {msg}")
        results.append(("ERR", 0, path))

print()
print("=" * 62)
print(f"  RESULT: {passed} PASSED | {failed} FAILED ({timeouts} timeouts) | {len(endpoints)} TOTAL")
print("=" * 62)

# Summary of failures
if failed > 0:
    print("\nFAILED ENDPOINTS:")
    for icon, status, path in results:
        if icon != "PASS":
            print(f"  [{icon}] {path[:70]}")
