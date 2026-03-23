import sys
import os
import time
import subprocess
import glob
import urllib.request
import json
sys.path.insert(0, "/root/.openclaw/workspace/skills/hidream-api-gen")
from scripts.kling import run as run_kling

TOKEN = "sk-dCDbwg87p4Lw3R4hZWqlhaag6PW1JCEI"

scenes = [
    "Scene 1: A massive generational starship drifting silently through deep space, illuminated by the cold light of distant stars.",
    "Scene 2: Inside the ship, a vast cryosleep chamber stretching into infinity. A single pod begins to thaw.",
    "Scene 3: A lone astronaut awakens, coughing, floating in zero gravity. The ship's emergency lights pulse a dim red.",
    "Scene 4: The astronaut floats through a ruined hydroponics bay, withered plants floating like ghosts in the dark.",
    "Scene 5: Reaching the bridge. The main viewscreen is shattered, exposing a glowing, unnatural nebula outside.",
    "Scene 6: The astronaut checks the navigation logs. The ship has been traveling for a million years.",
    "Scene 7: A strange, biomechanical growth covers the engine room. It pulses with an eerie, blue bioluminescence.",
    "Scene 8: The astronaut discovers they are not alone. A shadowy figure moves behind the frozen coolant pipes.",
    "Scene 9: The astronaut attempts to send a distress signal, but the comms console displays an alien language.",
    "Scene 10: The ship slowly descends into the swirling eye of the glowing nebula, disappearing completely."
]

def generate_video(prompt, index, max_retries=3):
    for attempt in range(max_retries):
        try:
            print(f"Generating scene {index} (Attempt {attempt + 1})...", flush=True)
            result = run_kling(
                version="Q2.5T-std",
                prompt=prompt,
                duration=5,
                wh_ratio="16:9",
                authorization=TOKEN
            )
            print(f"Result for scene {index}: {result}", flush=True)
            
            url = result.get('output', {}).get('video_url')
            if url:
                file_path = f"/root/.openclaw/workspace/scene_{index}.mp4"
                print(f"Downloading {url} to {file_path}...", flush=True)
                urllib.request.urlretrieve(url, file_path)
                return file_path
            return result
        except Exception as e:
            print(f"Error generating scene {index}: {e}", flush=True)
            time.sleep(10)
    return None

results = []
for i, scene in enumerate(scenes, 1):
    res = generate_video(scene, i)
    results.append({"scene": i, "result": res})

with open("/root/.openclaw/workspace/kling_results.txt", "w") as f:
    for res in results:
        f.write(f"Scene {res['scene']}: {res['result']}\n")

print("All tasks completed.", flush=True)

# Package and send
print("Packaging videos...", flush=True)
os.system("tar -czf /root/.openclaw/workspace/echoes_of_deep_space.tar.gz /root/.openclaw/workspace/scene_*.mp4 /root/.openclaw/workspace/kling_results.txt")

print("Sending email...", flush=True)
cmd = [
    "python3", "/root/.openclaw/workspace/skills/qqmail/scripts/qqmail.py", "send",
    "--to", "zhy20152015@qq.com",
    "--subject", "Echoes of Deep Space - Sci-Fi Video Scenes",
    "--body", "Attached is the completed video generation task for the 10-scene hard sci-fi sequence, Echoes of Deep Space. The archive contains the generated MP4 files and a text summary.",
    "--attachment", "/root/.openclaw/workspace/echoes_of_deep_space.tar.gz"
]

env = os.environ.copy()
env["QQMAIL_USER"] = "harry_zhu@qq.com"
env["QQMAIL_AUTH_CODE"] = "lzupkjrihisrcabj"

result = subprocess.run(cmd, env=env, capture_output=True, text=True)
print(f"Email send result: {result.stdout}", flush=True)
if result.stderr:
    print(f"Email send error: {result.stderr}", flush=True)

