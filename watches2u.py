# -*- coding: utf-8 -*-
import re
from urllib.parse import urljoin
import scrapy
from watches2U_spider.items import Watches2USpiderItem


class Watches2uSpider(scrapy.Spider):
    """basic crawler to crawl all the products in watches2u.com"""
    name = 'watches2u'
    allowed_domains = ['www.watches2u.com']
    start_urls = ['http://www.watches2u.com/']

    def parse(self, response):

        for href in response.xpath('//ul[@class="area_top_dds"]/li/a/@href'):
            url = response.urljoin(href.extract())
            yield scrapy.Request(url=url, callback=self.parse_item)

    def parse_item(self, response):

        product_urls = response.xpath('//div[@class="xcomponent_products_medium"]/a/@href')
        for url in product_urls:
            url = response.urljoin(url.extract())
            yield scrapy.Request(url, callback=self.parse_product)

        next_page_url = response.xpath('//a[@class="next"]/@onclick').extract()
        if next_page_url:
            page_num = re.search('page_num=([\d]+)', next_page_url[0]).group(1)
            url = urljoin(response.url, '?page_num='+page_num)
            yield scrapy.Request(url, callback=self.parse_item)



    def parse_product(self, response):

        watch = Watches2USpiderItem()

        url = response.url
        name = response.xpath('//span[@itemprop="name"]/text()').extract()
        brand = response.xpath('//span[@itemprop="brand"]/text()').extract()
        price = response.xpath('//span[@class="price"]//text()').extract()
        stock = response.xpath('//div[@class="stockdetail"]/text()').extract()
        image_url = response.xpath('//div[@id="page_products_details5_image_outer"]/div/img/@src').extract()
        category = response.xpath('//div[@itemprop="breadcrumb"]//text()').extract()
        category = ''.join(category)

        watch['url'] = url
        watch['name'] = name
        watch['brand'] = brand
        watch['price'] = price
        watch['stock'] = stock
        watch['image_url'] = image_url
        watch['category'] = category

        yield watch