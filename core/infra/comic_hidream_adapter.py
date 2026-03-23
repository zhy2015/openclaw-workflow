from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from core.infra.hidream_adapter import SeedreamImageAdapter


@dataclass(frozen=True)
class ComicHiDreamBundle:
    character_sheet_request: Dict[str, Any]
    panel_requests: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_sheet_request": self.character_sheet_request,
            "panel_requests": self.panel_requests,
        }


class ComicHiDreamAdapter:
    def __init__(self, skills_root: str):
        self.image_adapter = SeedreamImageAdapter(skills_root)

    def adapt_payloads(self, hidream_payloads: Dict[str, Any]) -> Dict[str, Any]:
        character_payload = hidream_payloads["character_sheet_payload"]
        panel_payloads = hidream_payloads["panel_payloads"]

        character_request = self.image_adapter.build_request({
            "prompt": character_payload["prompt"],
            "version": "M1",
            "resolution": "1536*1536",
            "img_count": 1,
        }).to_dict()

        panel_requests = []
        for panel in panel_payloads:
            panel_requests.append(self.image_adapter.build_request({
                "prompt": panel["prompt"],
                "version": "M1",
                "resolution": "1024*1536",
                "img_count": 1,
            }).to_dict() | {
                "panel_number": panel["panel_number"],
                "dialogue": panel["dialogue"],
                "sfx": panel["sfx"],
                "shot_type": panel["shot_type"],
                "dynamic_link": panel["dynamic_link"],
                "consistency_anchors": panel["consistency_anchors"],
                "theme": panel.get("theme"),
            })

        return ComicHiDreamBundle(
            character_sheet_request=character_request,
            panel_requests=panel_requests,
        ).to_dict()

    def submit_bundle(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        character_result = self.image_adapter.submit(bundle["character_sheet_request"])
        panel_results = []
        for panel in bundle["panel_requests"]:
            meta = {
                "panel_number": panel["panel_number"],
                "dialogue": panel.get("dialogue"),
                "sfx": panel.get("sfx"),
                "shot_type": panel.get("shot_type"),
                "dynamic_link": panel.get("dynamic_link"),
                "theme": panel.get("theme"),
            }
            result = self.image_adapter.submit(panel)
            panel_results.append({"meta": meta, "request": result["request"], "result": result["result"]})
        return {
            "character_sheet": character_result,
            "panels": panel_results,
        }
