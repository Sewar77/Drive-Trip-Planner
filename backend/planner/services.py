from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
import math
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
USER_AGENT = "SpotterFullStackAssessment/1.0"
M_TO_MILES = 0.000621371
SEC_TO_HOURS = 1 / 3600

DRIVE_LIMIT = 11.0
WINDOW_LIMIT = 14.0
BREAK_AFTER_DRIVING = 8.0
BREAK_HOURS = 0.5
DAILY_REST_HOURS = 10.0
CYCLE_LIMIT = 70.0
RESTART_HOURS = 34.0
SERVICE_HOURS = 1.0
FUEL_INTERVAL_MILES = 1000.0
FUEL_STOP_HOURS = 0.5

@dataclass
class Event:
    status: str
    start: datetime
    end: datetime
    label: str
    location: str = ""
    miles: float = 0.0

    @property
    def hours(self):
        return (self.end - self.start).total_seconds() / 3600

    def json(self):
        d = asdict(self)
        d["start"] = self.start.isoformat()
        d["end"] = self.end.isoformat()
        d["hours"] = round(self.hours, 3)
        d["miles"] = round(self.miles, 1)
        return d

class RoutingError(Exception):
    pass

def geocode(query: str) -> dict:
    response = requests.get(
        NOMINATIM_URL,
        params={"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "us"},
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    if not data:
        raise RoutingError(f'Could not find "{query}". Try a more specific U.S. city/address.')
    return {
        "name": data[0]["display_name"],
        "lat": float(data[0]["lat"]),
        "lon": float(data[0]["lon"]),
    }

def route(points: list[dict]) -> dict:
    coords = ";".join(f'{p["lon"]},{p["lat"]}' for p in points)
    response = requests.get(
        f"{OSRM_URL}/{coords}",
        params={"overview": "full", "geometries": "geojson", "steps": "false"},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise RoutingError("Routing service could not build this route.")
    r = data["routes"][0]
    return {
        "distance_miles": r["distance"] * M_TO_MILES,
        "duration_hours": r["duration"] * SEC_TO_HOURS,
        "geometry": r["geometry"],
    }

def _add(events, status, cursor, hours, label, location="", miles=0):
    if hours <= 1e-9:
        return cursor
    end = cursor + timedelta(hours=hours)
    events.append(Event(status, cursor, end, label, location, miles))
    return end

def _split_event_by_midnight(event: Event):
    pieces = []
    cursor = event.start
    while cursor < event.end:
        midnight = datetime.combine(
            (cursor + timedelta(days=1)).date(),
            datetime.min.time(),
            tzinfo=cursor.tzinfo,
        )
        end = min(event.end, midnight)
        ratio = (end - cursor).total_seconds() / max((event.end - event.start).total_seconds(), 1)
        pieces.append(Event(event.status, cursor, end, event.label, event.location, event.miles * ratio))
        cursor = end
    return pieces

def build_daily_logs(events: list[Event]):
    by_date = {}
    for event in events:
        for piece in _split_event_by_midnight(event):
            key = piece.start.date().isoformat()
            by_date.setdefault(key, []).append(piece)

    if not by_date:
        return []

    first = min(e.start for e in events)
    last = max(e.end for e in events)
    date_cursor = first.date()
    last_date = last.date()
    logs = []

    while date_cursor <= last_date:
        key = date_cursor.isoformat()
        day_start = datetime.combine(date_cursor, datetime.min.time(), tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        pieces = sorted(by_date.get(key, []), key=lambda e: e.start)

        # Fill uncovered parts of the 24-hour sheet as Off Duty.
        filled = []
        cursor = day_start
        for p in pieces:
            if p.start > cursor:
                filled.append(Event("off_duty", cursor, p.start, "Off Duty"))
            filled.append(p)
            cursor = max(cursor, p.end)
        if cursor < day_end:
            filled.append(Event("off_duty", cursor, day_end, "Off Duty"))
        if not filled:
            filled = [Event("off_duty", day_start, day_end, "Off Duty")]

        totals = {"off_duty": 0, "sleeper": 0, "driving": 0, "on_duty": 0}
        miles = 0
        for e in filled:
            totals[e.status] += e.hours
            miles += e.miles

        logs.append({
            "date": key,
            "total_miles": round(miles, 1),
            "totals": {k: round(v, 2) for k, v in totals.items()},
            "events": [e.json() for e in filled],
        })
        date_cursor += timedelta(days=1)
    return logs

def plan_hos(total_miles: float, driving_hours: float, current_cycle_used: float, pickup_name: str, dropoff_name: str):
    # A deterministic UTC noon start keeps generated logs readable without requiring a timezone input.
    now = datetime.now(timezone.utc)
    cursor = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if cursor < now:
        cursor += timedelta(days=1)

    events = []
    cycle_used = current_cycle_used
    drive_today = 0.0
    drive_since_break = 0.0
    window_used = 0.0
    miles_since_fuel = 0.0
    remaining_miles = total_miles
    remaining_drive_hours = driving_hours

    def restart_if_needed(required_on_duty=0.001):
        nonlocal cursor, cycle_used, drive_today, drive_since_break, window_used
        if cycle_used + required_on_duty > CYCLE_LIMIT + 1e-9:
            cursor = _add(events, "off_duty", cursor, RESTART_HOURS, "34-hour cycle restart")
            cycle_used = 0.0
            drive_today = 0.0
            drive_since_break = 0.0
            window_used = 0.0

    def daily_rest():
        nonlocal cursor, drive_today, drive_since_break, window_used
        cursor = _add(events, "off_duty", cursor, DAILY_REST_HOURS, "10-hour off-duty rest")
        drive_today = 0.0
        drive_since_break = 0.0
        window_used = 0.0

    def on_duty(hours, label, location):
        nonlocal cursor, cycle_used, window_used
        restart_if_needed(hours)
        if window_used + hours > WINDOW_LIMIT + 1e-9:
            daily_rest()
            restart_if_needed(hours)
        cursor = _add(events, "on_duty", cursor, hours, label, location)
        cycle_used += hours
        window_used += hours

    # Pickup happens before line-haul driving.
    on_duty(SERVICE_HOURS, "Pickup / loading", pickup_name)

    while remaining_drive_hours > 1e-6:
        restart_if_needed()

        available_cycle = CYCLE_LIMIT - cycle_used
        available_drive = DRIVE_LIMIT - drive_today
        available_window = WINDOW_LIMIT - window_used
        available_break = BREAK_AFTER_DRIVING - drive_since_break

        if available_cycle <= 1e-6:
            restart_if_needed(0.001)
            continue
        if available_drive <= 1e-6 or available_window <= 1e-6:
            daily_rest()
            continue
        if available_break <= 1e-6:
            cursor = _add(events, "off_duty", cursor, BREAK_HOURS, "30-minute rest break")
            window_used += BREAK_HOURS
            drive_since_break = 0.0
            if window_used >= WINDOW_LIMIT - 1e-6:
                daily_rest()
            continue

        # Estimate time until next required fuel threshold.
        avg_mph = total_miles / driving_hours if driving_hours > 0 else 55
        miles_to_fuel = FUEL_INTERVAL_MILES - miles_since_fuel
        hours_to_fuel = miles_to_fuel / max(avg_mph, 1)

        chunk = min(
            remaining_drive_hours,
            available_cycle,
            available_drive,
            available_window,
            available_break,
            hours_to_fuel,
        )

        if chunk <= 1e-6:
            # Fuel threshold reached.
            on_duty(FUEL_STOP_HOURS, "Fuel stop", "En route")
            miles_since_fuel = 0.0
            continue

        chunk_miles = min(remaining_miles, chunk * avg_mph)
        cursor = _add(events, "driving", cursor, chunk, "Driving", "En route", chunk_miles)
        remaining_drive_hours -= chunk
        remaining_miles -= chunk_miles
        drive_today += chunk
        drive_since_break += chunk
        window_used += chunk
        cycle_used += chunk
        miles_since_fuel += chunk_miles

        if remaining_drive_hours <= 1e-6:
            break

        if miles_since_fuel >= FUEL_INTERVAL_MILES - 0.1:
            on_duty(FUEL_STOP_HOURS, "Fuel stop", "En route")
            miles_since_fuel = 0.0
        elif drive_since_break >= BREAK_AFTER_DRIVING - 1e-6:
            cursor = _add(events, "off_duty", cursor, BREAK_HOURS, "30-minute rest break")
            window_used += BREAK_HOURS
            drive_since_break = 0.0
        elif drive_today >= DRIVE_LIMIT - 1e-6 or window_used >= WINDOW_LIMIT - 1e-6:
            daily_rest()

    on_duty(SERVICE_HOURS, "Drop-off / unloading", dropoff_name)

    return events, cycle_used

def build_trip_plan(current_location, pickup_location, dropoff_location, current_cycle_used):
    current = geocode(current_location)
    pickup = geocode(pickup_location)
    dropoff = geocode(dropoff_location)

    first_leg = route([current, pickup])
    second_leg = route([pickup, dropoff])

    total_miles = first_leg["distance_miles"] + second_leg["distance_miles"]
    total_driving_hours = first_leg["duration_hours"] + second_leg["duration_hours"]

    # Route the full geometry in the same waypoint order for display.
    display_route = route([current, pickup, dropoff])

    events, final_cycle = plan_hos(
        total_miles,
        total_driving_hours,
        current_cycle_used,
        pickup["name"],
        dropoff["name"],
    )

    stops = [
        e.json()
        for e in events
        if e.status != "driving"
        and ("break" in e.label.lower() or "rest" in e.label.lower() or "fuel" in e.label.lower()
             or "pickup" in e.label.lower() or "drop-off" in e.label.lower() or "restart" in e.label.lower())
    ]

    return {
        "summary": {
            "distance_miles": round(total_miles, 1),
            "estimated_driving_hours": round(total_driving_hours, 2),
            "current_cycle_used": round(current_cycle_used, 2),
            "final_cycle_used": round(final_cycle, 2),
            "number_of_daily_logs": len(build_daily_logs(events)),
        },
        "locations": {"current": current, "pickup": pickup, "dropoff": dropoff},
        "route": {
            "type": "Feature",
            "properties": {},
            "geometry": display_route["geometry"],
        },
        "events": [e.json() for e in events],
        "stops": stops,
        "daily_logs": build_daily_logs(events),
        "assumptions": [
            "Property-carrying driver using the 70-hour / 8-day cycle.",
            "Current Cycle Used is treated as currently consumed cycle hours because prior 8-day daily history is not supplied.",
            "A 34-hour restart is scheduled when cycle capacity is exhausted.",
            "Pickup and drop-off each take 1 hour on duty, not driving.",
            "Fuel is scheduled at least every 1,000 miles; this implementation assumes a 30-minute fuel stop.",
            "No adverse-driving-condition exception or split-sleeper optimization is used.",
        ],
    }
