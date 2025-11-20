"""
Vision processing using Gemini
Supports screen capture + camera input
OPTIMIZED: Captures 1 combined screen + 1 camera = 2 images total
WITH DEBUG: Saves captured images to disk for verification
"""

import re
import os
import time
import mss
from PIL import Image
from config.api_keys import GEMINI_KEYS
from config.settings import ENABLE_TTS
import logging
logger = logging.getLogger(__name__)

def needs_vision(query):
    """
    Pattern-based vision detection (no AI model required)
    Returns True if vision is needed
    """
    query_lower = query.lower().strip()
    
    # Vision patterns
    vision_patterns = [
        r'\b(can you|could you|please) ?(see|look at|view|watch|observe)',
        r'\b(see|look at|view|watch) (me|my|this|that|the|it)',
        r'\bwhat (do|can) you see',
        r'\bon (my|the|this) (screen|monitor|display)',
        r'\b(what\'s|what is) on (my|the) (screen|monitor)',
        r'\bwhat (am i|i am|do i)',
        r'\bwhat (is|are) (this|that|these|those|it)',
        r'\b(identify|recognize|detect) (this|that|what)',
        r'\bdescribe (this|that|what|the)',
        r'\b(analyze|examine|inspect) (this|that|the)',
        r'\bwhat (color|colour)',
        r'\bhow many (do you see|can you see|are there)',
        # r'\b(help|fix|debug|solve) (with )?(this|my) (code|error)',
        r'\bwhat (object|item|thing|person|animal|plant)',
        r'\b(who|what) (is in|appears in|can you see in) (this|that|the|my)',
        r'\bholding( in)? (my )?(hand|hands)',
        r'\bwearing\b',
        r'\bcompare (this|these|the)',
        # r'\bdifference between (this|these)',
        # r'\b(background|behind me|in the background|environment|surroundings)',
        r'\bhow (does|do) (it|this|that|they) look',
        r'\b(looks|appears|seems) (like|good|bad|correct|wrong)',
    ]
    
    for pattern in vision_patterns:
        if re.search(pattern, query_lower):
            print(f"Let me see...")
            return True
    
    return False

def save_debug_image(img, filename):
    """Save image for debugging purposes"""
    try:
        debug_folder = "debug_captures"
        if not os.path.exists(debug_folder):
            os.makedirs(debug_folder)
        
        filepath = os.path.join(debug_folder, filename)
        img.save(filepath, quality=95)
        print(f"💾 DEBUG: Saved {filename} ({img.size[0]}x{img.size[1]}px) to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save debug image: {e}")
        return None

def capture_combined_screen(debug=False):
    """
    Capture ALL screens combined into a single image
    Uses monitor index 0 which is the virtual combined monitor in MSS
    
    Args:
        debug: If True, saves the captured image to disk
    """
    try:
        with mss.mss() as sct:
            # Debug: Print all available monitors
            if debug:
                print(f"\n🖥️ DEBUG: Available monitors:")
                for i, monitor in enumerate(sct.monitors):
                    print(f"  Monitor {i}: {monitor}")
            
            # Monitor 0 is the virtual screen that combines all monitors
            monitor = sct.monitors[0]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # print(f"📸 Captured combined screen: {img.size[0]}x{img.size[1]}px")
            
            # Save debug image
            if debug:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                save_debug_image(img, f"screen_combined_{timestamp}.png")
            
            return img
    except Exception as e:
        logger.error(f"Combined screen capture error: {e}")
        raise

def capture_camera(debug=False):
    """
    Capture image from webcam at full quality
    
    Args:
        debug: If True, saves the captured image to disk
    """
    cam = None
    try:
        import cv2
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY)
        
        if not cam.isOpened():
            raise RuntimeError("Camera not accessible")
        
        # Set high resolution
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        # Warm up camera
        for _ in range(2):
            cam.read()
        
        ret, frame = cam.read()
        
        if not ret or frame is None:
            raise RuntimeError("Camera returned empty frame")
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        
        # print(f"📷 Captured camera: {img.size[0]}x{img.size[1]}px")
        
        # Save debug image
        if debug:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            save_debug_image(img, f"camera_{timestamp}.png")
        
        return img
    
    except Exception as e:
        logger.error(f"Camera error: {e}")
        raise
    finally:
        if cam is not None:
            cam.release()

