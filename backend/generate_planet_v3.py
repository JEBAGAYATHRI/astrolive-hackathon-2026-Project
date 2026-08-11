"""Generate additional cosmic ringed planet variants."""
import asyncio
import base64
import os
from pathlib import Path
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()

PROMPT = (
    "A large spherical futuristic cosmic ringed planet, centered composition, "
    "on a pure deep-space dark background with absolutely no other objects. "
    "The planet's surface is a rich luminous mixture of pink, magenta, violet, "
    "lavender, indigo blue and bright white, with multiple colors naturally blended "
    "together in swirling cloud-like turbulent Jupiter-style storm bands. "
    "Bright pink and pearly white highlights on the illuminated hemisphere, deep "
    "violet and indigo blue in the shaded areas, with delicate magenta wisps and "
    "lavender atmospheric layers. Layered glowing patterns, detailed cyclonic "
    "eddies, high-frequency cloud texture. Preserve the vibrant color richness — "
    "do NOT make the planet mostly plain purple or plain blue, do NOT make it a "
    "basic 3D sphere. Bright rim light around the planet edges. "
    "Surround the planet with a bright glowing Saturn-like ring system, tilted "
    "elegantly, made of multiple thin layered concentric rings that wrap in front "
    "of and behind the planet with proper occlusion. The rings have a strong "
    "neon glow of hot pink, magenta, lavender and pearly white, with soft "
    "atmospheric bloom, realistic light scattering, smooth and luminous, "
    "elegantly dimensional. "
    "Magical cosmic lighting, intense but elegant cosmic glow, cinematic 3D "
    "render, hyper-detailed, sharp, premium futuristic astrology aesthetic. "
    "STRICT RULES: ONLY the planet and its rings. No website UI, no text, no "
    "cards, no buttons, no people, no other stars, no other planets, no zodiac "
    "chart, no asteroids, no moons. Centered composition."
)


async def main() -> None:
    api_key = os.getenv("EMERGENT_LLM_KEY")
    assert api_key, "EMERGENT_LLM_KEY missing"

    chat = LlmChat(
        api_key=api_key,
        session_id="astro-live-planet-v3",
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
        out_path = out_dir / f"astro-planet-v3-{i}.png"
        out_path.write_bytes(base64.b64decode(img["data"]))
        print("Saved", out_path)


if __name__ == "__main__":
    asyncio.run(main())
