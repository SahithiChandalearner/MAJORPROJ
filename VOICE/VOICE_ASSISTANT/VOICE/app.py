from flask import Flask, request, jsonify, render_template
import datetime
import wikipedia
import pyjokes
import os
import random
import webbrowser
import pyautogui
import requests
import psutil

app = Flask(__name__)

# Global list to store command history and reminders
command_history = []
reminders = []

def process_query(query):
    """
    Process the spoken query and return a text response.
    Supported commands:
      - time: returns the current time.
      - date: returns the current date.
      - wishes: returns a greeting.
      - screenshot: takes a screenshot.
      - set a new name for the assistant.
      - play music: plays a random song from your Music directory.
      - search from wikipedia: "wikipedia" or "tell me about ..."
      - opens YouTube: "open youtube"
      - opens Google: "open google"
      - tells jokes: "joke"
      - shutdown: "shutdown"
      - restart: "restart"
      - calculator: calculates arithmetic expressions.
      - system volume: "volume up", "volume down", "mute"
      - weather information: "weather in <city>"
      - system info: "system info"
      - set reminder: "set reminder to <reminder>"
      - find file: "find file <filename>"
      - offline: "offline" or "exit"
    """
    query_lower = query.lower()

    # Load assistant name from file (default: "SIRI")
    assistant_name = "SIRI"
    try:
        with open("assistant_name.txt", "r") as f:
            assistant_name = f.read().strip() or "SIRI"
    except Exception:
        pass

    # TIME
    if "time" in query_lower:
        current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
        return f"The current time is {current_time}."

    # DATE
    elif "date" in query_lower:
        now = datetime.datetime.now()
        return f"The current date is {now.day}/{now.month}/{now.year}."

    # WISHES / GREETINGS
    elif "wish" in query_lower or "greet" in query_lower:
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            greeting = "Good morning, sir!"
        elif 12 <= hour < 17:
            greeting = "Good afternoon, sir!"
        elif 17 <= hour < 21:
            greeting = "Good evening, sir!"
        else:
            greeting = "Good night, sir!"
        return greeting

    # SCREENSHOT
    elif "screenshot" in query_lower:
        screenshot_dir = "screenshots"
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
        filename = os.path.join(
            screenshot_dir,
            "screenshot_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
        )
        try:
            # Make sure you have Pillow installed: pip install pillow
            img = pyautogui.screenshot()
            img.save(filename)
            return f"Screenshot saved as {filename}."
        except Exception as e:
            return f"Failed to take screenshot. Error: {e}"

    # SET A NEW NAME FOR THE ASSISTANT
    elif "set your name to" in query_lower or "change your name to" in query_lower:
        if "set your name to" in query_lower:
            new_name = query_lower.split("set your name to")[-1].strip()
        else:
            new_name = query_lower.split("change your name to")[-1].strip()
        try:
            with open("assistant_name.txt", "w") as f:
                f.write(new_name)
            return f"Alright, I will be called {new_name} from now on."
        except Exception:
            return "Unable to set the new name."

    # PLAY MUSIC
    elif "play music" in query_lower:
        music_dir = os.path.expanduser("~/Music")
        try:
            songs = os.listdir(music_dir)
            if songs:
                song = random.choice(songs)
                # os.startfile works on Windows. Adjust for other OS if needed.
                os.startfile(os.path.join(music_dir, song))
                return f"Playing {song}."
            else:
                return "No songs found in your music directory."
        except Exception as e:
            return f"Unable to play music. Error: {e}"

    # OPEN YOUTUBE
    elif "open youtube" in query_lower:
        try:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube."
        except Exception:
            return "Failed to open YouTube."

    # OPEN GOOGLE
    elif "open google" in query_lower:
        try:
            webbrowser.open("https://www.google.com")
            return "Opening Google."
        except Exception:
            return "Failed to open Google."

    # WIKIPEDIA SEARCH (handles "wikipedia" or "tell me about")
    elif "wikipedia" in query_lower or "tell me about" in query_lower:
        if "wikipedia" in query_lower:
            topic = query_lower.replace("wikipedia", "").strip()
        else:
            topic = query_lower.replace("tell me about", "").strip()
        if topic:
            try:
                summary = wikipedia.summary(topic, sentences=2)
                return summary
            except wikipedia.exceptions.DisambiguationError:
                return "Multiple results found. Please be more specific."
            except Exception:
                return "I couldn't find anything on Wikipedia."
        else:
            return "Please specify a topic to search on Wikipedia."

    # TELL A JOKE
    elif "joke" in query_lower:
        return pyjokes.get_joke()

    # SHUTDOWN
    elif "shutdown" in query_lower:
        try:
            os.system("shutdown /s /f /t 1")
            return "Shutting down the system."
        except Exception:
            return "Failed to shut down the system."

    # RESTART
    elif "restart" in query_lower:
        try:
            os.system("shutdown /r /f /t 1")
            return "Restarting the system."
        except Exception:
            return "Failed to restart the system."

    # CALCULATOR
    elif "calculate" in query_lower or "calculator" in query_lower:
        if "calculate" in query_lower:
            expr = query_lower.split("calculate", 1)[1].strip()
        else:
            expr = query_lower.split("calculator", 1)[1].strip()
        # Replace common words with symbols
        replacements = {
            "plus": "+",
            "minus": "-",
            "times": "*",
            "multiplied by": "*",
            "divided by": "/"
        }
        for word, symbol in replacements.items():
            expr = expr.replace(word, symbol)
        # Remove any remaining spaces so that "2 + 2" becomes "2+2"
        expr = expr.replace(" ", "")
        try:
            result = eval(expr)
            return f"The result is {result}."
        except Exception as e:
            return f"I couldn't perform the calculation. Error: {e}"

    # WEATHER INFORMATION
    elif "weather" in query_lower:
        # Expecting a command like "weather in <city>"
        if "in" in query_lower:
            city = query_lower.split("in")[-1].strip()
            api_key = os.environ.get("OPENWEATHER_API_KEY")
            if not api_key:
                return "Weather API key not configured."
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
                response = requests.get(url)
                data = response.json()
                if data.get("cod") != 200:
                    return f"City {city} not found."
                weather_desc = data["weather"][0]["description"]
                temp = data["main"]["temp"]
                return f"The weather in {city} is {weather_desc} with a temperature of {temp}°C."
            except Exception as e:
                return f"Failed to get weather information. Error: {e}"
        else:
            return "Please specify a city for weather information."

    # SYSTEM INFORMATION
    elif "system info" in query_lower:
        try:
            cpu = psutil.cpu_percent(interval=1)
            battery = psutil.sensors_battery()
            if battery:
                bat = battery.percent
                return f"CPU usage is {cpu}% and battery level is {bat}%."
            else:
                return f"CPU usage is {cpu}%. Battery information is not available."
        except Exception as e:
            return f"Failed to get system info. Error: {e}"

    # SET REMINDER
    elif "set reminder to" in query_lower:
        reminder_text = query_lower.split("set reminder to", 1)[1].strip()
        reminders.append(reminder_text)
        return f"Reminder set: {reminder_text}"

    # FIND FILE
    elif "find file" in query_lower:
        filename = query_lower.split("find file", 1)[1].strip()
        search_dir = os.path.expanduser("~")
        found_files = []
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if filename.lower() in file.lower():
                    found_files.append(os.path.join(root, file))
        if found_files:
            return "Found files: " + ", ".join(found_files[:3])
        else:
            return "No files found matching that name."

    # SYSTEM VOLUME CONTROLS
    elif "volume up" in query_lower:
        try:
            pyautogui.press("volumeup")
            return "Increasing volume."
        except Exception:
            return "Failed to increase volume."
    elif "volume down" in query_lower:
        try:
            pyautogui.press("volumedown")
            return "Decreasing volume."
        except Exception:
            return "Failed to decrease volume."
    elif "mute" in query_lower:
        try:
            pyautogui.press("volumemute")
            return "Muting volume."
        except Exception:
            return "Failed to mute volume."

    # OFFLINE
    elif "offline" in query_lower or "exit" in query_lower:
        return "Going offline. Have a good day!"

    # DEFAULT RESPONSE
    else:
        return "I did not understand the command."

@app.route("/")
def index():
    # On opening the interface, provide a welcome greeting.
    default_greeting = "Welcome back, sir!"
    return render_template("index.html", greeting=default_greeting)

@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    query = data.get("query", "")
    if query:
        result = process_query(query)
        # Save the command and response to history
        command_history.append({"query": query, "result": result})
        return jsonify({"query": query, "result": result})
    else:
        return jsonify({"error": "No query provided"}), 400

@app.route("/history", methods=["GET"])
def history():
    return jsonify(command_history)

@app.route("/reminders", methods=["GET"])
def get_reminders():
    return jsonify(reminders)

if __name__ == "__main__":
    app.run(debug=True)
