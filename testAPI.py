#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Created by lashkov on 24.05.2023"""
import base64

import requests as r
BASE_URL = "http://127.0.0.1:8080"

resp = r.post(BASE_URL+'/add_user', json={"name":"Вася"})
print(resp.status_code)
print(resp.json())
j = resp.json()
user_id = j['id']
user_token = j['token']

with open('test.wav', 'rb') as f:
    sound = f.read()

resp = r.post(BASE_URL+'/add_wav', json={"user_id": user_id,
                                         "user_token": user_token,
                                         "wav": base64.b64encode(sound).decode()})
print(resp.status_code)
print(resp.text)

