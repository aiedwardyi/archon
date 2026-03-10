"""Watson Discovery client for storing and retrieving best builds."""
from __future__ import annotations

import io
import json
import os
from typing import Any

from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import DiscoveryV2


class DiscoveryClient:
    def __init__(self) -> None:
        # Support both env var names for compatibility.
        api_key = os.getenv("WATSON_DISCOVERY_API_KEY") or os.getenv("WATSON_DISCOVERY_API")
        url = os.getenv("WATSON_DISCOVERY_URL")
        self.project_id = os.getenv("WATSON_DISCOVERY_PROJECT_ID")
        self.enabled = bool(api_key and url and self.project_id)
        self.collection_id: str | None = None
        self.client: DiscoveryV2 | None = None

        if self.enabled:
            authenticator = IAMAuthenticator(api_key)
            self.client = DiscoveryV2(version="2023-03-31", authenticator=authenticator)
            self.client.set_service_url(url)
        else:
            print("[Discovery] Disabled: missing credentials")

    def _resolve_collection(self) -> str | None:
        """Find the 'best_builds' collection ID in the configured project."""
        if self.collection_id:
            return self.collection_id
        if not self.enabled or not self.client:
            return None

        try:
            response = self.client.list_collections(project_id=self.project_id).get_result()
            for collection in response.get("collections", []):
                name = collection.get("name", "")
                if "best_builds" in name.lower():
                    self.collection_id = collection.get("collection_id")
                    print(f"[Discovery] Using collection '{name}' ({self.collection_id})")
                    return self.collection_id
            print("[Discovery] WARNING: No 'best_builds' collection found")
            return None
        except Exception as exc:
            print(f"[Discovery] Failed to list collections: {exc}")
            return None

    def _document_exists(self, project_id: int | str, version: int = 1) -> bool:
        """Best-effort idempotency check for an already ingested build."""
        if not self.enabled or not self.client:
            return False
        collection_id = self._resolve_collection()
        if not collection_id:
            return False

        filters = [
            f"project_id::{project_id}",
            f'metadata.project_id:"{project_id}"',
        ]
        for flt in filters:
            try:
                result = self.client.query(
                    project_id=self.project_id,
                    collection_ids=[collection_id],
                    filter=flt,
                    count=1,
                ).get_result()
                if result.get("results"):
                    return True
            except Exception:
                # Some filter styles can be rejected depending on index schema.
                continue
        return False

    def ingest_build(self, doc: dict[str, Any]) -> bool:
        """Ingest one build document into Watson Discovery."""
        if not self.enabled or not self.client:
            print("[Discovery] Disabled - skipping ingest")
            return False

        collection_id = self._resolve_collection()
        if not collection_id:
            return False

        project_id = doc.get("project_id", "unknown")
        archetype = doc.get("archetype", "unknown")
        version = int(doc.get("version", 1))

        if self._document_exists(project_id=project_id, version=version):
            print(f"[Discovery] Build already present for project {project_id} (v{version}); skipping")
            return True

        filename = f"build_{project_id}_{archetype}_v{version}.json"
        file_data = io.BytesIO(json.dumps(doc, ensure_ascii=False).encode("utf-8"))
        metadata = json.dumps(
            {
                "archetype": archetype,
                "eval_score": doc.get("eval_score"),
                "project_id": str(project_id),
                "version": version,
            }
        )

        try:
            result = self.client.add_document(
                project_id=self.project_id,
                collection_id=collection_id,
                file=file_data,
                filename=filename,
                file_content_type="application/json",
                metadata=metadata,
            ).get_result()
            document_id = result.get("document_id", "unknown")
            print(f"[Discovery] Ingested project {project_id} ({archetype}) as document {document_id}")
            return True
        except Exception as exc:
            print(f"[Discovery] Ingest failed for project {project_id}: {exc}")
            return False

    def query_best_build(self, archetype: str) -> dict[str, Any] | None:
        """Return the top scoring build document for a given archetype."""
        if not self.enabled or not self.client:
            return None

        collection_id = self._resolve_collection()
        if not collection_id:
            return None

        filters = [
            f'archetype:"{archetype}"',
            f'metadata.archetype:"{archetype}"',
        ]

        for flt in filters:
            try:
                result = self.client.query(
                    project_id=self.project_id,
                    collection_ids=[collection_id],
                    natural_language_query=f"best {archetype} web application",
                    filter=flt,
                    sort="-eval_score",
                    count=1,
                    return_=[
                        "archetype",
                        "prompt",
                        "plan_json",
                        "html_code",
                        "css_code",
                        "base_css",
                        "eval_score",
                        "project_id",
                        "version",
                        "created_at",
                    ],
                ).get_result()
                results = result.get("results", [])
                if results:
                    best = results[0]
                    print(
                        f"[Discovery] Found best build for '{archetype}' "
                        f"(project {best.get('project_id')}, score {best.get('eval_score')})"
                    )
                    return best
            except Exception as exc:
                print(f"[Discovery] Query failed for filter '{flt}': {exc}")

        print(f"[Discovery] No results for archetype '{archetype}'")
        return None
