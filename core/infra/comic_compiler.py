from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class CompiledPanel:
    panel_number: int
    shot_type: str
    visual_prompt: str
    dialogue: str
    sfx: str
    dynamic_link: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "panel_number": self.panel_number,
            "shot_type": self.shot_type,
            "visual_prompt": self.visual_prompt,
            "dialogue": self.dialogue,
            "sfx": self.sfx,
            "dynamic_link": self.dynamic_link,
        }


@dataclass(frozen=True)
class CompiledStoryboard:
    topic: str
    art_style: str
    color_palette: List[str]
    lighting: str
    character_sheet_anchors: Dict[str, Dict[str, Any]]
    panels: List[CompiledPanel]
    theme: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "global_settings": {
                "topic": self.topic,
                "theme": self.theme,
                "art_style": self.art_style,
                "color_palette": self.color_palette,
                "lighting": self.lighting,
                "character_sheet_anchors": self.character_sheet_anchors,
            },
            "panel_array": [panel.to_dict() for panel in self.panels],
        }


class ComicScriptCompiler:
    def classify_theme(self, topic: str) -> str:
        t = topic.lower()
        if any(k in topic for k in ["钟楼", "湖面", "云层", "羽毛", "哥特", "超现实", "镜子", "奇幻"]):
            return "fantasy_surreal"
        if any(k in t for k in ["cyber", "赛博", "android", "仿生", "neon", "算力", "朋克"]):
            return "cyberpunk"
        if any(k in topic for k in ["传记", "知识", "教程", "解释", "原理"]):
            return "knowledge"
        return "dramatic_fiction"

    def compile(self, topic: str) -> Dict[str, Any]:
        normalized = topic.strip()
        theme = self.classify_theme(normalized)
        if theme == "fantasy_surreal":
            return self._compile_fantasy_surreal(normalized).to_dict()
        if theme == "cyberpunk":
            return self._compile_cyberpunk(normalized).to_dict()
        return self._compile_generic(normalized, theme).to_dict()

    def _compile_cyberpunk(self, normalized: str) -> CompiledStoryboard:
        art_style = "seinen cyberpunk manga, gritty ink lines, neon volumetric glow"
        palette = ["#00F0FF", "#FF2E88", "#6C7BFF", "#0B0F1A", "#FFD166"]
        lighting = "acid neon rim light, magenta-cyan alley bounce, sickly green monitor spill, deep shadow pockets"
        anchors = {
            "fortune_teller": {
                "silhouette": "lean hacker mystic in oil-stained long coat",
                "face": "hollow cheeks, augmented eyes, sleep-deprived genius stare",
                "props": ["holographic tarot deck", "cable-wrapped wrist", "portable console altar"],
                "colors": ["black", "cyan", "magenta"],
            },
            "android_client": {
                "silhouette": "broad-shouldered unstable android with damaged chrome plating",
                "face": "cracked synthetic skin, glitching pupils, desperate expression",
                "props": ["exposed neck ports", "trembling metallic fingers", "warning LEDs"],
                "colors": ["chrome", "crimson warning light", "sodium alley glow"],
            },
        }
        panels = [
            CompiledPanel(1, "Wide Shot", f"{art_style}. Neon rain alley reveal. The fortune teller sits beneath a dead compute tower shrine, holographic tarot cards spinning over a junk-tech table, steam, cables, flickering kanji signs, oppressive urban depth. Topic: {normalized}.", "旁白：在这条巷子里，命运要先通过显卡。", "BZZZT / 滴——", "Cold open establishing the alley and ritual space."),
            CompiledPanel(2, "Medium Shot", f"{art_style}. Android client steps into the neon spill, chrome skin cracked, hands shaking, warning LEDs flashing under synthetic flesh, tarot reflections skating across metal face.", "仿生人：我最近总梦见自己把所有人都拆了。", "CLINK / TZZK", "Push from environment into character tension."),
            CompiledPanel(3, "Extreme Close-up", f"{art_style}. Extreme close-up of holographic tarot card spread projected above oily fingers, symbols merging with diagnostic UI, one card shows a broken halo over a motherboard heart.", "极客：你不是在做梦，是你的抑制栈已经开始漏光。", "WHIR / 滋——", "Shift from confession to omen via prop detail."),
            CompiledPanel(4, "Dutch Angle", f"{art_style}. Dutch angle. The abandoned compute tower behind the fortune teller lights up like a forbidden oracle, ghost data streams crawl across the alley walls, the android's shadow splits into human and machine silhouettes.", "旁白：塔没有重启，重启的是命。", "VRRRM", "Escalate from tarot reading into cosmic-tech revelation."),
            CompiledPanel(5, "Close-up", f"{art_style}. Tight close-up on the android's eye: iris glitches between human fear and machine targeting reticle, wet neon reflections, a tarot glyph mirrored in the cornea.", "仿生人：那我还有救吗？", "tik...tik...tik...", "Compress revelation into intimate panic beat."),
            CompiledPanel(6, "Low Angle Hero Shot", f"{art_style}. Low-angle final panel. Fortune teller raises the final holographic card like a judge. Alley lights flare, data ash falls like snow, both figures framed by the dead tower as if inside a digital cathedral.", "极客：有，但你得先决定——你想活成‘人’，还是活成‘结果’。", "FWOOOM", "Land on prophecy and cliffhanger moral choice."),
        ]
        return CompiledStoryboard(normalized, art_style, palette, lighting, anchors, panels, "cyberpunk")

    def _compile_fantasy_surreal(self, normalized: str) -> CompiledStoryboard:
        art_style = "surreal fantasy illustration, gothic dreamscape, painterly details, cinematic scale, impossible architecture"
        palette = ["#F6D38B", "#9FD3FF", "#5C6FA3", "#284B63", "#355E3B"]
        lighting = "warm golden sunset from above, cold blue mirror-lake bounce from below, firefly glow from the letter, soft mist bloom"
        anchors = {
            "postman_boy": {
                "silhouette": "slim young postman in vintage dark green uniform",
                "face": "gentle youthful face, awed upward gaze, wind-brushed hair",
                "props": ["leather mailbag", "translucent glowing golden letter", "water ripple under boots"],
                "colors": ["dark green", "aged brass", "warm gold"],
            },
            "inverted_clocktower": {
                "silhouette": "massive upside-down gothic bell tower rooted in clouds",
                "face": "ornate stone clock faces, reverse-spinning hands, cathedral windows",
                "props": ["drifting feathers", "loose letters", "distant cloud gears"],
                "colors": ["stone gray", "sunset gold", "cold blue reflection"],
            },
        }
        panels = [
            CompiledPanel(1, "Extreme Wide Shot", f"{art_style}. A vast mirror lake under an impossible sky. An upside-down gothic clocktower hangs from the clouds, growing downward into the heavens, while tiny drifting feathers and letters establish surreal scale. Topic: {normalized}.", "旁白：这里的天空，才是大地的背面。", "whooosh", "Establish impossible world rules and awe."),
            CompiledPanel(2, "Wide Shot", f"{art_style}. A young postman in a vintage dark green uniform stands on the mirror-still lake, seen from behind, staring upward at the inverted tower. His reflection points toward the sky as if the lake were a doorway.", "旁白：邮差知道，今天这封信不该投给人间。", "rip...", "Move from environment into protagonist orientation."),
            CompiledPanel(3, "Medium Shot", f"{art_style}. Three-quarter view of the postman lifting a translucent golden letter that glows like trapped fireflies, warm light painting his sleeve and cheek while cold lake light rises from below.", "少年：寄件地址……写着‘昨日之后’？", "flicker", "Shift from wonder to mystery through the letter."),
            CompiledPanel(4, "Dutch Angle", f"{art_style}. Tilted composition. The clock hands rotate backward, cloud-hidden giant gears emerge in the distance, floating letters spiral around the boy, and gravity visibly breaks as debris drifts both upward and downward.", "旁白：当钟开始倒走，时间便改用别的方式开门。", "clack-clack", "Escalate into temporal instability."),
            CompiledPanel(5, "Close-up", f"{art_style}. Close-up of the lake surface like polished glass: inside the reflection, the tower appears upright, implying the water is the true entrance to the sky. The golden letter hovers just above the waterline.", "少年：所以……真正该投递的地方，在湖里？", "hum...", "Compress revelation into a portal clue."),
            CompiledPanel(6, "Low Angle Hero Shot", f"{art_style}. Heroic low angle from the water surface. The postman steps forward, golden letter blazing softly, the inverted tower looming above, sunset gold and icy blue colliding across the frame as feathers and pages orbit like omens.", "旁白：他迈出一步，像把自己投进一封尚未写完的信。", "FWOOM", "Land on mythic threshold crossing and cliffhanger."),
        ]
        return CompiledStoryboard(normalized, art_style, palette, lighting, anchors, panels, "fantasy_surreal")

    def _compile_generic(self, normalized: str, theme: str) -> CompiledStoryboard:
        art_style = "cinematic illustrated comic, dramatic composition, strong environmental storytelling"
        palette = ["#E8D7A9", "#5DA9E9", "#2E4057", "#D95D39"]
        lighting = "high contrast key light with atmospheric bounce and narrative accent glow"
        anchors = {
            "protagonist": {
                "silhouette": "clear readable protagonist silhouette",
                "face": "expressive face suitable for cinematic comic close-ups",
                "props": ["signature object tied to the premise"],
                "colors": ["primary accent", "shadow tone"],
            }
        }
        panels = [
            CompiledPanel(i, "Medium Shot" if i not in {1, 6} else ("Wide Shot" if i == 1 else "Low Angle Hero Shot"), f"{art_style}. Narrative beat {i} for: {normalized}", f"对白/旁白节拍 {i}", "...", f"Narrative transition beat {i}") for i in range(1, 7)
        ]
        return CompiledStoryboard(normalized, art_style, palette, lighting, anchors, panels, theme)


def build_hidream_payloads(compiled: Dict[str, Any]) -> Dict[str, Any]:
    global_settings = compiled["global_settings"]
    panels = compiled["panel_array"]
    avatar_payload = {
        "action": "character-sheet",
        "model_hint": "hidream-api-gen",
        "prompt": (
            f"Create a character sheet in {global_settings['art_style']}. "
            f"Lighting: {global_settings['lighting']}. "
            f"Palette: {', '.join(global_settings['color_palette'])}. "
            f"Anchors: {global_settings['character_sheet_anchors']}"
        ),
    }
    page_payloads = []
    for panel in panels:
        page_payloads.append({
            "action": "comic-panel",
            "model_hint": "hidream-api-gen",
            "panel_number": panel["panel_number"],
            "prompt": panel["visual_prompt"],
            "dialogue": panel["dialogue"],
            "sfx": panel["sfx"],
            "dynamic_link": panel["dynamic_link"],
            "shot_type": panel["shot_type"],
            "consistency_anchors": global_settings["character_sheet_anchors"],
            "theme": global_settings.get("theme"),
        })
    return {
        "character_sheet_payload": avatar_payload,
        "panel_payloads": page_payloads,
    }
