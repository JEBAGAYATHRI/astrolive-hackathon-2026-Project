"""One-off script to generate the Astro Live cosmic owl mascot using Gemini Nano Banana."""
import asyncio
import base64
import os
from pathlib import Path
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()

PROMPT = (
    "A premium, futuristic 3D astrology mascot owl, centered and fully visible, "
    "shown from the front on a clean transparent-like deep-space background. "
    "The owl's feathers are richly multi-colored with luminous white, soft pink, "
    "magenta, lavender, violet, purple, and subtle blue/cyan tones blended naturally "
    "throughout the plumage. Colors are MIXED across the feathers with soft transitions, "
    "bright white and pink highlights on the chest, cheeks and brow, deep violet and "
    "blue shadows underneath the wings and around the outer feather edges. "
    "Feathers are highly detailed, layered, fluffy, dimensional, and luminous with "
    "subtle glowing feather edges, soft reflected pink and violet rim light, realistic "
    "specular highlights and gentle shadows, and a magical celestial glow that halos "
    "the whole body. The eyes are large, expressive, glowing with a soft violet-cyan "
    "inner light. Small ambient star particles float around the silhouette. "
    "Cinematic studio lighting, rich material depth, hyper-detailed, polished, "
    "premium quality, sharp focus, high resolution, cohesive with a cosmic Netflix/Apple "
    "level astrology dashboard aesthetic. "
    "STRICT RULES: Do NOT simplify the owl into a flat icon, basic vector, cartoon or "
    "single-color purple owl. Do NOT redesign the palette — preserve the pink + white "
    "+ violet + blue color mixing and luminous feather detailing. Output ONLY the owl, "
    "centered, no website, no UI, no cards, no text, no planets, no buttons."
)


async def main() -> None:
    api_key = os.getenv("EMERGENT_LLM_KEY")
    assert api_key, "EMERGENT_LLM_KEY missing"

    chat = LlmChat(
        api_key=api_key,
        session_id="astro-live-owl-mascot",
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
        out_path = out_dir / f"astro-owl-{i}.png"
        out_path.write_bytes(base64.b64decode(img["data"]))
        print("Saved", out_path)


if __name__ == "__main__":
    asyncio.run(main())
