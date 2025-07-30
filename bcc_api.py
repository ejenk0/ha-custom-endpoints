from datetime import date
from pydantic import BaseModel
from typing import Literal


def _query(route, params) -> tuple[dict, int]:
    import requests

    base_url = "https://data.brisbane.qld.gov.au/"
    url = f"{base_url}{route}?{params}"

    response = requests.get(url)
    try:
        return response.json(), response.status_code
    except requests.exceptions.JSONDecodeError:
        return {"error": "Invalid JSON response"}, response.status_code


class WasteCollectionDaysRecord(BaseModel):
    property_id: str
    unit_number: str | None
    house_number: str | None
    house_number_suffix: str | None
    street_name: str | None
    suburb: str | None

    collection_day: Literal[
        "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"
    ]
    zone: Literal["ZONE 1", "ZONE 2"]


class WasteCollectionDaysGoodResponse(BaseModel):
    total_count: int
    results: list[WasteCollectionDaysRecord]


class ErrorResponse(BaseModel):
    error: str
    status_code: int | None = None


def waste_collection_days(property_id):
    # Ensure property_id is a string consisting of only digits
    if not isinstance(property_id, str) or not property_id.isdigit():
        return ErrorResponse(error="property_id must be a string of digits")

    route = "api/explore/v2.1/catalog/datasets/waste-collection-days-collection-days/records"
    params = f"where=property_id={property_id}&limit=1"
    data, status_code = _query(route, params)
    if status_code != 200:
        return ErrorResponse(error="Failed to fetch data", status_code=status_code)
    if "error" in data:
        return ErrorResponse(error=data["error"], status_code=status_code)
    if not data.get("results"):
        return ErrorResponse(error="No results found for the given property_id")
    return WasteCollectionDaysGoodResponse(**data)


class WasteCollectionWeekRecord(BaseModel):
    week_starting: date
    zone: Literal["Zone 1", "Zone 2"]  # Yes, these are not capitalised in the response


class WasteCollectionDaysCollectionWeeksGoodResponse(BaseModel):
    total_count: int
    results: list[WasteCollectionWeekRecord]


def waste_collection_week(week_starting: date):
    route = "api/explore/v2.1/catalog/datasets/waste-collection-days-collection-weeks/records"
    params = f"refine=week_starting:{week_starting.strftime('%Y/%m/%d')}"
    data, status_code = _query(route, params)
    if status_code != 200:
        return ErrorResponse(error="Failed to fetch data", status_code=status_code)
    if "error" in data:
        return ErrorResponse(error=data["error"], status_code=status_code)
    if not data.get("results"):
        return ErrorResponse(error="No results found for the given week_starting")
    return WasteCollectionDaysCollectionWeeksGoodResponse(**data)
