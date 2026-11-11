#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Notification Olvid - s'execute DANS le conteneur train-alert-bot-1.

Appel : docker exec -i -e OLVID_DISCUSSION_ID=... -e MSG_BODY=... \
            train-alert-bot-1 python - < notify_olvid.py

Le conteneur fournit deja OLVID_CLIENT_KEY / OLVID_DAEMON_URL (SDK
olvid-bot 2.0.1, daemon :50051 du stack train-alert). Le script est
injecte par stdin, aucune modification du conteneur n'est necessaire.
"""

import asyncio
import os
import sys


async def main():
    from olvid import OlvidClient
    body = os.environ.get("MSG_BODY", "")
    discussion_id = int(os.environ.get("OLVID_DISCUSSION_ID", "0"))
    if not body or not discussion_id:
        print("MSG_BODY ou OLVID_DISCUSSION_ID manquant", file=sys.stderr)
        return 2
    client = OlvidClient()
    msg = await client.message_send(discussion_id=discussion_id, body=body)
    print(f"SEND_OK message_id={msg.id if hasattr(msg, 'id') else '?'}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
