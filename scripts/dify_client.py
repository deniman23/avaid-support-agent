"""Minimal Dify Console API client (cookie session + CSRF)."""
from __future__ import annotations

import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any


class DifyClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base = (base_url or os.environ.get("DIFY_CONSOLE_URL", "http://localhost")).rstrip("/")
        self.api = f"{self.base}/console/api"
        self.jar = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.csrf: str | None = None

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = {"Accept": "application/json"}
        if self.csrf:
            h["X-CSRF-Token"] = self.csrf
        if extra:
            h.update(extra)
        return h

    def _request(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        files: dict | None = None,
        raw_body: bytes | None = None,
        content_type: str | None = None,
    ) -> Any:
        url = f"{self.api}{path}"
        if files:
            boundary = "----DifySyncBoundary"
            body_parts: list[bytes] = []
            for key, (fname, content, mime) in files.items():
                body_parts.append(f"--{boundary}\r\n".encode())
                body_parts.append(
                    f'Content-Disposition: form-data; name="{key}"; filename="{fname}"\r\n'.encode()
                )
                body_parts.append(f"Content-Type: {mime}\r\n\r\n".encode())
                body_parts.append(content)
                body_parts.append(b"\r\n")
            body_parts.append(f"--{boundary}--\r\n".encode())
            body = b"".join(body_parts)
            headers = self._headers({"Content-Type": f"multipart/form-data; boundary={boundary}"})
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
        elif raw_body is not None:
            headers = self._headers({"Content-Type": content_type or "application/json"})
            req = urllib.request.Request(url, data=raw_body, headers=headers, method=method)
        elif data is not None:
            body = json.dumps(data).encode()
            headers = self._headers({"Content-Type": "application/json"})
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
        else:
            req = urllib.request.Request(url, headers=self._headers(), method=method)

        try:
            with self.opener.open(req, timeout=120) as resp:
                raw = resp.read().decode()
                if not raw:
                    return {}
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            raise RuntimeError(f"{method} {path} -> {e.code}: {err}") from e

    def login(self, email: str, password: str) -> None:
        payload = json.dumps({"email": email, "password": password, "remember_me": True}).encode()
        req = urllib.request.Request(
            f"{self.api}/login",
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with self.opener.open(req, timeout=60) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Login failed: {resp.status}")
            for c in self.jar:
                if "csrf" in c.name.lower():
                    self.csrf = c.value
        if not self.csrf:
            for c in self.jar:
                if "csrf" in c.name:
                    self.csrf = c.value
        me = self._request("GET", "/account/profile")
        if not me:
            raise RuntimeError("Login succeeded but profile unavailable")
        print(f"Logged in as {me.get('email', email)}")

    def list_datasets(self, keyword: str = "") -> list[dict]:
        q = urllib.parse.urlencode({"page": 1, "limit": 100, "keyword": keyword})
        res = self._request("GET", f"/datasets?{q}")
        return res.get("data", [])

    def find_dataset(self, name: str) -> dict | None:
        for ds in self.list_datasets(name):
            if ds.get("name") == name:
                return ds
        return None

    def create_dataset(self, name: str, description: str = "") -> dict:
        return self._request(
            "POST",
            "/datasets",
            {
                "name": name,
                "description": description,
                "indexing_technique": "economy",
                "permission": "only_me",
            },
        )

    def upload_file(self, path: Path) -> str:
        content = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "text/markdown"
        res = self._request(
            "POST",
            "/files/upload",
            files={"file": (path.name, content, mime)},
        )
        return res["id"]

    def add_documents(self, dataset_id: str, file_ids: list[str]) -> dict:
        payload = {
            "indexing_technique": "economy",
            "data_source": {
                "info_list": {
                    "data_source_type": "upload_file",
                    "file_info_list": {"file_ids": file_ids},
                }
            },
            "process_rule": {"mode": "automatic"},
            "doc_form": "text_model",
            "doc_language": "Russian",
            "duplicate": True,
        }
        return self._request("POST", f"/datasets/{dataset_id}/documents", payload)

    def list_documents(self, dataset_id: str) -> list[dict]:
        q = urllib.parse.urlencode({"page": 1, "limit": 100})
        res = self._request("GET", f"/datasets/{dataset_id}/documents?{q}")
        return res.get("data", [])

    def delete_document(self, dataset_id: str, document_id: str) -> None:
        q = urllib.parse.urlencode({"document_id": document_id})
        self._request("DELETE", f"/datasets/{dataset_id}/documents?{q}")

    def sync_folder_to_dataset(self, dataset_name: str, folder: Path, description: str = "") -> str:
        ds = self.find_dataset(dataset_name)
        if not ds:
            ds = self.create_dataset(dataset_name, description)
            print(f"Created dataset: {dataset_name}")
        dataset_id = ds["id"]

        existing = {d.get("name"): d.get("id") for d in self.list_documents(dataset_id)}
        files = sorted(folder.glob("*.md")) if folder.is_dir() else [folder]
        uploaded = 0
        for fp in files:
            if not fp.is_file():
                continue
            if fp.name in existing:
                print(f"  skip (exists): {fp.name}")
                continue
            fid = self.upload_file(fp)
            self.add_documents(dataset_id, [fid])
            print(f"  indexed: {fp.name}")
            uploaded += 1
        if uploaded == 0 and not existing:
            print(f"  warning: no files in {folder}")
        return dataset_id

    def list_apps(self, keyword: str = "") -> list[dict]:
        q = urllib.parse.urlencode({"page": 1, "limit": 50, "name": keyword})
        res = self._request("GET", f"/apps?{q}")
        return res.get("data", [])

    def import_app_yaml(self, yaml_content: str, name: str | None = None) -> dict:
        payload: dict[str, Any] = {"mode": "yaml-content", "yaml_content": yaml_content}
        if name:
            payload["name"] = name
        return self._request("POST", "/apps/imports", payload)

    def confirm_import(self, import_id: str) -> dict:
        return self._request("POST", f"/apps/imports/{import_id}/confirm")

    def create_api_tool(self, provider: str, schema: str, api_key: str, server_url: str) -> dict:
        schema_with_server = schema.replace("http://support-db-api:8090", server_url)
        return self._request(
            "POST",
            "/workspaces/current/tool-provider/api/add",
            {
                "provider": provider,
                "icon": {"content": "🛟", "background": "#E4FBCC"},
                "schema_type": "openapi",
                "schema": schema_with_server,
                "credentials": {
                    "auth_type": "api_key",
                    "api_key_header": "X-Support-Api-Key",
                    "api_key_value": api_key,
                },
                "labels": ["support", "avaid"],
                "privacy_policy": "",
                "custom_disclaimer": "Read-only Avaid support data",
            },
        )
