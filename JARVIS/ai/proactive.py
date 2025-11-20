"""
Proactive AI suggestions based on user patterns and context
Learns what users typically do and suggests helpful actions
"""
import time
import logging
import threading
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from config.settings import DATA_DIR
import json

logger = logging.getLogger(__name__)

class ProactiveSuggestion:
    """Represents a proactive suggestion"""
    
    def __init__(
        self,
        suggestion_id: str,
        title: str,
        description: str,
        command: str,
        confidence: float,
        reason: str,
        expires_at: float = None
    ):
        self.suggestion_id = suggestion_id
        self.title = title
        self.description = description
        self.command = command
        self.confidence = confidence
        self.reason = reason
        self.expires_at = expires_at or (time.time() + 3600)  # 1 hour default
        self.dismissed = False


class ProactiveSuggestionEngine:
    """
    Analyzes patterns and generates contextual suggestions
    """
    
    def __init__(self, context_manager, gui_handler):
        self.context = context_manager
        self.gui = gui_handler
        self.lock = threading.RLock()
        
        # Pattern tracking
        self.action_patterns = defaultdict(list)  # time_of_day -> [actions]
        self.app_sequences = defaultdict(int)     # app1->app2 -> count
        self.context_actions = defaultdict(list)  # context -> [actions]
        
        # Active suggestions
        self.active_suggestions: List[ProactiveSuggestion] = []
        self.dismissed_suggestions = set()
        
        # Load patterns
        self.patterns_file = DATA_DIR / "behavior_patterns.json"
        self._load_patterns()
        
        # Start suggestion engine
        self.running = True
        self.thread = threading.Thread(
            target=self._suggestion_loop,
            daemon=True,
            name="Proactive-Suggestions"
        )
        self.thread.start()
        
        logger.info("✅ Proactive suggestion engine started")
    
    def _load_patterns(self):
        """Load learned patterns from disk"""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r') as f:
                    data = json.load(f)
                    self.action_patterns = defaultdict(list, data.get('action_patterns', {}))
                    self.app_sequences = defaultdict(int, data.get('app_sequences', {}))
                    self.context_actions = defaultdict(list, data.get('context_actions', {}))
                logger.info("📚 Loaded behavior patterns")
            except Exception as e:
                logger.error(f"Failed to load patterns: {e}")
    
    def _save_patterns(self):
        """Save learned patterns to disk"""
        try:
            data = {
                'action_patterns': dict(self.action_patterns),
                'app_sequences': dict(self.app_sequences),
                'context_actions': dict(self.context_actions),
                'updated_at': time.time()
            }
            with open(self.patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
    
    def record_action(self, action: str, context: Dict = None):
        """
        Record user action for pattern learning
        
        Args:
            action: Description of action taken
            context: Optional context (time, app, etc.)
        """
        with self.lock:
            # Record time-based patterns
            hour = datetime.now().hour
            time_bucket = f"{hour:02d}:00"
            self.action_patterns[time_bucket].append({
                'action': action,
                'timestamp': time.time()
            })
            
            # Keep only last 100 actions per time bucket
            if len(self.action_patterns[time_bucket]) > 100:
                self.action_patterns[time_bucket] = self.action_patterns[time_bucket][-100:]
            
            # Record context-based patterns
            if context:
                context_key = json.dumps(context, sort_keys=True)
                self.context_actions[context_key].append(action)
                
                # Keep only last 50 actions per context
                if len(self.context_actions[context_key]) > 50:
                    self.context_actions[context_key] = self.context_actions[context_key][-50:]
            
            # Save periodically (every 10 actions)
            if sum(len(v) for v in self.action_patterns.values()) % 10 == 0:
                self._save_patterns()
    
    def _suggestion_loop(self):
        """Main loop for generating suggestions"""
        while self.running:
            try:
                # Clear expired suggestions
                self._clear_expired_suggestions()
                
                # Generate new suggestions every 30 seconds
                self._generate_suggestions()
                
                time.sleep(30)
            except Exception as e:
                logger.error(f"Suggestion loop error: {e}")
                time.sleep(10)
    
    def _clear_expired_suggestions(self):
        """Remove expired suggestions"""
        with self.lock:
            current_time = time.time()
            self.active_suggestions = [
                s for s in self.active_suggestions
                if s.expires_at > current_time and not s.dismissed
            ]
    
    def _generate_suggestions(self):
        """Generate contextual suggestions"""
        with self.lock:
            suggestions = []
            
            # Time-based suggestions
            suggestions.extend(self._suggest_time_based())
            
            # Context-based suggestions
            suggestions.extend(self._suggest_context_based())
            
            # Application workflow suggestions
            suggestions.extend(self._suggest_workflow())
            
            # Battery suggestions
            suggestions.extend(self._suggest_battery())
            
            # Idle time suggestions
            suggestions.extend(self._suggest_idle())
            
            # Add new suggestions
            for suggestion in suggestions:
                if suggestion.suggestion_id not in self.dismissed_suggestions:
                    self._add_suggestion(suggestion)
    
    def _suggest_time_based(self) -> List[ProactiveSuggestion]:
        """Generate time-based suggestions"""
        suggestions = []
        hour = datetime.now().hour
        
        # Morning suggestions (6-10 AM)
        if 6 <= hour < 10:
            suggestions.append(ProactiveSuggestion(
                suggestion_id='morning_email',
                title='Check Morning Emails',
                description='It\'s morning. Would you like to check your emails?',
                command='open gmail',
                confidence=0.7,
                reason='Morning routine'
            ))
        
        # Lunch break (12-1 PM)
        elif 12 <= hour < 13:
            suggestions.append(ProactiveSuggestion(
                suggestion_id='lunch_break',
                title='Take a Break',
                description='It\'s lunch time. Take a break?',
                command='remind me to resume work in 1 hour',
                confidence=0.6,
                reason='Lunch time'
            ))
        
        # End of day (5-7 PM)
        elif 17 <= hour < 19:
            suggestions.append(ProactiveSuggestion(
                suggestion_id='eod_summary',
                title='End of Day',
                description='Save your work and review today\'s tasks?',
                command='show today\'s tasks',
                confidence=0.8,
                reason='End of work day'
            ))
        
        return suggestions
    
    def _suggest_context_based(self) -> List[ProactiveSuggestion]:
        """Generate context-aware suggestions"""
        suggestions = []
        
        # Excel + recent data = suggest chart
        if 'excel' in self.context.active_window_title.lower():
            if self.context.clipboard_content and self.context.clipboard_content[0] == 'text':
                clipboard_text = self.context.clipboard_content[1]
                # Check if clipboard has numeric data
                if any(char.isdigit() for char in clipboard_text):
                    suggestions.append(ProactiveSuggestion(
                        suggestion_id='excel_chart',
                        title='Create Chart',
                        description='I see you have data. Create a chart?',
                        command='create a chart from this data',
                        confidence=0.75,
                        reason='Excel with numeric data'
                    ))
        
        # Code in clipboard = suggest review
        if self.context.clipboard_content and self.context.clipboard_content[0] == 'text':
            clipboard_text = self.context.clipboard_content[1]
            if any(keyword in clipboard_text for keyword in ['def ', 'class ', 'function', 'import']):
                suggestions.append(ProactiveSuggestion(
                    suggestion_id='code_review',
                    title='Review Code',
                    description='Would you like me to review this code?',
                    command='review this code',
                    confidence=0.8,
                    reason='Code detected in clipboard'
                ))
        
        # Browser with research tabs
        if 'chrome' in self.context.active_window_title.lower() or 'firefox' in self.context.active_window_title.lower():
            # If multiple tabs open for >30 min, suggest summarizing
            suggestions.append(ProactiveSuggestion(
                suggestion_id='summarize_research',
                title='Summarize Research',
                description='Summarize your open browser tabs?',
                command='summarize my open tabs',
                confidence=0.65,
                reason='Extended browsing session'
            ))
        
        return suggestions
    
    def _suggest_workflow(self) -> List[ProactiveSuggestion]:
        """Suggest next steps based on common workflows"""
        suggestions = []
        
        # Check recent app sequences
        active_app = self.context.active_window_title.lower()
        
        # Common workflows
        workflows = {
            'excel': ['powerpoint', 'word'],  # Excel -> PPT/Word
            'chrome': ['slack', 'teams'],     # Browser -> Communication
            'code': ['terminal', 'cmd'],      # Code -> Terminal
        }
        
        for trigger_app, next_apps in workflows.items():
            if trigger_app in active_app:
                for next_app in next_apps:
                    suggestions.append(ProactiveSuggestion(
                        suggestion_id=f'workflow_{trigger_app}_{next_app}',
                        title=f'Open {next_app.title()}',
                        description=f'Often after {trigger_app}, you open {next_app}',
                        command=f'open {next_app}',
                        confidence=0.7,
                        reason='Common workflow pattern',
                        expires_at=time.time() + 600  # 10 minutes
                    ))
        
        return suggestions
    
    def _suggest_battery(self) -> List[ProactiveSuggestion]:
        """Battery-related suggestions"""
        suggestions = []
        
        battery = self.context.battery_percent
        charging = self.context.charging_status
        
        # Low battery + important time
        if battery and battery < 20 and charging != "Charging":
            hour = datetime.now().hour
            if 9 <= hour < 17:  # During work hours
                suggestions.append(ProactiveSuggestion(
                    suggestion_id='battery_critical_work',
                    title='Save Your Work',
                    description=f'Battery at {battery}% - Save important work now',
                    command='save all files',
                    confidence=0.9,
                    reason='Critical battery during work hours'
                ))
        
        return suggestions
    
    def _suggest_idle(self) -> List[ProactiveSuggestion]:
        """Idle time suggestions"""
        suggestions = []
        
        idle_seconds = self.context.idle_time
        
        # Long idle = suggest break reminder or screen lock
        if idle_seconds and idle_seconds > 600:  # 10 minutes
            suggestions.append(ProactiveSuggestion(
                suggestion_id='idle_lock',
                title='Lock Screen?',
                description='You\'ve been away for a while. Lock your screen?',
                command='lock computer',
                confidence=0.75,
                reason='Extended idle time'
            ))
        
        return suggestions
    
    def _add_suggestion(self, suggestion: ProactiveSuggestion):
        """Add suggestion if not already present"""
        # Check if similar suggestion already exists
        for existing in self.active_suggestions:
            if existing.suggestion_id == suggestion.suggestion_id:
                return
        
        self.active_suggestions.append(suggestion)
        logger.info(f"💡 New suggestion: {suggestion.title}")
        
        # Show in GUI
        if self.gui:
            self._display_suggestion(suggestion)
    
    def _display_suggestion(self, suggestion: ProactiveSuggestion):
        """Display suggestion to user"""
        try:
            self.gui.queue_gui_task(
                lambda: self.gui.show_terminal_output(
                    f"💡 {suggestion.title}: {suggestion.description}",
                    color="cyan"
                )
            )
            
            # Optionally speak if confidence is high
            if suggestion.confidence >= 0.8:
                from config.settings import ENABLE_TTS
                if ENABLE_TTS:
                    from audio.tts import speak
                    speak(f"Suggestion: {suggestion.title}")
        except Exception as e:
            logger.error(f"Failed to display suggestion: {e}")
    
    def get_suggestions(self) -> List[ProactiveSuggestion]:
        """Get all active suggestions"""
        with self.lock:
            return [s for s in self.active_suggestions if not s.dismissed]
    
    def dismiss_suggestion(self, suggestion_id: str):
        """Dismiss a suggestion"""
        with self.lock:
            for suggestion in self.active_suggestions:
                if suggestion.suggestion_id == suggestion_id:
                    suggestion.dismissed = True
                    self.dismissed_suggestions.add(suggestion_id)
                    logger.info(f"Dismissed suggestion: {suggestion_id}")
                    break
    
    def accept_suggestion(self, suggestion_id: str) -> Optional[str]:
        """
        Accept and execute a suggestion
        
        Returns:
            Command to execute, or None
        """
        with self.lock:
            for suggestion in self.active_suggestions:
                if suggestion.suggestion_id == suggestion_id:
                    command = suggestion.command
                    suggestion.dismissed = True
                    logger.info(f"✅ Accepted suggestion: {suggestion.title}")
                    return command
        return None
    
    def shutdown(self):
        """Shutdown suggestion engine"""
        logger.info("🛑 Shutting down proactive suggestions...")
        self.running = False
        self._save_patterns()
        if self.thread.is_alive():
            self.thread.join(timeout=2)


# Global suggestion engine
_suggestion_engine = None

def get_suggestion_engine(context_manager=None, gui_handler=None):
    """Get or create global suggestion engine"""
    global _suggestion_engine
    if _suggestion_engine is None and context_manager and gui_handler:
        _suggestion_engine = ProactiveSuggestionEngine(context_manager, gui_handler)
    return _suggestion_engine