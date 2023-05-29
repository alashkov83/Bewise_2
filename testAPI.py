#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Created by lashkov on 24.05.2023"""
import argparse
import base64
from typing import NoReturn, IO

import requests as r

BASE_URL: str = "http://127.0.0.1:8080"

parser: argparse.ArgumentParser = argparse.ArgumentParser(prog='TestPiggSoundAPI',
                                                          description='There is program for PigWav service')
parser.add_argument('-m', '--mode', choices=['reg_user', 'wav_upload', 'mp3_download'], help='Режим работы')
parser.add_argument('-i', '--input', type=argparse.FileType('rb'), help="Имя входного файла")
parser.add_argument('-u', '--user', default='user', help='Имя пользователя')
parser.add_argument('-d', '--user_id', default=0, type=int, help='ID пользователя')
parser.add_argument('-t', '--token', default='', help='Токен доступа или ID записи (uuid)')
parser.add_argument('-o', '--output', default='output.txt', help='Имя выходного файла')
parser.add_argument('-a', '--address', default=BASE_URL, help='URI скачивания (для режима mp3_download)'
                                                              ' или базовый адрес сервиса')


def add_user(url: str, user_name: str) -> NoReturn:
    resp = r.post(url + '/add_user', json={"name": user_name})
    if resp.ok:
        if resp.headers.get('Content-Type', '') == 'application/json':
            j = resp.json()
            user_id = j.get('id', 'unknown')
            user_token = j.get('token', 'unknown')
            print(f"User ID: {user_id}\nToken: {user_token}")
        else:
            print('Invalid Content-Type')
    else:
        print(f'Status code: {resp.status_code}, reason: {resp.reason}')


def add_wav(url: str, user_id: int, user_token: str, file: IO) -> NoReturn:
    try:
        sound = file.read()
    except PermissionError:
        print('Permission denied!')
    else:
        resp: r.Response = r.post(url + '/add_wav', json={"user_id": user_id,
                                                          "user_token": user_token,
                                                          "wav": base64.b64encode(sound).decode()})
        if resp.ok:
            print(f'Download link: {resp.text}')
        else:
            print(f'Status code: {resp.status_code}, reason: {resp.reason}')
    finally:
        file.close()


def download_mp3(url: str, file: str) -> NoReturn:
    resp = r.get(url)
    if resp.ok:
        try:
            with open(file, 'wb') as f:
                f.write(resp.content)
        except (FileNotFoundError, PermissionError, IOError) as e:
            print(e)
    else:
        print(f'Status code: {resp.status_code}, reason: {resp.reason}')


if __name__ == '__main__':
    args = parser.parse_args()
    url: str = args.address
    try:
        if args.mode == 'reg_user':
            add_user(url, args.user)
        elif args.mode == 'wav_upload':
            if args.input:
                add_wav(url, args.user_id, args.token, args.input)
        elif args.mode == 'mp3_download':
            if args.output:
                download_mp3(url, args.output)
        else:
            print("Unknown mode!")
    except ConnectionError as e:
        print(e)
