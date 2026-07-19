#!/usr/bin/env python3
import json
import os
import requests


def main() -> int:
    key = os.getenv('GEMINI_API_KEY', '')
    if not key:
        print('FAIL: GEMINI_API_KEY not set')
        return 1

    model = 'gemini-2.0-flash'
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    headers = {
        'x-goog-api-key': key,
        'content-type': 'application/json',
    }
    payload = {
        'contents': [{'parts': [{'text': 'Return exactly {"ok":true}'}]}],
        'generationConfig': {'maxOutputTokens': 64},
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        print('FAIL:', e)
        return 1

    if resp.status_code != 200:
        print('FAIL: status', resp.status_code)
        print(resp.text)
        return 1

    print('PASS: LLM reachable')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
