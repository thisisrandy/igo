from tornado.httputil import HTTPHeaders
from igo.gameserver.containers import KeyPair
from igo.aiserver.http_client import start_ai_player
import unittest
from unittest.mock import AsyncMock, patch

from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPResponse


class HttpClientTestCase(unittest.IsolatedAsyncioTestCase):
    @patch.object(AsyncHTTPClient, "fetch")
    async def test_start_ai_player(self, fetch_mock: AsyncMock):
        xsrf = "s3kr3t"

        async def fetch(*args, **kwargs):
            return HTTPResponse(
                HTTPRequest("foo.com"),
                200,
                headers=HTTPHeaders({"Set-Cookie": f"_xsrf={xsrf};"}),
            )

        fetch_mock.side_effect = fetch
        keys = KeyPair("1234", "5678")

        # test that start fetches a GET followed by a POST and correctly
        # includes keys xsrf from the GET

        await start_ai_player(keys)
        self.assertEqual(fetch_mock.call_count, 2)
        # note that GET is the default for fetch, so it may not be explicitly specified
        method = fetch_mock.call_args_list[0][1].get("method", "GET")
        self.assertEqual(method, "GET")
        url = fetch_mock.call_args_list[-1][0][0]
        self.assertRegex(url, f"player_key={keys.player_key}")
        self.assertRegex(url, f"ai_secret={keys.ai_secret}")
        method = fetch_mock.call_args_list[-1][1]["method"]
        self.assertEqual(method, "POST")
        headers = fetch_mock.call_args_list[-1][1]["headers"]
        self.assertDictEqual(
            headers,
            {"X-XSRFToken": xsrf, "Cookie": f"_xsrf={xsrf}"},
        )

        # test that starting a second time doesn't re-get the xsrf token

        await start_ai_player(keys)
        self.assertEqual(fetch_mock.call_count, 3)
        method = fetch_mock.call_args_list[-1][1]["method"]
        self.assertEqual(method, "POST")

        # finally, test that calling w/o an AI secret fails

        keys.ai_secret = None
        with self.assertRaises(AssertionError):
            await start_ai_player(keys)
