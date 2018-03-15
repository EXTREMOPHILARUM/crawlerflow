from __future__ import print_function
import logging
from scrapy.responsetypes import responsetypes
from scrapy.utils.request import request_fingerprint
from scrapy.utils.python import to_bytes
from scrapy.http.headers import Headers
from elasticsearch_dsl import DocType, Date, Integer, Text, connections
from datetime import datetime
from webcrawler.settings import DATA_COLLECTION, DATABASE
from webcrawler.utils import get_urn, get_domain
import pysolr

logger = logging.getLogger(__name__)


class SolrCacheStorage(object):
    """
    should set HTTPCACHE_ES_DATABASE in the settings.py


    """
    COLLECTION_NAME = "weblinks"

    def __init__(self, settings):
        self.core_name = settings['INVANA_CRAWLER_COLLECTION']
        self.solr_host = settings.get('HTTPCACHE_SOLR_HOST', '127.0.0.1')

        self.solr = pysolr.Solr('http://{0}/solr/{1}'.format(self.solr_host, DATA_COLLECTION),
                                timeout=10)
        self.expiration_secs = settings.getint('HTTPCACHE_EXPIRATION_SECS')

    def open_spider(self, spider):
        logger.debug("Using solr cache storage with core name %(core_name)s" % {'core_name': self.core_name},
                     extra={'spider': spider})

    def close_spider(self, spider):
        pass

    def get_headers(self, obj):
        """
        this will convert all the headers_Server, headers_Date
        into "header": {
            "Server": "",
            "Date": ""
        }

        :param obj:
        :return:
        """
        headers = {}
        for k, v in obj.items():
            if k.startswith("headers_"):
                headers[k.replace("headers_", "")] = v

        obj['headers'] = headers
        return obj

    def retrieve_response(self, spider, request):
        data = self._read_data(spider, request)

        if data is None:
            return  # not cached
        else:
            if data['status'] == 200 and data['html'] is None:
                return None

        data = self.get_headers(data)
        url = data['url']
        status = data['status']
        headers = Headers(data['headers'])
        body = bytes(data['html'], encoding="utf-8")
        respcls = responsetypes.from_args(headers=headers, url=url)
        response = respcls(url=url, headers=headers, status=status, body=body)
        return response

    def _clean_headers(self, obj):
        cleaned_object = {}
        for k, v in obj.items():
            cleaned_object[k.decode('utf-8')] = v[0].decode('utf-8')
        return cleaned_object

    def _flatten_headers(self, obj):
        flat_data = {}
        for k, v in obj.items():
            flat_data['headers_{}'.format(k)] = v
        return flat_data

    def store_response(self, spider, request, response):
        data = {
            'status': response.status,
            'domain': get_domain(response.url),
            'url': response.url,
            'html': str(response.body).lstrip("b'").strip("'")
                .replace("\\n", "")
                .replace("\\t", "")
                .replace("\\\\", "\\"),
            'created': datetime.now()
        }
        data.update(self._flatten_headers(self._clean_headers(response.headers)))
        data['id'] = get_urn(response.url)
        self.solr.add([data])

    def _read_data(self, spider, request):
        try:
            result = self.solr.search(q='id:{}'.format(get_urn(request.url)))
            doc = result.docs[0]
            return doc
        except Exception as e:
            return None

    def _request_key(self, request):
        return to_bytes(request_fingerprint(request))