import requests
from bs4 import BeautifulSoup, element
from selenium import webdriver
import re
import json
import time
import datetime
import string
from Scrapedata import ScrapedData
import os

def extract_populartime_url(url):

    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--incognito")
    options.add_argument("--headless")
    driver = webdriver.Chrome("/Users/danielan/Downloads/chromedriver-2", chrome_options=options)

    driver.get(url)
    time.sleep(2)
    page_source = driver.page_source

    soup = BeautifulSoup(page_source, "html.parser")
    raw_results = soup.select('div[jsinstance]')

    results = []
    for x in raw_results:
        string = str(x.get('aria-label'))
        if string[0].isdigit():
            results.append(string)
        elif "Currently" in string:
            results.append(string)

    # elements = soup.find_all("div", class_ = "section-popular-times-bar")
    # results =[]

    # for element in elements:
    #     result = str(element).split("\"", 2)
    #     results.append(result[1])
    #     print(result[1])

    return results
    
def get_location_url(location_name):
    api_key = ""
    place_search_field = "place_id"
    response = requests.get("https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={location_name}&inputtype=textquery&fields={field}&key={key}".format(location_name = location_name, field = place_search_field, key = api_key))
    print("Place search api request status code: " + str(response.status_code))
    place_id = response.json()['candidates'][0]['place_id']
    place_detail_field = "url,opening_hours"
    place_detail_response = requests.get("https://maps.googleapis.com/maps/api/place/details/json?place_id={id}&fields={field}&key={key}".format(id =place_id, field = place_detail_field, key = api_key))
    print("Place detail api request status code: " + str(response.status_code))
    location_url = place_detail_response.json()['result']['url']
    opening_hours = place_detail_response.json()['result']['opening_hours']['weekday_text']
    opening_hours_url_dic = {
        "opening_hours": opening_hours,
        "url": location_url
    }
    
    return opening_hours_url_dic

#calculates how long the location is open for
def get_location_open_hours(results):
    hours = results[datetime.datetime.today().weekday()]
    open_hour = hours.split(":",1)[1].split("-")
    start_close_hour = []
    for hour in open_hour:
        replaced_hour = hour.replace(":","")
        start_close_hour.append(replaced_hour)
    
    start_close_hour_num =[]
    start_hour = start_close_hour[0]

    for hour in start_close_hour:
        if "PM" in hour:
            replaced_hour = hour.replace("PM","")
            start_close_hour_num.append(int(replaced_hour) + 1200)
        else:
            replaced_hour = hour.replace("AM","")
            start_close_hour_num.append(int(replaced_hour))
    
    hour_end = int(str(start_close_hour_num[1])[0:2])
    min_end = int(str(start_close_hour_num[1])[2:4])

    hour_start = int(str(start_close_hour_num[0])[0:2])
    #comeback to later hour_start getting 83 hours because 830
    min_start = int(str(start_close_hour_num[0])[2:4])

    return str(datetime.timedelta(hour_end, min_end) - datetime.timedelta(hour_start, min_start))
        

#weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
def get_today_popular_time(results, day):
    scraped_data_list = []

    #initalizing object and editing data
    for result in results:
        busy_percent = 0
        result_time = 0
        is_current = False
        if "Currently" in result:
            is_current = True
            busy_percent = result.split("%",1)[0].split("Currently ",1)[1]
            # print("current:" + busy_percent)
            result_time = result.split("usually ",1)[1][:-1].split("%",1)[0]
        
            data = ScrapedData(busy_percent, result_time, is_current)
            scraped_data_list.append(data)
        else:
            busy_percent = result.split("%",1)[0]
            # print("busy percent: " + busy_percent)
            result_time = result.split("at ",1)[1][:-1]
            
            data = ScrapedData(busy_percent, result_time, is_current)
            scraped_data_list.append(data)
        

    today_data_list = []
    parse_today_done = False
    i = 0
    day_count = 0
    #only for today_data_list 

    for data in scraped_data_list:
        if not parse_today_done:

            hour = 0
            time_period = ""

            next_hour = 0                
            next_time_period = ""

            if data.is_current:
                before_hour = int(scraped_data_list[i - 1].time.split(" ",1)[0])
                before_time_period = scraped_data_list[i - 1].time.split(" ",1)[1]

                next_hour = int(scraped_data_list[i + 1].time.split(" ",1)[0])                
                next_time_period = scraped_data_list[i + 1].time.split(" ",1)[1]

                if before_hour != 12:
                    # datat_time = str(before_hour + 1) + " " + before_time_period
                    hour = before_hour + 1
                    time_period = before_time_period
                elif before_hour == 12:
                    # data_time = "1 " + after_time_period
                    hour = 1
                    time_period = next_time_period
                else:
                    hour = before_hour + 1
                    time_period = before_time_period
        
            elif scraped_data_list[i + 1].is_current:
                
                after_time_period = scraped_data_list[i + 2].time.split(" ",1)[1]
                hour = int(data.time.split(" ",1)[0])
                time_period = data.time.split(" ",1)[1]
                if data.time != 12:
                    next_hour = 1
                    next_time_period = time_period
                elif before_hour == 12:
                    next_hour = 1
                    next_time_period = after_time_period
                else:
                    next_hour = data.time + 1
                    next_time_period = time_period
            else:
                hour = int(data.time.split(" ",1)[0])
                time_period = data.time.split(" ",1)[1]
                next_hour = int(scraped_data_list[i + 1].time.split(" ",1)[0])                
                next_time_period = scraped_data_list[i + 1].time.split(" ",1)[1]

            append_data = False

            #11 -> 6
            #implement 24h location later
            if ((hour + 1) == next_hour) and (time_period == next_time_period):
                append_data = True
            elif (hour == 11) and (next_hour == 12) and (time_period != next_time_period):
                append_data = True
            elif (hour == 12) and (next_hour == 1) and (time_period == next_time_period):
                append_data = True  
            elif ((hour + 1) != next_hour) and (time_period != next_time_period):
                append_data = True
                parse_today_done = True

            if append_data and (day == day_count):
                if data.is_current:
                    data.time = str(hour) + " " + time_period
                today_data_list.append(data)
                
            
            if parse_today_done:
                day_count = day_count + 1
                parse_today_done = False

            if (i + 2) != len(scraped_data_list):
                i = i + 1
            
    return today_data_list

