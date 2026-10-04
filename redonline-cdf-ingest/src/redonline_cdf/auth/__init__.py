"""Authentication helpers for Cognite and Red Online."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from cognite.client import CogniteClient


def create_cognite_client() -> CogniteClient:
    """Build a CogniteClient from environment variables (OIDC client credentials)."""
    from cognite.client import CogniteClient
    from cognite.client.config import ClientConfig
    from cognite.client.credentials import OAuthClientCredentials

    project = os.environ["CDF_PROJECT"]
    cluster = os.environ.get("CDF_CLUSTER", "westeurope-1")
    client_id = os.environ["CDF_CLIENT_ID"]
    client_secret = os.environ["CDF_CLIENT_SECRET"]
    tenant_id = os.environ["CDF_TENANT_ID"]
    token_url = os.environ.get(
        "CDF_TOKEN_URL",
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
    )
    base_url = f"https://{cluster}.cognitedata.com"
    scopes = [f"{base_url}/.default"]

    creds = OAuthClientCredentials(
        token_url=token_url,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )
    config = ClientConfig(
        client_name="redonline-cdf-ingest",
        project=project,
        base_url=base_url,
        credentials=creds,
    )
    return CogniteClient(config)


def resolve_redonline_token() -> str:
    """
    Return a Red Online / HSE API credential.

    Order:
    1. REDONLINE_API_KEY or REDONLINE_TOKEN env
    2. auth.api_key in config/endpoints.yaml
    3. OAuth client-credentials (REDONLINE_TOKEN_URL + client id/secret)
    """
    for name in ("REDONLINE_API_KEY", "REDONLINE_TOKEN"):
        static = os.getenv(name)
        if static:
            return static

    try:
        from redonline_cdf.config import load_endpoints

        api_key = (load_endpoints().get("auth") or {}).get("api_key")
        if api_key:
            return str(api_key)
    except Exception:  # noqa: BLE001 — fall through to OAuth / error
        pass

    token_url = os.getenv("REDONLINE_TOKEN_URL")
    client_id = os.getenv("REDONLINE_CLIENT_ID")
    client_secret = os.getenv("REDONLINE_CLIENT_SECRET")
    if not (token_url and client_id and client_secret):
        raise RuntimeError(
            "Set REDONLINE_API_KEY (or REDONLINE_TOKEN) in .env, "
            "or auth.api_key in config/endpoints.yaml, "
            "or OAuth via REDONLINE_TOKEN_URL + "
            "REDONLINE_CLIENT_ID + REDONLINE_CLIENT_SECRET"
        )

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    scope = os.getenv("REDONLINE_SCOPE")
    if scope:
        data["scope"] = scope

    with httpx.Client(timeout=30.0) as http:
        resp = http.post(token_url, data=data)
        resp.raise_for_status()
        payload = resp.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("Red Online token response missing access_token")
    return str(token)
