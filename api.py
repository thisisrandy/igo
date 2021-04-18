import uvicorn
from starlette.applications import Starlette
from starlette.responses import (
    JSONResponse,
    HTMLResponse,
    PlainTextResponse,
)
import os

app = Starlette()


def get_cors_header(request):
    return (
        {"Access-Control-Allow-Origin": request.headers["Origin"]}
        if "Origin" in request.headers
        else None
    )


@app.route("/newgame", methods=["GET"])
async def newgame(request):
    response_headers = get_cors_header(request)
    try:
        vs = request.query_params["vs"]
        color = request.query_params["color"]
        komi = (
            int(request.query_params["komi"]) if "komi" in request.query_params else 6.5
        )
    except KeyError as ke:
        return PlainTextResponse(
            f"Required param {ke} missing in request",
            status_code=400,
            headers=response_headers,
        )
    except ValueError as ve:
        return PlainTextResponse(
            f"Param 'komi' must be a valid integer value",
            status_code=400,
            headers=response_headers,
        )
    return JSONResponse(
        {"route": "newgame", "vs": vs, "color": color, "komi": komi},
        headers=response_headers,
    )


@app.route("/joingame", methods=["GET"])
async def joingame(request):
    response_headers = get_cors_header(request)
    try:
        key = request.query_params["key"]
    except KeyError as ke:
        return PlainTextResponse(
            f"Required param {ke} missing in request",
            status_code=400,
            headers=response_headers,
        )
    return JSONResponse(
        {"route": "joingame", "key": key},
        headers=response_headers,
    )


@app.route("/aheadof", methods=["GET"])
async def aheadof(request):
    response_headers = get_cors_header(request)
    try:
        key = request.query_params["key"]
        timestamp = request.query_params["timestamp"]
    except KeyError as ke:
        return PlainTextResponse(
            f"Required param {ke} missing in request",
            status_code=400,
            headers=response_headers,
        )
    return JSONResponse(
        {"route": "aheadof", "key": key, "timestamp": timestamp},
        headers=response_headers,
    )


@app.route("/status", methods=["GET"])
async def status(request):
    response_headers = get_cors_header(request)
    try:
        key = request.query_params["key"]
    except KeyError as ke:
        return PlainTextResponse(
            f"Required param {ke} missing in request",
            status_code=400,
            headers=response_headers,
        )
    return JSONResponse(
        {"route": "status", "key": key},
        headers=response_headers,
    )


@app.route("/move", methods=["GET"])
async def move(request):
    response_headers = get_cors_header(request)
    try:
        key = request.query_params["key"]
        i = int(request.query_params["i"])
        j = int(request.query_params["j"])
    except KeyError as ke:
        return PlainTextResponse(
            f"Required param {ke} missing in request",
            status_code=400,
            headers=response_headers,
        )
    except ValueError as ve:
        return PlainTextResponse(
            f"Params 'i' and 'j' must be valid integer values",
            status_code=400,
            headers=response_headers,
        )
    return JSONResponse(
        {"route": "move", "key": key, "i": i, "j": j},
        headers=response_headers,
    )


@app.route("/pass", methods=["GET"])
async def pass_move(request):
    response_headers = get_cors_header(request)
    try:
        key = request.query_params["key"]
    except KeyError as ke:
        return PlainTextResponse(
            f"Required param {ke} missing in request",
            status_code=400,
            headers=response_headers,
        )
    return JSONResponse(
        {"route": "pass", "key": key},
        headers=response_headers,
    )


@app.route("/requestdraw", methods=["GET"])
async def requestdraw(request):
    response_headers = get_cors_header(request)
    try:
        key = request.query_params["key"]
    except KeyError as ke:
        return PlainTextResponse(
            f"Required param {ke} missing in request",
            status_code=400,
            headers=response_headers,
        )
    return JSONResponse(
        {"route": "requestdraw", "key": key},
        headers=response_headers,
    )


@app.route("/responddraw", methods=["GET"])
async def responddraw(request):
    response_headers = get_cors_header(request)
    try:
        key = request.query_params["key"]
        response = request.query_params["response"].lower() == "true"
    except KeyError as ke:
        return PlainTextResponse(
            f"Required param {ke} missing in request",
            status_code=400,
            headers=response_headers,
        )
    return JSONResponse(
        {"route": "responddraw", "key": key, "response": response},
        headers=response_headers,
    )


@app.route("/markdead", methods=["GET"])
async def markdead(request):
    response_headers = get_cors_header(request)
    try:
        key = request.query_params["key"]
        i = int(request.query_params["i"])
        j = int(request.query_params["j"])
    except KeyError as ke:
        return PlainTextResponse(
            f"Required param {ke} missing in request",
            status_code=400,
            headers=response_headers,
        )
    except ValueError as ve:
        return PlainTextResponse(
            f"Params 'i' and 'j' must be valid integer values",
            status_code=400,
            headers=response_headers,
        )
    return JSONResponse(
        {"route": "markdead", "key": key, "i": i, "j": j},
        headers=response_headers,
    )


@app.route("/responddead", methods=["GET"])
async def responddead(request):
    response_headers = get_cors_header(request)
    try:
        key = request.query_params["key"]
        i = int(request.query_params["i"])
        j = int(request.query_params["j"])
        response = request.query_params["response"].lower() == "true"
    except KeyError as ke:
        return PlainTextResponse(
            f"Required param {ke} missing in request",
            status_code=400,
            headers=response_headers,
        )
    except ValueError as ve:
        return PlainTextResponse(
            f"Params 'i' and 'j' must be valid integer values",
            status_code=400,
            headers=response_headers,
        )
    return JSONResponse(
        {"route": "responddead", "key": key, "i": i, "j": j, "response": response},
        headers=response_headers,
    )


@app.route("/")
def root(request):
    response_headers = get_cors_header(request)
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>囲碁 - igo API server</title>
        </head>
        <body>
            <h2>囲碁 - igo API server</h2>
            <p>Available routes:</p>
            <ol>
                <li>GET /newgame: vs ("human" | "computer"), color ("black" | "white")[, komi=6.5]</li>
                <li>GET /joingame: key</li>
                <li>GET /aheadof key, timestamp</li>
                <li>GET /status: key</li>
                <li>POST /move: key, i, j</li>
                <li>POST /pass: key</li>
                <li>POST /requestdraw: key</li>
                <li>POST /responddraw: key, response ("True" | "False")</li>
                <li>POST /markdead: key, i, j</li>
                <li>POST /responddead: key, i, j, response ("True" | "False")</li>
            </ol>
        </body>
        </html>
        """,
        headers=response_headers,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8008))
    uvicorn.run(app, host="0.0.0.0", port=port)
