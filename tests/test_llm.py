#!/usr/bin/env python3
import os
import requests


def main() -> int:
    key = os.getenv('ANTHROPIC_API_KEY', '')
    if not key:
      print('FAIL: ANTHROPIC_API_KEY not set')
      return 1

    headers = {
        'x-api-key': key,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
    }
    payload = {
        'model': 'claude-3-5-sonnet-latest',
        'max_tokens': 64,
        'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': 'Return exactly {"ok":true}'}]}],
    }

    try:
        resp = requests.post('https://api.anthropic.com/v1/messages', headers=headers, json=payload, timeout=10)
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
