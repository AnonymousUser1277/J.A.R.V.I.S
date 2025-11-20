"""
CRITICAL FIXES Applied - Text-to-Speech
Fixes: Session errors, restart storms, queue issues
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
from queue import Queue, Full
import gc
import socket

logger = logging.getLogger(__name__)

class TextToSpeechEngine:
    """FORTIFIED TTS with critical bug fixes"""
    
    def __init__(self, website_path, voice_name="Microsoft Ryan"):
        self.lock = threading.RLock()
        self.website_path = website_path
        self.voice_name = voice_name
        
        self.process_marker = f"jarvis_tts_{os.getpid()}_{id(self)}_{int(time.time())}"
        self.chrome_user_data_dir = os.path.join(tempfile.gettempdir(), self.process_marker)
        
        # Process tracking
        self.driver_pid = None
        self.chrome_pids = set()
        self.parent_pid = os.getpid()
        
        # State flags
        self.initialized = False
        self.is_speaking = False
        self.driver_valid = False
        self.restart_in_progress = False
        self.driver_start_time = time.time()
        self.restart_interval = 1200  # ✅ FIXED: 20 min instead of 15 min
        self.cleanup_lock = threading.Lock()
        self.shutdown_flag = False
        
        # ✅ FIXED: Better queue management
        self.speech_queue = Queue(maxsize=100)  # Increased from 50
        self.dropped_messages = 0
        
        # Memory tracking
        self.initial_memory = 0
        self.restart_count = 0
        self.last_restart_time = time.time()
        self.memory_threshold_mb = 800  # ✅ FIXED: Increased from 500 to 800MB
        
        # Port tracking
        self.used_ports = set()
        
        # Speech health
        self.last_successful_speech = time.time()
        self.speech_failure_count = 0
        
        # Performance tracking
        self.speech_times = []
        self.performance_degradation_threshold = 3.0  # ✅ FIXED: Increased from 2.0
        
        # ✅ NEW: Page load verification
        self.page_load_timeout = 15
        self.element_wait_timeout = 10
        
        # Cleanup on startup
        self._nuclear_cleanup()
        time.sleep(1)
        
        # Create fresh profile
        os.makedirs(self.chrome_user_data_dir, exist_ok=True)
        
        # Setup Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument(f"--user-data-dir={self.chrome_user_data_dir}")
        self.chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
        self.chrome_options.add_argument("--log-level=3")
        self.chrome_options.add_argument("--disable-background-networking")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--js-flags=--max-old-space-size=256")
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # ✅ FIXED: Page load strategy
        self.chrome_options.page_load_strategy = 'normal'
        
        # Create driver
        try:
            self.driver = self._create_driver_with_retry()
            self.wait = WebDriverWait(self.driver, self.element_wait_timeout)
            self.driver_valid = True
            
            # Set timeouts
            self.driver.set_page_load_timeout(self.page_load_timeout)
            
            # Track processes
            self._track_chrome_processes()
            self._track_used_port()
            
            # Initialize TTS page
            self._initialize_tts()
            
            # Start watchdogs
            threading.Thread(target=self._continuous_cleanup_watchdog, daemon=True, name="TTS-Cleanup").start()
            threading.Thread(target=self._chrome_restart_watchdog, daemon=True, name="TTS-Restart").start()
            threading.Thread(target=self._speech_processor, daemon=True, name="TTS-Speech").start()
            threading.Thread(target=self._memory_monitor, daemon=True, name="TTS-Memory").start()
            threading.Thread(target=self._health_monitor, daemon=True, name="TTS-Health").start()
            
            atexit.register(self._emergency_cleanup)
            
            logger.info("✅ FORTIFIED TTS initialized")
            
        except Exception as e:
            logger.error(f"❌ TTS Engine initialization failed: {e}")
            self.driver_valid = False
            raise

    def _get_memory_usage(self):
        """Get current memory usage"""
        total_memory = 0
        try:
            for pid in list(self.chrome_pids):
                try:
                    proc = psutil.Process(pid)
                    total_memory += proc.memory_info().rss / 1024 / 1024
                except:
                    pass
        except:
            pass
        return total_memory

    def _memory_monitor(self):
        """Monitor memory usage"""
        while not self.shutdown_flag:
            try:
                time.sleep(120)  # ✅ FIXED: Every 2 min
                
                if self.shutdown_flag:
                    break
                
                current_memory = self._get_memory_usage()
                
                if current_memory > self.memory_threshold_mb:
                    logger.warning(f"⚠️ TTS Memory threshold exceeded: {current_memory:.1f}MB")
                    # ✅ FIXED: Don't restart while speaking
                    if not self.is_speaking and not self.restart_in_progress:
                        logger.info("🔄 Forcing TTS restart due to memory")
                        self._safe_restart_driver()
                        gc.collect()
                
            except Exception as e:
                logger.error(f"TTS memory monitor error: {e}")
                time.sleep(10)

    def _health_monitor(self):
        """Monitor speech synthesis health"""
        while not self.shutdown_flag:
            try:
                time.sleep(180)  # ✅ FIXED: Every 3 min
                
                if self.shutdown_flag:
                    break
                
                time_since_success = time.time() - self.last_successful_speech
                
                if self.speech_failure_count > 5:
                    logger.error(f"💀 Multiple TTS speech failures ({self.speech_failure_count})")
                    if not self.restart_in_progress:
                        self._safe_restart_driver()
                    self.speech_failure_count = 0
                
                # Check for stuck queue
                if not self.speech_queue.empty() and time_since_success > 300:
                    logger.warning("⚠️ TTS queue stuck, forcing restart")
                    if not self.restart_in_progress:
                        self._safe_restart_driver()
                
            except Exception as e:
                logger.error(f"TTS health monitor error: {e}")
                time.sleep(10)

    def _track_used_port(self):
        """Track port"""
        try:
            if hasattr(self.driver, 'service') and hasattr(self.driver.service, 'service_url'):
                url = self.driver.service.service_url
                port = int(url.split(':')[-1].split('/')[0])
                self.used_ports.add(port)
        except:
            pass

    def _is_port_available(self, port):
        """Check if port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result != 0
        except:
            return False

    def _is_driver_alive(self):
        """Check if driver is responsive"""
        try:
            if not hasattr(self, 'driver') or self.driver is None:
                return False
            _ = self.driver.title
            return True
        except:
            return False

    def _wait_for_driver_ready(self, timeout=15):  # ✅ FIXED: Increased timeout
        """Wait for driver to be ready"""
        start = time.time()
        while time.time() - start < timeout:
            if self.driver_valid and self._is_driver_alive():
                return True
            time.sleep(0.2)
        return False

    def _nuclear_cleanup(self):
        """Kill ONLY our TTS Chrome processes"""
        killed = 0
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    name = proc.info['name'].lower()
                    if 'chrome' not in name and 'chromedriver' not in name:
                        continue
                    
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if "jarvis_tts_" in cmdline and str(self.parent_pid) in cmdline:
                        proc.kill()
                        killed += 1
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            time.sleep(0.5)
            
            # Clean temp directories
            temp_dir = tempfile.gettempdir()
            for item in os.listdir(temp_dir):
                if item.startswith(f"jarvis_tts_{self.parent_pid}_"):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                    except:
                        pass
        
        except Exception as e:
            logger.warning(f"TTS cleanup error: {e}")
        
        if killed > 0:
            logger.debug(f"💀 Killed {killed} TTS Chrome processes")
    
    def _track_chrome_processes(self):
        """Track all Chrome processes"""
        with self.cleanup_lock:
            self.chrome_pids.clear()
            
            try:
                if hasattr(self.driver, 'service') and hasattr(self.driver.service, 'process'):
                    self.driver_pid = self.driver.service.process.pid
                    self.chrome_pids.add(self.driver_pid)
                    
                    parent = psutil.Process(self.driver_pid)
                    for child in parent.children(recursive=True):
                        self.chrome_pids.add(child.pid)
            
            except Exception as e:
                logger.debug(f"TTS process tracking error: {e}")

    def _cleanup_temp_directories(self):
        """Clean up temp directories"""
        try:
            temp_dir = tempfile.gettempdir()
            cleaned = 0
            
            for item in os.listdir(temp_dir):
                if item.startswith(f"jarvis_tts_{self.parent_pid}_"):
                    if item == os.path.basename(self.chrome_user_data_dir):
                        continue
                    
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                            cleaned += 1
                    except:
                        pass
            
            if cleaned > 0:
                logger.info(f"🗑️ Cleaned {cleaned} old TTS temp directories")
        
        except Exception as e:
            logger.debug(f"TTS temp cleanup error: {e}")
    
    def _continuous_cleanup_watchdog(self):
        """Cleanup orphaned processes"""
        cleanup_count = 0
        
        while not self.shutdown_flag:
            try:
                time.sleep(60)  # ✅ FIXED: Every 60s
                
                if self.shutdown_flag:
                    break
                
                cleanup_count += 1
                
                # Cleanup temps every 2 hours
                if cleanup_count % 120 == 0:
                    self._cleanup_temp_directories()
                
                with self.cleanup_lock:
                    killed = 0
                    for proc in psutil.process_iter(['pid', 'name', 'ppid', 'create_time', 'cmdline']):
                        try:
                            name = proc.info['name'].lower()
                            if 'chrome' not in name and 'chromedriver' not in name:
                                continue
                            
                            pid = proc.info['pid']
                            cmdline = ' '.join(proc.info.get('cmdline', []))
                            
                            if "jarvis_tts_" not in cmdline or str(self.parent_pid) not in cmdline:
                                continue
                            
                            try:
                                parent = psutil.Process(proc.info['ppid'])
                            except psutil.NoSuchProcess:
                                if pid not in self.chrome_pids:
                                    proc.kill()
                                    killed += 1
                                    continue
                            
                            if pid not in self.chrome_pids:
                                age = time.time() - proc.info['create_time']
                                if age > 600:  # ✅ FIXED: 10 min
                                    proc.kill()
                                    killed += 1
                        
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    if killed > 0:
                        logger.debug(f"🧹 TTS Watchdog killed {killed} orphaned processes")
            
            except Exception as e:
                logger.error(f"TTS cleanup watchdog error: {e}")
                time.sleep(10)
    
    def _chrome_restart_watchdog(self):
        """Auto-restart Chrome"""
        while not self.shutdown_flag:
            try:
                time.sleep(60)
                
                if self.shutdown_flag:
                    break
                
                # ✅ FIXED: Better restart storm prevention
                time_since_last_restart = time.time() - self.last_restart_time
                if time_since_last_restart < 300:  # 5 min
                    if self.restart_count > 2:
                        logger.error("⚠️ TTS: Too many restarts, backing off 10 minutes")
                        time.sleep(600)  # 10 min
                        self.restart_count = 0
                        continue
                else:
                    self.restart_count = 0
                
                # Check if driver crashed
                if not self._is_driver_alive():
                    logger.warning("⚠️ TTS ChromeDriver crashed!")
                    if not self.is_speaking and not self.restart_in_progress:
                        self._safe_restart_driver()
                    continue
                
                # Performance degradation
                if len(self.speech_times) > 10:
                    avg_time = sum(self.speech_times[-10:]) / 10
                    if self.speech_times and avg_time > (self.speech_times[0] * self.performance_degradation_threshold):
                        logger.warning(f"⚠️ TTS Performance degradation: {avg_time:.2f}s avg")
                        if not self.is_speaking and not self.restart_in_progress:
                            self._safe_restart_driver()
                            self.speech_times.clear()
                            continue
                
                # Periodic restart
                if time.time() - self.driver_start_time > self.restart_interval:
                    if not self.is_speaking and not self.restart_in_progress:
                        logger.info("🔄 TTS Scheduled restart")
                        self._safe_restart_driver()
                        self.driver_start_time = time.time()
            
            except Exception as e:
                logger.error(f"TTS restart watchdog error: {e}")
    
    def _kill_tracked_processes(self):
        """Kill all tracked processes"""
        with self.cleanup_lock:
            for pid in list(self.chrome_pids):
                try:
                    proc = psutil.Process(pid)
                    proc.kill()
                    proc.wait(timeout=3)
                except:
                    pass
            
            self.chrome_pids.clear()
            self.driver_pid = None
    
    def _safe_restart_driver(self):
        """Safely restart driver"""
        if self.restart_in_progress or self.shutdown_flag:
            return
        
        with self.lock:
            self.restart_in_progress = True
            self.driver_valid = False
            self.restart_count += 1
            self.last_restart_time = time.time()
            
            try:
                self._kill_tracked_processes()
                
                try:
                    if hasattr(self, 'driver') and self.driver:
                        self.driver.quit()
                except:
                    pass
                
                time.sleep(3)
                
                self._nuclear_cleanup()
                time.sleep(2)
                
                # Wait for port release
                if self.used_ports:
                    for i in range(10):
                        all_available = all(self._is_port_available(p) for p in self.used_ports)
                        if all_available:
                            break
                        time.sleep(1)
                
                os.makedirs(self.chrome_user_data_dir, exist_ok=True)
                
                self.driver = self._create_driver_with_retry()
                self.wait = WebDriverWait(self.driver, self.element_wait_timeout)
                self.driver.set_page_load_timeout(self.page_load_timeout)
                self.initialized = False
                self.driver_valid = True
                
                self._track_chrome_processes()
                self._track_used_port()
                self._initialize_tts()
                
                gc.collect()
                
                logger.info("✅ TTS Driver restarted successfully")
            
            except Exception as e:
                logger.error(f"TTS driver restart failed: {e}")
                self.driver_valid = False
            finally:
                self.restart_in_progress = False
    
    def _create_driver_with_retry(self, max_retries=3):
        """Create Chrome driver with retry"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    os.system("taskkill /F /IM chromedriver.exe /T >nul 2>&1")
                    time.sleep(3)
                
                service = Service()
                driver = webdriver.Chrome(service=service, options=self.chrome_options)
                logger.debug(f"✅ TTS ChromeDriver created (attempt {attempt + 1})")
                return driver
            
            except Exception as e:
                logger.error(f"TTS driver creation failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    raise
    
    def _initialize_tts(self):
        """Initialize TTS page with proper verification"""
        try:
            if not self._wait_for_driver_ready():
                raise Exception("Driver not ready")
            
            logger.debug("Loading TTS page...")
            self.driver.get(self.website_path)
            
            # ✅ CRITICAL: Wait for page to fully load
            time.sleep(2)
            
            # Wait for voice select
            try:
                self.wait.until(EC.presence_of_element_located((By.ID, "voiceSelect")))
                logger.debug("✅ Voice select found")
            except Exception as e:
                logger.error(f"❌ Voice select not found: {e}")
                raise
            
            # Wait for text content element
            try:
                self.wait.until(EC.presence_of_element_located((By.ID, "textContent")))
                logger.debug("✅ Text content found")
            except Exception as e:
                logger.error(f"❌ Text content not found: {e}")
                raise
            
            # Wait for voices to load
            time.sleep(1.5)
            
            self.initialized = True
            self.last_page_reload = time.time()
            logger.info("✅ TTS page fully initialized")
            
        except Exception as e:
            logger.error(f"TTS initialization failed: {e}")
            self.initialized = False
            raise
    
    def _speech_processor(self):
        """Background thread to process speech queue"""
        while not self.shutdown_flag:
            try:
                # Get text from queue
                text = self.speech_queue.get(timeout=1)
                
                if text and text.strip():
                    self._speak_internal(text)
                
            except:
                pass
            
            time.sleep(0.05)
    
    def _speak_internal(self, text, max_retries=2):
        """Internal method to speak text"""
        if self.shutdown_flag:
            return
        
        speech_start = time.time()
        retry_count = 0
        
        while retry_count < max_retries:
            # Wait for driver
            if not self._wait_for_driver_ready(timeout=10):
                logger.error("TTS driver not ready")
                self.speech_failure_count += 1
                if retry_count < max_retries - 1:
                    self._safe_restart_driver()
                retry_count += 1
                time.sleep(3)
                continue
            
            # JS heap reload check
            if hasattr(self, 'last_page_reload'):
                if time.time() - self.last_page_reload > 3600:
                    logger.info("🔄 Reloading TTS page to clear JS heap")
                    try:
                        self._initialize_tts()
                    except:
                        pass
            
            # Re-initialize if needed
            if not self.initialized:
                try:
                    self._initialize_tts()
                except:
                    self.speech_failure_count += 1
                    retry_count += 1
                    time.sleep(3)
                    continue
            
            try:
                with self.lock:
                    self.is_speaking = True
                    
                    # ✅ FIXED: Better text escaping
                    text_escaped = (text.replace('\\', '\\\\')
                                       .replace('`', '\\`')
                                       .replace('$', '\\$')
                                       .replace('\n', ' ')
                                       .replace('\r', ' ')
                                       .replace('"', '\\"')
                                       .replace("'", "\\'"))
                    
                    # Verify elements exist
                    try:
                        self.driver.find_element(By.ID, "textContent")
                    except NoSuchElementException:
                        logger.error("❌ textContent element missing!")
                        raise
                    
                    # Inject text and speak
                    self.driver.execute_script(
                        f"""
                        try {{
                            var textEl = document.getElementById('textContent');
                            if (textEl) {{
                                textEl.textContent = `{text_escaped}`;
                            }}
                            if (typeof speak === 'function') {{
                                speak(`{text_escaped}`);
                            }}
                        }} catch(e) {{
                            console.error('Speech error:', e);
                        }}
                        """
                    )
                    
                    # Wait for speech
                    words = len(text.split())
                    estimated_duration = max(words / 2.5, 1.5)
                    time.sleep(estimated_duration)
                    
                    self.is_speaking = False
                    self.last_successful_speech = time.time()
                    self.speech_failure_count = 0
                    
                    # Track performance
                    speech_time = time.time() - speech_start
                    self.speech_times.append(speech_time)
                    if len(self.speech_times) > 100:
                        self.speech_times.pop(0)
                    
                    logger.debug(f"✅ Spoke: {text[:50]}...")
                    return
            
            except Exception as e:
                logger.warning(f"TTS speak error (attempt {retry_count + 1}): {e}")
                self.is_speaking = False
                self.speech_failure_count += 1
                retry_count += 1
                
                if retry_count < max_retries:
                    self._safe_restart_driver()
                    time.sleep(3)
        
        logger.error(f"Failed to speak after {max_retries} attempts: {text[:50]}...")
    
    def speak(self, text):
        """
        Public method to speak text
        
        Returns:
            bool: True if queued successfully, False otherwise
        """
        if not text or not text.strip() or self.shutdown_flag:
            return False
        
        try:
            # ✅ FIXED: Try to queue with timeout
            self.speech_queue.put(text, block=True, timeout=0.5)
            return True
        except Full:
            # Queue full
            self.dropped_messages += 1
            if self.dropped_messages % 10 == 0:
                logger.warning(f"⚠️ TTS queue full, dropped {self.dropped_messages} messages")
            return False
        except Exception as e:
            logger.error(f"Failed to queue speech: {e}")
            return False
    
    def wait_until_done(self, timeout=30):
        """Wait until all queued speech is completed"""
        start = time.time()
        while not self.speech_queue.empty() or self.is_speaking:
            if time.time() - start > timeout:
                logger.warning("TTS wait timeout")
                return False
            time.sleep(0.1)
        return True
    
    def stop_speaking(self):
        """Stop current speech"""
        try:
            if self.driver_valid:
                self.driver.execute_script("window.speechSynthesis.cancel();")
            self.is_speaking = False
        except Exception as e:
            logger.debug(f"TTS stop error: {e}")
    
    def clear_queue(self):
        """Clear speech queue"""
        cleared = 0
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                cleared += 1
            except:
                break
        if cleared > 0:
            logger.info(f"🗑️ Cleared {cleared} queued TTS messages")
    
    def _emergency_cleanup(self):
        """Emergency cleanup on exit"""
        logger.debug("🚨 TTS Emergency cleanup triggered")
        self.shutdown_flag = True
        self._kill_tracked_processes()
        self._nuclear_cleanup()
    
    def cleanup(self):
        """Full cleanup"""
        logger.info("🧹 Starting TTS cleanup...")
        
        self.shutdown_flag = True
        
        with self.lock:
            self.is_speaking = False
            self.driver_valid = False
            
            self.clear_queue()
            self._kill_tracked_processes()
            
            try:
                if hasattr(self, 'driver') and self.driver:
                    self.driver.quit()
                    time.sleep(0.5)
            except:
                pass
            
            self._nuclear_cleanup()
            
            gc.collect()
        
        logger.info("✅ TTS cleanup completed")