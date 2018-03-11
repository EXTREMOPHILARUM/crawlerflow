# web-scout

A micro-framework to crawl the web pages - blogs/rss. You can literally define what sites you 
want to crawl through and even configure the type of data you want to crawl and gather.

## Install

```bash

pip install git+https://github.com/invanatech/web-crawler#egg=webcrawler

```

## Running and Usage 

### saving the data to MongoDB

```python

from webcrawler.utils import example_config
from webcrawler.parser import crawler
from datetime import datetime
import pymongo

MONGO_CONNECTION = {
    'MONGODB_SERVER': '127.0.0.1',
    'MONGODB_PORT': 27017,
    'MONGODB_DBNAME': 'test',
    'MONGODB_COLLECTION': 'crawled_data'
}


class MongoDBPipeline(object):
    def __init__(self):
        connection = pymongo.MongoClient(
            MONGO_CONNECTION.get('MONGODB_SERVER'),
            MONGO_CONNECTION.get('MONGODB_PORT')
        )
        self.db = connection[MONGO_CONNECTION.get('MONGODB_DBNAME')]
        self.collection = self.db[MONGO_CONNECTION.get('MONGODB_COLLECTION')]

    def process_item(self, item, spider):
        if self.collection is None:
            raise Exception("self.connect() it not called in the Pipiline, please make the connection first")
        data = dict(item)
        data['updated_at'] = datetime.now()
        self.collection.insert(data)

        items_keys = ['blogs', 'items', 'feeds']
        for key in items_keys:
            if key in data.keys():
                blogs = data.get(key, [])
                for blog in blogs:
                    data_ = dict(blog)
                    data_['updated_at'] = datetime.now()
                    self.db[key].insert(data_)
        print("Post added to MongoDB")
        return item


settings = {
    'FEED_URI': 'result.json',

}

if __name__ == '__main__':
    crawler(config=example_config, settings=settings)

``` 


### Using MongoDB as http cache

```bash


settings = {
    'FEED_URI': 'result.json',
    'ITEM_PIPELINES': {'__main__.MongoDBPipeline': 1},
    'HTTPCACHE_ENABLED': True,
    'HTTPCACHE_STORAGE': "webcrawler.httpcache.mongodb.MongoDBCacheStorage",
    'HTTPCACHE_MONGODB_DATABASE': "crawlers",
    "HTTPCACHE_MONGODB_PORT": 27017

}


```


### Saving data to json file
```python


from webcrawler.utils import example_config
from webcrawler.parser import crawler
 

settings = {
    'FEED_URI': 'result.json',
    'ITEM_PIPELINES': {'__main__.MongoDBPipeline': 1},

}

if __name__ == '__main__':
    crawler(config=example_config, settings=settings)


```




## References

- https://stackoverflow.com/a/14453186/3448851


