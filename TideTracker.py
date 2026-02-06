'''
****************************************************************
****************************************************************

                TideTracker for E-Ink Display

                        by Sam Baker

****************************************************************
****************************************************************
'''
import json
import platform
import sys
import time
import zoneinfo

import matplotlib.dates as mdates
import requests
import matplotlib.pyplot as plt
import numpy as np
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))

import waveshare_epd

from waveshare_epd import epd7in5_V2
from PIL import Image, ImageDraw, ImageFont
import logging
import os
from dotenv import load_dotenv

picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images')
icondir = os.path.join(picdir, 'icon')
fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'font')
from datetime import datetime, timezone, timedelta
from scipy.interpolate import make_interp_spline
'''
****************************************************************

Location specific info required

****************************************************************
'''

# # Optional, displayed on top left
# LOCATION = ''
# # NOAA Station Code for tide data
# StationID = #######
#
# # For weather data
# # Create Account on openweathermap.com and get API key



CACHE_FILE = 'stormglass_cache.json'

CACHE_FILE_HOURLY = 'stormglass_hourly_cache.json'

# Optional, displayed on top left
LOCATION = 'Potrero Costa Rica'
CR_TZ = zoneinfo.ZoneInfo("America/Costa_Rica")

LAT = '10.446603'
LONG = '-85.770069'
unit = 'fahrenheit'

WEATHER_API = 'https://api.open-meteo.com/v1/forecast'
ENDPOINT = '?latitude=' + LAT + '&longitude=' + LONG + '&daily=sunrise,sunset,temperature_2m_max,temperature_2m_min,weather_code,temperature_2m_mean&current=is_day,temperature_2m,relative_humidity_2m,weather_code,apparent_temperature,wind_speed_10m,uv_index&timezone=auto&forecast_days=3&temperature_unit=' + unit
TIDE_API = 'https://api.stormglass.io/v2'


weather_codes = {
    0: "Clear Sky",
    1: "Clear Sky",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    54: "Dense Drizzle",
    56: "Freezing Drizzle",
    57: "Freezing Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy rain",
    66: "Freezing Rain",
    67: "Freezing Rain",
    71: "Slight Snow",
    73: "Moderate Snow",
    75: "Heavy Snow",
    77: "Snow Grains",
    80: "Light Rain Shower",
    81: "Moderate Rain Shower",
    82: "Heavy Rain Shower",
    85: "Slight Snow Shower",
    86: "Snow Shower",
    95: "Thunderstorm",
    96: "Thunderstorm",
    99: "Thunderstorm"
}

weather_codes_icons = {
    "Clear Sky 1": "clear_day.png",
    "Clear Sky 0": "clear_night.png",
    "Partly Cloudy 1": "few_clouds_day.png",
    "Partly Cloudy 0": "few_clouds_night.png",
    "Overcast 1": "scattered_clouds_day.png",
    "Overcast 0": "scattered_clouds_night.png",
    "Fog 1": "mist_day.png",
    "Fog 0": "might_night.png",
    "Light Drizzle 1": "rain_day.png",
    "Light Drizzle 0": "rain_night.png",
    "Moderate Drizzle 1": "rain_day.png",
    "Moderate Drizzle 0": "rain_night.png",
    "Dense Drizzle 1": "shower_day.png",
    "Dense Drizzle 0": "shower_night.png",
    "Freezing Drizzle 1": "shower_day.png",
    "Freezing Drizzle 0": "shower_night.png",
    "Slight Rain 1": "rain_day.png",
    "Slight Rain 0": "rain_night.png",
    "Moderate Rain 1": "rain_day.png",
    "Moderate Rain 0": "rain_night.png",
    "Heavy Rain 1": "shower_day.png",
    "Heavy Rain 0": "shower_night.png",
    "Freezing Rain 1": "shower_day.png",
    "Freezing Rain 0": "shower_night.png",
    "Slight Snow 1": "shower_day.png",
    "Slight Snow 0": "shower_night.png",
    "Moderate Snow 1": "shower_day.png",
    "Moderate Snow 0": "shower_night.png",
    "Heavy Snow 1": "shower_day.png",
    "Heavy Snow 0": "shower_night.png",
    "Snow Grains 1": "shower_day.png",
    "Snow Grains 0": "shower_night.png",
    "Light Rain Shower 1": "shower_day.png",
    "Light Rain Shower 0": "shower_night.png",
    "Moderate Rain Shower 1": "shower_day.png",
    "Moderate Rain Shower 0": "shower_night.png",
    "Heavy Rain Shower 1": "shower_day.png",
    "Heavy Rain Shower 0": "shower_night.png",
    "Slight Snow Shower 1": "shower_day.png",
    "Slight Snow Shower 0": "shower_night.png",
    "Snow Shower 1": "shower_day.png",
    "Snow Shower 0": "shower_night.png",
    "Thunderstorm 1": "thunderstorm_day.png",
    "Thunderstorm 0": "thunderstorm_night.png"
}
'''
****************************************************************

Functions and defined variables

****************************************************************
'''

