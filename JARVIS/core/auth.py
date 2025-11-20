"""
Face recognition authentication system
"""

import os
import cv2
import numpy as np
import face_recognition
import time

def register_face():
    """Register face with proper resource management"""
    video_capture = None
    try:
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            raise RuntimeError("❌ Could not open camera")
        
        ret, frame = video_capture.read()
        
        if not ret or frame is None:
            raise RuntimeError("❌ Failed to capture frame")
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_encodings = face_recognition.face_encodings(rgb_frame)
        
        if not face_encodings:
            raise RuntimeError("❌ No face detected. Please face the camera.")
        
        if len(face_encodings) > 1:
            print("⚠️ Multiple faces detected, using first")
        
        np.save('known_face.npy', face_encodings[0])
        print("✅ Face registered successfully!\n")
        return True
        
    except Exception as e:
        print(f"❌ Face registration failed: {e}")
        return False
        
    finally:
        if video_capture is not None:
            video_capture.release()
            cv2.destroyAllWindows()

def login_with_face():
    """Login with face - improved error handling"""
    if not os.path.exists('known_face.npy'):
        raise FileNotFoundError("❌ No registered face found!")
    
    known_encoding = np.load('known_face.npy')
    video_capture = None
    
    try:
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            raise RuntimeError("❌ Could not open camera")
        
        start_time = time.time()
        timeout = 30  # seconds
        
        while True:
            ret, frame = video_capture.read()
            
            if not ret or frame is None:
                print("⚠️ Failed to capture frame, retrying...")
                continue
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            for encoding in face_encodings:
                match = face_recognition.compare_faces([known_encoding], encoding)[0]
                if match:
                    print("✅ Face authentication successful!\n")
                    return True
            
            cv2.imshow('Face Authentication', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("❌ Authentication cancelled by user")
                return False
            
            if time.time() - start_time > timeout:
                print(f"⏱️ Timeout: No face detected within {timeout} seconds")
                return False
        
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
        
    finally:
        if video_capture is not None:
            video_capture.release()
        cv2.destroyAllWindows()

def authenticate_user(startup_ui=None):
    """Main authentication flow"""
    if startup_ui:
        startup_ui.update_status("Checking authentication...\n")
    
    if not os.path.exists('known_face.npy'):
        if startup_ui:
            startup_ui.update_status("No known face found, registering...")
        print("📸 Registering face...")
        register_face()
        print("✅ Face registered successfully!")
    
    if startup_ui:
        startup_ui.update_status("Verifying face authentication...\n")
    
    print("🔐 Starting face authentication...\n")
    success = login_with_face()
    
    if success:
        print("✅ Login successful!\n")
    
    return success