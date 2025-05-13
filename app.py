# -*- coding: utf-8 -*-
# --- Imports ---
import os
import datetime
import pytz # For timezone handling
import requests
import json
import webbrowser # Will be commented out where not usable from backend
import time
import re # For command parsing

from dotenv import load_dotenv # For loading environment variables
from flask import Flask, request, jsonify
from flask_cors import CORS # For handling requests from the frontend

# --- Google Calendar Imports ---
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Load Environment Variables ---
load_dotenv()
WEATHER_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')
# Use the default from your notebook if env var is missing
DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'Navi Mumbai')
YOUR_TIMEZONE = os.getenv('YOUR_TIMEZONE', 'Asia/Kolkata') # Default from your notebook

# --- Google Calendar Setup ---
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json' # Should be in the same directory
TOKEN_FILE = 'token.json' # Will be created automatically after first auth

# --- Reminder Setup ---
REMINDER_FILE = 'reminders.json'
reminders = [] # Initialize reminders list globally

# --- Basic Validation (Prints warnings on server start) ---
if not WEATHER_API_KEY:
    print("⚠️ WARNING: OPENWEATHERMAP_API_KEY not found in .env file. Weather functionality will fail.")
if not os.path.exists(CREDENTIALS_FILE):
    print(f"⚠️ WARNING: Google Calendar credentials file ('{CREDENTIALS_FILE}') not found. Calendar functions will fail.")
else:
    print(f"Found '{CREDENTIALS_FILE}'.")

print(f"Default city set to: {DEFAULT_CITY}")
print(f"Timezone set to: {YOUR_TIMEZONE}")

# --- Initialize Flask App ---
app = Flask(__name__)
CORS(app) # Enable Cross-Origin Resource Sharing

# --- Helper Functions (Adapted from Notebook - No `speak` or `listen`) ---

def load_reminders():
    """Loads reminders from the JSON file."""
    global reminders
    if os.path.exists(REMINDER_FILE):
        try:
            # Ensure file is not empty before loading
            if os.path.getsize(REMINDER_FILE) > 0:
                with open(REMINDER_FILE, 'r') as f:
                    reminders = json.load(f)
                print(f"INFO: Loaded {len(reminders)} reminders from {REMINDER_FILE}")
            else:
                print(f"INFO: Reminder file {REMINDER_FILE} is empty. Starting with empty list.")
                reminders = []
        except json.JSONDecodeError:
            print(f"ERROR: Could not decode JSON from {REMINDER_FILE}. Starting with empty list.")
            reminders = []
        except Exception as e:
            print(f"ERROR: Error loading reminders: {e}")
            reminders = []
    else:
        print(f"INFO: Reminder file {REMINDER_FILE} not found. Starting with empty list.")
        reminders = []

def save_reminders():
    """Saves the current reminders list to the JSON file."""
    global reminders
    try:
        with open(REMINDER_FILE, 'w') as f:
            json.dump(reminders, f, indent=4)
    except Exception as e:
        print(f"ERROR: Error saving reminders: {e}")

