"""
Auto-Sync Connections Script
自动同步LinkedIn connections到Memory，检测新增connections

Features:
1. 导入全部connections（支持大量翻页）
2. 检测new connections（与上次对比）
3. 生成统计报告
"""
import os
import sys
import asyncio
import re
from datetime import datetime
from typing import List, Dict, Set

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from modules.logger_config import app_logger
from modules.coffee_chat_memory import CoffeeChatMemory


class ConnectionSyncer:
    """
    自动同步LinkedIn connections
    """
    
    def __init__(self):
        self.session = None
        self.memory = CoffeeChatMemory()
        self.stats_file = "data/connection_sync_stats.txt"
    
    async def sync_all_connections(self, max_pages: int = 30, detect_new: bool = True):
        """
        同步所有connections
        
        Args:
            max_pages: 最大翻页数（30页 ≈ 600-1500个connections）
            detect_new: 是否检测新增connections
        """
        print("🔄 Auto-Sync LinkedIn Connections")
        print("=" * 60)
        
        # Step 1: 获取当前Memory中的connections
        existing_urls = set()
        if detect_new:
            existing_contacts = self.memory.get_all_contacts()
            existing_urls = {c.get('linkedin_url') for c in existing_contacts if c.get('linkedin_url')}
            print(f"📊 Current connections in Memory: {len(existing_urls)}")
        
        async with stdio_client(
            StdioServerParameters(
                command="npx.cmd",
                args=["-y", "chrome-devtools-mcp@latest", "--user-data-dir=C:/temp/linkedin-automation-profile"],
                env=None
            )
        ) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await session.initialize()
                
                # Navigate to connections page
                print("\n📍 Opening LinkedIn Connections...")
                await session.call_tool("navigate_page", arguments={
                    "url": "https://www.linkedin.com/mynetwork/invite-connect/connections/",
                    "type": "url"
                })
                
                await asyncio.sleep(3)
                
                # Check login
                snapshot = await self._get_snapshot()
                if "sign in" in snapshot.lower():
                    print("⚠️ NOT LOGGED IN - Please login first!")
                    await asyncio.sleep(60)
                    return
                
                print("   ✅ Logged in")
                
                # Import connections with pagination
                all_connections = []
                new_connections = []
                seen_urls = set()  # Track URLs we've already parsed
                no_new_count = 0  # Count consecutive pages with no new contacts
                
                for page in range(max_pages):
                    print(f"\n📄 Page {page + 1}/{max_pages}...")
                    
                    snapshot = await self._get_snapshot()
                    connections = self._parse_connections(snapshot)
                    
                    if not connections:
                        print("   No connections found in snapshot")
                        break
                    
                    # Filter out duplicates from this snapshot
                    unique_connections = []
                    for conn in connections:
                        url = conn.get('linkedin_url', '')
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            unique_connections.append(conn)
                    
                    # Detect new connections (not in Memory)
                    page_new = 0
                    for conn in unique_connections:
                        url = conn.get('linkedin_url', '')
                        if not self.memory.has_contacted(url):
                            all_connections.append(conn)
                            
                            # Check if truly new (not in existing_urls)
                            if detect_new and url and url not in existing_urls:
                                new_connections.append(conn)
                                page_new += 1
                    
                    print(f"   Parsed {len(connections)} total, {len(unique_connections)} unique, {page_new} new")
                    print(f"   📊 Total seen so far: {len(seen_urls)} unique contacts")
                    
                    # Check if we're stuck (no new unique contacts)
                    if len(unique_connections) == 0:
                        no_new_count += 1
                        if no_new_count >= 5:  # Increased from 3 to 5
                            print("   ⚠️ No new contacts for 5 consecutive attempts, stopping")
                            break
                    else:
                        no_new_count = 0
                    
                    # Strategy: Scroll to bottom first, then click Load more
                    print("   🔽 Loading more connections...")
                    
                    # Step 1: Scroll to bottom to make "Load more" visible
                    for i in range(3):
                        await session.call_tool("evaluate_script", arguments={
                            "function": "() => { window.scrollTo(0, document.body.scrollHeight); }"
                        })
                        await asyncio.sleep(1)
                    
                    # Step 2: Try to click "Load more" button (support Chinese & English)
                    click_success = False
                    for attempt in range(3):  # Try 3 times
                        try:
                            result = await session.call_tool("evaluate_script", arguments={
                                "function": """() => {
                                    // Look for "Load more" button (Chinese or English)
                                    const buttons = Array.from(document.querySelectorAll('button'));
                                    const loadMoreBtn = buttons.find(b => {
                                        const text = b.innerText.toLowerCase();
                                        return text.includes('load more') || 
                                               text.includes('show more') ||
                                               text.includes('see more') ||
                                               text.includes('加载更多') ||
                                               text.includes('显示更多') ||
                                               text.includes('查看更多');
                                    });
                                    
                                    if (loadMoreBtn) {
                                        loadMoreBtn.click();
                                        return { success: true, text: loadMoreBtn.innerText };
                                    }
                                    
                                    return { success: false, buttonCount: buttons.length };
                                }"""
                            })
                            
                            # Check result
                            if result and result.content:
                                content_text = result.content[0].text if result.content else "{}"
                                if '"success": true' in content_text or '"success":true' in content_text:
                                    print(f"      ✅ Clicked Load more button (attempt {attempt + 1})")
                                    click_success = True
                                    break
                                else:
                                    print(f"      ⚠️ Button not found (attempt {attempt + 1})")
                            
                            await asyncio.sleep(1)
                            
                        except Exception as e:
                            print(f"      ⚠️ Click attempt {attempt + 1} failed: {e}")
                            await asyncio.sleep(1)
                    
                    if not click_success:
                        print("      ℹ️ No Load more button found, may have reached the end")
                    
                    # Wait for new content to load
                    print("   ⏳ Waiting for content...")
                    await asyncio.sleep(4)
                    
                    # Scroll back to top to parse new contacts
                    await session.call_tool("evaluate_script", arguments={
                        "function": "() => { window.scrollTo(0, 0); }"
                    })
                    await asyncio.sleep(1)

                
                # Save to memory
                print(f"\n💾 Saving {len(all_connections)} connections to memory...")
                
                for conn in all_connections:
                    contact_id = conn.get('linkedin_url', conn.get('name', ''))
                    self.memory.save_contact(contact_id, {
                        **conn,
                        'status': 'connected',
                        'imported_at': datetime.now().isoformat()
                    })
                
                # Generate report
                self._generate_report(
                    total_imported=len(all_connections),
                    new_detected=len(new_connections),
                    new_connections=new_connections
                )
                
                print(f"\n✅ Sync Complete!")
                print(f"   Total imported: {len(all_connections)}")
                if detect_new:
                    print(f"   New connections: {len(new_connections)}")
                print("=" * 60)
                
                print("\nBrowser will close in 10 seconds...")
                await asyncio.sleep(10)
    
    async def _get_snapshot(self) -> str:
        """Get page snapshot"""
        result = await self.session.call_tool("take_snapshot", arguments={})
        return result.content[0].text if result.content else ""
    
    def _parse_connections(self, snapshot: str) -> List[Dict]:
        """Parse connections from snapshot"""
        connections = []
        current = {}
        
        lines = snapshot.split('\n')
        
        for i, line in enumerate(lines):
            # Look for profile links
            if 'linkedin.com/in/' in line and 'link' in line:
                if current:
                    connections.append(current)
                
                url_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9\-]+)', line)
                name_match = re.search(r'link "([^"]+)"', line)
                
                if url_match:
                    current = {
                        'linkedin_url': f"https://www.linkedin.com/in/{url_match.group(1)}",
                        'name': name_match.group(1) if name_match else 'Unknown',
                        'connection_degree': '1st'  # Already connected
                    }
            
            # Look for title/company
            elif current and 'StaticText' in line:
                text_match = re.search(r'StaticText "([^"]+)"', line)
                if text_match:
                    text = text_match.group(1)
                    if not current.get('title') and len(text) > 3:
                        if ' at ' in text:
                            parts = text.split(' at ')
                            current['title'] = parts[0]
                            current['company'] = parts[1] if len(parts) > 1 else ''
                        else:
                            current['title'] = text
        
        if current:
            connections.append(current)
        
        return connections
    
    def _generate_report(self, total_imported: int, new_detected: int, new_connections: List[Dict]):
        """
        生成同步报告
        """
        report = f"""
╔══════════════════════════════════════════════════════════╗
║          LinkedIn Connection Sync Report                ║
╚══════════════════════════════════════════════════════════╝

📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 Statistics:
   • Total imported: {total_imported}
   • New connections detected: {new_detected}

"""
        
        if new_connections:
            report += "🆕 New Connections:\n"
            for i, conn in enumerate(new_connections[:10], 1):  # Show top 10
                name = conn.get('name', 'Unknown')
                company = conn.get('company', 'N/A')
                report += f"   {i}. {name} - {company}\n"
            
            if len(new_connections) > 10:
                report += f"   ... and {len(new_connections) - 10} more\n"
        
        report += "\n" + "=" * 60 + "\n"
        
        # Print to console
        print(report)
        
        # Save to file
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        with open(self.stats_file, 'a', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📁 Report saved to: {self.stats_file}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-Sync LinkedIn Connections')
    parser.add_argument('--pages', '-p', type=int, default=30,
                       help='Maximum pages to scroll (default: 30, ~600-1500 connections)')
    parser.add_argument('--no-detect-new', action='store_true',
                       help='Disable new connection detection')
    args = parser.parse_args()
    
    print("\n")
    print("=" * 60)
    print("   LinkedIn Connection Auto-Sync")
    print("=" * 60)
    print("\n⚠️ This will sync ALL your LinkedIn connections to Memory")
    print("   and detect any new connections since last sync.")
    
    print(f"\n📋 Configuration:")
    print(f"   Max pages: {args.pages}")
    print(f"   Detect new: {not args.no_detect_new}")
    
    print(f"\n🚀 Starting in 3 seconds... (Ctrl+C to cancel)")
    
    try:
        await asyncio.sleep(3)
    except KeyboardInterrupt:
        print("\n❌ Cancelled")
        return
    
    syncer = ConnectionSyncer()
    
    try:
        await syncer.sync_all_connections(
            max_pages=args.pages,
            detect_new=not args.no_detect_new
        )
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
