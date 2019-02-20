# -*- coding: utf-8 -*-
import json
import re

import scrapy
from scrapy import Selector
from destinationxl_spider.items import DestinationxlSpiderItem




class DestinationxlSpider(scrapy.Spider):
    name = 'destinationxl'
    allowed_domains = ['www.destinationxl.com']
    start_urls = ['http://www.destinationxl.com/mens-big-and-tall-store/']


    def parse(self, response):
        all_categories_url = response.xpath('//header/nav/ul//li//a/@href').extract()
        for category in all_categories_url:
            if 'athletic-fit-mens-jeans' in category:
                yield response.follow(category, callback=self.parse_all_pages)


    def parse_all_pages(self, response):
        script = response.css('script#dxl-state').extract_first()
        get_script = script.split('<script id="dxl-state" type="application/json">')[1]
        clean_data = get_script.strip('</script>')
        category = clean_data.replace('&q;', '"')
        data = json.loads(category)
        try:
            data_keys = data['plpResponse']['contents'][0]['SecondaryContent'][1]['' \
                                'contents'][0]['navigation']
        except IndexError:
            data_keys = None

        if data_keys:
            for raw_keys in data_keys:
                if 'refinements' not in raw_keys.keys():
                    return
                for keys in raw_keys['refinements']:
                    product_url = '{}{}'
                    url_n = keys['navigationState'].split('&')[0]
                    url = url_n.split('+')[0]

                    yield scrapy.Request(product_url.format(response.url, url),
                                         callback=self.parse_products)

    def parse_products(self, response):
        base_url = 'http://www.destinationxl.com'
        product_urls = response.css('.switch-hover a::attr(href)').extract()

        for product_url in product_urls:
            url = '{}{}'.format(base_url, product_url)
            yield scrapy.Request(url, callback=self.parse_item)

        if self.parse_next_url(response) != 0:
            for no_of_products in range(30, (self.parse_next_url(response)-1) * 30, 30):
                if no_of_products == 90:
                    break
                if self.parse_next_url(response) != 0:
                    if '&' in response.url:
                        next_url = response.url.split('&')[0]
                        url = '{}&No={}'.format(next_url, no_of_products)
                        yield scrapy.Request(url, callback=self.parse_products)
                    else:
                        url = '{}&No={}'.format(response.url, no_of_products)
                        yield scrapy.Request(url, callback=self.parse_products)

    def parse_item(self, response):
        item = DestinationxlSpiderItem()
        page_url = response.url
        item['page_url'] = page_url
        item['category'] = self.get_item_categroy(response)
        item_url = 'https://www.destinationxl.com/public/v1/dxlproducts/{}/{}'

        url = item_url.format(response.url.split('/')[-2], response.url.split('/')[-1])

        yield scrapy.Request(url, meta={'item': item}, callback=self.parse_combinations)

    def parse_combinations(self, response):
        item = response.meta['item']
        size_and_color = json.loads(response.text)
        description = []
        text = Selector(text=size_and_color['longDescription'])
        details = text.css('p::text').extract()
        lists = [[x] for x in details]
        description.append(lists)
        price = size_and_color['price']
        original_price = price['originalPrice']
        if bool(price['onSale']):
            sale_price = price['salePrice']
            on_sale = price['saleMessage']
        else:
            sale_price = None
            on_sale = False

        item['original_price'] = original_price
        item['sale_price'] = sale_price
        item['on_sale'] = on_sale
        item['description'] = description
        item['image_url'] = self.get_image_url(response)

        c_url = '{}?&isSelection=True&attributes=color={}'
        for colors in size_and_color['colorGroups']:
            for color_id in colors['colors']:
                url = c_url.format(response.url, color_id['id'])
                yield scrapy.Request(url, callback=self.get_size, meta=response.meta)


    def get_size(self, response):

        data = json.loads(response.text)
        item = response.meta['item']
        parts = response.url.split('/')[7]
        product_id = parts.split('?')[0]
        color_code = response.url.split('=')[3]
        sku = '{}_{}'.format(product_id, color_code)
        item['sku'] = sku
        if len(data['sizes']) > 1:
            item['info'] = []
            item['requests'] = {'requests': self.get_requests(response)}
        else:
            item['info'] = self.get_infos(response)
        return self.next_url(item)

    def get_requests(self, response):
        raw_product = json.loads(response.text)
        requests = []
        for size in raw_product['sizes'][0]['values']:
            if bool(size['available']):
                sizes_url = scrapy.Request('{}@{}Size={}'.format(response.url, raw_product['sizes']
                                                                 [0]['displayName'], size['name']),
                                           meta={'size': size['name']}, callback=self.parse_sizes)
                requests.append(sizes_url)
        return requests

    def get_infos(self, response):
        infos = []
        requests = []
        data = json.loads(response.text)
        if len(data['sizes']) > 0:
            for size in data['sizes'][0]['values']:
                combinations = {'size_identifier': size['name'],
                                'size_name': size['name']
                                }
                if bool(size['available']):
                    sizes_url = scrapy.Request('{}@{}Size={}'.format(response.url, data['sizes'][0]
                                                                     ['displayName'], size['name']),
                                               meta={'size': size['name']}, callback=self.parse_sizes)
                    requests.append(sizes_url)
                infos.append(combinations)
            return requests
        return infos

    def parse_sizes(self, response):
        data = json.loads(response.text)
        item = response.meta['item']
        sizes = data['sizes'][1]
        for size in sizes['values']:
            if bool(size['available']):
                size_name = {sizes['displayName']: size['name'],
                             data['sizes'][0]['displayName']: response.meta['size']
                             }

                combinations = {'size_name': size_name}
                item['info'].append(combinations)

        return self.next_url(item.copy())

    def next_url(self, item):
        if item['requests'].get('requests'):
            url = item['requests']['requests'].pop(0)
            url.meta['item'] = item
            return url
        del item['requests']
        return item

    def parse_next_url(self, response):
        no_of_pages = response.xpath('//*[contains(@class,"page-nos")]/span[last()-1]//text()')\
                                        .extract_first()
        if no_of_pages and no_of_pages != '' and no_of_pages != '...':
            return int(no_of_pages)
        else:
            return 0

    def get_image_url(self, response):
        data = json.loads(response.text)
        image_url = []
        image = data['colorGroups'][0]['colors'][0]['largeSwatchImageUrl']
        zoomed_url = image[:-17]
        image_url.append(zoomed_url)
        image_id = re.findall(r'([0-9]+)', image)
        for images in range(1, data['alternateImagesCount']+1):
            url = '{}{}_alt{}'.format(zoomed_url.split(image_id[0])[0], image_id[0], images)
            image_url.append(url)
        return image_url

    def get_item_categroy(self, response):
        category = response.xpath('//breadcrumb/nav/ul//li//text()').extract()[1:]
        category = [cat.strip('//') for cat in category]
        category = [i for i in category if i != ' ']
        return category

