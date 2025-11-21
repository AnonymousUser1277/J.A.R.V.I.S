"""
CRITICAL FIXES Applied - Speech-to-Text
Fixes: Page load timing, session errors, restart storms
ADDED: FINAL, Stabilized Real-time Mic Watchdog with Precise Path Matching
"""

import time
import threading
import os
import psutil
import tempfile
import shutil
import atexit
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from config.settings import settings
import gc
import socket

if os.name == 'nt':
    import winreg
    import ctypes

logger = logging.getLogger(__name__)

class SpeechToTextListener:
    """FORTIFIED STT with a FINAL, Stabilized, Path-Aware REAL-TIME Mic Watchdog"""
    
    def __init__(self, website_path=settings.stt_website_url, language=settings.stt_language, gui_handler=None):
        # ... (the __init__ is identical to the previous version)
        self.lock = threading.RLock()
        self.website_path = website_path
        self.language = language
        self.gui_handler = gui_handler
        self.driver_pid = None
        self.chrome_pids = set()
        self.parent_pid = os.getpid()
        self.process_marker = f"jarvis_stt_{os.getpid()}_{id(self)}_{int(time.time())}"
        self.chrome_user_data_dir = os.path.join(tempfile.gettempdir(), self.process_marker)
        self.is_listening = False
        self.stop_listening = False
        self.initialized = False
        self.wake_word_listening = False
        self.driver_start_time = time.time()
        self.restart_interval = 1200
        self.cleanup_lock = threading.Lock()
        self.driver_valid = False
        self.restart_in_progress = False
        self.shutdown_flag = False
        self.initial_memory = 0
        self.restart_count = 0
        self.last_restart_time = time.time()
        self.memory_threshold_mb = 800
        self.used_ports = set()
        self.operation_times = []
        self.performance_degradation_threshold = 3.0
        self.page_load_timeout = 15
        self.element_wait_timeout = 10
        self._nuclear_cleanup()
        time.sleep(1)
        os.makedirs(self.chrome_user_data_dir, exist_ok=True)
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument(f"--user-data-dir={self.chrome_user_data_dir}")
        self.chrome_options.add_argument("--use-fake-ui-for-media-stream")
        self.chrome_options.add_argument("--log-level=3")
        self.chrome_options.add_argument("--disable-background-networking")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--js-flags=--max-old-space-size=256")
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.chrome_options.page_load_strategy = 'normal'
        self.driver = self._create_driver_with_retry()
        self.wait = WebDriverWait(self.driver, self.element_wait_timeout)
        self.driver_valid = True
        self.driver.set_page_load_timeout(self.page_load_timeout)
        self._track_chrome_processes()
        self._track_used_port()
        threading.Thread(target=self._continuous_cleanup_watchdog, daemon=True, name="STT-Cleanup").start()
        threading.Thread(target=self._chrome_restart_watchdog, daemon=True, name="STT-Restart").start()
        threading.Thread(target=self._prewarm_chrome, daemon=True, name="STT-Prewarm").start()
        threading.Thread(target=self._memory_monitor, daemon=True, name="STT-Memory").start()
        threading.Thread(target=self._health_monitor, daemon=True, name="STT-Health").start()
        if os.name == 'nt':
            threading.Thread(target=self._mic_watchdog_event_driven, daemon=True, name="STT-MicWatchdog").start()
        atexit.register(self._emergency_cleanup)
        logger.info("✅ FORTIFIED STT initialized")

    # ### MODIFIED ### - This function now returns the exact registry path strings.
    def _get_current_mic_users(self):
        """
        Reads the registry and returns a set of the raw, specially-formatted
        path strings for all apps currently using the microphone.
        """
        mic_users = set()
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone\NonPackaged"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
            i = 0
            while True:
                try:
                    # This app_path is the string we need, e.g., '#...#chrome.exe'
                    app_path = winreg.EnumKey(key, i)
                    i += 1
                    app_key = winreg.OpenKey(key, app_path)
                    try:
                        value, _ = winreg.QueryValueEx(app_key, "LastUsedTimeStop")
                        if value == 0:
                            mic_users.add(app_path)
                    except FileNotFoundError:
                        pass
                    finally:
                        winreg.CloseKey(app_key)
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            pass
        return mic_users

    # ### MODIFIED ### - The watchdog now uses the precise path-matching logic.
    def _mic_watchdog_event_driven(self):
        """
        A stabilized, event-driven watchdog that monitors mic changes in real-time,
        waits 3 seconds for automatic recovery, then re-activates if needed.
        """
        
        HKEY_CURRENT_USER = 0x80000001
        KEY_NOTIFY = 0x0010
        REG_NOTIFY_CHANGE_LAST_SET = 0x00000004
        RegNotifyChangeKeyValue = ctypes.windll.advapi32.RegNotifyChangeKeyValue
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone\NonPackaged"

        time.sleep(10)
        logger.info("🎤 Real-time Mic Watchdog thread has started and is now waiting for events.")
        
        mic_was_active = False  # Track previous state
        
        while not self.shutdown_flag:
            try:
                # Wait for registry change event (blocking)
                reg_key = winreg.OpenKey(HKEY_CURRENT_USER, key_path, 0, KEY_NOTIFY)
                RegNotifyChangeKeyValue(reg_key.handle, True, REG_NOTIFY_CHANGE_LAST_SET, None, False)
                winreg.CloseKey(reg_key)

                if self.shutdown_flag:
                    break
                
                # Registry changed! Now check what happened
                time.sleep(0.5)  # Small debounce for registry to stabilize

                # Only care if we're actively listening
                if not self.is_listening and not self.wake_word_listening:
                    mic_was_active = False
                    continue
                
                # Get the set of full registry paths for apps using the mic
                current_user_paths = self._get_current_mic_users()
                
                # Check if ANY of the active user paths end with '#chrome.exe'
                is_chrome_active = any(path.lower().endswith("#chrome.exe") for path in current_user_paths)

                # Detect state change: mic went from active to inactive
                if mic_was_active and not is_chrome_active:
                    logger.warning("🎤 Mic watchdog [EVENT]: Chrome mic access lost! Waiting 3 seconds for auto-recovery...")
                    
                    # Wait 3 seconds for automatic recovery
                    recovery_start = time.time()
                    recovered = False
                    
                    while time.time() - recovery_start < 3.0:
                        if self.shutdown_flag:
                            break
                        
                        time.sleep(0.5)
                        
                        # Check if it recovered on its own
                        current_user_paths = self._get_current_mic_users()
                        is_chrome_active = any(path.lower().endswith("#chrome.exe") for path in current_user_paths)
                        
                        if is_chrome_active:
                            logger.info("✅ Mic recovered automatically within 3 seconds!")
                            recovered = True
                            break
                    
                    # If it didn't recover, force re-activation
                    if not recovered and not self.shutdown_flag:
                        logger.warning("⚠️ Mic did NOT recover after 3 seconds. Forcing re-activation...")
                        try:
                            with self.lock:
                                self.driver.execute_script("document.getElementById('click_to_record')?.click()")
                            
                            # Wait a moment and verify
                            time.sleep(1)
                            current_user_paths = self._get_current_mic_users()
                            is_chrome_active = any(path.lower().endswith("#chrome.exe") for path in current_user_paths)
                            
                            if is_chrome_active:
                                logger.info("✅ Mic successfully re-activated via button click")
                            else:
                                logger.error("❌ Failed to re-activate mic, may need page reload")
                                
                        except Exception as e:
                            logger.error(f"Mic watchdog failed to re-click button: {e}")
                
                # Update state for next iteration
                mic_was_active = is_chrome_active

            except FileNotFoundError:
                logger.error("Mic watchdog: Registry key not found. Monitoring cannot continue.")
                break
            except Exception as e:
                logger.error(f"Mic watchdog encountered a critical error: {e}")
                time.sleep(10)
        
        logger.info("🎤 Mic watchdog thread has stopped.")


    def _get_memory_usage(self):
        total_memory = 0
        try:
            for pid in list(self.chrome_pids):
                try:
                    proc = psutil.Process(pid)
                    total_memory += proc.memory_info().rss / 1024 / 1024
                except: pass
        except: pass
        return total_memory

    def _memory_monitor(self):
        while not self.shutdown_flag:
            try:
                time.sleep(120)
                if self.shutdown_flag: break
                current_memory = self._get_memory_usage()
                if current_memory > self.memory_threshold_mb:
                    logger.warning(f"⚠️ STT Memory threshold exceeded: {current_memory:.1f}MB > {self.memory_threshold_mb}MB")
                    if not self.is_listening and not self.restart_in_progress and not self.wake_word_listening:
                        logger.info("🔄 Forcing restart due to memory")
                        self._safe_restart_driver()
                        gc.collect()
            except Exception as e:
                logger.error(f"Memory monitor error: {e}")
                time.sleep(10)

    def _health_monitor(self):
        consecutive_failures = 0
        last_successful_operation = time.time()
        while not self.shutdown_flag:
            try:
                time.sleep(180)
                if self.shutdown_flag: break
                if self.is_listening or self.wake_word_listening:
                    last_successful_operation = time.time()
                    consecutive_failures = 0
                else:
                    idle_time = time.time() - last_successful_operation
                    if idle_time > 900:
                        if not self._is_driver_alive():
                            consecutive_failures += 1
                            logger.warning(f"❌ Health check failed ({consecutive_failures}/3)")
                            if consecutive_failures >= 3:
                                logger.error("💀 Multiple health check failures, forcing restart")
                                if not self.restart_in_progress:
                                    self._safe_restart_driver()
                                consecutive_failures = 0
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                time.sleep(10)

    def _track_used_port(self):
        try:
            if hasattr(self.driver, 'service') and hasattr(self.driver.service, 'service_url'):
                url = self.driver.service.service_url
                port = int(url.split(':')[-1].split('/')[0])
                self.used_ports.add(port)
        except: pass

    def _is_port_available(self, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                return s.connect_ex(('localhost', port)) != 0
        except: return False

    def _is_driver_alive(self):
        try:
            if not hasattr(self, 'driver') or self.driver is None: return False
            _ = self.driver.title
            return True
        except: return False

    def _wait_for_driver_ready(self, timeout=15):
        start = time.time()
        while time.time() - start < timeout:
            if self.driver_valid and self._is_driver_alive(): return True
            time.sleep(0.2)
        return False

    def _nuclear_cleanup(self):
        killed = 0
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    name = proc.info['name'].lower()
                    if 'chrome' not in name and 'chromedriver' not in name: continue
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if "jarvis_stt_" in cmdline and str(self.parent_pid) in cmdline:
                        proc.kill()
                        killed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied): pass
            time.sleep(0.5)
            temp_dir = tempfile.gettempdir()
            for item in os.listdir(temp_dir):
                if item.startswith(f"jarvis_stt_{self.parent_pid}_"):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isdir(item_path): shutil.rmtree(item_path, ignore_errors=True)
                    except: pass
        except Exception as e:
            logger.warning(f"STT cleanup error: {e}")
        if killed > 0: logger.debug(f"💀 Killed {killed} STT Chrome processes")

    def _track_chrome_processes(self):
        with self.cleanup_lock:
            self.chrome_pids.clear()
            try:
                if hasattr(self.driver, 'service') and hasattr(self.driver.service, 'process'):
                    self.driver_pid = self.driver.service.process.pid
                    self.chrome_pids.add(self.driver_pid)
                    parent = psutil.Process(self.driver_pid)
                    for child in parent.children(recursive=True): self.chrome_pids.add(child.pid)
            except Exception as e:
                logger.debug(f"Process tracking error: {e}")

    def _cleanup_temp_directories(self):
        try:
            temp_dir = tempfile.gettempdir()
            cleaned = 0
            for item in os.listdir(temp_dir):
                if item.startswith(f"jarvis_stt_{self.parent_pid}_"):
                    if item == os.path.basename(self.chrome_user_data_dir): continue
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                            cleaned += 1
                    except: pass
            if cleaned > 0: logger.info(f"🗑️ Cleaned {cleaned} old STT temp directories")
        except Exception as e: logger.debug(f"Temp cleanup error: {e}")

    def _continuous_cleanup_watchdog(self):
        cleanup_count = 0
        while not self.shutdown_flag:
            try:
                time.sleep(60)
                if self.shutdown_flag: break
                cleanup_count += 1
                if cleanup_count % 120 == 0: self._cleanup_temp_directories()
                with self.cleanup_lock:
                    killed = 0
                    for proc in psutil.process_iter(['pid', 'name', 'ppid', 'create_time', 'cmdline']):
                        try:
                            name = proc.info['name'].lower()
                            if 'chrome' not in name and 'chromedriver' not in name: continue
                            pid = proc.info['pid']
                            cmdline = ' '.join(proc.info.get('cmdline', []))
                            if "jarvis_stt_" not in cmdline or str(self.parent_pid) not in cmdline: continue
                            try: parent = psutil.Process(proc.info['ppid'])
                            except psutil.NoSuchProcess:
                                if pid not in self.chrome_pids:
                                    proc.kill(); killed += 1; continue
                            if pid not in self.chrome_pids:
                                if time.time() - proc.info['create_time'] > 600:
                                    proc.kill(); killed += 1
                        except (psutil.NoSuchProcess, psutil.AccessDenied): pass
                    if killed > 0: logger.debug(f"🧹 STT Watchdog killed {killed} orphaned processes")
            except Exception as e:
                logger.error(f"Cleanup watchdog error: {e}")
                time.sleep(10)

    def _chrome_restart_watchdog(self):
        while not self.shutdown_flag:
            try:
                time.sleep(60)
                if self.shutdown_flag: break
                time_since_last_restart = time.time() - self.last_restart_time
                if time_since_last_restart < 300:
                    if self.restart_count > 2:
                        logger.error("⚠️ Too many restarts, backing off 10 minutes")
                        time.sleep(600); self.restart_count = 0; continue
                else: self.restart_count = 0
                if not self._is_driver_alive():
                    logger.warning("⚠️ STT ChromeDriver crashed!")
                    if not self.is_listening and not self.restart_in_progress and not self.wake_word_listening:
                        self._safe_restart_driver()
                    continue
                if len(self.operation_times) > 10:
                    avg_time = sum(self.operation_times[-10:]) / 10
                    if self.operation_times and avg_time > (self.operation_times[0] * self.performance_degradation_threshold):
                        logger.warning(f"⚠️ Performance degradation detected: {avg_time:.2f}s avg")
                        if not self.is_listening and not self.restart_in_progress and not self.wake_word_listening:
                            self._safe_restart_driver(); self.operation_times.clear(); continue
                if time.time() - self.driver_start_time > self.restart_interval:
                    if not self.is_listening and not self.restart_in_progress and not self.wake_word_listening:
                        logger.info("🔄 STT Scheduled restart")
                        self._safe_restart_driver(); self.driver_start_time = time.time()
            except Exception as e: logger.error(f"Restart watchdog error: {e}")

    def _kill_tracked_processes(self):
        with self.cleanup_lock:
            for pid in list(self.chrome_pids):
                try:
                    proc = psutil.Process(pid); proc.kill(); proc.wait(timeout=3)
                except: pass
            self.chrome_pids.clear(); self.driver_pid = None

    def _safe_restart_driver(self):
        if self.restart_in_progress:
            logger.warning("Restart already in progress, skipping"); return
        with self.lock:
            self.restart_in_progress = True
            self.driver_valid = False
            self.restart_count += 1; self.last_restart_time = time.time()
            try:
                self._kill_tracked_processes()
                try:
                    if hasattr(self, 'driver') and self.driver: self.driver.quit()
                except: pass
                time.sleep(3)
                self._nuclear_cleanup(); time.sleep(2)
                if self.used_ports:
                    for i in range(10):
                        if all(self._is_port_available(p) for p in self.used_ports): break
                        time.sleep(1)
                os.makedirs(self.chrome_user_data_dir, exist_ok=True)
                self.driver = self._create_driver_with_retry()
                self.wait = WebDriverWait(self.driver, self.element_wait_timeout)
                self.driver.set_page_load_timeout(self.page_load_timeout)
                self.initialized = False; self.driver_valid = True
                self._track_chrome_processes(); self._track_used_port()
                gc.collect()
                logger.info("✅ STT Driver restarted successfully")
            except Exception as e:
                logger.error(f"STT driver restart failed: {e}"); self.driver_valid = False
            finally: self.restart_in_progress = False

    def _create_driver_with_retry(self, max_retries=3):
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    os.system("taskkill /F /IM chromedriver.exe /T >nul 2>&1"); time.sleep(3)
                service = Service()
                driver = webdriver.Chrome(service=service, options=self.chrome_options)
                logger.info(f"✅ STT ChromeDriver created (attempt {attempt + 1})")
                return driver
            except Exception as e:
                logger.error(f"STT driver creation failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1: time.sleep(5)
                else: raise

    def _prewarm_chrome(self):
        try:
            time.sleep(3)
            if not self.initialized and self._wait_for_driver_ready(timeout=20):
                self._initialize_stt_page()
        except Exception as e: logger.error(f"Pre-warm failed: {e}")

    def _initialize_stt_page(self):
        try:
            logger.debug("Loading STT page...")
            self.driver.get(self.website_path); time.sleep(2)
            try: self.wait.until(EC.presence_of_element_located((By.ID, "language_select"))); logger.debug("✅ Language select found")
            except Exception as e: logger.error(f"❌ Language select not found: {e}"); raise
            self.select_language(); time.sleep(1)
            try: self.wait.until(EC.presence_of_element_located((By.ID, "click_to_record"))); logger.debug("✅ Record button found")
            except Exception as e: logger.error(f"❌ Record button not found: {e}"); raise
            try: self.wait.until(EC.presence_of_element_located((By.ID, "convert_text"))); logger.debug("✅ Text element found")
            except Exception as e: logger.error(f"❌ Text element not found: {e}"); raise
            try: self.wait.until(EC.presence_of_element_located((By.ID, "is_recording"))); logger.debug("✅ Recording status found")
            except Exception as e: logger.error(f"❌ Recording status not found: {e}"); raise
            self.initialized = True; self.last_page_reload = time.time()
            self._track_chrome_processes()
            logger.info("✅ STT page fully initialized")
        except Exception as e:
            logger.error(f"STT page initialization failed: {e}"); self.initialized = False; raise

    def select_language(self):
        try: self.driver.execute_script(f"var s=document.getElementById('language_select');if(s){{s.value='{self.language}';var e=new Event('change');s.dispatchEvent(e);}}")
        except Exception as e: logger.error(f"Language selection failed: {e}")

    def get_text(self):
        try: return self.driver.find_element(By.ID, "convert_text").text
        except NoSuchElementException: logger.error("❌ convert_text element not found!"); return ""

    def clear_text(self):
        try: self.driver.execute_script("var el=document.getElementById('convert_text');if(el)el.textContent='';")
        except: pass

    def stop_recording(self): self.stop_listening = True

    def listen_for_wake_word(self, wake_word=settings.Wake_word, max_retries=2):
        operation_start = time.time()
        with self.lock: self.wake_word_listening = True
        retry_count = 0
        while retry_count < max_retries:
            if not self._wait_for_driver_ready(timeout=10):
                logger.error("Driver not ready, triggering restart"); self._safe_restart_driver(); retry_count += 1; time.sleep(3); continue
            if hasattr(self, 'last_page_reload') and time.time() - self.last_page_reload > 3600:
                logger.info("🔄 Reloading page to clear JS heap")
                try: self._initialize_stt_page()
                except: pass
            if not self.initialized:
                try: self._initialize_stt_page()
                except Exception as e: logger.error(f"Wake word init failed: {e}"); self._safe_restart_driver(); retry_count += 1; time.sleep(3); continue
            try:
                self.driver.find_element(By.ID, "is_recording"); self.driver.find_element(By.ID, "click_to_record"); self.driver.find_element(By.ID, "convert_text")
            except NoSuchElementException as e: logger.error(f"❌ Required element missing: {e}"); self._safe_restart_driver(); retry_count += 1; time.sleep(3); continue
            try:
                if not self.driver.find_element(By.ID, "is_recording").text.startswith("Recording: True"):
                    self.driver.find_element(By.ID, "click_to_record").click(); time.sleep(0.1)
            except Exception as e: logger.warning(f"Failed to start recording: {e}"); retry_count += 1; self._safe_restart_driver(); time.sleep(3); continue
            last_text = ""; consecutive_errors = 0
            while self.wake_word_listening:
                try:
                    if not self._is_driver_alive(): raise WebDriverException("Driver died")
                    if not self.driver.find_element(By.ID, "is_recording").text.startswith("Recording: True"):
                        self.driver.find_element(By.ID, "click_to_record").click(); time.sleep(0.1)
                    text = self.get_text().lower()
                    if text != last_text:
                        if wake_word in text:
                            self.clear_text()
                            op_time = time.time() - operation_start; self.operation_times.append(op_time)
                            if len(self.operation_times) > 100: self.operation_times.pop(0)
                            return True
                        last_text = text
                    consecutive_errors = 0; time.sleep(0.1)
                except NoSuchElementException as e:
                    consecutive_errors += 1; logger.warning(f"Element not found (error {consecutive_errors}/3): {e}")
                    if consecutive_errors > 3: logger.warning("Too many consecutive errors"); break
                    time.sleep(0.5)
                except Exception as e:
                    consecutive_errors += 1
                    if consecutive_errors > 3: logger.warning(f"Too many consecutive errors: {e}"); break
                    time.sleep(0.5)
            if not self.wake_word_listening: return False
            logger.warning("Wake word loop broken, restarting driver"); self._safe_restart_driver(); retry_count += 1; time.sleep(3)
        logger.error("Max retries exceeded for wake word detection"); return False

    def stop_wake_word_listening(self): self.wake_word_listening = False

    def main(self):
        if not self._wait_for_driver_ready(timeout=10): logger.error("Driver not ready for recording"); return ""
        if not self.initialized:
            try: self._initialize_stt_page()
            except: return ""
        try:
            if not self.driver.find_element(By.ID, "is_recording").text.startswith("Recording: True"):
                self.driver.find_element(By.ID, "click_to_record").click(); time.sleep(0.1)
        except: return ""
        print("\rListening...", end='', flush=True)
        while not self.stop_listening:
            try:
                if not self.driver.find_element(By.ID, "is_recording").text.startswith("Recording: True"): break
                text = self.get_text()
                if text: print(f"\rUser Speaking: {text}", end='', flush=True)
            except: break
            time.sleep(0.1)
        try:
            if self.driver.find_element(By.ID, "is_recording").text.startswith("Recording: True"):
                self.driver.find_element(By.ID, "click_to_record").click()
        except: pass
        return self.get_text() if not self.stop_listening else ""

    def listen(self, check_stop_words=False, stop_words=None):
        from config.settings import STOP_WORDS, IGNORE_WORDS
        self.stop_listening = False; self.is_listening = True
        result = self.main()
        self.is_listening = False
        if result and len(result) != 0 and not self.stop_listening:
            print("\r" + " " * (len(result) + 16) + "\r", end="", flush=True)
            print(f"YOU SAID: {result}\n")
            result_lower = result.lower().strip()
            for stop_word in STOP_WORDS:
                if stop_word in result_lower:
                    self.clear_text()
                    if hasattr(self, 'gui_handler') and self.gui_handler: self.gui_handler.mute_microphone()
                    return "STOP_COMMAND"
            if self.is_listening:
                for ignore_word in IGNORE_WORDS:
                    if result_lower == ignore_word: self.clear_text(); return None
            if check_stop_words and stop_words:
                for stop_word in stop_words:
                    if stop_word in result_lower: self.clear_text(); return "STOP_COMMAND"
            self.clear_text()
            return result.lower().strip()
        self.clear_text()
        return None

    def _emergency_cleanup(self):
        logger.info("🚨 STT Emergency cleanup triggered")
        self.shutdown_flag = True; self._kill_tracked_processes(); self._nuclear_cleanup()

    def cleanup(self):
        logger.info("🧹 Starting STT cleanup...")
        self.shutdown_flag = True
        with self.lock:
            self.wake_word_listening = False; self.stop_listening = True; self.driver_valid = False
            self._kill_tracked_processes()
            try:
                if hasattr(self, 'driver') and self.driver:
                    self.driver.quit(); time.sleep(0.5)
            except: pass
            self._nuclear_cleanup(); gc.collect()
        logger.info("✅ STT cleanup completed")
