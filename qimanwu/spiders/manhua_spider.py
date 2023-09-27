import json
import re
from typing import Any

from scrapy import FormRequest, Request, Spider

from ..items import *
from ..settings import *


class ManhuaSpider(Spider):
    name = 'manhua'

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    def start_requests(self):
        for manhua_id, manhua_name in manhua_items.items():
            manhua_id = manhua_id
            chapter_path = base_url + manhua_id + '/'
            # 获取作品的隐藏章节
            yield FormRequest(url=manhua_chapters, formdata={"id": manhua_id, "id2": "1"},
                              callback=self.parse, cb_kwargs={'manhua_id': manhua_id, 'manhua_name': manhua_name,
                                                              'chapter_path': chapter_path})

    def parse_index(self, response):
        """
        处理漫画作品中的所有显示章节，将章节地址传给self.parse_chapter，获取章节内的图片
        :param response: 访问漫画作品首页的响应
        :return:
        """
        urls = response.xpath('//div[@class="catalog-list"]/ul/li').re(r"href=\".*?\"")
        url_num = len(urls)
        start_index = int(response.meta['start_index'])
        start_index += url_num
        for i in range(len(urls)):
            urls[i] = urls[i][6: -1]
        names = response.xpath('//div[@class="catalog-list"]/ul/li/a').re(r">.*?<")
        for i in range(len(names)):
            names[i] = names[i][1: -1]

        for i in range(len(urls)):
            yield Request(base_url + urls[i], callback=self.parse_chapter,
                          meta={'chapter_name': ("%05d" % start_index) + "_" + names[i]})
            start_index -= 1

    def parse(self, response, **kwargs):
        """
        处理漫画作品中的所有隐藏章节，将章节地址传给self.parse_chapter，获取章节内的图片
        :param response: 获取漫画隐藏章节的响应
        :param kwargs: 字典，包括漫画的id、名字、首页地址
        :return:
        """
        response = json.loads(response.text)
        k = 0
        yield Request(kwargs['chapter_path'], callback=self.parse_index, meta={'start_index': len(response)})
        for index in response:
            k += 1
            new_url = kwargs['chapter_path'] + index["id"] + ".html"
            yield Request(url=new_url, callback=self.parse_chapter,
                          meta={'chapter_name': ("%05d" % (len(response) - k + 1)) + "_" + index["name"]},
                          cb_kwargs={'manhua_id': kwargs['manhua_id'], 'manhua_name': kwargs['manhua_name'],
                                     'chapter_id': index["id"], 'chapter_name': index["name"]})

    # 获取并解析漫画网页顺序
    def parse_chapter(self, response, **kwargs):
        chapter_item = ChapterItem()
        chapter_item['manhua_id'] = kwargs['manhua_id']
        chapter_item['chapter_id'] = kwargs['chapter_id']
        chapter_item['name'] = kwargs['chapter_name']
        chapter_item['url'] = response.url.replace(base_url, '')
        yield chapter_item
        urls = ''
        vals = []
        for sel in response.xpath('//script').re(r'\[.*?\]'):
            if len(sel) > 30:
                urls = sel
        for sel in response.xpath('//script').re(r',\'.*?\''):
            if len(sel) > 30:
                vals = sel.split("|")
        len_val = len(vals)
        vals[0] = vals[0][2:]
        vals[len_val - 1] = vals[len_val - 1][:-2]
        pattern = re.compile(r"\".*?\"")
        urls = pattern.findall(urls)
        for i in range(len(urls)):
            urls[i] = urls[i][1:-1]
        index = 1
        for url in urls:
            rel_url = ""
            for i in url:
                if not self.need_change(i):
                    rel_url = rel_url + i
                elif self.char2num(i) < len_val:
                    if vals[self.char2num(i)] != "":
                        rel_url = rel_url + vals[self.char2num(i)]
                    else:
                        rel_url = rel_url + i
                else:
                    rel_url = rel_url + i
            item = ContentItem()
            item['manhua_id'] = kwargs['manhua_id']
            item['manhua_name'] = kwargs['manhua_name']
            item['chapter_id'] = response.meta['chapter_id']
            item['chapter_name'] = response.meta['chapter_name']
            item['name'] = "%04d" % index
            item['url'] = rel_url
            index += 1
            yield item

    @staticmethod
    def need_change(data):
        if '9' >= data >= "0":
            return True
        elif 'z' >= data >= "a":
            return True
        else:
            return False

    @staticmethod
    def char2num(data):
        if '9' >= data >= "0":
            return ord(data) - ord('0')
        else:
            return ord(data) - ord('a') + 10
