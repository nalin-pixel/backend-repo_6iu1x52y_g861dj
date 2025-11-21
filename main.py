import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from database import create_document

app = FastAPI(title="Bobber Customizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# Models
# ------------------------------
class Selection(BaseModel):
    color: str = Field(..., description="Primary paint color")
    seat: str = Field(..., description="Seat style")
    bars: str = Field(..., description="Handlebar style")
    exhaust: str = Field(..., description="Exhaust option")
    tires: str = Field(..., description="Tire option")

class PriceResponse(BaseModel):
    base_price: float
    addons: Dict[str, float]
    total: float
    currency: str = "USD"

# ------------------------------
# In-memory catalogs (static options)
# ------------------------------
BASE_PRICE = 9800.0
CATALOG = {
    "color": {
        "Matte Black": 0,
        "Gunmetal": 120,
        "Pearl White": 220,
        "Crimson": 180,
        "Olive Drab": 150,
    },
    "seat": {
        "Solo Minimal": 0,
        "Diamond Stitch": 260,
        "Brown Vintage": 180,
    },
    "bars": {
        "Low Drag": 0,
        "Clip-ons": 320,
        "Mini Ape": 240,
    },
    "exhaust": {
        "Stock": 0,
        "Shorty": 420,
        "Slash-Cut": 520,
    },
    "tires": {
        "Street": 0,
        "Semi-Slick": 180,
        "Whitewall": 260,
    },
}

# Helpful metadata to drive UI accents/thumbnails
THUMBNAILS = {
    "color": {
        "Matte Black": "https://img.shields.io/badge/Matte%20Black-000000.svg?style=for-the-badge",
        "Gunmetal": "https://img.shields.io/badge/Gunmetal-2f2f2f.svg?style=for-the-badge",
        "Pearl White": "https://img.shields.io/badge/Pearl%20White-f8fafc.svg?style=for-the-badge",
        "Crimson": "https://img.shields.io/badge/Crimson-dc2626.svg?style=for-the-badge",
        "Olive Drab": "https://img.shields.io/badge/Olive%20Drab-374151.svg?style=for-the-badge",
    },
    "seat": {
        "Solo Minimal": "https://img.shields.io/badge/Solo%20Minimal-111827.svg?style=for-the-badge",
        "Diamond Stitch": "https://img.shields.io/badge/Diamond%20Stitch-1f2937.svg?style=for-the-badge",
        "Brown Vintage": "https://img.shields.io/badge/Brown%20Vintage-92400e.svg?style=for-the-badge",
    },
    "bars": {
        "Low Drag": "https://img.shields.io/badge/Low%20Drag-0f172a.svg?style=for-the-badge",
        "Clip-ons": "https://img.shields.io/badge/Clip--ons-0f172a.svg?style=for-the-badge",
        "Mini Ape": "https://img.shields.io/badge/Mini%20Ape-0f172a.svg?style=for-the-badge",
    },
    "exhaust": {
        "Stock": "https://img.shields.io/badge/Stock-0f172a.svg?style=for-the-badge",
        "Shorty": "https://img.shields.io/badge/Shorty-0f172a.svg?style=for-the-badge",
        "Slash-Cut": "https://img.shields.io/badge/Slash--Cut-0f172a.svg?style=for-the-badge",
    },
    "tires": {
        "Street": "https://img.shields.io/badge/Street-0f172a.svg?style=for-the-badge",
        "Semi-Slick": "https://img.shields.io/badge/Semi--Slick-0f172a.svg?style=for-the-badge",
        "Whitewall": "https://img.shields.io/badge/Whitewall-0f172a.svg?style=for-the-badge",
    },
}

ACCENT_COLORS = {
    "Matte Black": "#0b0f19",
    "Gunmetal": "#2f3136",
    "Pearl White": "#f1f5f9",
    "Crimson": "#dc2626",
    "Olive Drab": "#374151",
}

# ------------------------------
# Routes
# ------------------------------
@app.get("/")
def read_root():
    return {"message": "Bobber Customizer Backend (FastAPI)"}

@app.get("/api/options")
def get_options():
    return {"base_price": BASE_PRICE, "options": CATALOG, "thumbnails": THUMBNAILS, "accents": ACCENT_COLORS}

@app.post("/api/price", response_model=PriceResponse)
def calculate_price(selection: Selection):
    addons: Dict[str, float] = {}
    try:
        addons["color"] = CATALOG["color"][selection.color]
        addons["seat"] = CATALOG["seat"][selection.seat]
        addons["bars"] = CATALOG["bars"][selection.bars]
        addons["exhaust"] = CATALOG["exhaust"][selection.exhaust]
        addons["tires"] = CATALOG["tires"][selection.tires]
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid selection: {e}")

    total = BASE_PRICE + sum(addons.values())
    return PriceResponse(base_price=BASE_PRICE, addons=addons, total=total)

class SaveBuildRequest(Selection):
    total: Optional[float] = None
    currency: str = "USD"
    created_by: Optional[str] = None
    notes: Optional[str] = None

@app.post("/api/builds")
def save_build(payload: SaveBuildRequest):
    """Persist the user's current build selection to the database."""
    # Ensure total is computed server-side for integrity
    addons: Dict[str, float] = {
        "color": CATALOG["color"].get(payload.color, 0),
        "seat": CATALOG["seat"].get(payload.seat, 0),
        "bars": CATALOG["bars"].get(payload.bars, 0),
        "exhaust": CATALOG["exhaust"].get(payload.exhaust, 0),
        "tires": CATALOG["tires"].get(payload.tires, 0),
    }
    total = BASE_PRICE + sum(addons.values())
    doc = {
        "color": payload.color,
        "seat": payload.seat,
        "bars": payload.bars,
        "exhaust": payload.exhaust,
        "tires": payload.tires,
        "total": total,
        "currency": payload.currency,
        "created_by": payload.created_by,
        "notes": payload.notes,
    }
    try:
        inserted_id = create_document("build", doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    return {"ok": True, "id": inserted_id, "total": total}

@app.get("/api/demo/java")
def java_demo():
    """Demo endpoint to represent a Java microservice response."""
    return {
        "service": "java-demo",
        "status": "ok",
        "message": "Hello from the Java demo service (simulated)",
        "version": "1.0.0",
    }

@app.get("/api/demo/cpp")
def cpp_demo():
    """Demo endpoint to represent a C++ microservice response."""
    return {
        "service": "cpp-demo",
        "status": "ok",
        "message": "Hello from the C++ demo service (simulated)",
        "build": "gcc-13",
    }

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
