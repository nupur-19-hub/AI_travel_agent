import streamlit as st

from agents.travel_agent import (
    generate_full_plan,
    run_travel_agent_query,
    is_agent_ready,
    set_openai_api_key,
)

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
)

st.title("✈️ AI Travel Planning Assistant")

st.markdown(
    """
    Plan trips using local travel tools and optionally enhance them
    with OpenAI-generated summaries and follow-up travel assistance.
    """
)

# Session State
if "plan" not in st.session_state:
    st.session_state.plan = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# Sidebar
with st.sidebar:
    st.header("Trip Builder")

    st.subheader("OpenAI Settings")

    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Set Key"):
            if api_key.strip():
                set_openai_api_key(api_key.strip())
                st.success("API key set successfully.")
            else:
                st.warning("Enter a valid API key.")

    with col2:
        if st.button("Clear Key"):
            set_openai_api_key(None)
            st.info("API key removed.")

    st.divider()

    source = st.text_input("Source City")

    destination = st.text_input("Destination City")

    days = st.slider(
        "Trip Length (Days)",
        min_value=1,
        max_value=14,
        value=3,
    )

    use_agent = st.checkbox(
        "Use OpenAI for AI Summary",
        value=False,
    )

    st.divider()

    if st.button("Plan My Trip", use_container_width=True):

        if not source.strip():
            st.error("Please enter a source city.")

        elif not destination.strip():
            st.error("Please enter a destination city.")

        elif source.strip().lower() == destination.strip().lower():
            st.error("Source and destination must be different.")

        else:
            with st.spinner("Generating your travel plan..."):

                plan = generate_full_plan(
                    source=source,
                    destination=destination,
                    days=days,
                    use_agent=use_agent,
                )

                st.session_state.plan = plan


# Agent Status
with st.expander("Agent Status"):

    if is_agent_ready():
        st.success("OpenAI Agent is ready.")
    else:
        st.warning(
            "Agent mode disabled. Enter a valid OpenAI API key in the sidebar."
        )


# Display Plan
if st.session_state.plan:

    plan = st.session_state.plan

    tabs = st.tabs(
        [
            "Overview",
            "Itinerary",
            "Weather & Budget",
            "AI Assistant",
        ]
    )

    # Overview Tab
    with tabs[0]:

        st.subheader("Trip Summary")

        st.write(
            plan.get(
                "trip_summary",
                "No summary available.",
            )
        )

        st.divider()

        st.subheader("Flight")

        flight = plan.get("flight", {})

        if isinstance(flight, dict):

            st.write(
                f"**Airline:** {flight.get('airline', 'N/A')}"
            )

            st.write(
                f"**Route:** {flight.get('from', 'N/A')} → {flight.get('to', 'N/A')}"
            )

            st.write(
                f"**Departure:** {flight.get('departure_time', 'N/A')}"
            )

            st.write(
                f"**Arrival:** {flight.get('arrival_time', 'N/A')}"
            )

            st.write(
                f"**Price:** ₹{flight.get('price', 'N/A')}"
            )

        st.divider()

        st.subheader("Hotel")

        hotel = plan.get("hotel", {})

        if isinstance(hotel, dict):

            st.write(
                f"**Name:** {hotel.get('name', 'N/A')}"
            )

            st.write(
                f"**City:** {hotel.get('city', 'N/A')}"
            )

            st.write(
                f"**Stars:** {hotel.get('stars', 'N/A')} ⭐"
            )

            st.write(
                f"**Price Per Night:** ₹{hotel.get('price_per_night', 'N/A')}"
            )

            amenities = hotel.get("amenities", [])

            if amenities:
                st.write(
                    f"**Amenities:** {', '.join(amenities)}"
                )

        st.divider()

        st.subheader("Reasoning")

        st.write(
            plan.get(
                "reasoning",
                "No reasoning available.",
            )
        )

    # Itinerary Tab
    with tabs[1]:

        st.subheader("Day-wise Itinerary")

        itinerary = plan.get("itinerary", [])

        if itinerary:

            for day in itinerary:
                st.write(f"• {day}")

        else:
            st.info("No itinerary available.")

    # Weather & Budget Tab
    with tabs[2]:

        st.subheader("Weather Forecast")

        weather = plan.get("weather")

        try:

            dates = weather["daily"]["time"]
            temps = weather["daily"]["temperature_2m_max"]

            for date, temp in zip(dates[:days], temps[:days]):
                st.write(
                    f"• {date}: {temp}°C"
                )

        except Exception:
            st.warning(
                "Weather data unavailable."
            )

        st.divider()

        st.subheader("Budget Breakdown")

        budget = plan.get("budget", {})

        st.write(
            f"Flight Cost: ₹{budget.get('Flight Cost', 'N/A')}"
        )

        st.write(
            f"Hotel Cost: ₹{budget.get('Hotel Cost', 'N/A')}"
        )

        st.write(
            f"Food & Transport: ₹{budget.get('Food & Transport', 'N/A')}"
        )

        st.write(
            f"Total Budget: ₹{budget.get('Total Budget', 'N/A')}"
        )

    # AI Assistant Tab
    with tabs[3]:

        st.subheader("Travel Assistant")

        if not is_agent_ready():

            st.warning(
                "OpenAI Agent not ready. Set a valid API key."
            )

        else:

            question = st.text_input(
                "Ask a travel question"
            )

            if st.button("Send"):

                if question.strip():

                    answer = run_travel_agent_query(
                        question
                    )

                    st.session_state.chat_history.append(
                        ("You", question)
                    )

                    st.session_state.chat_history.append(
                        ("Agent", answer)
                    )

        if st.session_state.chat_history:

            st.divider()

            for speaker, message in st.session_state.chat_history:

                st.markdown(
                    f"**{speaker}:** {message}"
                )

else:

    st.info(
        "Fill in the trip details in the sidebar and click 'Plan My Trip'."
    )