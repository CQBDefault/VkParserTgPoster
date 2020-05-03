
# -*- coding: utf-8 -*-

import os
import sys
import vk_api
import telebot
import configparser
import logging
from time import sleep
from telebot.types import InputMediaPhoto

# Считываем настройки
config_path = os.path.join(sys.path[0], 'settings.ini')
config = configparser.ConfigParser()
config.read(config_path)
LOGIN = config.get('VK', 'LOGIN')
PASSWORD = config.get('VK', 'PASSWORD')
DOMAIN = config.get('VK', 'DOMAIN')
COUNT = config.get('VK', 'COUNT')
VK_TOKEN = config.get('VK', 'TOKEN', fallback=None)
BOT_TOKEN = config.get('Telegram', 'BOT_TOKEN')
CHANNEL = config.get('Telegram', 'CHANNEL')
INCLUDE_LINK = config.getboolean('Settings', 'INCLUDE_LINK')
PREVIEW_LINK = config.getboolean('Settings', 'PREVIEW_LINK')


message_breakers = [':', ' ', '\n']
max_message_length = 4091

bot = telebot.TeleBot(BOT_TOKEN)


# Получаем данные из vk.com
def get(domain_vk, count_vk):
	global LOGIN
	global PASSWORD
	global VK_TOKEN
	global config
	global config_path

	# подключаемся к ВК и получаем токен
	if VK_TOKEN is not None:
		vk_session = vk_api.VkApi(LOGIN, PASSWORD, VK_TOKEN)
		vk_session.auth(token_only=True)
	else:
		vk_session = vk_api.VkApi(LOGIN, PASSWORD)
		vk_session.auth()

	new_token = vk_session.token['access_token']

	# записываем токен в конфиг
	if VK_TOKEN != new_token:
		VK_TOKEN = new_token
		config.set('VK', 'TOKEN', new_token)
		with open(config_path, "w") as config_file:
			config.write(config_file)

	vk = vk_session.get_api()

	# Используем метод wall.get из документации по API vk.com
	response = vk.wall.get(domain=domain_vk, count=count_vk)

	return response


# Проверяем данные по условиям перед отправкой
def check():
	global DOMAIN
	global COUNT
	global INCLUDE_LINK
	global bot
	global config
	global config_path

	response = get(DOMAIN, COUNT)
	response = reversed(response['items'])

	for post in response:

		# читаем последний известный id из файла
		id = config.get('Settings', 'LAST_ID')

		# сравниваем id, пропускаем уже опубликованные
		if int(post['id']) <= int(id):
			continue

		print('------------------------------------------------------------------------------------------------')
		print(post)

		# текст
		text = post['text']

		# проверяем есть ли что то прикрепленное к посту
		images = []
		links = []
		attachments = []
		if 'attachments' in post:
			attach = post['attachments']
			for add in attach:
				if add['type'] == 'photo':
					img = add['photo']
					images.append(img)
				elif add['type'] == 'audio':
					continue
				elif add['type'] == 'video':
					video = add['video']
					if 'player' in video:
						links.append(video['player'])
				else:
					for (key, value) in add.items():
						if key != 'type' and 'url' in value:
							attachments.append(value['url'])

		# прикрепляем ссылку на пост, если INCLUDE_LINK = true в конфиге
		if INCLUDE_LINK:
			post_url = "https://vk.com/" + DOMAIN + "?w=wall" + \
				str(post['owner_id']) + '_' + str(post['id'])
			links.insert(0, post_url)

		text = '\n'.join([text] + links)


		# если картинка будет одна, то прикрепим её к посту, как ссылку
		if len(images) == 1:
			image_url = str(max(img["sizes"], key=lambda size: size["type"])["url"])

			bot.send_message(CHANNEL, '<a href="' + image_url + '">⁠</a>' + text, parse_mode='HTML')

		# если их несколько, то текст отправим в одном посте, картинки - в другом
		elif len(images) > 1:
			image_urls = list(map(lambda img: max(
				img["sizes"], key=lambda size: size["type"])["url"], images))
			print(image_urls)

			send_text(text)

			bot.send_media_group(CHANNEL, map(lambda url: InputMediaPhoto(url), image_urls))
		else:
			send_text(text)

		# проверяем есть ли репост другой записи
		if 'copy_history' in post:
			copy_history = post['copy_history']
			copy_history = copy_history[0]
			print('--copy_history--')
			print(copy_history)
			text = copy_history['text']
			send_text(text)

			# проверяем есть ли у репоста прикрепленное сообщение
			if 'attachments' in copy_history:
				copy_add = copy_history['attachments']
				copy_add = copy_add[0]

				# если это картинки
				if copy_add['type'] == 'photo':
					attach = copy_history['attachments']
					for img in attach:
						image = img['photo']
						send_img(image)

		# записываем id в файл
		config.set('Settings', 'LAST_ID', str(post['id']))
		with open(config_path, "w") as config_file:
			config.write(config_file)


# отправляем посты в телеграмм

# текст
def send_text(text):
	global CHANNEL
	global PREVIEW_LINK
	global bot

	if text == '':
		print('without text')
	else:
		# в телеграмме есть ограничения на длину одного сообщения в 4091 символ, разбиваем длинные сообщения на части
		for msg in split(text):
			bot.send_message(CHANNEL, msg, disable_web_page_preview=not PREVIEW_LINK)


# разделитель
def split(text):
	global message_breakers
	global max_message_length

	if len(text) >= max_message_length:
		last_index = max(
			map(lambda separator: text.rfind(separator, 0, max_message_length), message_breakers))
		good_part = text[:last_index]
		bad_part = text[last_index + 1:]
		return [good_part] + split(bad_part)
	else:
		return [text]


# Отправка изображений
def send_img(img):
	global bot

	# Находим картинку с максимальным качеством
	url = max(img["sizes"], key=lambda size: size["type"])["url"]
	bot.send_photo(CHANNEL, url)


# RUN
if __name__ == '__main__':
	check()
	while True:
		sleep(60)
		check()
