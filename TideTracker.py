'''
****************************************************************
****************************************************************

                TideTracker for E-Ink Display

                        by Sam Baker

****************************************************************
****************************************************************
'''

import sys
import os
import time
import traceback
import requests
from io import BytesIO
import noaa_coops as nc
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt

sys.path.append('lib')
# from waveshare_epd import epd7in5_V2
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import logging
import urllib3

picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images')
icondir = os.path.join(picdir, 'icon')
fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'font')
from datetime import datetime, timezone, timedelta
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
API_KEY = ''
# # Get LATITUDE and LONGITUDE of location
# LATITUDE = 'XX.XXXXXX'
# LONGITUDE = '-XX.XXXXXX'
# UNITS = 'imperial'
#
# # Create URL for API call
# BASE_URL = 'http://api.openweathermap.org/data/2.5/onecall?'
# URL = BASE_URL + 'lat=' + LATITUDE + '&lon=' + LONGITUDE + '&units=' + UNITS +'&appid=' + API_KEY


# Optional, displayed on top left
LOCATION = 'Potrero Costa Rica'

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
                    level=logging.CRITICAL,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


# define funciton for writing image and sleeping for specified time
# def write_to_screen(image, sleep_seconds):
#     print('Writing to screen.') # for debugging
#     # Create new blank image template matching screen resolution
#     h_image = Image.new('1', (epd.width, epd.height), 255)
#     # Open the template
#     screen_output_file = Image.open(os.path.join(picdir, image))
#     # Initialize the drawing context with template as background
#     h_image.paste(screen_output_file, (0, 0))
#
#     h_image.save("/home/pi/last_display.png")
#     epd.display(epd.getbuffer(h_image))
#     # Sleep
#     epd.sleep() # Put screen to sleep to prevent damage
#     print('Sleeping for ' + str(sleep_seconds) +'.')
#     time.sleep(sleep_seconds) # Determines refresh rate on data
#     epd.init() # Re-Initialize screen


# define function for displaying error
# def display_error(error_source):
#     # Display an error
#     print('Error in the', error_source, 'request.')
#     # Initialize drawing
#     error_image = Image.new('1', (epd.width, epd.height), 255)
#     # Initialize the drawing
#     draw = ImageDraw.Draw(error_image)
#     draw.text((100, 150), error_source +' ERROR', font=font50, fill=black)
#     draw.text((100, 300), 'Retrying in 30 seconds', font=font22, fill=black)
#     current_time = datetime.now().strftime('%H:%M')
#     draw.text((300, 365), 'Last Refresh: ' + str(current_time), font = font50, fill=black)
#     # Save the error image
#     error_image_file = 'error.png'
#     error_image.save(os.path.join(picdir, error_image_file))
#     # Close error image
#     error_image.close()
#     # Write error to screen
#     write_to_screen(error_image_file, 30)


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

# last 24 hour data, add argument for start/end_date
def past24(StationID):
    # Create Station Object
    stationdata = nc.Station(StationID)

    # Get today date string
    today = dt.datetime.now()
    todaystr = today.strftime("%Y%m%d %H:%M")
    # Get yesterday date string
    yesterday = today - dt.timedelta(days=1)
    yesterdaystr = yesterday.strftime("%Y%m%d %H:%M")

    # Get water level data
    WaterLevel = stationdata.get_data(
        begin_date=yesterdaystr,
        end_date=todaystr,
        product="water_level",
        datum="MLLW",
        time_zone="lst_ldt")

    return WaterLevel


# Plot last 24 hours of tide
def plotTide(TideData):
    # Adjust data for negative values
    minlevel = TideData['water_level'].min()
    TideData['water_level'] = TideData['water_level'] - minlevel

    # Create Plot
    fig, axs = plt.subplots(figsize=(12, 4))
    TideData['water_level'].plot.area(ax=axs, color='black')
    plt.title('Tide- Past 24 Hours', fontsize=20)
    #fontweight="bold",
    #axs.xaxis.set_tick_params(labelsize=20)
    #axs.yaxis.set_tick_params(labelsize=20)
    plt.savefig('images/TideLevel.png', dpi=60)
    #plt.show()


# Get High and Low tide info
def HiLo(StationID):
    # Create Station Object
    stationdata = nc.Station(StationID)

    # Get today date string
    today = dt.datetime.now()
    todaystr = today.strftime("%Y%m%d")
    # Get yesterday date string
    tomorrow = today + dt.timedelta(days=1)
    tomorrowstr = tomorrow.strftime("%Y%m%d")

    # Get Hi and Lo Tide info
    TideHiLo = stationdata.get_data(
        begin_date=todaystr,
        end_date=tomorrowstr,
        product="predictions",
        datum="MLLW",
        interval="hilo",
        time_zone="lst_ldt")

    return TideHiLo


