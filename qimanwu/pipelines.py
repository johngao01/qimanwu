# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import cx_Oracle
from scrapy.exceptions import DropItem

from .items import *


class QimanwuPipeline:
    def process_item(self, item, spider):
        return item


class OraclePipeline:
    def __init__(self, dsn, user, password):
        self.dsn = dsn
        self.user = user
        self.password = password

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        dsn = settings.get('DSN')
        user = settings.get('USER')
        password = settings.get('PASSWORD')
        return cls(dsn, user, password)

    def open_spider(self, spider):
        self.conn = cx_Oracle.connect(self.user, self.password, self.dsn)
        self.cursor = self.conn.cursor()

    def close_spider(self, spider):
        self.cursor.close()
        self.conn.close()

    def process_item(self, item, spider):
        try:
            # 插入数据到Oracle数据库
            if isinstance(item, ChapterItem):
                self.cursor.execute(
                    "INSERT INTO CHAPTER (manhua_id, chapter_id, index_num, name, url) VALUES (:1, :2, :3, :4, :5)",
                    (item['manhua_id'], item['chapter_id'], item['index_num'], item['name'], item['url'])
                )
            elif isinstance(item, ContentItem):
                self.cursor.execute(
                    "INSERT INTO CONTENT (manhua_id, chapter_id, index_num, name, url) VALUES (:1, :2, :3, :4, :5)",
                    (item['manhua_id'], item['chapter_id'], item['index_num'], item['name'], item['url'])
                )
            else:
                return item
            self.conn.commit()
        except cx_Oracle.DatabaseError as e:
            # 处理插入失败的情况
            self.conn.rollback()
            print(e)
            raise DropItem(f"Failed to insert item into Oracle: {str(e)}")

        return item
