"""
Agent Activity Tracker - Monitors agent activity and updates status
"""

from datetime import datetime, timedelta
from .models import db, Agent
import threading
import time

class ActivityTracker:
    """Tracks agent activity and updates status"""
    
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.thread = None
        
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
    def start_tracking(self):
        """Start the activity tracking thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._track_activity, daemon=True)
            self.thread.start()
            print("📊 Agent activity tracker started")
    
    def stop_tracking(self):
        """Stop the activity tracking thread"""
        self.running = False
        if self.thread:
            self.thread.join()
            print("📊 Agent activity tracker stopped")
    
    def _track_activity(self):
        """Main tracking loop"""
        while self.running:
            try:
                with self.app.app_context():
                    self._update_agent_statuses()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"Error in activity tracker: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _update_agent_statuses(self):
        """Update agent statuses based on activity"""
        try:
            # Get all agents
            agents = Agent.query.all()
            
            # Define activity thresholds
            inactive_threshold = datetime.utcnow() - timedelta(minutes=5)  # 5 minutes
            offline_threshold = datetime.utcnow() - timedelta(minutes=15)  # 15 minutes
            
            for agent in agents:
                if not agent.last_active:
                    # No activity recorded, mark as offline
                    if agent.status != 'offline':
                        agent.status = 'offline'
                        print(f"📴 Agent {agent.name} marked as offline (no activity recorded)")
                elif agent.last_active < offline_threshold:
                    # Agent hasn't been active for 15+ minutes
                    if agent.status != 'offline':
                        agent.status = 'offline'
                        print(f"📴 Agent {agent.name} marked as offline (inactive for 15+ minutes)")
                elif agent.last_active < inactive_threshold:
                    # Agent hasn't been active for 5+ minutes but less than 15
                    if agent.status not in ['offline', 'busy']:
                        agent.status = 'away'
                        print(f"⏰ Agent {agent.name} marked as away (inactive for 5+ minutes)")
                else:
                    # Agent is active - but DON'T automatically set to available
                    # Only update status if they're currently offline/away and have active sessions
                    if agent.status == 'offline' or agent.status == 'away':
                        # Only restore status if they have active sessions (indicating they're actually working)
                        if agent.current_sessions > 0:
                            if agent.current_sessions >= agent.max_concurrent_sessions:
                                agent.status = 'busy'
                            else:
                                agent.status = 'available'
                            print(f"✅ Agent {agent.name} marked as {agent.status} (recently active with sessions)")
                        else:
                            # Agent is active but has no sessions - keep them offline until they login
                            print(f"ℹ️ Agent {agent.name} is active but has no sessions - keeping offline status")
            
            db.session.commit()
            
        except Exception as e:
            print(f"Error updating agent statuses: {e}")
            db.session.rollback()

# Global activity tracker instance
activity_tracker = ActivityTracker()

def init_activity_tracker(app):
    """Initialize and start the activity tracker"""
    activity_tracker.init_app(app)
    activity_tracker.start_tracking()

def update_agent_activity(agent_id):
    """Update specific agent's last activity time"""
    try:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        if agent:
            agent.last_active = datetime.utcnow()
            # Only update status if agent is not offline (meaning they're logged in)
            if agent.status != 'offline':
                # Update status based on current workload
                if agent.current_sessions >= agent.max_concurrent_sessions:
                    agent.status = 'busy'
                else:
                    agent.status = 'available'
            # If agent is offline, don't change their status - they need to login first
            db.session.commit()
            return True
    except Exception as e:
        print(f"Error updating agent activity: {e}")
        db.session.rollback()
    return False
