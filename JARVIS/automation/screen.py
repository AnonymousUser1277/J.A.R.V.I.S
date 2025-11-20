"""
Screen capture and OCR utilities
Click/move cursor to text on screen
"""

import re
import cv2
import numpy as np
import pyautogui
import pytesseract
from PIL import ImageGrab
from config.loader import settings
# Configure Tesseract path
import os
tesseract_path = settings.tesseract_cmd
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    print("⚠️ Tesseract not found - OCR features disabled")
    # Disable OCR functions gracefully

def parse_command_code(command):
    """Parse click/move commands"""
    command = command.lower().strip()
    
    if "click" in command:
        match = re.search(r"click\s+(?:on\s+)?(.+)", command)
        if match:
            return {"action": "click", "target_text": match.group(1).strip()}
    
    elif "move" in command:
        match = re.search(r"move\s+(?:the\s+cursor\s+to\s+)?(.+)", command)
        if match:
            return {"action": "move", "target_text": match.group(1).strip()}
    
    return {"action": "click", "target_text": command}

def take_screenshot():
    """Take screenshot with preprocessing"""
    img = ImageGrab.grab(all_screens=True)
    original_size = img.size
    img_np = np.array(img)
    img_gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    img_inverted = cv2.bitwise_not(img_gray)
    img_blur = cv2.GaussianBlur(img_inverted, (3, 3), 0)
    _, img_thresh = cv2.threshold(img_blur, 127, 255, cv2.THRESH_BINARY)
    
    scale_factor = 1.5
    width = int(img_thresh.shape[1] * scale_factor)
    height = int(img_thresh.shape[0] * scale_factor)
    img_scaled = cv2.resize(img_thresh, (width, height), interpolation=cv2.INTER_CUBIC)
    
    return img_scaled, original_size, scale_factor

def detect_text_positions(image, target_text, original_size, scale_factor):
    """Detect text positions using OCR"""
    custom_config = r'--oem 1 --psm 11'
    
    try:
        data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            config=custom_config
        )
        
        target_words = target_text.lower().strip().split()
        positions = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            word = data['text'][i]
            if not word.strip():
                continue
            
            conf = int(data['conf'][i])
            if conf < 10:
                continue
            
            word_clean = word.lower().strip()
            matched = False
            matched_text = word
            
            # Single word match
            if word_clean == target_text.lower():
                matched = True
            elif target_text.lower() in word_clean:
                matched = True
            elif word_clean in target_text.lower() and len(word_clean) > 2:
                matched = True
            
            # Multi-word match
            if not matched and len(target_words) > 1 and target_words[0] == word_clean:
                match = True
                for j, target in enumerate(target_words[1:], 1):
                    if i + j >= n_boxes:
                        match = False
                        break
                    next_word = data['text'][i + j].lower().strip()
                    if next_word != target:
                        match = False
                        break
                
                if match:
                    matched = True
                    matched_text = " ".join(data['text'][i:i + len(target_words)])
            
            if matched:
                x_scaled = data['left'][i] + data['width'][i] // 2
                y_scaled = data['top'][i] + data['height'][i] // 2
                x_original = int(x_scaled / scale_factor)
                y_original = int(y_scaled / scale_factor)
                positions.append((x_original, y_original, matched_text, conf))
        
        # Sort by confidence
        positions.sort(key=lambda x: x[3], reverse=True)
        
        # Remove duplicates
        unique_positions = []
        for pos in positions:
            is_duplicate = False
            for existing in unique_positions:
                if abs(pos[0] - existing[0]) < 10 and abs(pos[1] - existing[1]) < 10:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_positions.append((pos[0], pos[1], pos[2]))
        
        return unique_positions
    
    except Exception as e:
        return []

def click_on_text(positions):
    """Click on detected text position"""
    if not positions:
        return False
    
    x, y, word = positions[0]
    pyautogui.moveTo(x, y, duration=0)
    pyautogui.click()
    return True

def click_on_any_text_on_screen(text):
    """Main function: Click on any text on screen"""
    if not text:
        return
    
    parsed = parse_command_code(text)
    
    if parsed['action'] == 'click' and 'target_text' in parsed:
        img, original_size, scale_factor = take_screenshot()
        target_text = parsed['target_text']
        positions = detect_text_positions(img, target_text, original_size, scale_factor)
        click_on_text(positions)

def move_cursor_to_text(text):
    """Move cursor to text on screen"""
    if not text:
        return
    
    parsed = parse_command_code(text)
    
    if parsed['action'] == 'move' and 'target_text' in parsed:
        img, original_size, scale_factor = take_screenshot()
        target_text = parsed['target_text']
        positions = detect_text_positions(img, target_text, original_size, scale_factor)
        
        if positions:
            x, y, word = positions[0]
            pyautogui.moveTo(x, y, duration=0)
            return True
        else:
            print("target not found")
            return False