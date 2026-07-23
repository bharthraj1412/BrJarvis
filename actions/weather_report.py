import webbrowser
import json
from urllib.parse import quote_plus


def weather_action(
    parameters: dict,
    player=None,
    session_memory=None,
) -> str:
    city     = (parameters.get("city") or "").strip()
    when     = (parameters.get("time") or "today").strip()

    # ── Try to fetch real weather data from wttr.in (JSON) ────────────────
    weather_text = _fetch_weather_data(city)

    if weather_text:
        # Build a Google search URL so later 'open it in brave' can resolve it
        from urllib.parse import quote_plus as _qp
        google_url = f"https://www.google.com/search?q={_qp(f'weather in {city} {when}')}"
        # Also open browser for visual display if city specified
        if city:
            url = google_url
            try:
                webbrowser.open(url)
            except Exception:
                pass

        # Embed URL so context resolver can reopen in a specific browser
        weather_text_with_url = weather_text + f"\nSearch URL: {google_url}"
        _log(weather_text_with_url, player)

        if session_memory:
            try:
                session_memory.set_last_search(
                    query=f"weather in {city} {when}", response=weather_text_with_url
                )
            except Exception:
                pass

        return weather_text_with_url

    # ── Fallback: open browser and return a clear completion message ──────
    search_query  = f"weather in {city} {when}"
    url           = f"https://www.google.com/search?q={quote_plus(search_query)}"

    try:
        opened = webbrowser.open(url)
        if not opened:
            raise RuntimeError("webbrowser.open returned False")
    except Exception as e:
        msg = f"Sir, I couldn't open the browser for the weather report: {e}"
        _log(msg, player)
        return msg

    # Embed URL so context resolver can reopen in a different browser on request
    msg = (
        f"Weather for {city} ({when}): Opened in browser. "
        f"Search URL: {url} "
        f"[DONE — no further weather calls needed]"
    )
    _log(msg, player)

    if session_memory:
        try:
            session_memory.set_last_search(query=search_query, response=msg)
        except Exception:
            pass

    return msg


def _fetch_weather_data(city: str) -> str | None:
    """Fetch real weather data from wttr.in API (free, no key needed)."""
    try:
        import urllib.request
        url = f"https://wttr.in/{quote_plus(city)}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/37.5"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        current = data.get("current_condition", [{}])[0]
        temp_c  = current.get("temp_C", "?")
        feels   = current.get("FeelsLikeC", "?")
        humidity = current.get("humidity", "?")
        desc    = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
        wind_km = current.get("windspeedKmph", "?")
        wind_dir = current.get("winddir16Point", "")

        area = data.get("nearest_area", [{}])[0]
        area_name = area.get("areaName", [{}])[0].get("value", city)
        country   = area.get("country", [{}])[0].get("value", "")

        return (
            f"Weather in {area_name}, {country}:\n"
            f"• Condition: {desc}\n"
            f"• Temperature: {temp_c}°C (Feels like {feels}°C)\n"
            f"• Humidity: {humidity}%\n"
            f"• Wind: {wind_km} km/h {wind_dir}"
        )
    except Exception:
        return None


def _log(message: str, player=None) -> None:
    print(f"[Weather] {message}")
    if player:
        try:
            player.write_log(f"JARVIS: {message}")
        except Exception:
            pass