def get_weather(city):
    """Fetches weather data and RETURNS a report string or error message."""
    if not WEATHER_API_KEY:
        return "Weather API key is not configured. Cannot fetch weather."

    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}appid={WEATHER_API_KEY}&q={city}&units=metric"

    try:
        response = requests.get(complete_url, timeout=10) # Add a timeout
        response.raise_for_status() # Raises HTTPError for bad responses (4XX, 5XX)
        weather_data = response.json()

        # Handle API error codes within JSON response
        # OpenWeatherMap uses string codes sometimes, check both
        if str(weather_data.get("cod")) not in ["200", 200]:
            error_message = weather_data.get("message", "Unknown API error")
            print(f"Weather API Error for {city}: {weather_data}")
            return f"Sorry, I couldn't find weather data for {city}. Reason: {error_message}"

        main = weather_data.get("main", {})
        weather_desc_list = weather_data.get("weather", [{}])
        weather_desc = weather_desc_list[0].get("description", "No description available") if weather_desc_list else "No description available"
        temp = main.get("temp")
        feels_like = main.get("feels_like")
        humidity = main.get("humidity")
        wind_data = weather_data.get("wind", {})
        wind_speed = wind_data.get("speed")

        if temp is None:
            return f"Sorry, I couldn't get the temperature details for {city}."

        report = (f"The weather in {city.capitalize()} is currently {weather_desc}. "
                  f"The temperature is {temp:.1f} degrees Celsius")
        if feels_like is not None:
            report += f", feeling like {feels_like:.1f} degrees."
        else:
            report += "."
        if humidity is not None:
            report += f" Humidity is at {humidity} percent."
        if wind_speed is not None:
            report += f" Wind speed is {wind_speed:.1f} meters per second."

        return report # Return the report string

    except requests.exceptions.HTTPError as http_err:
        status_code = http_err.response.status_code if http_err.response else 'N/A'
        print(f"HTTP Error fetching weather for {city}: {http_err} - Status Code: {status_code}")
        if status_code == 401: return "Authentication failed for weather service. Check API key."
        elif status_code == 404: return f"Sorry, I couldn't find the city: {city}."
        else: return f"An HTTP error occurred while fetching weather: {http_err}"
    except requests.exceptions.Timeout:
        print(f"Timeout Error fetching weather for {city}")
        return "Sorry, the request to the weather service timed out."
    except requests.exceptions.RequestException as req_err:
        print(f"Connection Error fetching weather: {req_err}")
        return f"Sorry, I couldn't connect to the weather service. Error: {req_err}"
    except KeyError as key_err:
        print(f"KeyError parsing weather data: {key_err} - Data received: {weather_data if 'weather_data' in locals() else 'N/A'}")
        return f"Error parsing weather data for {city}. Unexpected data format."
    except Exception as e:
        print(f"❌ Unexpected Weather Error: {e}")
        import traceback
        traceback.print_exc() # Print full trace for debugging
        return f"An unexpected error occurred while fetching weather for {city}."

def play_music_action(query):
    """Handles music request and RETURNS a confirmation string with a URL."""
    if not query:
        return "Please specify what music you want to play."

    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    print(f"INFO: Music search requested for '{query}'. URL: {search_url}")
    # webbrowser.open(search_url) # Cannot reliably open browser from backend server
    return f"Okay, I looked up '{query}' on YouTube. You can try this link: {search_url}" # Provide link instead

def set_reminder(reminder_text):
    """Adds reminder to list/file and RETURNS confirmation string."""
    if not reminder_text:
        return "What should I remind you about?"

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reminders.append({"text": reminder_text, "set_at": now})
    save_reminders()
    print(f"--- Reminder Added ---")
    print(f"Task: {reminder_text}, Set at: {now}, Total: {len(reminders)}")
    return f"Okay, I will remember: '{reminder_text}'."

def show_reminders():
    """RETURNS a string listing the currently stored reminders."""
    if not reminders:
        return "You have no reminders set right now."

    response_str = f"Okay, you have {len(reminders)} reminder{'s' if len(reminders) > 1 else ''}: "
    for i, reminder in enumerate(reminders):
        # Add a pause or separator for better readability in speech
        response_str += f"Number {i+1}. {reminder['text']} (set at {reminder['set_at']}). "
    return response_str.strip()

