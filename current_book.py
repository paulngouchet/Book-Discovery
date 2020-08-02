import scrapy
import time
import difflib
import ast
import pickle
import json
import os
import os.path
import requests
from flask import Flask, render_template, request
from os import path
from os import getcwd
from subprocess import call
from scrapy.crawler import CrawlerProcess
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
searches_cache =  None
urls_cache = None
dict_urls_cache = None
books_cache = None
dict_books_cache = None
product_ids_cache = None

def matching(a,b):
    seq = difflib.SequenceMatcher(None,a,b)
    d = seq.ratio()*100
    print(d)
    if d >= 70:
        return True
    else:
        return False
    
class Urls(Document):
    url = StringField()
    info = StringField()
    books_found =  StringField()

class Searches(Document):
    query = StringField()
    urls = StringField()

class Books(Document):
    name = StringField()
    info = StringField()
    answer = StringField()

class Product_ids(Document):
    id_number = StringField()
    info = StringField()

def build_dict(db_object, a, b):  
    dict_object = {}
    
    for object in db_object:
        dict_object[object[a]] = object[b]
        
    return dict_object


def refresh():
    global searches_cache
    global urls_cache
    global dict_urls_cache
    global books_cache
    global dict_books_cache
    global product_ids_cache
    searches_cache =  Searches.objects()
    print("called")
    urls_cache = Urls.objects()
    dict_urls_cache = build_dict(urls_cache, "url", "books_found")
    #print(dict_urls_cache)
    books_cache = Books.objects()
    dict_books_cache = build_dict(books_cache, "name", "answer")
    product_ids_cache = Product_ids.objects()

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
    print(rj)
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
    print(rj)
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
    books_found = []
    data = []
    db_book_name = {} # For mongo db, string : string
    db_product_id = {} # For mongo db, string : array string
    # product id, then product name
    
    for url_book, product in urls.items():
        print("is this the error 1")
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
                refresh()
                data.clear()
                #print("only url", amazon)
            else:
                data.append(book[1])
                data.append(book[0])
                amazon = amazon_url(book[0])  # Create Amazon url
                data.append(amazon)
                product1 = Product_ids(id_number=book[0], info=str([amazon, book[1]])) # Save in the database
                product1.save()
                refresh()
                if book[1] in dict_books_cache:
                    final_data.append(ast.literal_eval(dict_books_cache[book[1]]))
                    books_found.append(book[1])
                else:
                    result = search_book(book[1]) # Search Each book, # Might need to come back for code review
                    data.append(result) # Might be useful, to be deleted
                    frontend_data.append(data)
                    #print("frontend_data", frontend_data)
                    answer = generate(result)
                    if bool(answer) == False:
                        continue
                    data_display[url_book] = answer # Might be useless
                    answer["url"] = amazon
                    final_data.append(answer)
                    books_found.append(book[1])
                    book1 = Books(name=book[1], info=str(result), answer=str(answer))
                    book1.save()
                    refresh()
                    data.clear()
                    
        url1 = Urls(url=url_book, info=str(product), books_found=str(books_found))
        url1.save()
        books_found.clear()
        refresh()
        #print("url and book", amazon, book[1])
            
app = Flask(__name__)

@app.route('/')
def hello_world():
    data_display.clear()
    final_data.clear()
    print(len(Searches.objects()))
    
    if len(Searches.objects()) > 0:
        refresh()
        #print(dict_urls_cache)
        for key, value in dict_urls_cache.items():
            print(key)
    '''print(Searches.objects())
    print("cached searches" ,searches_cache)
    print("cached urls", urls_cache)
    print("dict cached urls", dict_urls_cache)
    print("cached books", books_cache)
    print("dict cached books",dict_books_cache)'''
    return  render_template("index.html")


@app.route('/search', methods=['POST', 'GET'] )  # I am not the class spider above anymore. so i need to figure out about the urls saving into datab
def query_books():
    tic = time.time()
    data_display.clear()
    final_data.clear()
    
    if request.method == 'POST':
        query = request.form['search']
        search_query = "Best books about " + query
        match = None
        if searches_cache != None:
            for object in searches_cache:
                if matching(object.query, query) == True:
                    match = object
                    break
        if match != None:
            match_urls = ast.literal_eval(match.urls)
            output = []
            print("size output",len(output))
            for url in match_urls:
                if url in dict_urls_cache:
                    print(url)
                    print(len(dict_urls_cache))
                    match_books = dict_urls_cache[url]
                    match_books = ast.literal_eval(match_books)
                    print("match is ", len(match_books))
                    for book in match_books:
                        output.append(ast.literal_eval(dict_books_cache[book]))
                        #print(output)
            print("output is", len(output))
            
      return render_template("books1.html", books=output)

      url_searches = search_web(search_query)
      search = Searches(query=query, urls=str(url_searches))
      search.save()
      refresh()
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
        #return str(frontend_data) # To be fixed
        #return str(final_data) # To be fixed
        toc = time.time()
        print(toc - tic)
        return render_template("books1.html", books=final_data)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False, port="3002")