def safe_busy_percent(today_data_list):
    i = 0 
    busy_percent_sum = 0 
    for data in today_data_list:
        if data.busy_percent != 0:
            i = i + 1
            busy_percent_sum = busy_percent_sum + int(data.busy_percent)
    
    if i == 0:
        i = 1
    
    return (busy_percent_sum/i)

def safe_visit_hours(today_data_list):
    safe_percent = safe_busy_percent(today_data_list)
    green_hours = []
    orange_hours = []
    red_hours = []

    for data in today_data_list:
        if data.busy_percent < safe_percent:
            green_hours.append(str(data.busy_percent) + " " + data.time_period)
        elif data.busy_percent == safe_percent:
            orange_hours.append(str(data.busy_percent) + " " + data.time_period)
        elif data.busy_percent > safe_busy_percent:
            red_hours.append(str(data.busy_percent) + " " + data.time_period)
    
    recommened_hours = {
        "green": green_hours,
        "orange": orange_hours,
        "red": red_hours
    }

    return recommened_hours

def display_user_info():
    results = []
    if os.stat('user_list_data.txt').st_size and os.stat('location_name_list.txt') != 0:
        url_list = []
        file = open('user_list_data.txt','r')
        url = file.read()[1:-1]

        location_name_list = []
        file2 = open('location_name_list.txt', 'r')
        location_name = file2.read()[1:-1]

        if '""' not in url:
            url_list.append(url)
            location_name_list.append(location_name)
        else:
            url_list = url.split('""')
            location_name_list = location_name.split('""')

        for url, name_location in zip(url_list, location_name_list):
            popular_time_today = get_today_popular_time(extract_populartime_url(url), datetime.date.today().weekday())

            time_today = []
            busy_percent = []
            is_time_current = []
            is_safe = []

            today_safe_percent = safe_busy_percent(popular_time_today)

            for data in popular_time_today:
                time_today.append(data.time)
                busy_percent.append(data.busy_percent)
                is_time_current.append(data.is_current)
                if int(data.busy_percent) > int(today_safe_percent):
                    is_safe.append(False)
                else:
                    is_safe.append(True)

            display_data = {
                "location_name": name_location,
                "location_url": url,
                "time": time_today,
                "busy_percent": busy_percent,
                "is_time_current": is_time_current,
                "is_safe": is_safe
            }

            results.append(display_data)
    
    return results

# def main():
#     # url = "https://www.google.ca/maps/place/Tim+Hortons/@43.4653171,-80.5327216,15z/data=!4m5!3m4!1s0x882bf476e18efc3d:0xd0c2193a912167b7!8m2!3d43.4690156!4d-80.5236644"
#     # url_tim = "https://www.google.com/maps/place/Tim+Hortons/@43.4690146,-80.5258531,17z/data=!3m1!4b1!4m12!1m6!3m5!1s0x0:0x7fdc5f4fcbb463d0!2sShoppers+Drug+Mart!8m2!3d43.4636634!4d-80.522646!3m4!1s0x882bf476e18efc3d:0xd0c2193a912167b7!8m2!3d43.4690146!4d-80.5236644"
#     # url_shoppers = "https://www.google.com/maps/place/Shoppers+Drug+Mart/@43.4636634,-80.5248347,17z/data=!3m1!4b1!4m5!3m4!1s0x882bf412af6c47c5:0x7fdc5f4fcbb463d0!8m2!3d43.4636634!4d-80.522646"
#     # opening_hours_url_dic = get_location_url("Shoppers%20Drug%20Mart")
#     # extract_populartime_url(opening_hours_url_dic['url'])

#     # opening_hours = ["Monday: 8:30 AM - 9:00 PM", "Tuesday: 8:00 AM - 9:00 PM", "Wednesday: 8:00 AM - 9 PM"]
#     # print(opening_hours)
#     #get_location_open_hours(opening_hours)

#     # data = get_today_popular_time(extract_populartime_url(url_tim), 2)
#     # print("========================")
#     # for x in data:
#     #     print(x.time)
#     #     print(x.busy_percent)
#     #     print(x.is_current)

#     # extract_populartime_url(url_shoppers)
        

# if __name__=="__main__":
#     main()

