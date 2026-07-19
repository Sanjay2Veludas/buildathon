#!/usr/bin/env python3
import subprocess


def main() -> int:
    text = 'Audio output test from AI sentry.'
    synth = subprocess.run(['espeak-ng', '-w', '/tmp/test_tts.wav', text], check=False)
    if synth.returncode != 0:
        print('FAIL: espeak-ng synthesis failed')
        return 1

    play = subprocess.run(['aplay', '/tmp/test_tts.wav'], check=False)
    if play.returncode != 0:
        print('FAIL: aplay failed')
        return 1

    print('PASS: audio output path OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
