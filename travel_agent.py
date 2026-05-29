import os
from typing import Any

import openai
from tools.budget_tool import calculate_budget
from tools.flight_tool import get_cheapest_flight
from tools.hotel_tool import get_best_hotel
from tools.itinerary_tool import generate_itinerary
from tools.places_tool import get_top_places
from tools.weather_tool import get_weather

MODEL_NAME = "gpt-3.5-turbo"
OPENAI_API_KEY = None


def set_openai_api_key(api_key: str | None) -> None:
    """Set or clear the OpenAI API key for this session."""
    global OPENAI_API_KEY
    OPENAI_API_KEY = api_key.strip() if api_key else None


def _get_api_key() -> str | None:
    return OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")


def _create_client():
    api_key = _get_api_key()
    if not api_key:
        return None

    try:
        openai.api_key = api_key
        return openai
    except Exception:
        return None


def is_agent_ready() -> bool:
    return _create_client() is not None


def _invoke_llm(prompt: str) -> str | None:
    client = _create_client()
    if client is None:
        return None

    try:
        completion = client.ChatCompletion.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"OpenAI Error: {str(e)}"


def _generate_ai_summary(plan: dict[str, Any]) -> str:
    prompt = (
        f"A user is taking a {plan['days']}-day trip from {plan['source']} to {plan['destination']}. "
        "Summarize the trip, including the flight, hotel, itinerary highlights, weather expectations, "
        "and the budget breakdown in a friendly tone."
    )
    result = _invoke_llm(prompt)
    return result or plan.get("trip_summary", "No summary available.")


def run_travel_agent_query(question: str) -> str:
    if not is_agent_ready():
        return "Agent is not ready. Set OPENAI_API_KEY in the environment and restart the app."

    prompt = f"Answer this travel planning question concisely:\n\n{question}"
    result = _invoke_llm(prompt)
    return result or "I could not generate an answer."


def generate_full_plan(source: str, destination: str, days: int, use_agent: bool = False) -> dict[str, Any]:
    flight = get_cheapest_flight(source, destination)
    hotel = get_best_hotel(destination)
    places = get_top_places(destination)

    flight_error = None
    hotel_error = None

    if isinstance(flight, str):
        flight_error = flight
        flight = {}

    if isinstance(hotel, str):
        hotel_error = hotel
        hotel = {}

    itinerary = []
    if places and isinstance(places, list):
        itinerary = generate_itinerary(places, days)

    weather = None
    try:
        weather = get_weather(destination)
    except Exception:
        weather = {"error": "Unable to fetch weather data."}

    flight_price = flight.get("price", 0) if isinstance(flight, dict) else 0
    hotel_price = hotel.get("price_per_night", 0) if isinstance(hotel, dict) else 0
    budget = calculate_budget(flight_price, hotel_price, days)

    plan = {
        "source": source,
        "destination": destination,
        "days": days,
        "trip_summary": f"A {days}-day trip from {source} to {destination}.",
        "flight": {**flight, "error": flight_error} if flight_error else flight,
        "hotel": {**hotel, "error": hotel_error} if hotel_error else hotel,
        "itinerary": itinerary,
        "weather": weather,
        "budget": budget,
        "reasoning": "This plan was generated using local travel tools.",
    }

    if use_agent and is_agent_ready():
        plan["trip_summary"] = _generate_ai_summary(plan)
        plan["reasoning"] = "This plan uses local tools plus OpenAI for a better summary."

    return plan
