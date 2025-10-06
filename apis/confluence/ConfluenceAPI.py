import os
import base64
import html
import re
import requests
from dotenv import load_dotenv


class ConfluenceAPI:
    """Confluence API helper focused on creating pages.

    Required env vars (used automatically):
      CONFLUENCE_URL              Base URL OR direct /rest/api/content endpoint.
                                  Examples:
                                    https://tomtom.atlassian.net/wiki
                                    https://tomtom.atlassian.net/wiki/rest/api/content
      CONFLUENCE_USERNAME         Atlassian account email
      CONFLUENCE_API_TOKEN        API token
      CONFLUENCE_SPACE_KEY        (Optional default space key)
      CONFLUENCE_PARENT_PAGE_ID   (Optional default ancestor page id)
    """

    def __init__(self, domain=None, email=None, api_token=None):
        load_dotenv()
        # Respect explicit params but fall back to env
        self.base_url = (domain or os.getenv("CONFLUENCE_URL", "")).rstrip("/")
        self.username = email or os.getenv("CONFLUENCE_USERNAME")
        self.api_token = api_token or os.getenv("CONFLUENCE_API_TOKEN")
        self.default_space = os.getenv("CONFLUENCE_SPACE_KEY")
        self.default_parent = os.getenv("CONFLUENCE_PARENT_PAGE_ID")

    # ---------------- Public API ---------------- #
    def create_page(self, title: str, body: str, space_key: str = None, parent_id: str = None, markdown: bool = True):
        """Create a Confluence page using environment-driven configuration.

        Args:
            title: Page title.
            body: Content (markdown or raw storage HTML depending on markdown flag).
            space_key: Confluence space key (falls back to CONFLUENCE_SPACE_KEY).
            parent_id: Optional ancestor page id (falls back to CONFLUENCE_PARENT_PAGE_ID if not provided).
            markdown: If True, attempt very light markdown -> storage HTML conversion; else treat body as storage ready.

        Returns:
            dict: {id,title,link,status} on success OR {error:..., details:...}
        """
        # Validate config
        if not self.base_url:
            return {"error": "MISSING_BASE_URL", "message": "CONFLUENCE_URL not configured."}
        if not (self.username and self.api_token):
            return {"error": "MISSING_CREDENTIALS", "message": "CONFLUENCE_USERNAME / CONFLUENCE_API_TOKEN not configured."}
        if not title:
            return {"error": "MISSING_TITLE", "message": "title required"}
        space = space_key or self.default_space
        if not space:
            return {"error": "MISSING_SPACE_KEY", "message": "Provide space_key or set CONFLUENCE_SPACE_KEY"}
        ancestor = parent_id or self.default_parent

        # Determine candidate content endpoints (support direct full endpoint & fallbacks)
        content_endpoints = self._candidate_content_endpoints(self.base_url)
        debug = os.getenv("CONFLUENCE_DEBUG") == "1"
        if debug:
            print(
                "[ConfluenceAPI] Base URL: " + self.base_url + "\n" +
                "[ConfluenceAPI] Candidate endpoints: " + ", ".join(content_endpoints)
            )
        # Always log a concise payload summary (safe fields only)
        print(f"[ConfluenceAPI] Preparing page create: title='{title}' len(body)={len(body) if body else 0} space='{space}' ancestor='{ancestor}' markdown={markdown}")

        # Prepare body
        if markdown:
            storage_value = self._markdown_to_storage_html(body)
        else:
            storage_value = body

        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space},
            "body": {
                "storage": {
                    "value": storage_value,
                    "representation": "storage"
                }
            }
        }
        if ancestor:
            payload["ancestors"] = [{"id": str(ancestor)}]

        headers = {
            "Authorization": f"Basic {self._basic_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        last_error = None
        for idx, ep in enumerate(content_endpoints, start=1):
            print(f"[ConfluenceAPI] Attempt {idx}/{len(content_endpoints)} -> POST {ep}")
            try:
                resp = requests.post(ep, json=payload, headers=headers, timeout=30)
                # Log every response (status + truncated body)
                truncated = resp.text[:500].replace('\n', ' ') if resp.text else ''
                print(f"[ConfluenceAPI] Response {resp.status_code} (len={len(resp.text)}) body[0:500]='{truncated}'")
            except requests.RequestException as e:
                last_error = {"error": "REQUEST_FAILED", "message": str(e), "attempted_endpoint": ep}
                print(f"[ConfluenceAPI] Network/Request error on {ep}: {e}")
                continue

            if resp.status_code in (200, 201):
                data = resp.json()
                print(f"[ConfluenceAPI] Page created id={data.get('id')} title='{data.get('title')}'")
                return {
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "link": self._build_link(data),
                    "status": "created",
                    "endpoint_used": ep
                }

            # Parse error body
            try:
                details = resp.json()
            except Exception:
                details = {"raw": resp.text}

            hint = None
            if resp.status_code == 401:
                hint = "Check username/token; ensure token hasn't expired and matches the site."
            elif resp.status_code == 403:
                hint = "Forbidden: user may lack add page permission in this space or under ancestor."
            elif resp.status_code == 404:
                hint = "Endpoint 404: trying next variant (if any)."
            elif resp.status_code == 409:
                hint = "Title conflict: page with same title already exists under this parent."

            last_error = {
                "error": "CREATE_FAILED",
                "status_code": resp.status_code,
                "hint": hint,
                "attempted_endpoint": ep,
                "details": details,
                "payload_title": title,
                "space": space,
                "ancestor": ancestor
            }
            print(f"[ConfluenceAPI] Attempt failed status={resp.status_code} hint={hint}")
            # Only continue to next endpoint automatically on 404; break for others
            if resp.status_code != 404:
                break

        return last_error or {"error": "UNKNOWN", "message": "Failed to create page", "endpoints_tried": content_endpoints}

    # --------------- Helpers --------------- #
    def _basic_token(self) -> str:
        raw = f"{self.username}:{self.api_token}".encode("utf-8")
        return base64.b64encode(raw).decode("utf-8")

    def _candidate_content_endpoints(self, base_url: str):
        base = base_url.rstrip('/')
        lowered = base.lower()
        candidates = []
        # Direct endpoint provided (with or without trailing slash)
        if '/rest/api/content' in lowered:
            # normalize by stripping any trailing slash after content
            if lowered.endswith('/rest/api/content'):
                candidates.append(base)
            elif lowered.endswith('/rest/api/content/'):  # unlikely after rstrip
                candidates.append(base.rstrip('/'))
            return candidates
        # If user supplied a /wiki root
        if lowered.endswith('/wiki'):
            candidates.append(base + '/rest/api/content')
            # fallback without /wiki in case instance doesn't use it
            root_no_wiki = base.rsplit('/wiki', 1)[0]
            candidates.append(root_no_wiki + '/rest/api/content')
        else:
            # Provided root without /wiki; try with wiki first (cloud) then without
            candidates.append(base + '/wiki/rest/api/content')
            candidates.append(base + '/rest/api/content')
        # Deduplicate preserving order
        seen = set()
        ordered = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                ordered.append(c)
        return ordered

    def _markdown_to_storage_html(self, md: str) -> str:
        if md is None:
            return "<p></p>"
        # Escape HTML first to avoid injection, then reintroduce basic formatting.
        text = md.replace('\r\n', '\n')
        # Code fences
        blocks = []
        code_pattern = re.compile(r"```(\w+)?\n([\s\S]*?)```", re.MULTILINE)
        last = 0
        for m in code_pattern.finditer(text):
            blocks.append(self._para_html(text[last:m.start()]))
            lang = m.group(1) or ''
            code_content = html.escape(m.group(2).rstrip('\n'))
            blocks.append(
                f"<ac:structured-macro ac:name=\"code\">" +
                (f"<ac:parameter ac:name=\"language\">{lang}</ac:parameter>" if lang else "") +
                f"<ac:plain-text-body><![CDATA[{code_content}]]></ac:plain-text-body></ac:structured-macro>"
            )
            last = m.end()
        blocks.append(self._para_html(text[last:]))
        return ''.join(b for b in blocks if b)

    def _para_html(self, segment: str) -> str:
        seg = segment.strip('\n')
        if not seg.strip():
            return ''
        # Split paragraphs by blank lines
        paras = re.split(r"\n{2,}", seg)
        html_paras = []
        for p in paras:
            p_html = html.escape(p)
            # Basic bold/italic inline restoration AFTER escaping (simple markdown subset)
            p_html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p_html)
            p_html = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", p_html)
            p_html = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", p_html)
            html_paras.append(f"<p>{p_html}</p>")
        return ''.join(html_paras)

    def _build_link(self, data: dict):
        links = data.get('_links', {})
        base = links.get('base')
        webui = links.get('webui')
        if base and webui:
            return f"{base}{webui}"
        if webui and self.base_url:
            # attempt to reconstruct
            if self.base_url.endswith('/rest/api/content'):
                # strip that path
                root = self.base_url.rsplit('/rest/api/content', 1)[0]
            else:
                root = self.base_url
            return f"{root}{webui}"
        return None


__all__ = ["ConfluenceAPI"]
