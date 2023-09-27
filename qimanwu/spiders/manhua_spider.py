import json
import re
from ..settings import *
from typing import Any
from ..items import *
from scrapy import FormRequest, Request, Spider


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
        urls = response.xpath('//div[@class="catalog-list"]/ul/li').re(r"href=\".*?\"")
        url_num = len(urls)
        start_index = int(response.meta['startindex'])
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
        response = json.loads(response.text)
        k = 0
        yield Request(kwargs['chapter_path'], callback=self.parse_index, meta={'startindex': len(response)})
        for index in response:
            k += 1
            new_url = kwargs['chapter_path'] + index["id"] + ".html"
            yield Request(url=new_url, callback=self.parse_chapter,
                          meta={'chapter_name': ("%05d" % (len(response) - k + 1)) + "_" + index["name"]},
                          cb_kwargs={'manhua_id': kwargs['manhua_id'], 'manhua_name': kwargs['manhua_name']})

    # 获取并解析漫画网页顺序
    def parse_chapter(self, response, **kwargs):
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
            item = ImageSpiderItem()
            item['url'] = rel_url
            item['name'] = "%05d" % index
            item['chapter_name'] = response.meta['chapter_name']
            item['manhua_id'] = kwargs['manhua_id']
            item['manhua_name'] = kwargs['manhua_name']
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
