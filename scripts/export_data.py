"""Export catalog.db to data/products.json for static site."""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "Meat for Kings" / "catalog.db"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "products.json"


def export():
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row

    # All columns except scraped_at
    cols = [
        "id", "name", "brand", "category", "model_number", "fuel_type",
        "price_current", "price_retail", "price_sale",
        "price_formatted", "retail_formatted", "savings_formatted", "savings_percent",
        "image_url", "product_url",
        "rating", "review_count",
        "description", "bullet_points",
        "stock_status", "ships_in", "is_free_shipping", "video_url",
    ]

    rows = db.execute(f"SELECT {', '.join(cols)} FROM products ORDER BY price_current ASC").fetchall()

    products = []
    for row in rows:
        p = dict(row)

        # Parse bullet_points from JSON string to real array
        bp = p.get("bullet_points")
        if bp:
            try:
                p["bullet_points"] = json.loads(bp)
            except (json.JSONDecodeError, TypeError):
                p["bullet_points"] = []
        else:
            p["bullet_points"] = []

        # Convert is_free_shipping from int 0/1 to boolean
        p["is_free_shipping"] = bool(p.get("is_free_shipping"))

        products.append(p)

    # Compute meta
    brands = sorted({p["brand"] for p in products if p.get("brand")})
    fuel_types = sorted({p["fuel_type"] for p in products if p.get("fuel_type")})
    prices = [p["price_current"] for p in products if p.get("price_current") is not None]

    meta = {
        "total": len(products),
        "brands": brands,
        "fuel_types": fuel_types,
        "price_min": min(prices) if prices else 0,
        "price_max": max(prices) if prices else 0,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump({"products": products, "meta": meta}, f, separators=(",", ":"))

    db.close()
    print(f"Exported {len(products)} products to {OUT_PATH}")
    print(f"  Brands: {len(brands)}, Fuel types: {len(fuel_types)}")
    print(f"  Price range: {meta['price_min']} - {meta['price_max']}")
    print(f"  File size: {OUT_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    export()
