"""Credential resolver for multi-user mode.

Extracts per-request credentials from tool call _meta field,
enabling a single MCP process to serve multiple users.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from cachetools import TTLCache

from mcp_atlassian.confluence import ConfluenceConfig, ConfluenceFetcher
from mcp_atlassian.jira import JiraConfig, JiraFetcher

logger = logging.getLogger("mcp-atlassian-multi.multi-user")

_jira_cache: TTLCache[str, JiraFetcher] = TTLCache(maxsize=50, ttl=300)
_confluence_cache: TTLCache[str, ConfluenceFetcher] = TTLCache(maxsize=50, ttl=300)


def _hash_credentials(creds: dict[str, str]) -> str:
    """Create deterministic hash of credentials for cache key."""
    sorted_items = sorted(creds.items())
    raw = "|".join(f"{k}={v}" for k, v in sorted_items)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def resolve_jira_from_meta(meta: dict[str, Any] | None) -> JiraFetcher | None:
    """Resolve JiraFetcher from _meta credentials if present."""
    if not meta:
        return None
    creds = meta.get("credentials")
    if not creds or not isinstance(creds, dict):
        return None
    jira_url = creds.get("jira_url")
    if not jira_url:
        return None
    cache_key = _hash_credentials(creds)
    cached = _jira_cache.get(cache_key)
    if cached:
        logger.debug("Using cached JiraFetcher for hash=%s", cache_key[:8])
        return cached
    jira_username = creds.get("jira_username") or creds.get("jira_email")
    jira_token = creds.get("jira_token") or creds.get("jira_api_token")
    jira_pat = creds.get("jira_personal_token") or creds.get("jira_pat")
    try:
        if jira_pat:
            config = JiraConfig(
                url=jira_url, auth_type="pat",
                personal_token=jira_pat, ssl_verify=True,
            )
        elif jira_username and jira_token:
            config = JiraConfig(
                url=jira_url, auth_type="basic",
                username=jira_username, api_token=jira_token, ssl_verify=True,
            )
        else:
            logger.warning("Incomplete Jira credentials in _meta")
            return None
        fetcher = JiraFetcher(config=config)
        _jira_cache[cache_key] = fetcher
        logger.info("Created JiraFetcher hash=%s url=%s", cache_key[:8], jira_url)
        return fetcher
    except Exception as e:
        logger.error("Failed to create JiraFetcher from _meta: %s", e)
        return None


def resolve_confluence_from_meta(
    meta: dict[str, Any] | None,
) -> ConfluenceFetcher | None:
    """Resolve ConfluenceFetcher from _meta credentials if present."""
    if not meta:
        return None
    creds = meta.get("credentials")
    if not creds or not isinstance(creds, dict):
        return None
    confluence_url = creds.get("confluence_url")
    if not confluence_url:
        return None
    cache_key = _hash_credentials(creds)
    cached = _confluence_cache.get(cache_key)
    if cached:
        logger.debug("Using cached ConfluenceFetcher hash=%s", cache_key[:8])
        return cached
    username = creds.get("confluence_username") or creds.get("confluence_email")
    token = creds.get("confluence_token") or creds.get("confluence_api_token")
    pat = creds.get("confluence_personal_token") or creds.get("confluence_pat")
    try:
        if pat:
            config = ConfluenceConfig(
                url=confluence_url, auth_type="pat",
                personal_token=pat, ssl_verify=True,
            )
        elif username and token:
            config = ConfluenceConfig(
                url=confluence_url, auth_type="basic",
                username=username, api_token=token, ssl_verify=True,
            )
        else:
            logger.warning("Incomplete Confluence credentials in _meta")
            return None
        fetcher = ConfluenceFetcher(config=config)
        _confluence_cache[cache_key] = fetcher
        logger.info(
            "Created ConfluenceFetcher hash=%s url=%s",
            cache_key[:8], confluence_url,
        )
        return fetcher
    except Exception as e:
        logger.error(
            "Failed to create ConfluenceFetcher from _meta: %s", e
        )
        return None