# --- Google Calendar Functions ---
def get_google_calendar_service():
    """Authenticates (if necessary) and RETURNS the Google Calendar API service client."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"Error loading token file '{TOKEN_FILE}': {e}. Will try to re-authenticate.")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Refreshing calendar access token...")
                creds.refresh(Request())
                print("Token refreshed.")
                # Save the refreshed token
                try:
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                    print(f"Refreshed credentials saved to '{TOKEN_FILE}'.")
                except IOError as e:
                    print(f"❌ Error saving refreshed token: {e}")

            except Exception as e:
                print(f"❌ Token Refresh Error: {e}")
                if os.path.exists(TOKEN_FILE):
                    try: os.remove(TOKEN_FILE); print("Removed invalid token file.")
                    except OSError as oe: print(f"Could not remove token file: {oe}")
                return None # Stop if refresh fails
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"❌ Missing {CREDENTIALS_FILE}. Cannot authenticate Google Calendar.")
                return None
            try:
                print(f"Starting Google Calendar authentication flow using '{CREDENTIALS_FILE}'...")
                # Use run_local_server for easier dev, might need run_console() in some prod environments
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0) # Opens browser for auth
                print("Google Calendar authentication successful.")
                # Save credentials after successful auth
                try:
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                    print(f"Credentials saved to '{TOKEN_FILE}'.")
                except IOError as e:
                    print(f"❌ Error saving token: {e}")
            except FileNotFoundError:
                 print(f"❌ ERROR: Credentials file '{CREDENTIALS_FILE}' not found during auth flow.")
                 return None
            except Exception as e:
                 print(f"❌ Google Calendar Authentication Error: {e}")
                 return None

    # Build and return the service object
    try:
        service = build('calendar', 'v3', credentials=creds)
        print("Google Calendar service client created successfully.")
        return service
    except Exception as e:
        print(f"❌ Google Calendar Service Build Error: {e}")
        return None

def add_calendar_event(summary, description, start_time_str, end_time_str):
    """Adds event to Google Calendar and RETURNS confirmation/error string."""
    service = get_google_calendar_service()
    if not service:
        return "Cannot access Google Calendar service. Please check setup and authentication."

    try:
        local_tz = pytz.timezone(YOUR_TIMEZONE)
        # Expecting 'YYYY-MM-DD HH:MM' format from process_command
        naive_start_dt = datetime.datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
        naive_end_dt = datetime.datetime.strptime(end_time_str, '%Y-%m-%d %H:%M')
        # Make the datetime objects timezone-aware using the specified timezone
        aware_start_dt = local_tz.localize(naive_start_dt)
        aware_end_dt = local_tz.localize(naive_end_dt)
        # Format for Google Calendar API (RFC3339 format)
        start_iso = aware_start_dt.isoformat()
        end_iso = aware_end_dt.isoformat()

        event = {
            'summary': summary, 'description': description,
            'start': {'dateTime': start_iso, 'timeZone': YOUR_TIMEZONE}, # Include timezone
            'end': {'dateTime': end_iso, 'timeZone': YOUR_TIMEZONE},     # Include timezone
            'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 30}]},
        }
        print(f"Creating calendar event: {summary} from {start_iso} to {end_iso}")
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        event_link = created_event.get('htmlLink', 'No link available')
        print(f"Event created: {event_link}")
        # Don't open webbrowser from backend
        return f"Event '{summary}' created successfully! You can view it here: {event_link}"

    except ValueError as ve:
        print(f"❌ Date/Time parsing error: {ve}. Input: Start='{start_time_str}', End='{end_time_str}'")
        return "Sorry, I couldn't understand the date or time. Please use the format 'YYYY-MM-DD HH:MM'."
    except HttpError as error:
        # Provide more detail from the HttpError if possible
        error_details = error.resp.get('content', str(error)).decode('utf-8')
        try:
            error_json = json.loads(error_details)
            error_message = error_json.get('error', {}).get('message', error_details)
        except json.JSONDecodeError:
            error_message = error_details
        print(f"❌ Calendar Event Creation HttpError: {error_message}")
        return f"An error occurred creating the calendar event: {error_message}"
    except pytz.UnknownTimeZoneError:
         print(f"❌ Invalid Timezone configured: {YOUR_TIMEZONE}")
         return f"The configured timezone '{YOUR_TIMEZONE}' is invalid. Please check your .env file."
    except Exception as e:
        print(f"❌ Unexpected Calendar Error: {e}")
        import traceback
        traceback.print_exc()
        return "An unexpected error occurred while creating the calendar event."

def get_joke():
    """Fetches a joke from icanhazdadjoke and RETURNS it or an error string."""
    try:
        headers = {'Accept': 'application/json'}
        response = requests.get("https://icanhazdadjoke.com/", headers=headers, timeout=5) # Add timeout
        response.raise_for_status()
        joke_data = response.json()
        joke = joke_data.get("joke")
        if joke:
            return joke
        else:
            print("Joke API response missing 'joke' field.")
            return "Sorry, I couldn't get the joke text from the service."
    except requests.exceptions.Timeout:
        print("Joke API request timed out.")
        return "Sorry, the joke service took too long to respond."
    except requests.exceptions.RequestException as e:
        print(f"Joke API request error: {e}")
        return "Sorry, I couldn't connect to the joke service right now."
    except json.JSONDecodeError:
         print(f"Joke API JSON decode error.")
         return "Sorry, the joke service gave a response I couldn't understand."
    except Exception as e:
         print(f"Unexpected Joke error: {e}")
         return "Sorry, an unexpected error occurred while getting a joke."

# --- Main Command Processing Function ---
def process_command(command):
    """Parses the text command and executes the corresponding action, returning a string response."""
    if not command:
        return "No command received."

    command = command.lower().strip()
    # Default response if no specific command matches
    response = f"Sorry, I didn't fully understand: '{command}'. Could you try rephrasing or asking differently?"
    processed = False # Flag to track if a command was successfully handled

    # --- Basic Commands (Exact or keyword matching) ---
    if command in ["hello", "hi", "hey", "hey assistant", "good morning", "good afternoon", "good evening"]:
        # Could add time-based greeting logic here if desired
        response = "Hello there! How can I assist you?"
        processed = True
    elif command in ["what time is it", "current time", "time now", "tell me the time"]:
        try:
            now = datetime.datetime.now(pytz.timezone(YOUR_TIMEZONE))
            response = f"The current time is {now.strftime('%I:%M %p')} ({YOUR_TIMEZONE})."
            processed = True
        except Exception as e:
             print(f"Error getting time: {e}")
             response = "Sorry, I had trouble getting the current time."
             processed = True # Still processed, even on error
    elif command in ["what is today's date", "date today", "tell me the date", "today's date"]:
         try:
             today = datetime.date.today()
             response = f"Today's date is {today.strftime('%B %d, %Y')}."
             processed = True
         except Exception as e:
             print(f"Error getting date: {e}")
             response = "Sorry, I had trouble getting today's date."
             processed = True # Still processed

    # --- Weather (Using startswith for flexibility) ---
    elif command.startswith("weather in ") or command.startswith("forecast for "):
        city = ""
        if command.startswith("weather in "): city = command.split("weather in", 1)[-1].strip()
        elif command.startswith("forecast for "): city = command.split("forecast for", 1)[-1].strip()

        # Basic check if city name seems valid (not empty)
        if city and city != "?": # Avoid empty string or just "?" if parsing failed
            response = get_weather(city)
        else:
            response = "Which city's weather would you like? Please say 'weather in [City Name]'."
        processed = True
    elif command == "weather" or command == "forecast":
         response = get_weather(DEFAULT_CITY) # Use default city if no specific one mentioned
         processed = True

    # --- Music (Using startswith) ---
    elif command.startswith(("play music ", "play song ", "search youtube for ")):
        query = ""
        if command.startswith("play music "): query = command.split("play music ", 1)[-1].strip()
        elif command.startswith("play song "): query = command.split("play song ", 1)[-1].strip()
        elif command.startswith("search youtube for "): query = command.split("search youtube for ", 1)[-1].strip()

        if query:
            response = play_music_action(query)
        else:
            response = "What music, song, or video would you like me to search for on YouTube?"
        processed = True

    # --- Reminders (Using startswith and exact match) ---
    elif command.startswith("remind me to "):
        reminder_text = command.split("remind me to", 1)[-1].strip()
        if reminder_text:
            response = set_reminder(reminder_text)
        else:
            response = "What should I remind you about? Please say 'remind me to [your task]'."
        processed = True
    elif command in ["show reminders", "what are my reminders", "list reminders", "read reminders"]:
         response = show_reminders()
         processed = True

    # --- Calendar (Using Regex for structured input) ---
    elif command.startswith(("add calendar event ", "schedule event ")):
        # Regex to capture 'Title', 'Start Date/Time', 'End Date/Time', optional 'Description'
        # Expects single quotes around title, dates, and description
        pattern = r"(?:add calendar event|schedule event)\s+'([^']*)'\s+from\s+'([^']*)'\s+to\s+'([^']*)'(?:\s+description\s+'([^']*)')?"
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            summary, start_str, end_str, description = match.groups()
            description = description if description else "" # Handle if description is missing
            # Basic validation for date/time format before calling API
            try:
                datetime.datetime.strptime(start_str, '%Y-%m-%d %H:%M')
                datetime.datetime.strptime(end_str, '%Y-%m-%d %H:%M')
                response = add_calendar_event(summary, description, start_str, end_str)
            except ValueError:
                 response = "The date/time format seems incorrect. Please use 'YYYY-MM-DD HH:MM'."
        else:
            response = ("To add an event, please use the format: "
                        "add calendar event 'Title' from 'YYYY-MM-DD HH:MM' to 'YYYY-MM-DD HH:MM' description 'Details'")
        processed = True

    # --- Jokes (Exact or keyword matching) ---
    elif command in ["tell me a joke", "make me laugh", "tell a joke", "joke"]:
         response = get_joke()
         processed = True

    # --- Exit/Stop Command Acknowledgement ---
    elif command in ["goodbye", "exit", "stop listening", "stop", "shut down", "that's all"]:
        response = "Okay, goodbye!"
        # This response doesn't stop the server, just acknowledges the user's intent.
        processed = True

    # --- Log the interaction ---
    # Use the 'processed' flag to see if the default fallback message is being used
    if not processed:
        print(f"Command NOT recognized: '{command}'. Sending default response.")
    else:
        print(f"Command recognized: '{command}' --> Response generated.")

    return response

# --- Flask Routes ---

@app.route('/')
def home():
    # Simple HTML page to confirm the server is running
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Voice Assistant Backend</title></head>
    <body>
        <h1>Voice Assistant Backend</h1>
        <p>The Flask server is running.</p>
        <p>The frontend should send POST requests to the <code>/process</code> endpoint.</p>
    </body>
    </html>
    """

