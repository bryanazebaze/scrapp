import asyncio
from sqlalchemy.orm import Session
from core.database import SessionLocal
from core.models import Location
import httpx
import time

def geocode_locations():
    db = SessionLocal()
    locations = db.query(Location).filter(Location.lat.is_(None)).all()
    print(f"Found {len(locations)} locations to geocode.")
    
    headers = {"User-Agent": "CentralImmoApp/1.0 (bryan@example.com)"}
    
    for loc in locations:
        query = f"{loc.neighborhood}, {loc.city}, Cameroon" if loc.neighborhood else f"{loc.city}, Cameroon"
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        try:
            resp = httpx.get(url, headers=headers, timeout=10.0)
            data = resp.json()
            if data:
                loc.lat = float(data[0]['lat'])
                loc.lng = float(data[0]['lon'])
                db.commit()
                print(f"✅ Geocoded: {query} -> {loc.lat}, {loc.lng}")
            else:
                print(f"❌ Not found: {query}")
        except Exception as e:
            print(f"⚠️ Error geocoding {query}: {e}")
        time.sleep(1.5)  # To avoid rate limits
        
    db.close()
    print("Done.")

if __name__ == "__main__":
    geocode_locations()
