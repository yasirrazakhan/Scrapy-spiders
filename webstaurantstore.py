# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request, HtmlResponse


class WebstaurantstoreSpiderItem(scrapy.Item):
    # define the fields for your item here like:

    Title = scrapy.Field()
    Price = scrapy.Field()
    UPC = scrapy.Field()


class WebstaurantstoreSpider(scrapy.Spider):
    name = 'webstaurantstore'
    allowed_domains = ['webstaurantstore.com']
    start_urls = ['http://webstaurantstore.com/']

    def parse(self, response):
        categories = response.xpath('//*[@id="product-categories"]/ul/li/a/@href').extract()
        for cat in categories:
            yield Request('https://www.webstaurantstore.com/restaurant-consumables.html',
                          callback=self.parse_sub_categories)

    def parse_sub_categories(self, response):
        base_url = 'http://webstaurantstore.com'
        subcategories = response.xpath('//*[@id="main"]/div[1]/div/span/span/div/a/@href').extract()
        subcategories += response.xpath('//*[@id="main"]/div[1]/div/div/div[1]/div/div[1]/a/@href').extract()
        for subcat in subcategories:
            print(subcat)
            url = "{}{}"
            yield Request(url.format(base_url, subcat), callback=self.parse_root_categories)

    def parse_root_categories(self, response):
        base_url = 'http://webstaurantstore.com'
        root_category = response.xpath('//*[@id="main"]/div[1]/div/span/span/a/@href').extract()
        root_category += response.xpath('//*[@id="main"]/div[1]/a/@href').extract()
        if root_category:
            for root in root_category:
                url = '{}{}'
                yield Request(url.format(base_url, root), callback=self.parse_products)
                yield Request(url.format(base_url, root), callback=self.parse_subroot_categories)
        else:
            yield scrapy.Request(response.url, callback=self.parse_subroot_categories)

    def parse_subroot_categories(self, response):
        subroot_categories = response.xpath('//*[@id="main"]/div[1]/div/div/a/@href').extract()
        # subroot_categories += response.xpath('//*[@id="main"]/div[1]/div/div[1]/div[1]/div/div[1]/a/@href').extract()
        for subroot in subroot_categories:
            url = '{}{}'
            base_url = 'http://webstaurantstore.com'
            yield Request(url.format(base_url, subroot), callback=self.parse_products)

    def parse_products(self,response):
        product_urls = response.xpath('//*[@id="product_listing"]//div/div/a[2]/@href').extract()
        base_url = 'http://webstaurantstore.com'
        for product_url in product_urls:
            url = '{}{}'
            yield Request(url.format(base_url, product_url), callback=self.parse_details)

        next_page = response.xpath('//*[@id="paging"]/div/ul/li[last()]/a/@href').extract_first()
        if next_page:
                url = '{}{}'
                yield Request(url.format(base_url,next_page), callback=self.parse_products)

    def parse_details(self, response):
        item = WebstaurantstoreSpiderItem()
        item['Title'] = response.xpath('//*[@id="mainProductContentContainer"]/h1/text()').extract()
        price = response.xpath('//form[@id="productform"]/input[@name="price"]/@value').extract_first()
        item['Price'] = '$' + price
        upc = response.xpath('//*[@id="page"]//span[@class="product__stat-desc"]/text()').extract_first()
        if upc:
            item['UPC'] = upc.strip('\n')
        else:
            item['UPC'] = 'NA'
        yield item