def call_gemini(question, images=None, gui_handler=None):
    """
    Try each Gemini key until one works
    Uses REST API to avoid gRPC issues
    """
    import google.generativeai as genai
    
    if images is None:
        images = []
    
    if not GEMINI_KEYS:
        raise RuntimeError("No Gemini keys configured")
    
    last_exc = None
    
    for idx, key in enumerate(GEMINI_KEYS, 1):
        try:
            api_key = key if isinstance(key, str) else key.get('key') if isinstance(key, dict) else str(key)
            
            genai.configure(api_key=api_key, transport='rest')
            
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            
            custom_prompt = (
                "YOU have human eyes, so give response like human in short and accurate way "
                "but do not say that you are seeing any image or photo, act like you are seeing me sitting beside me."
                f"\n\nUser Query: {question}"
            )
            
            payload = [custom_prompt] + images if images else custom_prompt
            
            print("Observing...")
            
            resp = model.generate_content(
                payload,
                generation_config={
                    "temperature": 0,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            
            # Extract text
            text = None
            try:
                text = resp.text
            except Exception:
                try:
                    text = resp.candidates[0].content.parts[0].text
                except Exception:
                    text = str(resp)
            
            if not text or text.strip() == "":
                raise ValueError("Empty response from Gemini")
            
            return text.strip()
        
        except Exception as e:
            last_exc = e
            logger.warning(f"Gemini key {idx} failed: {e}")
            time.sleep(0.5)
            continue
    
    error_msg = f"All {len(GEMINI_KEYS)} Gemini keys failed. Last error: {last_exc}"
    logger.error(error_msg)
    raise RuntimeError(error_msg) from last_exc
def capture_screen_region(region: tuple = None, debug: bool = False):
    """
    Capture specific screen region instead of all monitors
    
    Args:
        region: (left, top, width, height) tuple, or None for full screen
        debug: Save captured image for debugging
    """
    try:
        import mss
        
        with mss.mss() as sct:
            if region:
                # Capture specific region
                monitor = {
                    'left': region[0],
                    'top': region[1],
                    'width': region[2],
                    'height': region[3]
                }
            else:
                # Capture all screens
                monitor = sct.monitors[0]
            
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            if debug:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                save_debug_image(img, f"region_{timestamp}.png")
            
            return img
    except Exception as e:
        logger.error(f"Region capture error: {e}")
        raise

def Vision_main(Query, gui_handler=None, debug=False, region=None):
    """
    Enhanced vision with optional region selection
    
    Args:
        Query: User's question
        gui_handler: GUI handler
        debug: Save debug images
        region: Optional (left, top, width, height) to capture specific region
    """
    try:
        question = Query.strip()
        if not question:
            return
        
        imgs = []
        
        # Capture screen (with optional region)
        try:
            if region:
                screen_img = capture_screen_region(region, debug=debug)
            else:
                screen_img = capture_combined_screen(debug=debug)
            imgs.append(screen_img)
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            if gui_handler:
                gui_handler.show_terminal_output(f"❌ Screen capture failed: {e}", color="red")
            return
        
        # Capture camera (optional - only if specifically requested)
        if "camera" in Query.lower() or "webcam" in Query.lower():
            try:
                cam_img = capture_camera(debug=debug)
                imgs.append(cam_img)
            except Exception as e:
                logger.warning(f"Camera unavailable: {e}")
        # Verify we have images
        if not imgs:
            error_msg = "❌ Failed to capture any images"
            logger.error(error_msg)
            if gui_handler:
                gui_handler.show_terminal_output(error_msg, color="red")
            return
        
        if debug:
            print(f"✅ DEBUG: Images saved to 'debug_captures' folder - check them to verify screen capture!")
        
        # Call Gemini
        try:
            gemini_resp = call_gemini(question, imgs, gui_handler)
            
            # Show response
            if gui_handler:
                gui_handler.show_terminal_output(f"💬 {gemini_resp}", color="green")
            
            # --- START: CORRECTED CODE ---
            # Stop mic if active and use the NEW state manager
            if gui_handler:
                # Just reset the visual state, don't kill the listener logic
                gui_handler.queue_gui_task(lambda: gui_handler._update_button_state("idle"))
                # Restore volume so user can hear the description
                try:
                    gui_handler.volume_controller.restore_volume()
                except: pass
            # --- END: CORRECTED CODE ---
            
            # ✅ Speak response (if TTS enabled)
            if ENABLE_TTS:
                gui_handler.audio_coordinator.speak(gemini_resp)
        
        except Exception as e:
            error_msg = f"❌ Gemini analysis failed: {e}"
            logger.error(error_msg)
            
            if gui_handler:
                gui_handler.show_terminal_output(error_msg, color="red")
    
    except Exception as e:
        error_msg = f"❌ Vision_main error: {e}"
        logger.error(error_msg)
        
        if gui_handler:
            gui_handler.show_terminal_output(error_msg, color="red")
