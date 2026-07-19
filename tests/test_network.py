#!/usr/bin/env python3
import socket


def main() -> int:
    try:
        sock = socket.create_connection(('api.anthropic.com', 443), timeout=3)
        sock.close()
        print('PASS: network path to api.anthropic.com:443')
        return 0
    except OSError as e:
        print('FAIL:', e)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
