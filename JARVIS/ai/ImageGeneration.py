"""
Enhanced image generation with multiple models and styles
"""
import os
from random import randint
from huggingface_hub import InferenceClient
from config.api_keys import HUGGINGFACE_KEYS
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Available models
MODELS = {
    'sdxl': "stabilityai/stable-diffusion-xl-base-1.0",
    'sd2': "stabilityai/stable-diffusion-2-1",
    'openjourney': "prompthero/openjourney",
    'realistic': "SG161222/Realistic_Vision_V5.1_noVAE",
    'anime': "Linaqruf/animagine-xl-3.0",
}

# Style presets
STYLES = {
    'realistic': "photorealistic, ultra detailed, 8k, professional photography",
    'artistic': "artistic, oil painting, masterpiece, dramatic lighting",
    'anime': "anime style, manga, vibrant colors, detailed",
    'cyberpunk': "cyberpunk, neon lights, futuristic, dark atmosphere",
    'fantasy': "fantasy art, magical, ethereal, detailed environment",
    'minimalist': "minimalist, clean, simple, modern",
}

# Ensure output folder exists
try:
    downloads_path = str(Path.home() / "Downloads")
    OUTPUT_FOLDER = downloads_path
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
except Exception as e:
    logger.error(f"Could not create or access Downloads folder: {e}")
    OUTPUT_FOLDER = "generated_images"
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def get_hf_client():
    """Initializes the Hugging Face client with a key from config."""
    if not HUGGINGFACE_KEYS:
        logger.error("❌ No Hugging Face API keys found in config.")
        return None
    
    api_key = HUGGINGFACE_KEYS[0].get('key')
    if not api_key:
        logger.error("❌ Hugging Face API key is empty.")
        return None
        
    try:
        return InferenceClient(token=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize HuggingFace InferenceClient: {e}")
        return None


client = get_hf_client()


def generate_single_image(
    prompt: str,
    model: str = 'sdxl',
    style: str = None,
    negative_prompt: str = None,
    width: int = 1024,
    height: int = 1024
):
    """
    Generate a single image with advanced options
    
    Args:
        prompt: Image description
        model: Model to use (sdxl, sd2, openjourney, realistic, anime)
        style: Style preset (realistic, artistic, anime, cyberpunk, fantasy, minimalist)
        negative_prompt: Things to avoid in the image
        width: Image width
        height: Image height
    """
    if not client:
        print("❌ Image generation is unavailable. Hugging Face client not initialized.")
        return None

    try:
        seed = randint(0, 1_000_000)
        
        # Build full prompt with style
        full_prompt = prompt
        if style and style in STYLES:
            full_prompt = f"{prompt}, {STYLES[style]}"
        
        # Add quality boosters
        full_prompt = f"masterpiece, best quality, {full_prompt}, sharp focus, high resolution"
        
        # Default negative prompt
        if not negative_prompt:
            negative_prompt = (
                "blurry, low quality, distorted, deformed, ugly, bad anatomy, "
                "watermark, signature, text, worst quality, low res"
            )
        
        # Get model path
        model_path = MODELS.get(model, MODELS['sdxl'])
        
        logger.info(f"🎨 Generating image with {model} model...")
        print(f"🎨 Generating: {prompt[:50]}...")
        
        # Generate the image
        image = client.text_to_image(
            full_prompt,
            model=model_path,
            negative_prompt=negative_prompt,
            width=width,
            height=height
        )
        
        # Save the image
        safe_prompt = "".join(c for c in prompt if c.isalnum() or c in " _-").rstrip()
        filename = f"{safe_prompt[:50]}_{seed}_{model}.png"
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        image.save(file_path)
        
        # print(f"✅ Image saved: {filename}")
        
        # Open the downloads folder
        os.startfile(OUTPUT_FOLDER)
        
        return file_path
        
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        logger.error(f"Image generation failed for prompt '{prompt}': {e}", exc_info=True)
        return None


def GenerateImages(prompt: str, model: str = 'sdxl', style: str = None):
    """
    Main entry point for image generation
    
    Args:
        prompt: Image description
        model: Model name (sdxl, sd2, openjourney, realistic, anime)
        style: Style preset
    """
    return generate_single_image(prompt, model=model, style=style)


def list_available_models():
    """List all available image generation models"""
    return list(MODELS.keys())


def list_available_styles():
    """List all available style presets"""
    return list(STYLES.keys())


if __name__ == "__main__":
    print("🎨 Enhanced Image Generation")
    print(f"Available models: {', '.join(list_available_models())}")
    print(f"Available styles: {', '.join(list_available_styles())}")
    print()
    
    while True:
        try:
            prompt_input = input("Enter a prompt (or 'exit'): ")
            if not prompt_input.strip() or prompt_input.lower() == 'exit':
                break
            
            # Optional: model selection
            print(f"Models: {', '.join(list_available_models())}")
            model_input = input("Select model (or press Enter for SDXL): ").strip().lower()
            model = model_input if model_input in MODELS else 'sdxl'
            
            # Optional: style selection
            print(f"Styles: {', '.join(list_available_styles())}")
            style_input = input("Select style (or press Enter for none): ").strip().lower()
            style = style_input if style_input in STYLES else None
            
            print("\n🚀 Generating Image...")
            filepath = GenerateImages(prompt_input, model=model, style=style)
            if filepath:
                print(f"✅ Image saved to: {filepath}")
            print()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")