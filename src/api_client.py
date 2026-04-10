import logging
import requests
from config import LND_PASS, ACCT_ID


BASE_URL = "https://api-my.te.eg/echannel/service/besapp/base/rest/busiservice"

COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "https://api-my.te.eg",
    "Referer": "https://api-my.te.eg/echannel/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "channelId": "702",
    "csrftoken": "",
    "delegatorSubsId": "",
    "isCoporate": "false",
    "isMobile": "false",
    "isSelfcare": "true",
    "languageCode": "en-US",
    "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}


def _build_headers(**overrides):
    """Return a copy of COMMON_HEADERS with optional overrides."""
    headers = COMMON_HEADERS.copy()
    headers.update(overrides)
    return headers


def init_session(session: requests.Session):
    """Step 1: Hit the querySysParams endpoint to seed session cookies."""
    url = f"{BASE_URL}/v1/common/querySysParams"
    headers = _build_headers(
        Host="api-my.te.eg",
        **{"Cache-Control": "no-cache", "Pragma": "no-cache"}
    )
    resp = session.post(url, headers=headers, json={})
    resp.raise_for_status()
    return resp


def authenticate(session: requests.Session):
    """Step 2: Authenticate and return (name, subscriberId, token)."""
    url = f"{BASE_URL}/v1/auth/userAuthenticate"
    headers = _build_headers(Host="api-my.te.eg")
    payload = {
        "acctId": ACCT_ID,
        "appLocale": "en-US",
        "password": LND_PASS,
    }

    resp = session.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()

    if data["header"]["retCode"] != "0":
        return None

    body = data["body"]
    logging.info("WE API authentication succeeded.")
    return {
        "name": body["customer"]["custName"],
        "subscriberId": body["subscriber"]["subscriberId"],
        "token": body["token"],
    }


def get_offers(session: requests.Session, token: str):
    """Step 3: Fetch subscribed offerings and return the main offer ID."""
    url = f"{BASE_URL}/cz/v1/auth/getSubscribedOfferings"
    headers = _build_headers(csrftoken=token)
    payload = {
        "msisdn": ACCT_ID,
        "numberServiceType": "FBB",
        "groupId": "",
    }

    resp = session.post(url, headers=headers, json=payload)
    data = resp.json()

    if data["header"]["retCode"] != "0":
        return None

    return data["body"]["offeringList"][0]["mainOfferingId"]


def get_quota(session: requests.Session, token: str, subscriber_id: str, offer_id: str):
    """Step 4: Query free-unit / quota details and return the first body entry."""
    url = f"{BASE_URL}/cz/cbs/bb/queryFreeUnit"
    headers = _build_headers(csrftoken=token)
    payload = {
        "subscriberId": subscriber_id,
        "mainOfferId": offer_id,
    }

    resp = session.post(url, headers=headers, json=payload)
    data = resp.json()

    if data["header"]["retCode"] != "0" or len(data["body"]) == 0:
        return None

    quota = data["body"][0]
    logging.info("Quota data fetched successfully.")
    return quota


def fetch_quota_data():
    """
    Orchestrates the full TE API flow:
      1. Seed cookies
      2. Authenticate
      3. Get offers
      4. Get quota details

    Returns (auth_info, quota_body) on success, or (None, error_msg) on failure.
    """
    with requests.Session() as session:
        init_session(session)

        auth = authenticate(session)
        if auth is None:
            return None, "Authentication failed. Please check your credentials."

        offer_id = get_offers(session, auth["token"])
        if offer_id is None:
            return None, "Failed to get subscription offerings."

        quota = get_quota(session, auth["token"], auth["subscriberId"], offer_id)
        if quota is None:
            return None, "Failed to retrieve quota details."

        return auth, quota
