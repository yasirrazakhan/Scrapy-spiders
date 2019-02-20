# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MangoSpiderItem(scrapy.Item):
    title = scrapy.Field()
    category = scrapy.Field()
    sale_price = scrapy.Field()
    crossed_out_price = scrapy.Field()
    discount = scrapy.Field()
    stock = scrapy.Field()
    sizes = scrapy.Field()
    page_url = scrapy.Field()
    image_url = scrapy.Field()
