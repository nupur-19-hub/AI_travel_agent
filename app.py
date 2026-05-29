import streamlit as st

from agents.travel_agent import (
    generate_full_plan,
    run_travel_agent_query,
    is_agent_ready,
)

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
)

st.title("✈️ AI Travel Planning Assistant")
st.markdown(
    "Use the sidebar to build your custom trip plan. The planner uses local tools by default, "
    "and can optionally use OpenAI if your server environment already provides a key."
)

if "plan" not in st.session_state:
    st.session_state.plan = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.header("Trip Builder")
    source = st.text_input("Source city")
    destination = st.text_input("Destination city")
    days = st.slider("Trip length (days)", 1, 14, 3)
    use_agent = st.checkbox("Use AI planning agent", value=False)
    st.markdown("---")
    st.write("Enter source, destination, and days, then click Plan My Trip.")

    if st.button("Plan My Trip"):
        if not source or not destination:
            st.error("Please enter both source and destination cities.")
        elif source.strip().lower() == destination.strip().lower():
            st.error("Source and destination must be different.")
        else:
            with st.spinner("Planning your trip..."):
                plan = generate_full_plan(source, destination, days, use_agent=use_agent)
                st.session_state.plan = plan

with st.expander("Agent status"):
    if is_agent_ready():
        st.success("AI planning agent is ready.")
    else:
        st.info(
            "Agent mode is not available yet. Set an OpenAI key in your environment. "
            "The planner still works locally."
        )

if st.session_state.plan:
    plan = st.session_state.plan
    tabs = st.tabs(["Overview", "Itinerary", "Weather & Budget", "Agent Output"])

    with tabs[0]:
        st.subheader("Trip Summary")
        st.write(plan.get("trip_summary", "No summary available."))

        st.subheader("Selected Flight")
        flight = plan.get("flight", {})
        if flight.get("error"):
            st.error(flight["error"])
        else:
            st.write(f"**Airline:** {flight.get('airline', 'N/A')}")
            st.write(f"**Route:** {flight.get('from', 'N/A')} → {flight.get('to', 'N/A')}")
            st.write(f"**Departure:** {flight.get('departure_time', 'N/A')}")
            st.write(f"**Arrival:** {flight.get('arrival_time', 'N/A')}")
            st.write(f"**Price:** ₹{flight.get('price', 'N/A')}")

        st.subheader("Hotel Recommendation")
        hotel = plan.get("hotel", {})
        if hotel.get("error"):
            st.error(hotel["error"])
        else:
            st.write(f"**Name:** {hotel.get('name', 'N/A')}")
            st.write(f"**City:** {hotel.get('city', 'N/A')}")
            st.write(f"**Stars:** {hotel.get('stars', 'N/A')} ⭐")
            st.write(f"**Price per night:** ₹{hotel.get('price_per_night', 'N/A')}")
            amenities = hotel.get("amenities", [])
            if amenities:
                st.write(f"**Amenities:** {', '.join(amenities)}")

        st.subheader("Reasoning")
        st.write(plan.get("reasoning", "No reasoning provided."))

    with tabs[1]:
        st.subheader("Day-wise Itinerary")
        itinerary = plan.get("itinerary", [])
        if itinerary:
            for day in itinerary:
                st.write(f"- {day}")
        else:
            st.write("No itinerary available.")

    with tabs[2]:
        st.subheader("Weather Forecast")
        weather = plan.get("weather")
        if isinstance(weather, dict) and "daily" in weather and "time" in weather["daily"]:
            dates = weather["daily"]["time"]
            temps = weather["daily"]["temperature_2m_max"]
            for date, temp in zip(dates[:days], temps[:days]):
                st.write(f"- {date}: {temp}°C")
        else:
            st.warning("Weather data is unavailable.")

        st.subheader("Budget Breakdown")
        budget = plan.get("budget", {})
        st.write(f"- Flight Cost: ₹{budget.get('Flight Cost', 'N/A')}")
        st.write(f"- Hotel Cost: ₹{budget.get('Hotel Cost', 'N/A')}")
        st.write(f"- Food & Transport: ₹{budget.get('Food & Transport', 'N/A')}")
        st.write(f"- Total Budget: ₹{budget.get('Total Budget', 'N/A')}")

    with tabs[3]:
        st.subheader("Agent Output")
        st.write("Use this area to ask follow-up questions.")
        if not is_agent_ready():
            st.warning("Agent mode is disabled. Set an OpenAI key in your environment to enable it.")
            st.text_input("Ask the travel assistant a follow-up question", key="chat_input", disabled=True)
            st.button("Send question", key="send_question", disabled=True)
        else:
            question = st.text_input("Ask the travel assistant a follow-up question", key="chat_input")
            if st.button("Send question", key="send_question"):
                answer = run_travel_agent_query(question)
                st.session_state.chat_history.append(("You", question))
                st.session_state.chat_history.append(("Agent", answer))

        if st.session_state.chat_history:
            for speaker, text in st.session_state.chat_history:
                st.markdown(f"**{speaker}:** {text}")
else:
    st.info("Use the sidebar to build your first trip plan. The results will appear here.")
