# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class QimanwuItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class ImageSpiderItem(scrapy.Item):
    # Field类仅是内置字典类（dict）的一个别名，并没有提供额外的方法和属性。
    # 被用来基于类属性的方法来支持item生命语法。
    url = scrapy.Field()
    name = scrapy.Field()
    chapter_name = scrapy.Field()
    manhua_id = scrapy.Field()
    manhua_name = scrapy.Field()
