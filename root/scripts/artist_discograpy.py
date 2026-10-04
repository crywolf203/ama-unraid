#!/usr/bin/env python3

import http.cookiejar
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


GW_URL = "http://www.deezer.com/ajax/gw-light.php"

GW_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/79.0.3945.130 Safari/537.36"
)


def get_limit():
    value = os.environ.get("MAX_ALBUMS_PER_ARTIST", "").strip()

    # Historical AMA behavior is unlimited. Some older/test images carried
    # MAX_ALBUMS_PER_ARTIST=25 internally even though the Unraid template did
    # not expose it. Treat 25 as legacy/unset unless explicitly changed later.
    if not value or value == "25":
        return 0

    try:
        parsed = int(value)
    except ValueError:
        return 0

    return max(parsed, 0)


def add_album_id(album_ids, seen, album_id, limit=0):
    album_id = str(album_id or "").strip()

    if not album_id or album_id in seen:
        return False

    seen.add(album_id)
    album_ids.append(album_id)

    if limit and len(album_ids) >= limit:
        return True

    return False


def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AMA-Unraid/2.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(
            response.read().decode("utf-8", errors="replace")
        )


def get_api_artist_albums(artist_id):
    album_ids = []
    seen = set()

    url = (
        "https://api.deezer.com/artist/"
        f"{urllib.parse.quote(str(artist_id))}/albums?limit=100"
    )

    while url:
        data = fetch_json(url)

        for album in data.get("data", []):
            add_album_id(
                album_ids,
                seen,
                album.get("id"),
                0,
            )

        url = data.get("next") or ""

    return album_ids


def load_arl():
    value = os.environ.get("ARL_TOKEN", "").strip()

    if value:
        return value

    login_paths = (
        Path("/config/deemix/bambanah/login.json"),
        Path("/deemix-config/login.json"),
    )

    for path in login_paths:
        try:
            if not path.is_file():
                continue

            data = json.loads(
                path.read_text(encoding="utf-8")
            )

            value = str(
                data.get("arl") or ""
            ).strip()

            if value:
                return value

        except Exception:
            pass

    arl_paths = (
        Path("/config/deemix/bambanah/.arl"),
        Path("/deemix-config/.arl"),
        Path("/config/deemix/xdg/deemix/.arl"),
    )

    for path in arl_paths:
        try:
            if not path.is_file():
                continue

            value = path.read_text(
                encoding="utf-8"
            ).strip()

            if value:
                return value

        except Exception:
            pass

    return ""


def create_gateway_session():
    arl = load_arl()

    if not arl:
        raise RuntimeError(
            "No Deezer ARL credential found"
        )

    cookie_jar = http.cookiejar.CookieJar()

    cookie_jar.set_cookie(
        http.cookiejar.Cookie(
            version=0,
            name="arl",
            value=arl,
            port=None,
            port_specified=False,
            domain=".deezer.com",
            domain_specified=True,
            domain_initial_dot=True,
            path="/",
            path_specified=True,
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={"HttpOnly": None},
            rfc2109=False,
        )
    )

    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(
            cookie_jar
        )
    )

    return opener


def gateway_call(
    opener,
    method,
    args,
    api_token="null",
):
    params = urllib.parse.urlencode(
        {
            "api_version": "1.0",
            "api_token": api_token,
            "input": "3",
            "method": method,
        }
    )

    req = urllib.request.Request(
        f"{GW_URL}?{params}",
        data=json.dumps(args).encode("utf-8"),
        headers={
            "User-Agent": GW_USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with opener.open(
        req,
        timeout=30,
    ) as response:
        payload = json.loads(
            response.read().decode(
                "utf-8",
                errors="replace",
            )
        )

    error = payload.get("error")

    if error:
        raise RuntimeError(
            f"Deezer gateway error for "
            f"{method}: {error}"
        )

    return payload.get("results", {})


def gateway_authenticated_session():
    opener = create_gateway_session()

    user_data = gateway_call(
        opener,
        "deezer.getUserData",
        {},
        "null",
    )

    user_id = (
        user_data.get("USER", {})
        .get("USER_ID", 0)
    )

    token = str(
        user_data.get("checkForm") or ""
    ).strip()

    if not user_id:
        raise RuntimeError(
            "Deezer ARL did not create "
            "an authenticated session"
        )

    if not token:
        raise RuntimeError(
            "Deezer gateway did not return "
            "a CSRF token"
        )

    return opener, token


def as_bool(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value != 0

    return str(value).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def get_gw_artist_albums(artist_id):
    opener, token = gateway_authenticated_session()

    raw_releases = []
    start = 0
    limit = 100

    while True:
        result = gateway_call(
            opener,
            "album.getDiscography",
            {
                "ART_ID": str(artist_id),
                "discography_mode": "all",
                "nb": limit,
                "nb_songs": 0,
                "start": start,
            },
            token,
        )

        releases = result.get("data", [])
        total = int(
            result.get("total") or 0
        )

        raw_releases.extend(releases)

        start += limit

        if start >= total or not releases:
            break

    all_ids = []
    featured_ids = []
    more_ids = []

    raw_seen = set()

    for release in raw_releases:
        album_id = str(
            release.get("ALB_ID") or ""
        ).strip()

        if not album_id or album_id in raw_seen:
            continue

        raw_seen.add(album_id)

        release_artist = str(
            release.get("ART_ID") or ""
        )

        try:
            role_id = int(
                release.get("ROLE_ID")
            )
        except (TypeError, ValueError):
            role_id = None

        official = as_bool(
            release.get(
                "ARTISTS_ALBUMS_IS_OFFICIAL"
            )
        )

        # Match Bambanah/deezer-sdk
        # get_artist_discography_tabs().
        if (
            (
                release_artist == str(artist_id)
                or (
                    release_artist
                    != str(artist_id)
                    and role_id == 0
                )
            )
            and official
        ):
            all_ids.append(album_id)

        elif role_id == 5:
            featured_ids.append(album_id)

        elif role_id == 0:
            more_ids.append(album_id)
            all_ids.append(album_id)

    album_ids = []
    seen = set()

    # Preserve the effective AMA ordering:
    # main catalog first, featured appearances after.
    for bucket in (
        all_ids,
        featured_ids,
        more_ids,
    ):
        for album_id in bucket:
            add_album_id(
                album_ids,
                seen,
                album_id,
                0,
            )

    return album_ids


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        raise SystemExit(0)

    artist_id = sys.argv[1]
    limit = get_limit()

    seen = set()
    album_ids = []

    for getter in (
        get_api_artist_albums,
        get_gw_artist_albums,
    ):
        try:
            for album_id in getter(artist_id):
                if add_album_id(
                    album_ids,
                    seen,
                    album_id,
                    limit,
                ):
                    break

        except Exception as exc:
            print(
                "artist_discograpy.py warning: "
                f"{getter.__name__} failed: {exc}",
                file=sys.stderr,
            )

        if limit and len(album_ids) >= limit:
            break

    for album_id in album_ids:
        print(album_id)
