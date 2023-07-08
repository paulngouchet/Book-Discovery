# Book-Discovery
Search Engine for the best books about any topic. It will scroll the Web, find the best books and you can buy directly on Amazon. Built using Python Flask, Scrapy.

Book Discovery - Web app

http://157.230.159.18:3002

zip -r book_discovery.zip scrapy_spider2  

scp Directory/current_book.py root@157.230.159.18:/root/scrapy_spider2

scp  root@157.230.159.18:/root/book_discovery.zip Directory/Old_Startups

gunicorn --bind 0.0.0.0:3002 wsgi:app --daemon


The main file is current_book.py

http://157.230.159.18:3002/
