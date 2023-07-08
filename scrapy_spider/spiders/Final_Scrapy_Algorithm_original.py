import scrapy
import time
import pickle
import os.path
from os import path
from os import getcwd


# To run do
#  scrapy runspider amazon.py -s LOG_ENABLED=False
dict_url_book = {}


class BlogSpider(scrapy.Spider):
    name = 'blogspider'
    itemlist = []
    
    with open ("outfile", 'rb') as fp:
        itemlist = pickle.load(fp)

    print("list of urls is ", itemlist)
    #start_urls = ['https://www.benzinga.com/money/best-investing-books/']
    #start_urls = ['https://www.thebalance.com/best-books-for-learning-about-stocks-4171823'] # Gives no answer
    #start_urls = ['https://www.thewaystowealth.com/investing/best-investing-books/']
    #start_urls = ['https://www.thebalance.com/best-personal-finance-books-4154809']
    #start_urls = ['http://nymag.com/strategist/article/best-personal-finance-books.html', 'https://www.thebalance.com/best-personal-finance-books-4154809', 'https://www.thewaystowealth.com/investing/best-investing-books/', 'https://www.cloudways.com/blog/best-startup-books-for-new-entrepreneurs/' ]
    start_urls = itemlist

    def parse(self, response):
        tic = time.clock()
        #product_urls = response.xpath('//a[contains(@href,  "https://www.amazon.com/gp/product/")]/@href').extract()
        product_urls = response.xpath('//a[contains(@href,  "https://www.amazon.com/")]/@href').extract()
        #print(len(product_urls))
        #print(product_urls)
        product_urls_unique = list(set(product_urls))
        #print(product_urls_unique)
        print(len(product_urls_unique))
        list_book_per_url = self.book_name_id(product_urls_unique)
        dict_url_book[response.request.url] = list_book_per_url
        
        yield dict_url_book

        #print(dict_url_book) # input - list urls from Google search , Final Output - {url1: [[id, product_name], [id]], url2: [[id, product_name], [id]], url3: [[id, product_name], [id]]}
        toc = time.clock()
        print("time is ", toc - tic)  # Time will be about 3 seconds to process 3 urls





    def book_name_id(self , urls):
        list_info_url = []
        for url in urls:
            new_info = []
            info = url.split('?')[0]
            info = info.split('/')
            # gp

            if len(info) == 5: #https://www.amazon.com/dp/0143130404?ascsubtag=[]st[i]f5HMfJ&tag=thestrategistsite-20
                id = info[-1] # Get the product id, This link only has the product id
                new_info.append(id)
                list_info_url.append(new_info)

            elif len(info) == 6: #https://www.amazon.com/Will-Teach-You-Be-Rich/dp/0761147489
                # When The Url is longer
                id = info[-1] # Get the product id
                book_name = info[3] # Get the product name
                new_info.append(id)
                if book_name != 'gp':
                    book_name = book_name.replace("-", " ")
                    new_info.append(book_name)
                list_info_url.append(new_info)

            elif len(info) == 7:# https://www.amazon.com/Designing-Your-Life-Well-Lived-Joyful-ebook/dp/B01BJSRSEC/ref=sr_1_1
                id = info[-2] # Get the product id
                book_name = info[3] # Get the product name
                new_info.append(id)
                if book_name != 'gp':
                    book_name = book_name.replace("-", " ")
                    new_info.append(book_name)


                list_info_url.append(new_info)

        return list_info_url
