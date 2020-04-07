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

from threading import Thread

from mongoengine import *
connect('book_search_db', host='localhost', port=27017)


# For optimization and speed, My code will certainly need lot of caching because i am going over the same arrays data many times


cx= '005331999340111559203:nb9u1-ynjkw'

#googleapikey="AIzaSyCbkWvy9ETOPHh5_lvsRVrdEQNiZt7mlHQ"

googleapikey="AIzaSyBfvhGJU-PqPyOemkIfjozyhmKg54KHlnU"

final_data = []

dict_url_book = {}

frontend_data = [] # Use Jinja, array of all the book information, [ index 0 - Book_name, index 1 - product_id,  index 3 - amazon_url, index 4 - Google book url ]

other_frontend_data = [] # Just index 0 - the product_id, index 1 - amazon_url


data_display = {}

store = {}


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


def generate(book):

    dict_object = {}
    print("INFO ABOUT THE BOOK")
    if book.get("volumeInfo") and book["volumeInfo"].get("imageLinks") and book["volumeInfo"].get("description") and book["volumeInfo"].get("title") and book["volumeInfo"].get("authors") :  # Needs to be fixed, i need to display more books
        print(book["volumeInfo"]["title"])
        print(book["volumeInfo"]["description"])
        book_description = book["volumeInfo"]["authors"][0] + " - " + book["volumeInfo"]["title"] + " - " + book["volumeInfo"]["description"]
        dict_object["text"] = book_description
        dict_object["title"] = book["volumeInfo"]["title"]
        dict_object["thumbnail"] = book["volumeInfo"]["imageLinks"]["thumbnail"]
        dict_object["authors"] = book["volumeInfo"]["authors"][0]

    return dict_object

def search_book(value):
    parms = {"q":value, 'key':googleapikey, 'maxResults':1}
    r = requests.get(url="https://www.googleapis.com/books/v1/volumes", params=parms)
    print(r.url)
    rj = r.json()

    #print(rj)

    #print(rj["items"][0]["volumeInfo"]["title"])
    '''if rj["items"][0] != None:
        return rj["items"][0]
    else:
        return False'''

    return rj["items"][0]


def search_web(value):
    parms = {"q":value,  'key':googleapikey, 'cx':cx, 'num':10}  # 10 maximum results
    # For restricted queries, use this version of the requests
    #r = requests.get(url="https://www.googleapis.com/customsearch/v1/siterestrict", params=parms)

    # For the non restricted version - use - 10K query limit a day - 100 free - $ 5 for every 1000 queries
    r = requests.get(url="https://www.googleapis.com/customsearch/v1", params=parms)
    print(r.url)
    rj = r.json()
    #print(rj)


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


    book_range = []
    book_dict = {}

    data = []
    db_book_name = {} # For mongo db, string : string
    db_product_id = {} # For mongo db, string : array string
    # product id, then product name

    print("len urls is", len(urls))
    for url_book, product in urls.items():
        print("is this the error 1")
        url1 = Urls(url=url_book, info=str(product))
        url1.save()

        for book in product:
            print("is this the error 2")
            data.clear()
             # Use Jinja, array of all the book information, [ index 0 - Book_name, index 1 - product_id,  index 3 - amazon_id, index 4 - Google book url ]

            if len(book) == 1:
                data.append(book[0])
                amazon = amazon_url(book[0]) # Create Amazon url
                data.append(amazon)
                other_frontend_data.append(data)
                #print("other_frontend_data", other_frontend_data)

                product1 = Product_ids(id_number=book[0], info=str([amazon])) # save in db
                product1.save()
                data.clear()

                #print("only url", amazon)
            else:

                data.append(book[1])
                data.append(book[0])
                amazon = amazon_url(book[0])  # Create Amazon url
                data.append(amazon)

                product1 = Product_ids(id_number=book[0], info=str([amazon, book[1]])) # Save in the database
                product1.save()

                print("appending ?")

                book_dict[str(book[1])] = str(amazon)

                book_range.append(str(book[1]))



                #print("url and book", amazon, book[1])

    print("book range and book dict", len(book_range), len(book_dict))

    print(book_range)
    print(book_dict)

    return book_range, book_dict




def process_range_book(book_range, store = None):

    if store is None:
        stotr = {}
    for book in book_range:
        store[book] = search_book(book)

    return store

def threaded_process_range(book_range):

    threads = []

    # Will be the total number of books, might have no need for this

    books = book_range
    t = Thread(target=process_range_book, args=(books,store))
    threads.append(t)

    [t.start() for t in threads]

    [t.join() for t in threads]

    return store



def book_thread(book_range, book_dict):

    print(len(book_range))
    threaded_process_range(book_range)

    while len(store) == 0:
        print(len(store))

    for key, value in store.items():
        answer = generate(value)
        if bool(answer) == False:
            continue
        answer["url"] = book_dict[key]

        final_data.append(answer)
        book1 = Books(name=key, info=str(value))
        book1.save()

    print("size is", len(store))



app = Flask(__name__)

@app.route('/')
def hello_world():
    data_display.clear()
    final_data.clear()
    return  render_template("index.html")


@app.route('/search', methods=['POST', 'GET'] )  # I am not the class spider above anymore. so i need to figure out about the urls saving into datab
def query_books():
    tic = time.time()
    data_display.clear()
    final_data.clear()
    if request.method == 'POST':
        query = request.form['search']

        search_query = "Best books about " + query
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
        print(dict_url_book)



        book_range, book_dict = process_dict_url(dict_url_book)

        book_thread(book_range, book_dict)

        #return "success"
        #return str(frontend_data) # To be fixed

        #return str(final_data) # To be fixed

        toc = time.time()

        print(toc - tic)

        return render_template("books1.html", books=final_data)



if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False, port="3002")