from fastapi import APIRouter, HTTPException

from app.models.brand import Brand
from app.rules.pacing_rules import Rules, load_rules, save_rules
from app.services.brand_matcher import load_catalog, save_catalog

router = APIRouter()


@router.get("/brands")
def get_brands():
    return load_catalog().brands


@router.post("/brands")
def add_brand(brand: Brand):
    if not brand.brand_id.strip() or not brand.brand_name.strip():
        raise HTTPException(400, "brand_id and brand_name are required")
    catalog = load_catalog()
    catalog.brands = [b for b in catalog.brands if b.brand_id != brand.brand_id] + [brand]
    save_catalog(catalog)
    return brand


@router.delete("/brands/{brand_id}")
def delete_brand(brand_id: str):
    catalog = load_catalog()
    before = len(catalog.brands)
    catalog.brands = [b for b in catalog.brands if b.brand_id != brand_id]
    if len(catalog.brands) == before:
        raise HTTPException(404, "Brand not found")
    save_catalog(catalog)
    return {"deleted": brand_id}


@router.get("/rules")
def get_rules():
    return load_rules()


@router.put("/rules")
def put_rules(rules: Rules):
    return save_rules(rules)