logging.basicConfig(filename='weather_display.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

def is_cache_valid():
    try:
        with open(CACHE_FILE, "r") as f:
            data_cache = json.load(f)
            fetched_at = datetime.fromisoformat(data_cache["fetched_at"])
            fetched_cr = fetched_at.astimezone(CR_TZ)
            today_cr = datetime.now(tz=CR_TZ).date()
            return fetched_cr.date() == today_cr
    except(FileNotFoundError, KeyError, json.JSONDecodeError):
        return False

def is_cache_valid_hourly():
    try:
        with open(CACHE_FILE_HOURLY, "r") as f:
            data_cache = json.load(f)
            times_in_cache = []

            for t in data_cache['data']:
                times_in_cache.append(t['time'])

            times_in_cache = [datetime.fromisoformat(t.replace("Z", "+00:00")) for t in times_in_cache]
            times_in_cache = [t.astimezone(CR_TZ) for t in times_in_cache]

            targets = [
                now.replace(minute=0, second=0, microsecond=0),
                (now + timedelta(hours=24)).replace(minute=0, second=0, microsecond=0),
            ]

            tolerance = timedelta(minutes=10)

            def has_time_near(target, times):
                return any(abs(t - target) <= tolerance for t in times)

            has_now = has_time_near(targets[0], times_in_cache)
            has_24h = has_time_near(targets[1], times_in_cache)
            return has_now and has_24h
    except(FileNotFoundError, KeyError, json.JSONDecodeError):
        return False


# define funciton for writing image and sleeping for specified time
def write_to_screen(image, sleep_seconds):
    print('Writing to screen.')
    logging.info("Write to screen")# for debugging
    # Create new blank image template matching screen resolution
    h_image = Image.new('1', (epd.width, epd.height), 255)
    # Open the template
    screen_output_file = Image.open(os.path.join(picdir, image))
    # Initialize the drawing context with template as background
    h_image.paste(screen_output_file, (0, 0))

    h_image.save("/home/soup222/last_display.png")
    epd.display(epd.getbuffer(h_image))
    # Sleep
    epd.sleep() # Put screen to sleep to prevent damage
    print('Sleeping for ' + str(sleep_seconds) +'.')
    time.sleep(sleep_seconds) # Determines refresh rate on data
    epd.init() # Re-Initialize screen


# define function for displaying error
def display_error(error_source):
    # Display an error
    print('Error in the', error_source, 'request.')
    logging.info("Error in the " + error_source + ' request')
    # Initialize drawing
    error_image = Image.new('1', (epd.width, epd.height), 255)
    # Initialize the drawing
    draw = ImageDraw.Draw(error_image)
    draw.text((100, 150), error_source +' ERROR', font=font50, fill=black)
    draw.text((100, 300), 'Retrying in 30 seconds', font=font22, fill=black)
    current_time = datetime.now().strftime('%H:%M')
    draw.text((300, 365), 'Last Refresh: ' + str(current_time), font = font50, fill=black)
    # Save the error image
    error_image_file = 'error.png'
    error_image.save(os.path.join(picdir, error_image_file))
    # Close error image
    error_image.close()
    # Write error to screen
    write_to_screen(error_image_file, 30)


# define function for getting weather data
def getWeather(URL):
    # Ensure there are no errors with connection
    error_connect = True
    while error_connect:
        try:
            # HTTP request
            print('Attempting to connect to Weather API.')
            logging.info("Attempting to connect to Weather API.")
            response = requests.get(URL)

            if response.status_code == 200:
                print('Connection to Open Weather successful.')
                logging.info("Connection to Weather API successful.")
                # get data in jason format
                data = response.json()
                error_connect = None
                return data

            else:
                print('Connection to Open Weather successful.')
                logging.warning("Connection to Weather API unsuccessful. Status Code: %s.", response.status_code)
                # display_error("HTTP")
                return None
        except requests.exceptions.RequestException as e:
            # Call function to display connection error
            print('Connection error.')
            logging.error("Error connecting: %s", e)
            # display_error('CONNECTION')

def ftoc(f):
    return (f-32) * 5 /9

def utc_to_costa_rica(utc_time_str):
    # Parse ISO 8601 UTC time
    utc_time = datetime.fromisoformat(utc_time_str.replace("Z", "+00:00"))

    # Costa Rica is UTC-6 (no DST)
    costa_rica_tz = timezone(timedelta(hours=-6))

    # Convert time
    costa_rica_time = utc_time.astimezone(costa_rica_tz)
    return costa_rica_time


def getNewTideData():
    error_connect = True
    while error_connect:
        try:
            now_cr = datetime.now(tz=CR_TZ)

            # Start at 12:00 AM today
            start_cr = now_cr.replace(hour=0, minute=0, second=0, microsecond=0)

            # End 3 days later
            end_cr = start_cr + timedelta(days=3) - timedelta(seconds=1)

            now_utc = start_cr.astimezone(zoneinfo.ZoneInfo("UTC"))
            end_utc = end_cr.astimezone(zoneinfo.ZoneInfo("UTC"))

            start_iso = now_utc.isoformat().split("+")[0]
            end_iso = end_utc.isoformat().split("+")[0]
            load_dotenv(dotenv_path="keys.env")  # loads variables from .env

            API_KEY = os.getenv("API_KEY")

            response = requests.get(
                'https://api.stormglass.io/v2/tide/extremes/point',
                params={
                    'lat': LAT,
                    'lng': LONG,
                    'start': start_iso,
                    'end': end_iso,
                },
                headers={
                    'Authorization': API_KEY
                }
            )

            print('Attempting to connect to Stormglass API...')
            logging.info("Attempting to connect to Stormglass API.")


            if response.status_code == 200:
                print('Connection successful.')
                logging.info("Connection to Stormglass API successful.")

                tide_data = response.json()

                tide_data["fetched_at"] = datetime.now(tz=zoneinfo.ZoneInfo("UTC")).isoformat()

                with open(CACHE_FILE, "w") as f:
                    json.dump(tide_data, f)

                error_connect = False
                return tide_data

            else:
                print(f'Connection unsuccessful. Status Code: {response.status_code}')
                logging.warning("Connection unsuccessful. Status Code: %s", response.status_code)
                # display_error("HTTP")
                return None

        except requests.exceptions.RequestException as e:
            print('Connection error. Retrying...')
            logging.error("Error connecting to Stormglass API: %s", e)
            # Optionally, wait a few seconds before retrying
            # display_error('CONNECTION')
            import time
            time.sleep(5)

def getNewHourlyTideData():
    error_connect = True
    while error_connect:
        try:
            now_cr_1 = datetime.now(tz=CR_TZ)

            end_cr_1 = now_cr_1 + timedelta(days=3) - timedelta(seconds=1)

            now_utc_1 = now_cr_1.astimezone(zoneinfo.ZoneInfo("UTC"))
            end_utc_1 = end_cr_1.astimezone(zoneinfo.ZoneInfo("UTC"))

            start_iso_1 = now_utc_1.isoformat().split("+")[0]
            end_iso_1 = end_utc_1.isoformat().split("+")[0]
            load_dotenv(dotenv_path="keys.env")  # loads variables from .env

            API_KEY = os.getenv("API_KEY")

            response_hourly = requests.get(
                'https://api.stormglass.io/v2/tide/sea-level/point',
                params={
                    'lat': LAT,
                    'lng': LONG,
                    'start': start_iso_1,
                    'end': end_iso_1,
                },
                headers={
                    'Authorization': API_KEY
                }
            )

            print('Attempting to connect to Stormglass API for Hourly Tides...')
            logging.info("Attempting to connect to Stormglass API for Hourly Tides.")


            if response_hourly.status_code == 200:
                print('Connection successful.')
                logging.info("Connection to Stormglass API successful.")

                tide_data_hourly = response_hourly.json()

                tide_data_hourly["fetched_at"] = datetime.now(tz=zoneinfo.ZoneInfo("UTC")).isoformat()

                with open(CACHE_FILE_HOURLY, "w") as f:
                    json.dump(tide_data_hourly, f)

                error_connect = False
                return tide_data_hourly

            else:
                print(f'Connection unsuccessful. Status Code: {response_hourly.status_code}')
                logging.warning("Connection unsuccessful. Status Code: %s", response_hourly.status_code)
                # display_error("HTTP")
                return None

        except requests.exceptions.RequestException as e:
            print('Connection error. Retrying...')
            logging.error("Error connecting to Stormglass API: %s", e)
            # Optionally, wait a few seconds before retrying
            # display_error('CONNECTION')
            import time
            time.sleep(5)


def plotTide(tideDataHourly):
    now = datetime.now(CR_TZ)
    start = now.replace(minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=24)

    times = []
    heights = []

    for point in tideDataHourly.get("data", []):
        time_utc = datetime.fromisoformat(point["time"].replace("Z", "+00:00"))
        time_cr = time_utc.astimezone(CR_TZ)

        height = point.get("sg")

        if height is not None and start <= time_cr <= end:
            times.append(time_cr)
            heights.append(height)

    x = mdates.date2num(times)
    y = np.array(heights)

    # Create smooth curve
    x_smooth = np.linspace(x.min(), x.max(), 300)
    spline = make_interp_spline(x, y, k=3)
    y_smooth = spline(x_smooth)

    # Convert back to datetime for plotting
    times_smooth = mdates.num2date(x_smooth)

    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman']

    # Plot
    fig, axs = plt.subplots(figsize=(10, 4))
    axs.fill_between(times_smooth, y_smooth, color='black', alpha=1.0)

    # Titles and labels
    axs.set_title('Tide - Next 24 Hours', fontsize=20, color='black')
    axs.set_ylabel('Water Level (m)', fontsize=14, color='black')

    # X-axis ticks (8 ticks across)
    tick_times = times[::max(1, len(times)//8)]
    axs.set_xticks(tick_times)

    # Custom labels: add date under midnight
    labels = []
    prev_day = None
    for t in tick_times:
        current_day = t.date()
        if prev_day is None or current_day != prev_day:
            # New day → show time + date
            labels.append(t.strftime('%H:%M\n%b %d'))  # e.g. 00:00\nFeb 03
        else:
            # Same day → just show time
            labels.append(t.strftime('%H:%M'))
        prev_day = current_day

    axs.set_xticklabels(labels, fontsize=18)

    # Y-axis increments of 0.5
    ymin = (min(heights) // 0.5) * 0.5
    ymax = (max(heights) // 0.5 + 1) * 0.5
    axs.set_yticks(np.arange(ymin, ymax + 0.5, 0.5))
    axs.tick_params(axis='y', labelsize=18, colors='black')
    axs.tick_params(axis='x', labelsize=18, colors='black')


    # Styling
    axs.grid(False)

    times = sorted(times)
    if times[0] <= now <= times[-1]:
        axs.axvline(
            now,
            color='grey',
            linestyle='--',
            linewidth=2,
            alpha=0.9,
            zorder=10        )
    plt.tight_layout()
    plt.savefig('images/TideLevel2.png', dpi=60)
    plt.show()
# now_cr = datetime.now(tz=CR_TZ)
    # end_cr = now_cr + timedelta(hours=24)

    # # Adjust data for negative values
    # times = []
    # heights = []
    #
    # now_cr = datetime.now(tz=CR_TZ)
    # end_cr = now_cr + timedelta(hours=24)
    #
    # for p in tideData.get("data", []):
    #     time_utc = datetime.fromisoformat(p["time"])
    #     time_cr = time_utc.astimezone(CR_TZ)
    #
    #     if now_cr <= time_cr <= end_cr:
    #         height = p["height"]
    #         if heights is not None:
    #             times.append(time_cr)
    #             heights.append(height)
    #
    # # Create Plot
    # fig, axs = plt.subplots(figsize=(12, 4))
    #
    #
    # TideData['water_level'].plot.area(ax=axs, color='black')
    # plt.title('Tide - Next 24 Hours', fontsize=20)
    #fontweight="bold",
    #axs.xaxis.set_tick_params(labelsize=20)
    #axs.yaxis.set_tick_params(labelsize=20)
    #plt.show()

# Set the font sizes
font15 = ImageFont.truetype(os.path.join(fontdir, 'Times New Roman.ttf'), 15)
font20 = ImageFont.truetype(os.path.join(fontdir, 'Times New Roman.ttf'), 20)
font22 = ImageFont.truetype(os.path.join(fontdir, 'Times New Roman.ttf'), 22)
font30 = ImageFont.truetype(os.path.join(fontdir, 'Times New Roman.ttf'), 30)
font35 = ImageFont.truetype(os.path.join(fontdir, 'Times New Roman.ttf'), 35)
font50 = ImageFont.truetype(os.path.join(fontdir, 'Times New Roman.ttf'), 50)
font60 = ImageFont.truetype(os.path.join(fontdir, 'Times New Roman.ttf'), 60)
font100 = ImageFont.truetype(os.path.join(fontdir, 'Times New Roman.ttf'), 100)
font160 = ImageFont.truetype(os.path.join(fontdir, 'Times New Roman.ttf'), 160)

# Set the colors
black = 'rgb(0,0,0)'
white = 'rgb(255,255,255)'
grey = 'rgb(235,235,235)'


'''
****************************************************************

Main Loop

****************************************************************
'''

#Initialize and clear screen
print('Initializing and clearing screen.')
epd = epd7in5_V2.EPD() # Create object for display functions
epd.init()
epd.Clear()

while True:
    # Get weather data
    data = getWeather(WEATHER_API + ENDPOINT)



    # Current Weather
    current = data['current']
    tempCurrent_f = current['temperature_2m']
    feels_like_f = current['apparent_temperature']
    tempCurrent_c = ftoc(tempCurrent_f)
    feels_like_c = ftoc(feels_like_f)
    humidity = current['relative_humidity_2m']
    weather = current['weather_code']
    report = weather_codes.get(weather)

    isDay = str (current['is_day'])
    icon_today = weather_codes_icons.get(report + " " + isDay)
    uvIndex = current['uv_index']

    # Daily Weather
    daily = data['daily']

    daily_temp_today_f = daily['temperature_2m_mean'][0]
    daily_temp_tmr_f = daily['temperature_2m_mean'][1]
    daily_temp_two_days_f = daily['temperature_2m_mean'][2]

    temp_max_today_f = daily['temperature_2m_max'][0]
    temp_max_tmr_f = daily['temperature_2m_max'][1]
    temp_max_two_days_f = daily['temperature_2m_max'][2]

    temp_min_today_f = daily['temperature_2m_min'][0]
    temp_min_tmr_f = daily['temperature_2m_min'][1]
    temp_min_two_days_f = daily['temperature_2m_min'][2]

    daily_temp_today_c = ftoc(daily_temp_today_f)
    daily_temp_tmr_c = ftoc(daily_temp_tmr_f)
    daily_temp_two_days_c = ftoc(daily_temp_two_days_f)

    temp_max_today_c = ftoc(temp_max_today_f)
    temp_max_tmr_c = ftoc(temp_max_tmr_f)
    temp_max_two_days_c = ftoc(temp_max_two_days_f)

    temp_min_today_c = ftoc(temp_min_today_f)
    temp_min_tmr_c = ftoc(temp_min_tmr_f)
    temp_min_two_days_c = ftoc(temp_min_tmr_f)

    weather_code_today = daily['weather_code'][0]
    weather_code_tmr = daily['weather_code'][1]
    weather_code_two_days = daily['weather_code'][2]

    sunrise_today = daily['sunrise'][0]
    sunrise_tmr = daily['sunrise'][1]
    sunrise_tmr_tmr = daily['sunrise'][2]

    sunset_today = daily['sunset'][0]
    sunset_tmr = daily['sunset'][1]
    sunset_tmr_tmr = daily['sunset'][2]

    # Set strings to be printed to screen
    string_location = LOCATION
    string_temp_current = format(tempCurrent_f, '.0f') + u'\N{DEGREE SIGN}F / ' +  format(tempCurrent_c, '.0f') + u'\N{DEGREE SIGN}C'

    string_feels_like = 'Feels like: ' + format(feels_like_f, '.0f') +  u'\N{DEGREE SIGN}F / ' + format(feels_like_c, '.0f') +  u'\N{DEGREE SIGN}C'
    string_humidity = 'Humidity: ' + str(humidity) + '%'
    string_uv_index = 'UV Index: ' + str(uvIndex)

    string_report = report
    string_temp_max = format(temp_max_today_f, '>.0f') + u'\N{DEGREE SIGN}F / ' + format(temp_max_today_c, '>.0f') + u'\N{DEGREE SIGN}C'
    string_temp_min = format(temp_min_today_f, '>.0f') + u'\N{DEGREE SIGN}F / ' + format(temp_min_today_c, '>.0f') + u'\N{DEGREE SIGN}C'

    sunrise_today_string = 'Sunrise: ' + sunrise_today.split("T")[1]
    sunset_today_string = 'Sunset: ' + sunset_today.split("T")[1]

    sunrise_tmr_string = 'Sunrise: ' + sunrise_tmr.split("T")[1]
    sunset_tmr_string = 'Sunset: ' + sunset_tmr.split("T")[1]

    sunrise_tmr_tmr_string = 'Sunrise: ' + sunrise_tmr_tmr.split("T")[1]
    sunset_tmr_tmr_string = 'Sunset: ' + sunset_tmr_tmr.split("T")[1]


    # Tomorrow Forcast Strings
    tmr_high = format(temp_max_tmr_f, '>.0f') + u'\N{DEGREE SIGN}F / ' + format(temp_max_tmr_c, '>.0f') + u'\N{DEGREE SIGN}C'
    tmr_low = format(temp_min_tmr_f, '>.0f') + u'\N{DEGREE SIGN}F / ' + format(temp_min_tmr_c, '>.0f') + u'\N{DEGREE SIGN}C'
    nx_weather = weather_codes.get(weather_code_tmr)
    nx_icon = weather_codes_icons.get(nx_weather + " 1")

    # Two Day Forcast Strings
    two_day_high = 'High:\n' + format(temp_max_two_days_f, '>.0f') + u'\N{DEGREE SIGN}F / ' + format(temp_max_two_days_c, '>.0f') + u'\N{DEGREE SIGN}C'
    two_day_low = 'Low: \n' + format(temp_min_two_days_f, '>.0f') + u'\N{DEGREE SIGN}F / ' + format(temp_min_two_days_c, '>.0f') + u'\N{DEGREE SIGN}C'
    nx_nx_weather = weather_codes.get(weather_code_two_days)
    nx_nx_icon = weather_codes_icons.get(nx_nx_weather + " 1")

    # print(LOCATION)
    # print(string_temp_current)
    # print(string_feels_like)
    # print(string_humidity)
    # print(string_uv_index)
    # print(string_report)
    # print(string_temp_max)
    # print(string_temp_min)
    # print(icon_today)
    # print(sunrise_today_string)
    # print(sunset_today_string)
    #
    # print(tmr_high)
    # print(tmr_low)
    # print(nx_weather)
    # print(nx_icon)
    # print(sunrise_tmr_string)
    # print(sunset_tmr_string)
    #
    # print(two_day_high)
    # print(two_day_low)
    # print(nx_nx_weather)
    # print(nx_nx_icon)
    # print(sunrise_tmr_tmr_string)
    # print(sunset_tmr_tmr_string)

    # Last updated time
    # Costa Rica timezone
    cr_tz = zoneinfo.ZoneInfo("America/Costa_Rica")

    # Current local time in Costa Rica
    now = datetime.now(tz=cr_tz)
    current_time = now.strftime("%H:%M")
    last_update_string = 'Last Updated: ' + current_time

    if is_cache_valid():
        with open(CACHE_FILE, "r") as f:
            storm_data = json.load(f)
        print("Loaded High/Low Tide data from cache.")
        logging.info("Loaded High/Low Tide data from cache")
    else:
        storm_data = getNewTideData()
        print("Fetched new data from Stormglass API for High/Low Tides.")
        logging.info("Calling Stormglass API for High/Low Tides")



    if is_cache_valid_hourly():
        with open(CACHE_FILE_HOURLY, "r") as f:
            hourly_tides = json.load(f)
        print("Loaded Hourly Tide data from cache.")
        logging.info("Loaded Hourly Tide data from cache")
    else:
        hourly_tides = getNewHourlyTideData()
        print("Fetched new data from Stormglass API for Hourly Tides.")
        logging.info("Calling Stormglass API for Hourly Tides")


    for tide in storm_data.get("data", []):
        # Original time from API is in UTC
        time_utc = datetime.fromisoformat(tide["time"])
        time_cr = time_utc.astimezone(CR_TZ)

        # Add back to dict for convenience
        tide["time_cr"] = time_cr

    now_cr = datetime.now(tz=CR_TZ)
    start_cr = now_cr.replace(hour=0, minute=0, second=0, microsecond=0)

    today = start_cr.date()

    today_tides = [t for t in storm_data["data"] if t["time_cr"].date() == today]

    today_tides_strings = []

    # print(f"High and Low Tides:")
    for t in today_tides:
        today_tides_strings.append(f"{t['type'].capitalize()}: {t['time_cr'].strftime('%H:%M')}")

    # for t in today_tides_strings:
    #     print(t)


    plotTide(hourly_tides)

    template = Image.open(os.path.join(picdir, 'template.png'))
    # Initialize the drawing context with template as background
    draw = ImageDraw.Draw(template)

    # # Current weather
    ## Open icon file
    icon_image = Image.open(os.path.join(icondir, icon_today))
    icon_image = icon_image.resize((130,130))
    # template.paste(icon_image, (64, 80))
    #



    casa_box_left = 5
    casa_box_width = 280

    icon_x = casa_box_left + (casa_box_width - icon_image.width) // 2
    # print(icon_x)
    template.paste(icon_image, (icon_x, 70))

    text_box_temp = draw.textbbox((0,0), text="Casa Agave", font=font35)
    text_width = text_box_temp[2]-text_box_temp[0]
    text_x = casa_box_left + (casa_box_width-text_width) / 2
    draw.text((text_x,10), "Casa Agave", font=font35, fill=black)

    text_box_temp = draw.textbbox((0,0), text="Playa Potrero, Costa Rica", font=font22)
    text_width = text_box_temp[2]-text_box_temp[0]
    text_x = casa_box_left + (casa_box_width-text_width) / 2
    draw.text((text_x,55), "Playa Potrero, Costa Rica", font=font22, fill=black)

    text_box_temp = draw.textbbox((0,0), text=string_temp_current, font=font30)
    text_width = text_box_temp[2]-text_box_temp[0]
    text_x = casa_box_left + (casa_box_width-text_width) / 2
    draw.text((text_x,185), string_temp_current, font=font30, fill=black)


    # y = 65
    # draw.text((350,y), string_feels_like, font=font20, fill=black)
    # draw.text((350,y+25), string_uv_index, font=font20, fill=black)
    # draw.text((350,y+50), string_temp_max, font=font20, fill=black)
    # draw.text((350,y+75), string_temp_min, font=font20, fill=black)



    today_box_left = 296
    today_box_width = 248

    day_of_week = now_cr.strftime('%A')

    if platform.system() == 'Windows':
        day_format = '%#d'
    else:
        day_format = "%-d"

    date_now = now_cr.strftime(f'%b {day_format}')
    tomorrow_cr = now_cr + timedelta(days=1)

    day_of_week_tmr = tomorrow_cr.strftime('%A')
    date_tmr = tomorrow_cr.strftime(f'%b {day_format}')


    text_box_temp = draw.textbbox((0,0), text='Today', font=font30)
    text_width = text_box_temp[2]-text_box_temp[0]
    text_x_3 = today_box_left + (today_box_width-text_width) / 2
    draw.text((text_x_3,25), 'Today', font=font30, fill=black)


    text_box_temp = draw.textbbox((0,0), text=day_of_week + ", " + date_now, font=font15)
    text_width = text_box_temp[2]-text_box_temp[0]
    text_x_3 = today_box_left + (today_box_width-text_width) / 2
    draw.text((text_x_3,60), day_of_week + ", " + date_now, font=font15, fill=black)

    y=115
    text_box_temp = draw.textbbox((0,0), text=string_feels_like, font=font20)
    text_width = text_box_temp[2]-text_box_temp[0]
    text_x_3 = today_box_left + (today_box_width-text_width) / 2
    draw.text((text_x_3,y), string_feels_like, font=font20, fill=black)

    text_box_temp = draw.textbbox((0,0), text=string_uv_index, font=font20)
    text_width = text_box_temp[2]-text_box_temp[0]
    text_x_3 = today_box_left + (today_box_width-text_width) / 2
    draw.text((text_x_3,y+25), string_uv_index, font=font20, fill=black)


    text_box_temp = draw.textbbox((0,0), text=sunrise_today_string, font=font20)
    text_width = text_box_temp[2]-text_box_temp[0]
    text_x_3 = today_box_left + (today_box_width-text_width) / 2
    draw.text((text_x_3,180), sunrise_today_string, font=font20, fill=black)

    text_box_temp = draw.textbbox((0,0), text=sunset_today_string, font=font20)
    text_width = text_box_temp[2]-text_box_temp[0]
    text_x_3 = today_box_left + (today_box_width-text_width) / 2
    draw.text((text_x_3,210), sunset_today_string, font=font20, fill=black)


    # draw.text((450,84), string_temp_max, font=font15, fill=black)
    # draw.text((320,84), string_temp_min, font=font15, fill=black)

    tmr_box_left = 554
    tmr_box_width = 238

    text_box_temp = draw.textbbox((0,0), text=day_of_week_tmr + ", " + date_tmr, font=font15)
    text_width = text_box_temp[2]-text_box_temp[0]
    text_x_2 = tmr_box_left + (tmr_box_width-text_width) / 2
    draw.text((text_x_2,60), day_of_week_tmr + ", " + date_tmr, font=font15, fill=black)


    icon_image_tmr = Image.open(os.path.join(icondir, nx_icon))
    icon_image = icon_image_tmr.resize((130,130))
    icon_x_tmr = tmr_box_left + (tmr_box_width - icon_image.width) // 2
    # print(icon_x_tmr)

    template.paste(icon_image, (icon_x_tmr, 70))


    text_box_temp = draw.textbbox((0,0), text='Tomorrow', font=font30)
    text_width = text_box_temp[2]-text_box_temp[0]
    text_x_2 = tmr_box_left + (tmr_box_width-text_width) / 2
    draw.text((text_x_2,25), 'Tomorrow', font=font30, fill=black)
    # draw.text((700,100), "High:", font=font20, fill=black)
    # draw.text((560,100), "Low:", font=font20, fill=black)
    # draw.text((700,120), tmr_high, font=font20, fill=black)
    # draw.text((560,120), tmr_low, font=font20, fill=black)


    draw.text((700,84), tmr_high, font=font15, fill=black)
    draw.text((575,84), tmr_low, font=font15, fill=black)

    text_box_temp = draw.textbbox((0,0), text=sunset_tmr_string, font=font20)
    text_width = text_box_temp[2]-text_box_temp[0]
    text_x_2 = tmr_box_left + (tmr_box_width-text_width) / 2
    draw.text((text_x_2,180), sunrise_tmr_string, font=font20, fill=black)

    text_box_temp = draw.textbbox((0,0), text=sunset_tmr_string, font=font20)
    text_width = text_box_temp[2]-text_box_temp[0]
    text_x_2 = tmr_box_left + (tmr_box_width-text_width) / 2
    draw.text((text_x_2,210), sunset_tmr_string, font=font20, fill=black)
    #
    #
    #
    # ## Dividing lines
    draw.line((550,10,550,220), fill='black', width=3)

    draw.line((295,10,295,220), fill='black', width=3)
    #
    #
    # # Tide Info
    # # Graph
    tidegraph = Image.open('images/TideLevel2.png')
    # tidegraph = tidegraph.resize((520, 225))
    template.paste(tidegraph, (190, 240))
    #
    # Large horizontal dividing line
    h = 240
    draw.line((25, h, 775, h), fill='black', width=3)


    draw.text((35,260), "Today's Tide", font=font30, fill=black)

    y_loc = 325


    for t in today_tides_strings:
        draw.text((60,y_loc), t, font=font22, fill=black)
        y_loc += 25 # This bumps the next prediction down a line


    current_time = now_cr.strftime("%H:%M")
    last_update_string = 'Last Updated: ' + current_time
    draw.text((20,462), last_update_string, font=font30, fill=black)

# # Save the image for display as PNG
    screen_output_file = os.path.join(picdir, 'screen_output2.png')
    template.save(screen_output_file)
    # Close the template file
    template.close()
    #
    write_to_screen(screen_output_file, 600)
    epd.Clear()
