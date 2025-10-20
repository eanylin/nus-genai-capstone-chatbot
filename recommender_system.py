import requests
import sqlite3
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class WeatherAgent:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_weather(self, location, date):
        # Use current weather as we are dealing with same-day recommendations
        url = f"http://api.weatherapi.com/v1/current.json"
        params = {
            "key": self.api_key,
            "q": location,
            "aqi": "no"
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Weather API error: {str(e)}")

class EventAgent:
    def get_events(self, date, event_type=None):
        conn = sqlite3.connect('events.db')
        c = conn.cursor()

        try:
            if event_type:
                c.execute('SELECT * FROM events WHERE date = ? AND type = ?', (date, event_type))
            else:
                c.execute('SELECT * FROM events WHERE date = ?', (date,))

            events = c.fetchall()
            return events
        except sqlite3.Error as e:
            raise Exception(f"Database error: {str(e)}")
        finally:
            conn.close()

class RecommendationAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def generate_recommendation(self, weather_data, events):
        # Create context for GPT
        try:
            # Handle both current and forecast data
            if 'current' in weather_data:
                weather_condition = weather_data['current']['condition']['text']
                temperature = weather_data['current']['temp_c']
                context = f"Weather: {weather_condition}, Temperature: {temperature}°C\n\n"
            else:
                context = "Weather data unavailable\n\n"

            context += "Available events:\n"
            for event in events:
                # Schema: 1=name, 2=type, 3=description, 4=venue
                context += f"- {event[1]} ({event[2]}): {event[3]} at {event[4]}\n"

            # Use llm.invoke()
            system_prompt = """You are a helpful event recommender. Consider the weather conditions
            and suggest suitable events. For outdoor events, consider the temperature and weather conditions.
            Be specific about why you recommend certain events over others. Keep your response concise but informative.
            If weather data is unavailable, focus on providing a balanced recommendation of both indoor and outdoor events."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=context)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
        
        except Exception as e:
            raise Exception(f"Recommendation error: {str(e)}")

class CoordinatorAgent:
    def __init__(self, weather_api_key, llm: ChatOpenAI):
        self.weather_agent = WeatherAgent(weather_api_key)
        self.event_agent = EventAgent()
        self.recommendation_agent = RecommendationAgent(llm)

    def get_recommendations(self, location, date):
        try:
            # Get weather data
            print(f"\nFetching weather data for {location} on {date}...")
            weather_data = self.weather_agent.get_weather(location, date)

            # Get events
            print("Fetching events...")
            events = self.event_agent.get_events(date)

            if not events:
                return "No events found for this date."

            # Generate recommendations
            print("Generating recommendations...")
            recommendations = self.recommendation_agent.generate_recommendation(
                weather_data, events
            )

            return recommendations

        except Exception as e:
            return f"Error: {str(e)}"

# Entrypoint function for app.py
def run_event_recommender(location: str, llm: ChatOpenAI, weather_key: str) -> str:
    """
    Main function for the Streamlit app to call.
    It runs the event recommendation for TODAY'S date.
    """
    try:
        coordinator = CoordinatorAgent(weather_key, llm)
        # Get today's date in 'YYYY-MM-DD' format
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"--- Event Recommender Tool searching for {location} on {today_date} ---")
        
        return coordinator.get_recommendations(location, today_date)
    except Exception as e:
        print(f"--- Event Recommender Tool FAILED: {str(e)} ---")
        return f"Error in event recommender: {str(e)}"
