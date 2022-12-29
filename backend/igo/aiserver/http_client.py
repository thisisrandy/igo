import asyncio
from igo.game import GameStatus
import logging
from tornado.options import define, options
from igo.gameserver.containers import ClientData, KeyPair
from tornado.httpclient import AsyncHTTPClient, HTTPResponse
import re
from typing import Optional, Dict
from asyncio import Lock

define(
    "ai_server_url",
    default="http://localhost:1918",
    help="the url of the AI server",
    type=str,
)

SLEEP_FOR = 2
_client = AsyncHTTPClient()
_xsrf_headers: Optional[Dict[str, str]] = None
_xsrf_lock: Lock = Lock()

__all__ = ("start_ai_player",)


async def start_ai_player(
    keys: KeyPair,
    just_once: bool = False,
    previous_subscription: Optional[ClientData] = None,
) -> None:
    """
    This is the client's method to initiate communication with the AI server. It
    will try continuously to successfully POST to the AI server's http listener
    unless `just_once`, in which case it will re-raise any exceptions on
    failure. If `previous_subscription` is provided, check whether the previous
    subscription should really have been ended. If so, we do nothing, and
    otherwise (as would be the case if an AI server failed or network problems
    were encountered) attempt to reconnect
    """

    global _xsrf_headers
    assert keys.ai_secret, "Cannot start an AI player without their secret"

    if previous_subscription:
        if (
            previous_subscription.opponent_connected
            and previous_subscription.game.status is not GameStatus.complete
        ):
            logging.warning(
                f"An AI player using key {keys.player_key} disconnected while their"
                " opponent was still playing. Reconnecting..."
            )
        else:
            logging.info("No need to reconnect previously unsubscribed AI player")
            return

    endpoint = f"{options.ai_server_url}/start"
    res: HTTPResponse
    while True:
        try:
            if not _xsrf_headers:
                async with _xsrf_lock:
                    if not _xsrf_headers:
                        res = await _client.fetch(endpoint)
                        xsrf = re.search(r"_xsrf=(.*?);", res.headers["Set-Cookie"])[1]
                        _xsrf_headers = {"X-XSRFToken": xsrf, "Cookie": f"_xsrf={xsrf}"}

            await _client.fetch(
                (
                    f"{endpoint}?"
                    f"player_key={keys.player_key}"
                    f"&ai_secret={keys.ai_secret}"
                ),
                method="POST",
                headers=_xsrf_headers,
                body="",
            )

        except Exception as e:
            if just_once:
                raise Exception("Failed to contact the AI server") from e
            else:
                logging.exception(
                    f"Failed to contact the AI server. Sleeping for {SLEEP_FOR}s and"
                    " trying again"
                )
                await asyncio.sleep(SLEEP_FOR)

        else:
            logging.info(
                f"Successfully contracted the AI server to play for key {keys.player_key}"
            )
            break
