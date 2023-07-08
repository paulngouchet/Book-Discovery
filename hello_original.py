from flask import Flask, render_template, request
import scrapy
import time
from scrapy.crawler import CrawlerProcess
from subprocess import call
import pickle
import json
import os
import os.path
from os import path
from os import getcwd
import requests
from mongoengine import *
connect('book_search_db', host='localhost', port=27017)

# For optimization and speed, My code will certainly need lot of caching because i am going over the same arrays data many times
cx= ''
googleapikey=""
dict_url_book = {}
frontend_data = [] # Use Jinja, array of all the book information, [ index 0 - Book_name, index 1 - product_id,  index 3 - amazon_url, index 4 - Google book url ]
other_frontend_data = [] # Just index 0 - the product_id, index 1 - amazon_url
app = Flask(__name__)

class Urls(Document):
    url = StringField()
    info = StringField()

class Searches(Document):
    query = StringField()
    urls = StringField()

class Books(Document):
    name = StringField()
    info = StringField()

class Product_ids(Document):
    id_number = StringField()
    info = StringField()



def search_book(value):
    parms = {"q":value, 'key':googleapikey, 'maxResults':1}
    r = requests.get(url="https://www.googleapis.com/books/v1/volumes", params=parms)
    print r.url
    rj = r.json()
    print(rj["items"][0]["volumeInfo"]["title"])

    return rj["items"][0]


def search_web(value):
    parms = {"q":value,  'key':googleapikey, 'cx':cx, 'num':10}  # 10 maximum results
    # For restricted queries, use this version of the requests
    #r = requests.get(url="https://www.googleapis.com/customsearch/v1/siterestrict", params=parms)
    # For the non restricted version - use - 10K query limit a day - 100 free - $ 5 for every 1000 queries
    r = requests.get(url="https://www.googleapis.com/customsearch/v1", params=parms)
    print r.url
    rj = r.json()
    list_website_url = []

    for web in rj["items"]:
        list_website_url.append(web['link'])

    return list_website_url


def amazon_url(id):
    format = 'http://amzn.com/'
    product_id = id
    amazon_id = 'paulngouche0c-20'
    result = format + id + '/?tag=' + amazon_id
    return result


def process_dict_url(urls):
    data = []
    db_book_name = {} # For mongo db, string : string
    db_product_id = {} # For mongo db, string : array string
    # product id, then product name
    for url_book, product in urls.items():
        print("is this the error 1")
        url1 = Urls(url=url_book, info=str(product))
        url1.save()

        for book in product:
            print("is this the error 2")
            data = []
             # Use Jinja, array of all the book information, [ index 0 - Book_name, index 1 - product_id,  index 3 - amazon_id, index 4 - Google book url ]
            if len(book) == 1:
                data.append(book[0])
                amazon = amazon_url(book[0]) # Create Amazon url
                data.append(amazon)
                other_frontend_data.append(data)
                print("other_frontend_data", other_frontend_data)
                product1 = Product_ids(id_number=book[0], info=str([amazon])) # save in db
                product1.save()
                print("only url", amazon)
            else:

                data.append(book[1])
                data.append(book[0])
                amazon = amazon_url(book[0])  # Create Amazon url
                data.append(amazon)

                product1 = Product_ids(id_number=book[0], info=str([amazon, book[1]])) # Save in the database
                product1.save()
                result = search_book(book[1]) # Search Each book
                data.append(result)
                frontend_data.append(data)
                print("frontend_data", frontend_data)
                book1 = Books(name=book[1], info=str(result))
                book1.save()
                print("url and book", amazon, book[1])


@app.route('/')
def hello_world():
    return  render_template("index.html")


@app.route('/search', methods=['POST', 'GET'] )  # I am not the class spider above anymore. so i need to figure out about the urls saving into datab
def query_books():
    if request.method == 'POST':
        query = request.form['search']
        search_query = query
        url_searches = search_web(search_query)
        search = Searches(query=search_query, urls=str(url_searches))
        search.save()
        print("getting here")

        with open('outfile', 'wb') as fp:
            pickle.dump(url_searches, fp)

        path_file = getcwd() + "/ blogspider.json"

        if path.exists(path_file):
            os.remove(path_file)

        name = 'blogspider'
        call(["scrapy", "crawl", "{0}".format(name), "-o {0}.json".format(name)])

        with open(path_file) as json_file:
            data = json.load(json_file)
            dict_url_book = data[-1]
        print("getting here")
        #print(dict_url_book)
        process_dict_url(dict_url_book)
        print(len(frontend_data))
        #return "success"
        return str(frontend_data) # To be fixed



if __name__ == '__main__':
    app.run(debug=False)
