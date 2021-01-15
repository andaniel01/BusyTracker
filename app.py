from flask import Flask, render_template, request, redirect, url_for
from popularTimeScraper import *
import json

app = Flask(__name__)

@app.route('/')
def hello():
    results = display_user_info()
    return render_template("index.html",results=results)

@app.route('/add_location',methods=['POST'])
def add_location():
    location_name = request.form['locationName']
    location_url = request.form['locationUrl']

    txt_file_url = location_url

    with open('user_list_data.txt','a') as f:
        json.dump(txt_file_url, f)

    with open('location_name_list.txt', 'a') as f:
        json.dump(location_name, f)
            
    return redirect(url_for('hello'))

if __name__ == "__main__":
    app.run(debug=True)