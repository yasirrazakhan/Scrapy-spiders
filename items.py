
# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Watches2USpiderItem(scrapy.Item):

    url = scrapy.Field()
    name = scrapy.Field()
    price = scrapy.Field()
    image_url = scrapy.Field()
    brand = scrapy.Field()
    stock = scrapy.Field()
    category = scrapy.Field()
    