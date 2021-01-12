import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import re
import json
import time
from locationDetail import LocationDetail
import datetime
import string
from Scrapedata import ScrapedData

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
    elements = soup.find_all("div", class_ = "section-popular-times-bar")
    results =[]

    for element in elements:
        result = str(element).split("\"", 2)
        results.append(result[1])

    return results
    
def get_location_url(location_name):
    api_key = "AIzaSyDlLh_syaCqWXswA_ddWgkfi5IcAgpVyok"
    place_search_field = "place_id"
    response = requests.get("https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={location_name}&inputtype=textquery&fields={field}&key={key}".format(location_name = location_name, field = place_search_field, key = api_key))
    print("Place search api request status code: " + str(response.status_code))
    place_id = response.json()['candidates'][0]['place_id']
    place_detail_field = "url,opening_hours"
    place_detail_response = requests.get("https://maps.googleapis.com/maps/api/place/details/json?place_id={id}&fields={field}&key={key}".format(id =place_id, field = place_detail_field, key = api_key))
    print("Place detail api request status code: " + str(response.status_code))
    location_url = place_detail_response.json()['result']['url']
    opening_hours = place_detail_response.json()['result']['opening_hours']['weekday_text']
    print(opening_hours)
    opening_hours_url_dic = {
        "opening_hours": opening_hours,
        "url": location_url
    }
    
    return opening_hours_url_dic

#calculates how long the location is open for
def get_location_open_hours(results):
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours = results[datetime.datetime.today().weekday()]
    print(hours)
    open_hour = hours.split(":",1)[1].split("-")
    print(open_hour)
    start_close_hour = []
    for hour in open_hour:
        replaced_hour = hour.replace(":","")
        start_close_hour.append(replaced_hour)
    
    print(start_close_hour)
    start_close_hour_num =[]
    start_hour = start_close_hour[0]

    for hour in start_close_hour:
        if "PM" in hour:
            replaced_hour = hour.replace("PM","")
            start_close_hour_num.append(int(replaced_hour) + 1200)
        else:
            replaced_hour = hour.replace("AM","")
            start_close_hour_num.append(int(replaced_hour))
    
    print(start_close_hour_num)
    hour_end = int(str(start_close_hour_num[1])[0:2])
    min_end = int(str(start_close_hour_num[1])[2:4])
    print(hour_end)
    hour_start = int(str(start_close_hour_num[0])[0:2])
    #comeback to later hour_start getting 83 hours because 830
    min_start = int(str(start_close_hour_num[0])[2:4])
    print(hour_start)

    print(str(datetime.timedelta(hour_end, min_end) - datetime.timedelta(hour_start, min_start)))

    return str(datetime.timedelta(hour_end, min_end) - datetime.timedelta(hour_start, min_start))
        

def get_today_popular_time(results):
    scraped_data_list = []

    for result in results:
        busy_percent = 0
        result_time = 0
        is_current = False
        if "Current" in result:
            is_current = True

        busy_percent = result.split("%",1)[0]
        result_time = result.split("at ",1)[1][:-1]
        data = ScrapedData(busy_percent, result_time, is_current)
        scraped_data_list.append(data)

    today_data_list = []
    parse_today_done = False
    i = 0

    #only for today_data_list 
    for data in scraped_data_list:
        if not parse_today_done:
            hour = int(data.time.split(" ",1)[0])
            time_period = data.time.split(" ",1)[1]

            next_hour = int(scraped_data_list[i + 1].time.split(" ",1)[0])
            next_time_period = scraped_data_list[i + 1].time.split(" ",1)[1]
            
            #11 -> 6
             #implement 24h location later
            if ((hour + 1) == next_hour) and (time_period == next_time_period):
                today_data_list.append(data)
            elif (hour == 11) and (next_hour == 12) and (time_period != next_time_period):
                today_data_list.append(data)
            elif (hour == 12) and (next_hour == 1) and (time_period == next_time_period):
                today_data_list.append(data)  
            elif ((hour + 1) != next_hour) and (time_period != next_time_period):
                today_data_list.append(data)
                parse_today_done = True

            if (i + 2) != len(scraped_data_list):
                i = i + 1
            
    return today_data_list

def is_visit_safe():
    

def main():
    url = "https://www.google.ca/maps/place/Tim+Hortons/@43.4653171,-80.5327216,15z/data=!4m5!3m4!1s0x882bf476e18efc3d:0xd0c2193a912167b7!8m2!3d43.4690156!4d-80.5236644"
    url_shoppers = "https://www.google.com/maps/place/Shoppers+Drug+Mart/@43.4636634,-80.5248347,17z/data=!3m1!4b1!4m5!3m4!1s0x882bf412af6c47c5:0x7fdc5f4fcbb463d0!8m2!3d43.4636634!4d-80.522646"
    # opening_hours_url_dic = get_location_url("Shoppers%20Drug%20Mart")
    # extract_populartime_url(opening_hours_url_dic['url'])

    # opening_hours = ["Monday: 8:30 AM - 9:00 PM", "Tuesday: 8:00 AM - 9:00 PM", "Wednesday: 8:00 AM - 9 PM"]
    # print(opening_hours)
    #get_location_open_hours(opening_hours)

    data = get_today_popular_time(extract_populartime_url(url_shoppers))
    for x in data:
        print(data.busy_percent)
        print(data.time)
        print(data.is_current)


if __name__=="__main__":
    main()

