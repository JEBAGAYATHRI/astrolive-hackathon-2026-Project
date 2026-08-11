"""Generate the cosmic planet with a TRUE transparent background."""
import asyncio
import base64
import os
from pathlib import Path
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()

PROMPT = (
    "A single cosmic ringed planet with luminous swirling pink, magenta, violet, "
    "lavender, indigo blue and white cloud bands, wrapped by a bright neon "
    "hot-pink and lavender Saturn-like ring system with multiple thin concentric "
    "layered rings. Cinematic 3D render, hyper-detailed, sharp, premium "
    "futuristic astrology aesthetic. "
    "CRITICAL: The output MUST be a PNG with a FULLY TRANSPARENT ALPHA BACKGROUND. "
    "NO black background, NO dark navy background, NO rectangular frame, NO "
    "stars, NO nebula, NO other objects behind or beside the planet. Only the "
    "planet and its rings floating on pure alpha-transparent empty pixels. "
    "The area outside the planet+ring silhouette must be transparent (alpha=0), "
    "not black, not dark, not anything — completely see-through. "
    "Centered composition, only the planet+ring subject visible."
)


async def main() -> None:
    api_key = os.getenv("EMERGENT_LLM_KEY")
    assert api_key, "EMERGENT_LLM_KEY missing"

    chat = LlmChat(
        api_key=api_key,
        session_id="astro-live-planet-transparent",
        system_message="You are an expert cosmic illustrator that outputs images with alpha-transparent backgrounds.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(
        modalities=["image", "text"]
    )

    msg = UserMessage(text=PROMPT)
    text, images = await chat.send_message_multimodal_response(msg)
    print("Text response head:", (text or "")[:120])
    if not images:
        raise SystemExit("No images returned")

    out_dir = Path("/app/frontend/public/mascot")
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, img in enumerate(images):
        out_path = out_dir / f"astro-planet-clean-{i}.png"
        out_path.write_bytes(base64.b64decode(img["data"]))
        print("Saved", out_path)


if __name__ == "__main__":
    asyncio.run(main())
