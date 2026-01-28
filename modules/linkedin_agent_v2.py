"""
LinkedIn Agent V2 (The "New MCP" Logic)
Uses direct CDP browser control to perform Deep Dive -> Draft -> Paste workflow.
"""
import time
import logging
from typing import Dict, Optional

# Import the new browser automation module
from modules.browser_automation import BrowserAutomation
from modules.agent_manager import AgentManager # To get personalizer

logger = logging.getLogger(__name__)

class LinkedInAgentV2:
    def __init__(self):
        self.browser = BrowserAutomation(port=9222)
        self.agent_manager = AgentManager() # Existing agent manager for GPT
    
    def connect_browser(self) -> bool:
        """Connect to the browser instance"""
        return self.browser.connect()
        
    def navigate_to_profile(self, url: str):
        """Navigate to a LinkedIn profile"""
        if not self.browser.ws:
            self.browser.connect()
        self.browser.navigate(url)
        time.sleep(4) # Wait for load
        
    def deep_dive_and_generate_draft(self, contact_name: str, contact_url: str) -> Dict[str, str]:
        """
        1. Navigate to profile
        2. Scrape (read) text
        3. Generate personalized message
        """
        if not self.browser.ws:
            if not self.browser.connect():
                return {"error": "Could not connect to Chrome"}
        
        # 1. Navigate
        logger.info(f"Navigating to {contact_name}: {contact_url}")
        self.browser.navigate(contact_url)
        time.sleep(5) # Let it render
        
        # 2. Scrape Profile text
        # Simple scraping of the visible text
        snapshot = self.browser.get_snapshot()
        
        # 3. Generate Message using AgentManager's Personalizer with Deep Dive
        # We pass the full snapshot to the new method
        
        draft = self.agent_manager.personalizer.generate_message_from_snapshot(
            contact_name=contact_name,
            snapshot=snapshot
        )
        
        # Log success
        logger.info(f"Generated deep dive draft for {contact_name}")
        
        return {
            "success": True,
            "draft": draft,
            "profile_text": snapshot[:500] + "..." # Snippet
        }

    def open_message_box(self) -> Dict:
        """Click the 'Message' button on the profile"""
        if not self.browser.ws:
            return {"success": False, "error": "Not connected"}
            
        # JS to find and click message button
        js = """
        (function() {
            const buttons = Array.from(document.querySelectorAll('button'));
            // Find button with 'Message' text
            const msgBtn = buttons.find(b => 
                b.textContent.trim().includes('Message') && !b.disabled
            );
            if (msgBtn) {
                msgBtn.click();
                return {found: true};
            }
            return {found: false};
        })()
        """
        res = self.browser.evaluate_script(js)
        if res and res.get('result', {}).get('value', {}).get('found'):
            return {"success": True}
        return {"success": False, "error": "Message button not found"}

    def paste_message(self, text: str) -> Dict:
        """Paste text into the focused message box"""
        if not self.browser.ws:
            return {"success": False, "error": "Not connected"}
            
        # 1. Ensure focus on contenteditable
        # The user might need to click specifically, but usually clicking "Message" focuses it.
        # We can try to finding the message box and focusing it.
        
        focus_js = """
        (function() {
            const box = document.querySelector('div[contenteditable="true"][role="textbox"]');
            if (box) {
                box.focus();
                return true;
            }
            return false;
        })()
        """
        self.browser.evaluate_script(focus_js)
        time.sleep(1)
        
        # 2. Paste
        res = self.browser.paste_to_focused_element(text)
        if res and res.get('result', {}).get('value', {}).get('success'):
             return {"success": True}
        
        return {"success": False, "error": "Paste failed"}

