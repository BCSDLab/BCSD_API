#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from datetime import datetime
from urllib.request import Request, urlopen

BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("SLACK_CERTBOT_CHANNEL", "")
SERVER_NAME = os.environ.get("SLACK_SERVER_NAME", "*[인터널]*")


def main():
    notify_start()
    result = renew()
    report(result)


def notify_start():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"{SERVER_NAME} :gear: Certbot 갱신 cron 작업을 시작합니다. ({timestamp})"
    send([{"type": "section", "text": {"type": "mrkdwn", "text": text}}])


def renew():
    return subprocess.run(
        ["certbot", "renew", "--webroot", "-w", "/var/www/certbot"],
        capture_output=True, text=True,
    )


def report(result):
    output = result.stdout + result.stderr
    lines = output.splitlines()
    renewed = [parse_domain(l) for l in lines if "(success)" in l]
    skipped = [parse_domain(l) for l in lines if "(skipped)" in l]
    failed = [parse_domain(l) for l in lines if "(failure)" in l]
    send(build_blocks(renewed, skipped, failed))


def parse_domain(line):
    return line.split("/")[-2]


def build_blocks(renewed, skipped, failed):
    if not renewed and not skipped and not failed:
        text = f"{SERVER_NAME} :information_source: 처리할 인증서가 없습니다."
        return [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]
    title = f"{SERVER_NAME} :heavy_check_mark: Certbot 갱신 작업 결과"
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": title}}]
    if renewed:
        blocks.extend(list_block("갱신 성공", ":sparkles:", renewed))
    if skipped:
        blocks.extend(list_block("갱신 건너뜀", ":fast_forward:", skipped))
    if failed:
        blocks.extend(list_block("갱신 실패", ":warning:", failed))
    return blocks


def list_block(title, emoji, domains):
    elements = [
        {"type": "rich_text_section", "elements": [{"type": "text", "text": d}]}
        for d in domains
    ]
    return [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"{emoji} *{title}*"}},
        {"type": "rich_text", "elements": [{"type": "rich_text_list", "style": "bullet", "elements": elements}]},
    ]


def send(blocks):
    if not BOT_TOKEN or not CHANNEL_ID:
        return
    payload = json.dumps({"channel": CHANNEL_ID, "blocks": blocks}).encode()
    headers = {
        "Authorization": f"Bearer {BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    req = Request("https://slack.com/api/chat.postMessage", data=payload, headers=headers)
    try:
        urlopen(req, timeout=10)
    except Exception as exc:
        print(f"Slack failed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
