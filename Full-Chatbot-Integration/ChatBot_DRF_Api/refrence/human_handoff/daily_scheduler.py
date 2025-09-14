"""
Daily Scheduler for Super Admin Dashboard
Handles automatic daily reset at 12 AM Nepal time
"""

import threading
import time
from datetime import datetime, timedelta, timezone
import requests
import logging
from .models import db, Agent, ChatSession, AgentSession, Message

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DailyScheduler:
    def __init__(self, app=None, base_url="http://127.0.0.1:5001"):
        self.app = app
        self.base_url = base_url
        # Nepal timezone is UTC+5:45
        self.nepal_tz = timezone(timedelta(hours=5, minutes=45))
        self.scheduler_thread = None
        self.running = False
        
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
    def start_scheduler(self):
        """Start the daily scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Daily scheduler started - will reset at 12:00 AM Nepal time")
        
    def stop_scheduler(self):
        """Stop the daily scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Daily scheduler stopped")
        
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Get current time in Nepal
                nepal_now = datetime.now(self.nepal_tz)
                
                # Calculate next midnight in Nepal time
                next_midnight = nepal_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                
                # Calculate seconds until next midnight
                seconds_until_midnight = (next_midnight - nepal_now).total_seconds()
                
                logger.info(f"Next daily reset scheduled for: {next_midnight.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                logger.info(f"Time until reset: {seconds_until_midnight/3600:.2f} hours")
                
                # Sleep until midnight (check every minute to allow for graceful shutdown)
                while seconds_until_midnight > 0 and self.running:
                    sleep_time = min(60, seconds_until_midnight)  # Sleep for 1 minute or remaining time
                    time.sleep(sleep_time)
                    
                    # Recalculate remaining time
                    nepal_now = datetime.now(self.nepal_tz)
                    seconds_until_midnight = (next_midnight - nepal_now).total_seconds()
                
                # If we're still running, perform the daily reset
                if self.running:
                    logger.info("Performing daily reset...")
                    self._perform_daily_reset()
                    
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                # Sleep for 5 minutes before retrying
                time.sleep(300)
                
    def _perform_daily_reset(self):
        """Perform the daily reset operation"""
        try:
            if not self.app:
                logger.error("Flask app not initialized")
                return
                
            with self.app.app_context():
                # Reset agent status
                agents = Agent.query.all()
                agents_reset = 0
                
                for agent in agents:
                    agent.current_sessions = 0
                    agent.status = 'offline'  # Set to offline, they need to login to be available
                    agent.last_active = datetime.utcnow()
                    agent.total_sessions_handled = 0  # Reset daily handled sessions count
                    agents_reset += 1
                
                # Clear pending sessions
                pending_sessions = ChatSession.query.filter_by(
                    requires_human=True,
                    status='escalated',
                    assigned_agent_id=None
                ).all()
                
                pending_cleared = 0
                for session in pending_sessions:
                    session.status = 'resolved'
                    session.requires_human = False
                    session.updated_at = datetime.utcnow()
                    pending_cleared += 1
                    
                    # Add system message
                    system_message = Message(
                        session_id=session.session_id,
                        sender_type='system',
                        message_content='Daily reset - session automatically resolved',
                        timestamp=datetime.utcnow()
                    )
                    db.session.add(system_message)
                
                # Complete active agent sessions
                active_agent_sessions = AgentSession.query.filter_by(status='active').all()
                active_completed = 0
                
                for agent_session in active_agent_sessions:
                    agent_session.status = 'completed'
                    agent_session.ended_at = datetime.utcnow()
                    active_completed += 1
                
                # Reset assigned sessions
                assigned_sessions = ChatSession.query.filter(
                    ChatSession.assigned_agent_id.isnot(None),
                    ChatSession.status == 'assigned'
                ).all()
                
                assigned_reset = 0
                for session in assigned_sessions:
                    session.assigned_agent_id = None
                    session.status = 'resolved'
                    session.updated_at = datetime.utcnow()
                    assigned_reset += 1
                
                # Commit all changes
                db.session.commit()

                # Emit socket event to notify all agents about the daily reset
                try:
                    from .socketio_events import socketio
                    socketio.emit('daily_reset', {
                        'message': 'Daily reset completed - total handled sessions reset to 0',
                        'agents_reset': agents_reset,
                        'pending_cleared': pending_cleared,
                        'timestamp': datetime.utcnow().isoformat()
                    }, room='agents')
                    logger.info("Daily reset notification sent to all agents")
                except Exception as socket_error:
                    logger.error(f"Error sending daily reset notification: {socket_error}")

                nepal_time = datetime.now(self.nepal_tz).strftime('%Y-%m-%d %H:%M:%S %Z')
                logger.info(f"Daily reset completed successfully at {nepal_time}")
                logger.info(f"- Agents reset: {agents_reset}")
                logger.info(f"- Pending sessions cleared: {pending_cleared}")
                logger.info(f"- Active sessions completed: {active_completed}")
                logger.info(f"- Assigned sessions reset: {assigned_reset}")
                
        except Exception as e:
            logger.error(f"Error performing daily reset: {e}")
            try:
                db.session.rollback()
            except:
                pass
                
    def get_next_reset_time(self):
        """Get the next scheduled reset time"""
        nepal_now = datetime.now(self.nepal_tz)
        next_midnight = nepal_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return next_midnight
        
    def get_time_until_reset(self):
        """Get time remaining until next reset"""
        nepal_now = datetime.now(self.nepal_tz)
        next_reset = self.get_next_reset_time()
        return next_reset - nepal_now
        
    def manual_reset(self):
        """Manually trigger a reset (for testing)"""
        logger.info("Manual reset triggered")
        self._perform_daily_reset()

# Global scheduler instance
daily_scheduler = DailyScheduler()

def init_daily_scheduler(app):
    """Initialize and start the daily scheduler"""
    daily_scheduler.init_app(app)
    daily_scheduler.start_scheduler()
    return daily_scheduler

def get_scheduler_status():
    """Get current scheduler status"""
    if not daily_scheduler.running:
        return {
            'status': 'stopped',
            'next_reset': None,
            'time_until_reset': None
        }
    
    next_reset = daily_scheduler.get_next_reset_time()
    time_until = daily_scheduler.get_time_until_reset()
    
    return {
        'status': 'running',
        'next_reset': next_reset.isoformat(),  # ISO format for JavaScript parsing
        'next_reset_display': next_reset.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'time_until_reset': str(time_until).split('.')[0],  # Remove microseconds
        'nepal_time': datetime.now(daily_scheduler.nepal_tz).strftime('%Y-%m-%d %H:%M:%S %Z')
    }
