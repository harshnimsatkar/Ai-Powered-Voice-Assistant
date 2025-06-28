# Ai-Powered-Voice-Assistant

A web-based AI voice assistant built with Python (Flask) for the backend and HTML, CSS, and JavaScript (Web Speech API) for the frontend. It can understand voice commands, perform actions, and respond with voice.

## Features

*   **Voice Interaction:** Uses browser's Web Speech API for speech-to-text and text-to-speech.
*   **Greetings & Basic Chat:** Responds to simple greetings.
*   **Time & Date:** Tells the current time and date based on your configured timezone.
*   **Weather Forecasts:** Fetches and reports current weather for a specified city (or a default city) using the OpenWeatherMap API.
*   **Music Playback:** Searches for music/videos on YouTube and provides a link.
*   **Reminders:** Allows users to set reminders, which are stored locally in a `reminders.json` file. Users can also view their set reminders.
*   **Google Calendar Integration:**
    *   Authenticates with Google Calendar API via OAuth 2.0.
    *   Adds events to your primary Google Calendar.
*   **Jokes:** Tells jokes fetched from the icanhazdadjoke API.
*   **User-Friendly Interface:** Simple web page to interact with the assistant.

## Tech Stack

*   **Backend:**
    *   Python 3
    *   Flask (Web framework)
    *   `requests` (for HTTP requests to external APIs)
    *   `pytz` (for timezone handling)
    *   `python-dotenv` (for managing environment variables)
    *   `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2` (for Google Calendar API)
    *   `Flask-CORS` (for Cross-Origin Resource Sharing)
*   **Frontend:**
    *   HTML5
    *   CSS3
    *   JavaScript (ES6+)
    *   Web Speech API (SpeechRecognition and SpeechSynthesis)
*   **APIs Used:**
    *   OpenWeatherMap API
    *   Google Calendar API
    *   icanhazdadjoke API

## Prerequisites

1.  **Python 3.7+** and **pip**.
2.  A **modern web browser** that supports the Web Speech API (e.g., Google Chrome, Microsoft Edge).
3.  A **Google Account** (for Google Calendar integration).
4.  A **Google Cloud Platform Project** with the Google Calendar API enabled.
5.  An **OpenWeatherMap API Key**.

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-name>
    ```

2.  **Google Calendar API Setup:**
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project or select an existing one.
    *   Navigate to "APIs & Services" > "Library".
    *   Search for "Google Calendar API" and enable it.
    *   Navigate to "APIs & Services" > "Credentials".
    *   Click "Create Credentials" > "OAuth client ID".
    *   If prompted, configure the OAuth consent screen (User Type: External, fill in required app info). Add your Google email as a test user during development if your app is in "testing" publishing status.
    *   Choose "Desktop app" as the Application type.
    *   Name your client (e.g., "VoiceAssistantCalendarClient").
    *   Click "Create".
    *   Download the JSON file. **Rename this file to `credentials.json` and place it in the root of your project directory.**
    *   *Note:* The `token.json` file will be created automatically in the project root after you successfully authenticate the application with Google Calendar for the first time.

3.  **OpenWeatherMap API Key:**
    *   Sign up at [OpenWeatherMap](https://openweathermap.org/appid).
    *   Get your API key from your account page.

4.  **Environment Variables:**
    *   Create a file named `.env` in the root of your project directory.
    *   Add your API key and preferences to this file:
        ```env
        OPENWEATHERMAP_API_KEY="YOUR_OPENWEATHERMAP_API_KEY"
        DEFAULT_CITY="YourDefaultCity" # e.g., New York
        YOUR_TIMEZONE="Your/Timezone"  # e.g., America/New_York (Find valid names from pytz documentation or a list like https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
        ```
    *   Replace placeholders with your actual key, city, and timezone.

5.  **Python Dependencies:**
    *   It's highly recommended to use a virtual environment:
        ```bash
        python -m venv venv
        # On Windows:
        # venv\Scripts\activate
        # On macOS/Linux:
        # source venv/bin/activate
        ```
    *   Install the required Python packages:
        ```bash
        pip install Flask Flask-CORS requests python-dotenv pytz google-api-python-client google-auth-oauthlib google-auth-httplib2
        ```
        (Alternatively, you can create a `requirements.txt` file with these package names and run `pip install -r requirements.txt`)

6.  **Configure Backend URL (if necessary):**
    *   Open `script.js`.
    *   Ensure the `BACKEND_URL` constant points to your Flask server's address (default is `http://127.0.0.1:5000/process`).

## Running the Application

1.  **Start the Flask Backend Server:**
    *   Open your terminal, navigate to the project's root directory, and ensure your virtual environment is activated.
    *   Run the Python application:
        ```bash
        python app.py
        ```
    *   You should see output indicating the server is running, typically on `http://127.0.0.1:5000/`.

2.  **Open the Frontend:**
    *   Open the `index.html` file in your web browser.

3.  **First-Time Google Calendar Authentication:**
    *   When you use a command that interacts with Google Calendar for the first time (e.g., "add calendar event..."), your browser will open a new tab/window for Google authentication.
    *   Follow the prompts to allow the application access to your calendar.
    *   After successful authentication, a `token.json` file will be created in your project directory, storing your credentials for future sessions.

## How to Use

1.  Open `index.html` in your browser.
2.  Click the "🎤 Start Listening" button.
3.  Your browser will likely ask for permission to use your microphone. Allow it.
4.  The button text will change to "🛑 Stop Listening" and the status will update to "Listening...".
5.  Speak your command clearly. Examples:
    *   "Hello"
    *   "What time is it?"
    *   "What is today's date?"
    *   "Weather in London"
    *   "Play music arijit singh"
    *   "Remind me to call mom tomorrow"
    *   "Show reminders"
    *   "Add calendar event 'Doctor Appointment' from '2024-08-15 10:00' to '2024-08-15 11:00' description 'Annual checkup'"
    *   "Tell me a joke"
    *   "Goodbye"
6.  The assistant will process your command, display your speech and its reply, and speak the reply.


