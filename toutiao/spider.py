import requests
from requests.exceptions import RequestException
import json
from datetime import datetime
import re
import pymongo
from multiprocessing import Pool
from config import *

client = pymongo.MongoClient(IP, PORT)
db = client[DB]
table = db[TABLE]


def get_page_html(offset):
	try:
		headers = {
			'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/63.0.3239.84 Chrome/63.0.3239.84 Safari/537.36'
		}
		params = {
			'offset': offset,
			'format': 'json',
			'keyword': '街拍',
			'autoload': 'true',
			'count': 20,
			'cur_tab': 3,
			'from': 'gallery'
		}
		url = 'https://www.toutiao.com/search_content/'
		response = requests.get(url, headers=headers, params=params)
		if response.status_code == 200:
			return response.text
		return None
	except RequestException:
		return None

def get_urls(html):
	data = json.loads(html)
	if data and 'data' in data.keys():
		for item in data['data']:
			data =  {
				'title': item['title'],
				'url': item['url'],
				'media_name': item['media_name'],
				'publish_time': str(datetime.fromtimestamp(item['publish_time'])),
			}
			pics = parse_pics(data['url'])
			data['images'] = pics
			save_to_mongo(data)

def save_to_mongo(data):
	try:
		table.update(data, {"$set":{'title': data['title']}}, upsert=True)
		print('save to mongo success', data)
	except Exception:
		print('save to mongo fail', data)

def parse_pics(url):
	try:
		headers = {
				'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/63.0.3239.84 Chrome/63.0.3239.84 Safari/537.36'
			}
		response = requests.get(url, headers=headers)
		images = []
		if response.status_code == 200:
			html = response.text
			pattern = re.compile(r'gallery: JSON.parse\("(.*?)"\),', re.S)
			if re.search(pattern, html):
				pics_raw = re.search(pattern, html).group(1)
				pics = re.sub(r'\\', '', pics_raw)
				pics_data = json.loads(pics)
				for item in pics_data['sub_images']:
					images.append(item['url'])
				return images
			return None
		else:
			print('failed to open the page: ', url)
	except RequestException:
		return None


def main(i):
	html = get_page_html(i)
	get_urls(html)
		

if __name__ == '__main__':
	pool = Pool()
	pool.map(main, [i*20 for i in range(10)])