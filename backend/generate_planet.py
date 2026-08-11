"""One-off script to generate the Astro Live cosmic ringed planet using Gemini Nano Banana."""
import asyncio
import base64
import os
from pathlib import Path
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()

PROMPT = (
    "A large spherical futuristic cosmic ringed gas-giant planet, centered composition, "
    "on a deep-space dark background with no other objects. "
    "The planet surface is a rich swirling mixture of DEEP VIOLET, ROYAL PURPLE, "
    "INDIGO BLUE and DEEP BLUE as the DOMINANT colors, with softer accents of magenta, "
    "pink and warm amber-orange only in a few storm-band highlights, and small bright "
    "white cloud highlights scattered across. Jupiter-like horizontal marbled cloud bands "
    "with realistic swirling turbulent storm textures, layered atmospheric wisps and "
    "detailed cyclonic eddies. Bright rim light on the upper-left edge of the planet, "
    "cool violet-blue shadow on the lower-right. Do NOT make the planet pink-dominant, "
    "do NOT make it red or mostly magenta — violet+blue must dominate, pink is only a "
    "secondary accent. "
    "Around the planet a bright glowing Saturn-like ring system made of multiple thin "
    "layered concentric rings, tilted elegantly, wrapping in front of and behind the "
    "planet with proper occlusion. Rings have a strong hot-pink and magenta neon glow "
    "on the inner edge fading to lavender and soft white on the outer edges, with soft "
    "atmospheric bloom and realistic light scattering, smooth and luminous. "
    "Cinematic 3D render, hyper-detailed, sharp, premium futuristic astrology aesthetic, "
    "intense but elegant cosmic glow. "
    "STRICT RULES: ONLY the planet and its rings. No website UI, no text, no cards, "
    "no buttons, no people, no other stars, no other planets, no zodiac chart, no "
    "asteroids, no moons. Centered composition, pure dark cosmic background."
)


async def main() -> None:
    api_key = os.getenv("EMERGENT_LLM_KEY")
    assert api_key, "EMERGENT_LLM_KEY missing"

    chat = LlmChat(
        api_key=api_key,
        session_id="astro-live-planet-mascot",
        system_message="You are an expert cosmic illustrator.",
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
        out_path = out_dir / f"astro-planet-v2-{i}.png"
        out_path.write_bytes(base64.b64decode(img["data"]))
        print("Saved", out_path)


if __name__ == "__main__":
    asyncio.run(main())
