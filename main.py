import logging
import os

import requests

from random import randint

from dotenv import load_dotenv
from requests.exceptions import HTTPError


logger = logging.getLogger('logger_main')


def raise_vk_exception(response):
    if 'error' in response:
        message = (
            f'Error code - {response["error"]["error_code"]}, '
            f'{response["error"]["error_msg"]}'
        )
        raise requests.exceptions.HTTPError(message)


def load_photo(url, file_name, params=None):
    response = requests.get(url=url, params=params)
    response.raise_for_status()
    with open(file_name, mode='wb') as file:
        file.write(response.content)
    logger.info(f'Download comic to {file_name}')
    return file_name


def get_commic(comic_num):
    response = requests.get(f'https://xkcd.com/{comic_num}/info.0.json')
    response.raise_for_status()
    comic = response.json()
    return comic['alt'], comic['img']


def get_upload_addr(vk_app_token, owner_id):
    payload = {
        'access_token': vk_app_token,
        'group_id': owner_id,
        'v': 5.81
    }
    response = requests.post(
        'https://api.vk.com/method/photos.getWallUploadServer',
        data=payload
        )
    response.raise_for_status()
    raise_vk_exception(response.json())
    logger.info('Get addr for load comic')
    return response.json()


def upload_photo(url, vk_app_token, owner_id, file_name):
    with open(file_name, 'rb') as file:
        payload = {
            'photo': file
        }
        response = requests.post(url, files=payload)
    response.raise_for_status()
    raise_vk_exception(response.json())
    return response.json()


def save_photo(vk_app_token, owner_id, photo, server, photo_hash, caption='caption'):
    payload = {
        'access_token': vk_app_token,
        'group_id': owner_id,
        'photo': photo,
        'server': server,
        'hash': photo_hash,
        'caption': caption,
        'v': 5.81
    }
    response = requests.post(
        'https://api.vk.com/method/photos.saveWallPhoto',
        data=payload
        )
    response.raise_for_status()
    raise_vk_exception(response.json())
    return response.json()


def publish_message(vk_app_token, owner_id, media_owner, media_id, text):
    payload = {
        'access_token': vk_app_token,
        'owner_id': f'-{owner_id}',
        'from_group': 0,
        'attachments': f'photo{media_owner}_{media_id}',
        'message': text,
        'v': 5.81
    }
    response = requests.post(
        'https://api.vk.com/method/wall.post',
        data=payload
        )
    response.raise_for_status()
    raise_vk_exception(response.json())
    return response.json()['response']['post_id']


def remove_photo(file_name):
    if os.path.isfile(file_name):
        os.remove(file_name)
        logger.info(f'Remove {file_name}')


def get_last_comic_number():
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()['num']


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    load_dotenv()
    vk_app_token = os.environ.get('VK_APP_TOKEN')
    vk_group_id = os.environ.get('VK_GROUP_ID')
    folder = os.path.join(os.getcwd(), 'Files')
    os.makedirs(folder, exist_ok=True)
    comic_num = randint(0, get_last_comic_number())
    alt, url = get_commic(comic_num)
    file_name = os.path.join(folder, url.split('/')[-1])
    load_photo(url, file_name)
    try:
        upload_address = get_upload_addr(vk_app_token, vk_group_id)
        photo = upload_photo(
            upload_address['response']['upload_url'],
            vk_app_token,
            vk_group_id,
            file_name
            )
        photo = save_photo(
            vk_app_token,
            vk_group_id,
            photo['photo'],
            photo['server'],
            photo['hash'])
        message_id = publish_message(
            vk_app_token,
            vk_group_id,
            photo['response'][0]['owner_id'],
            photo['response'][0]['id'],
            alt
            )
        logger.info(f'Posted message {message_id}')
    except HTTPError as err:
        logger.error(err)
    finally:
        remove_photo(file_name)


if __name__ == '__main__':
    main()