# Set the font sizes
font15 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 15)
font20 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 20)
font22 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 22)
font30 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 30)
font35 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 35)
font50 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 50)
font60 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 60)
font100 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 100)
font160 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 160)

# Set the colors
black = 'rgb(0,0,0)'
white = 'rgb(255,255,255)'
grey = 'rgb(235,235,235)'


'''
****************************************************************

Main Loop

****************************************************************
'''

# Initialize and clear screen
# print('Initializing and clearing screen.')
# epd = epd7in5_V2.EPD() # Create object for display functions
# epd.init()
# epd.Clear()

while True:
    # Get weather data
    data = getWeather(WEATHER_API + ENDPOINT)



    # # get current dict block
    current = data['current']
    # # get current
    tempCurrent_f = current['temperature_2m']
    # # get feels like
    feels_like_f = current['apparent_temperature']

    tempCurrent_c = ftoc(tempCurrent_f)
 # get feels like
    feels_like_c = ftoc(feels_like_f)

    # # get humidity
    humidity = current['relative_humidity_2m']
    # # get pressure
    # wind = current['wind_speed']
    # # get description
    weather = current['weather_code']
    report = weather_codes.get(weather)

    isDay = str (current['is_day'])

    icon_today = weather_codes_icons.get(report + " " + isDay)

    uvIndex = current['uv_index']

    # # get daily dict block
    daily = data['daily']
    # # get daily precip
    # daily_precip_float = daily[0]['pop']
    # #format daily precip
    # daily_precip_percent = daily_precip_float * 100
    # # get min and max temp
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
    string_temp_max = 'High: ' + format(temp_max_today_f, '>.0f') + u'\N{DEGREE SIGN}F / ' + format(temp_max_today_c, '>.0f') + u'\N{DEGREE SIGN}C'
    string_temp_min = 'Low:  ' + format(temp_min_today_f, '>.0f') + u'\N{DEGREE SIGN}F / ' + format(temp_min_today_c, '>.0f') + u'\N{DEGREE SIGN}C'

    sunrise_today_string = 'Sunrise: ' + sunrise_today.split("T")[1]
    sunset_today_string = 'Sunset: ' + sunset_today.split("T")[1]

    sunrise_tmr_string = 'Sunrise: ' + sunrise_tmr.split("T")[1]
    sunset_tmr_string = 'Sunset: ' + sunset_tmr.split("T")[1]

    sunrise_tmr_tmr_string = 'Sunrise: ' + sunrise_tmr_tmr.split("T")[1]
    sunset_tmr_tmr_string = 'Sunset: ' + sunset_tmr_tmr.split("T")[1]


    # Tomorrow Forcast Strings
    tmr_high = 'High: ' + format(temp_max_tmr_f, '>.0f') + u'\N{DEGREE SIGN}F / ' + format(temp_max_tmr_c, '>.0f') + u'\N{DEGREE SIGN}C'
    tmr_low = 'Low:  ' + format(temp_min_tmr_f, '>.0f') + u'\N{DEGREE SIGN}F / ' + format(temp_min_tmr_c, '>.0f') + u'\N{DEGREE SIGN}C'
    nx_weather = weather_codes.get(weather_code_tmr)
    nx_icon = weather_codes_icons.get(nx_weather + " 1")

    # Two Day Forcast Strings
    two_day_high = 'High: ' + format(temp_max_two_days_f, '>.0f') + u'\N{DEGREE SIGN}F / ' + format(temp_max_two_days_c, '>.0f') + u'\N{DEGREE SIGN}C'
    two_day_low = 'Low:  ' + format(temp_min_two_days_f, '>.0f') + u'\N{DEGREE SIGN}F / ' + format(temp_min_two_days_c, '>.0f') + u'\N{DEGREE SIGN}C'
    nx_nx_weather = weather_codes.get(weather_code_two_days)
    nx_nx_icon = weather_codes_icons.get(nx_nx_weather + " 1")

    print(LOCATION)
    print(string_temp_current)
    print(string_feels_like)
    print(string_humidity)
    print(string_uv_index)
    print(string_report)
    print(string_temp_max)
    print(string_temp_min)
    print(icon_today)
    print(sunrise_today_string)
    print(sunset_today_string)

    print(tmr_high)
    print(tmr_low)
    print(nx_weather)
    print(nx_icon)
    print(sunrise_tmr_string)
    print(sunset_tmr_string)

    print(two_day_high)
    print(two_day_low)
    print(nx_nx_weather)
    print(nx_nx_icon)
    print(sunrise_tmr_tmr_string)
    print(sunset_tmr_tmr_string)

    # Last updated time
    now = dt.datetime.now()
    current_time = now.strftime("%H:%M")
    last_update_string = 'Last Updated: ' + current_time

    # Tide Data
    # Get water level
    # wl_error = True
    # while wl_error == True:
    #     try:
    #         WaterLevel = past24(StationID)
    #         wl_error = False
    #     except:
    #         display_error('Tide Data')
    #
    # plotTide(WaterLevel)
    #
    #
    # # Open template file
    # template = Image.open(os.path.join(picdir, 'template.png'))
    # # Initialize the drawing context with template as background
    # draw = ImageDraw.Draw(template)
    #
    # # Current weather
    # ## Open icon file
    # icon_file = icon_code + '.png'
    # icon_image = Image.open(os.path.join(icondir, icon_file))
    # icon_image = icon_image.resize((130,130))
    # template.paste(icon_image, (50, 50))
    #
    # draw.text((125,10), LOCATION, font=font35, fill=black)
    #
    # # Center current weather report
    # w, h = draw.textsize(string_report, font=font20)
    # #print(w)
    # if w > 250:
    #     string_report = 'Now:\n' + report.title()
    #
    # center = int(120-(w/2))
    # draw.text((center,175), string_report, font=font20, fill=black)
    #
    # # Data
    # draw.text((250,55), string_temp_current, font=font35, fill=black)
    # y = 100
    # draw.text((250,y), string_feels_like, font=font15, fill=black)
    # draw.text((250,y+20), string_wind, font=font15, fill=black)
    # draw.text((250,y+40), string_precip_percent, font=font15, fill=black)
    # draw.text((250,y+60), string_temp_max, font=font15, fill=black)
    # draw.text((250,y+80), string_temp_min, font=font15, fill=black)
    #
    # draw.text((125,218), last_update_string, font=font15, fill=black)
    #
    # # Weather Forcast
    # # Tomorrow
    # icon_file = nx_icon + '.png'
    # icon_image = Image.open(os.path.join(icondir, icon_file))
    # icon_image = icon_image.resize((130,130))
    # template.paste(icon_image, (435, 50))
    # draw.text((450,20), 'Tomorrow', font=font22, fill=black)
    # draw.text((415,180), nx_day_high, font=font15, fill=black)
    # draw.text((515,180), nx_day_low, font=font15, fill=black)
    # draw.text((460,200), nx_precip_percent, font=font15, fill=black)
    #
    # # Next Next Day Forcast
    # icon_file = nx_nx_icon + '.png'
    # icon_image = Image.open(os.path.join(icondir, icon_file))
    # icon_image = icon_image.resize((130,130))
    # template.paste(icon_image, (635, 50))
    # draw.text((625,20), 'Next-Next Day', font=font22, fill=black)
    # draw.text((615,180), nx_nx_day_high, font=font15, fill=black)
    # draw.text((715,180), nx_nx_day_low, font=font15, fill=black)
    # draw.text((660,200), nx_nx_precip_percent, font=font15, fill=black)
    #
    #
    # ## Dividing lines
    # draw.line((400,10,400,220), fill='black', width=3)
    # draw.line((600,20,600,210), fill='black', width=2)
    #
    #
    # # Tide Info
    # # Graph
    # tidegraph = Image.open('images/TideLevel.png')
    # template.paste(tidegraph, (125, 240))
    #
    # # Large horizontal dividing line
    # h = 240
    # draw.line((25, h, 775, h), fill='black', width=3)
    #
    # # Daily tide times
    # draw.text((30,260), "Today's Tide", font=font22, fill=black)
    #
    # # Get tide time predictions
    # hilo_error = True
    # while hilo_error == True:
    #     try:
    #         hilo_daily = HiLo(StationID)
    #         hilo_error = False
    #     except:
    #         display_error('Tide Prediction')
    #
    # # Display tide preditions
    # y_loc = 300 # starting location of list
    # # Iterate over preditions
    # for index, row in hilo_daily.iterrows():
    #     # For high tide
    #     if row['hi_lo'] == 'H':
    #         tide_time = index.strftime("%H:%M")
    #         tidestr = "High: " + tide_time
    #     # For low tide
    #     elif row['hi_lo'] == 'L':
    #         tide_time = index.strftime("%H:%M")
    #         tidestr = "Low:  " + tide_time
    #
    #     # Draw to display image
    #     draw.text((40,y_loc), tidestr, font=font15, fill=black)
    #     y_loc += 25 # This bumps the next prediction down a line
    #
    #
    # # Save the image for display as PNG
    # screen_output_file = os.path.join(picdir, 'screen_output.png')
    # template.save(screen_output_file)
    # # Close the template file
    # template.close()
    #
    # write_to_screen(screen_output_file, 600)
    #epd.Clear()
