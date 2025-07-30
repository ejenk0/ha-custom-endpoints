from flask import Flask, jsonify, request
from datetime import datetime, timedelta, timezone
from bcc_api import (
    waste_collection_days,
    waste_collection_week,
    ErrorResponse,
)

app = Flask(__name__)

BRISBANE_TZ = timezone(timedelta(hours=10), "Brisbane")


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "pong", "date": datetime.now().isoformat()})


"""
Custom endpoint to get the next bin collection day based on address.

parameters:
- property_id: The address for which to find the next bin collection day.
"""


@app.route("/bcc-bin-day", methods=["GET"])
def bcc_bin_day():
    property_id = request.args.get("property_id")
    if not property_id:
        return jsonify({"error": "Property ID parameter is required"}), 400

    response = waste_collection_days(property_id)
    if isinstance(response, ErrorResponse):
        return jsonify(response.model_dump_json(), status=response.status_code or 500)

    zone = response.results[0].zone
    day = response.results[0].collection_day
    weekday = [
        "MONDAY",
        "TUESDAY",
        "WEDNESDAY",
        "THURSDAY",
        "FRIDAY",
        "SATURDAY",
        "SUNDAY",
    ].index(day)

    next_collection_date = datetime.now()
    days_ahead = (weekday - next_collection_date.weekday()) % 7
    if days_ahead == 0 and next_collection_date.hour >= 7:
        days_ahead = 7
    next_collection_date += timedelta(days=days_ahead)
    next_collection_date = next_collection_date.replace(
        hour=7, minute=0, second=0, microsecond=0, tzinfo=BRISBANE_TZ
    )

    # Get first day of the week of the next collection date
    first_day_of_week = next_collection_date - timedelta(
        days=next_collection_date.weekday()
    )
    first_day_of_week = first_day_of_week.replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    week_response = waste_collection_week(first_day_of_week)
    if isinstance(week_response, ErrorResponse):
        return jsonify(
            week_response.model_dump_json(), status=week_response.status_code or 500
        )

    is_recycling_week = False
    if week_response.results[0].zone.upper() == zone:
        is_recycling_week = True

    return jsonify(
        {
            "next_collection_day": day.capitalize(),
            "next_collection_date": next_collection_date.isoformat(),
            "is_recycling_week": is_recycling_week,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