@app.route('/process', methods=['POST'])
def handle_command():
    """Endpoint to receive commands from the frontend via POST request."""
    # Ensure the request contains JSON data
    if not request.is_json:
        print("Error: Request received was not JSON")
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400

    data = request.get_json()
    user_query = data.get('query')

    # Ensure the 'query' key exists in the JSON data
    if user_query is None: # Check specifically for None
        print("Error: 'query' field missing in request JSON")
        return jsonify({"error": "Missing 'query' field in request JSON."}), 400

    # Log the received query for debugging
    print(f"Received query from frontend: '{user_query}'")

    # Call the main processing function and handle potential errors
    try:
        assistant_reply = process_command(user_query)
        # Return the successful reply in JSON format
        print(f"Sending reply to frontend: '{assistant_reply}'")
        return jsonify({"reply": assistant_reply})
    except Exception as e:
        # Log unexpected errors during command processing
        print(f"--- FATAL ERROR DURING process_command ---")
        print(f"Query: '{user_query}'")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Details: {e}")
        # Log the full traceback for detailed debugging
        import traceback
        traceback.print_exc()
        # Return a generic server error message to the frontend
        return jsonify({"error": "An internal server error occurred while processing the command. Please check server logs."}), 500

# --- Main Execution Block ---
if __name__ == '__main__':
    print("--- Initializing Voice Assistant Backend ---")
    load_reminders() # Load reminders from file on server startup

    # Optional: Could add a check/attempt for Google Auth here if desired
    # print("Checking Google Calendar service availability...")
    # get_google_calendar_service() # Calling this might trigger auth flow if needed

    print("--- Flask Server Starting ---")
    print("Backend is ready to receive requests from the frontend.")
    # Use host='127.0.0.1' for local access only.
    # Use host='0.0.0.0' to make accessible on your local network (use with caution).
    # debug=True is helpful for development (auto-reloads on code changes, shows detailed errors)
    # Turn debug=False for any kind of production/deployment scenario.
    app.run(debug=True, port=5000, host='127.0.0.1')