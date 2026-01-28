"""
Browser Automation via Chrome DevTools Protocol (CDP)
Mimics MCP tools behavior but runs directly in Python via WebSocket
"""
import json
import time
import requests
import websocket
import logging

logger = logging.getLogger(__name__)

import os

class BrowserAutomation:
    def __init__(self, port=9222):
        # Allow checking host.docker.internal for Docker support
        self.host = os.getenv('CDP_HOST', 'localhost')
        self.port = port
        self.ws_url = None
        self.ws_url = None
        self.page_id = None
        self.ws = None
        self._id_counter = 0

    def connect(self):
        """Connect to the browser's first active page"""
        try:
            # Get list of pages
            response = requests.get(f"http://{self.host}:{self.port}/json")
            pages = response.json()
            
            # Find a suitable page (type 'page')
            target_page = None
            for page in pages:
                if page['type'] == 'page':
                    target_page = page
                    break
            
            if not target_page:
                logger.error("No pages found")
                return False
                
            self.ws_url = target_page['webSocketDebuggerUrl']
            self.page_id = target_page['id']
            self.ws = websocket.create_connection(self.ws_url)
            logger.info(f"Connected to page {self.page_id}")
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def close(self):
        if self.ws:
            self.ws.close()

    def _send_command(self, method, params=None):
        """Send a CDP command and return result"""
        if not self.ws:
            if not self.connect():
                return None
        
        self._id_counter += 1
        cmd_id = self._id_counter
        
        message = {
            "id": cmd_id,
            "method": method,
            "params": params or {}
        }
        
        try:
            self.ws.send(json.dumps(message))
            
            # Wait for response with matching ID
            start_time = time.time()
            while time.time() - start_time < 30: # 30s timeout
                response = json.loads(self.ws.recv())
                if response.get('id') == cmd_id:
                    if 'error' in response:
                        logger.error(f"CDP Error: {response['error']}")
                        return None
                    return response.get('result')
                
            logger.error("Command timeout")
            return None
            
        except BrokenPipeError:
            logger.error("WebSocket disconnected, reconnecting...")
            self.ws = None
            if self.connect():
                return self._send_command(method, params)
            return None

    def navigate(self, url):
        """Navigate to URL"""
        logger.info(f"Navigating to {url}")
        return self._send_command("Page.navigate", {"url": url})

    def get_url(self):
        """Get current URL"""
        script = "window.location.href"
        result = self.evaluate_script(script)
        if result and 'result' in result and 'value' in result['result']:
            return result['result']['value']
        return ""

    def evaluate_script(self, script, await_promise=False):
        """Evaluate JavaScript"""
        return self._send_command("Runtime.evaluate", {
            "expression": script,
            "returnByValue": True,
            "awaitPromise": await_promise
        })

    def get_snapshot(self):
        """Get page accessibility snapshot (mimicking MCP take_snapshot somewhat)"""
        # For simplicity, we'll return document.body.innerText unless ax tree is needed
        # MCP take_snapshot typically returns accessibility tree.
        # But for my quick hacks, innerText + filtering usually works or I read DOM via JS.
        # Let's return innerText to be simple.
        
        res = self.evaluate_script("document.body.innerText")
        if res and 'result' in res:
            return res['result'].get('value', "")
        return ""

    def copy_to_clipboard(self, text):
        """Copy text to clipboard via JS (requires permission/focus)"""
        # This is tricky in background. Better to set value directly.
        pass

    def paste_to_focused_element(self, text):
        """Simulate pasting text into the currently focused element (e.g. message box)"""
        # We can try to use document.execCommand('insertText') or setting value.
        # For LinkedIn message box (contenteditable), setting textContent works but might not trigger events.
        # Best approach: Input events.
        
        escaped_text = json.dumps(text)[1:-1] # Escape for JS string
        
        js = f"""
        (function() {{
            const el = document.activeElement;
            if (!el) return {{success: false}};
            
            // Try insertText first (most native)
            if (document.queryCommandSupported('insertText')) {{
                document.execCommand('insertText', false, "{escaped_text}");
                return {{success: true}};
            }}
            
            // Fallback for contenteditable
            if (el.isContentEditable) {{
                el.innerText = "{escaped_text}";
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                return {{success: true}};
            }}
            
            // Fallback for input/textarea
            if (el.value !== undefined) {{
                el.value = "{escaped_text}";
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                return {{success: true}};
            }}
            
            return {{success: false}};
        }})()
        """
        return self.evaluate_script(js)

    def find_and_click(self, selector):
        """Find element by selector and click"""
        js = f"""
        (function() {{
            const el = document.querySelector('{selector}');
            if (el) {{
                el.click();
                return {{found: true}};
            }}
            return {{found: false}};
        }})()
        """
        return self.evaluate_script(js)
