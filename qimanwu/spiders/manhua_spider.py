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
        for manhua_id, manhua_name in MANHUA_ITEMS.items():
            manhua_id = manhua_id
            chapter_path = BASE_URL + manhua_id + '/'
            # 获取作品的隐藏章节
            yield FormRequest(url=MANHUA_CHAPTERS, formdata={"id": manhua_id, "id2": "1"},
                              callback=self.parse, cb_kwargs={'manhua_id': manhua_id, 'manhua_name': manhua_name,
                                                              'chapter_path': chapter_path})

    def parse_index(self, response, **kwargs):
        """
        处理漫画作品中的所有显示章节，将章节地址传给self.parse_chapter，获取章节内的图片
        :param response: 访问漫画作品首页的响应
        :return:
        """
        urls = response.xpath('//div[@class="catalog-list"]/ul/li').re(r"href=\".*?\"")
        url_num = len(urls)
        start_index = int(response.meta['start_index'])
        start_index += url_num
        for i in range(url_num):
            urls[i] = urls[i][6: -1]
        names = response.xpath('//div[@class="catalog-list"]/ul/li/a').re(r">.*?<")
        for i in range(len(names)):
            names[i] = names[i][1: -1]

        for i in range(len(urls)):
            chapter_id = urls[i][len(kwargs['manhua_id']) + 2:-5]
            yield Request(BASE_URL + urls[i], callback=self.parse_chapter,
                          meta={'chapter_name': ("%05d" % start_index) + "_" + names[i]},
                          cb_kwargs={'manhua_id': kwargs['manhua_id'], 'manhua_name': kwargs['manhua_name'],
                                     'chapter_id': chapter_id, 'chapter_name': names[i], 'index_num': start_index})
            start_index -= 1

    def parse(self, response, **kwargs):
        """
        处理漫画作品中的所有隐藏章节，将章节地址传给self.parse_chapter，获取章节内的图片
        :param response: 获取漫画隐藏章节的响应
        :param kwargs: 字典，包括漫画的id、名字、首页地址
        :return:
        """
        response = json.loads(response.text)
        chapter_nums = len(response)
        k = 0
        yield Request(kwargs['chapter_path'], callback=self.parse_index, meta={'start_index': len(response)},
                      cb_kwargs={'manhua_id': kwargs['manhua_id'], 'manhua_name': kwargs['manhua_name']})
        for index in response:
            k += 1
            new_url = kwargs['chapter_path'] + index["id"] + ".html"
            index_num = chapter_nums - k + 1
            yield Request(url=new_url, callback=self.parse_chapter,
                          meta={'chapter_name': ("%05d" % index_num) + "_" + index["name"]},
                          cb_kwargs={'manhua_id': kwargs['manhua_id'], 'manhua_name': kwargs['manhua_name'],
                                     'chapter_id': index["id"], 'chapter_name': index["name"], 'index_num': index_num})

    # 获取并解析漫画网页顺序
    def parse_chapter(self, response, **kwargs):
        chapter_item = ChapterItem()
        chapter_item['manhua_id'] = kwargs['manhua_id']
        chapter_item['chapter_id'] = kwargs['chapter_id']
        chapter_item['index_num'] = kwargs['index_num']
        chapter_item['name'] = kwargs['chapter_name']
        chapter_item['url'] = response.url.replace(BASE_URL, '')
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
            item['chapter_id'] = kwargs['chapter_id']
            item['chapter_name'] = kwargs['chapter_name']
            item['name'] = "%03d" % index
            item['index_num'] = index
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
