"""
Telegram Radar Engine
Main module for monitoring Telegram groups and processing messages
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.types import PeerChat, PeerChannel, PeerUser
import aiohttp

from db import (
    get_enabled_accounts, get_keywords, get_setting, log_message,
    set_setting
)
from ai_classifier import classify_message_async
from logger_util import setup_logger

logger = setup_logger(__name__)

class RadarEngine:
    def __init__(self):
        self.clients: Dict[str, TelegramClient] = {}
        self.is_running = False
        self.keywords: Set[str] = set()
        self.ai_enabled = False
        self.api_key = None
        self.semaphore = asyncio.Semaphore(10)  # Limit concurrent operations
        self.message_cache: Dict[int, datetime] = {}  # Cache to avoid duplicate processing
        self.cache_ttl = 300  # 5 minutes
        
    async def initialize(self):
        """Initialize the radar engine"""
        logger.info("Initializing Radar Engine...")
        await self.reload_settings()
        await self.reload_keywords()
        await self.load_accounts()
        logger.info("Radar Engine initialized successfully")
        
    async def reload_settings(self):
        """Reload settings from database"""
        self.ai_enabled = get_setting('ai_enabled', 'false').lower() == 'true'
        self.api_key = get_setting('openrouter_api_key')
        logger.info(f"Settings reloaded - AI Enabled: {self.ai_enabled}")
        
    async def reload_keywords(self):
        """Reload keywords from database"""
        keywords = get_keywords()
        self.keywords = set(kw.lower() for kw in keywords)
        logger.info(f"Keywords reloaded: {len(self.keywords)} keywords loaded")
        
    async def load_accounts(self):
        """Load and initialize all enabled accounts"""
        accounts = get_enabled_accounts()
        logger.info(f"Loading {len(accounts)} enabled accounts...")
        
        for account in accounts:
            try:
                await self.add_client(account)
            except Exception as e:
                logger.error(f"Failed to load account {account['phone']}: {str(e)}")
                
    async def add_client(self, account: Dict):
        """Add a new Telegram client for an account"""
        phone = account['phone']
        api_id = account['api_id']
        api_hash = account['api_hash']
        
        session_file = f"sessions/{phone}.session"
        
        try:
            client = TelegramClient(
                session_file,
                api_id,
                api_hash,
                system_version="4.16.30-vxCUSTOM",
                device_model="Custom Device",
                app_version="Telegram Radar v1.0"
            )
            
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.warning(f"Account {phone} requires authorization")
                return False
            
            # Register event handler
            @client.on(events.NewMessage(incoming=True))
            async def handle_message(event):
                await self.process_message(event, phone)
            
            self.clients[phone] = client
            logger.info(f"Client for {phone} connected successfully")
            return True
            
        except SessionPasswordNeededError:
            logger.error(f"Account {phone} requires 2FA password")
            return False
        except Exception as e:
            logger.error(f"Error connecting account {phone}: {str(e)}")
            return False
    
    async def process_message(self, event, phone: str):
        """Process incoming message"""
        try:
            # Skip if message is not in a group
            if not isinstance(event.peer_id, (PeerChat, PeerChannel)):
                return
            
            # Skip if message is from the bot itself
            if event.out:
                return
            
            # Skip if message is from a bot
            if event.from_id is None:
                return
            
            # Skip service messages
            if event.action:
                return
            
            # Skip old messages (older than 1 minute)
            if event.date < datetime.now() - timedelta(minutes=1):
                return
            
            message_text = event.message.text or ""
            
            # Skip empty messages
            if not message_text.strip():
                return
            
            # Check cache to avoid duplicate processing
            message_id = event.id
            if message_id in self.message_cache:
                if datetime.now() - self.message_cache[message_id] < timedelta(seconds=self.cache_ttl):
                    return
            
            self.message_cache[message_id] = datetime.now()
            
            # Check for keywords
            message_lower = message_text.lower()
            found_keywords = [kw for kw in self.keywords if kw in message_lower]
            
            if not found_keywords:
                return
            
            logger.info(f"🔍 Keyword detected in message from {phone}: {found_keywords}")
            
            # Get sender information
            sender = await event.get_sender()
            sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
            sender_id = sender.username or f"ID: {sender.id}"
            
            # Get group information
            chat = await event.get_chat()
            group_name = chat.title or "Unknown Group"
            
            # Classify message if AI is enabled
            classification = None
            should_forward = True
            
            if self.ai_enabled and self.api_key:
                async with self.semaphore:
                    classification = await classify_message_async(message_text, self.api_key)
                    
                    # If marketer with high confidence, skip forwarding
                    if (classification['type'] == 'marketer' and 
                        classification['confidence'] > 60):
                        logger.info(f"🚫 Marketer detected (confidence: {classification['confidence']}%)")
                        should_forward = False
                        log_message(message_id, chat.id, phone, 'ignored', 
                                  classification['type'], classification['confidence'])
                        return
            
            # Forward message to alert group
            if should_forward:
                await self.forward_message(event, phone, sender_name, sender_id, group_name)
                log_message(message_id, chat.id, phone, 'forwarded',
                          classification['type'] if classification else None,
                          classification['confidence'] if classification else None)
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    async def forward_message(self, event, phone: str, sender_name: str, 
                             sender_id: str, group_name: str):
        """Forward message to alert group"""
        try:
            # Get alert group for this account
            accounts = get_enabled_accounts()
            alert_group = None
            
            for account in accounts:
                if account['phone'] == phone:
                    alert_group = account['alert_group']
                    break
            
            # Use default alert group if not specified
            if not alert_group:
                alert_group = get_setting('default_alert_group')
            
            if not alert_group:
                logger.warning(f"No alert group configured for {phone}")
                return
            
            client = self.clients.get(phone)
            if not client:
                logger.error(f"Client for {phone} not found")
                return
            
            message_text = event.message.text or ""
            
            # Create formatted message
            footer = f"""🚨 **رادار ذكي - طلب مساعدة**
━━━━━━━━━━━━━━━━━━━
📝 **النص الأصلي**: {message_text}
👤 **المرسل**: {sender_name} - {sender_id}
🏢 **المجموعة**: {group_name}
━━━━━━━━━━━━━━━━━━━"""
            
            try:
                # Try to forward the message
                await client.forward_messages(alert_group, event.message)
                # Send footer as separate message
                await client.send_message(alert_group, footer)
                logger.info(f"✅ Message forwarded to {alert_group}")
            except Exception as e:
                # If forward fails, send a copy with footer
                logger.warning(f"Forward failed, sending copy: {str(e)}")
                await client.send_message(alert_group, footer)
                
                # Forward media if exists
                if event.media:
                    try:
                        await client.send_file(alert_group, event.media)
                    except Exception as media_error:
                        logger.warning(f"Failed to forward media: {str(media_error)}")
                        
        except FloodWaitError as e:
            logger.warning(f"Flood wait: {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Error forwarding message: {str(e)}")
    
    async def start(self):
        """Start the radar engine"""
        if self.is_running:
            logger.warning("Radar is already running")
            return
        
        logger.info("🚀 Starting Radar Engine...")
        self.is_running = True
        set_setting('radar_status', 'running')
        
        try:
            # Start all clients
            tasks = [client.run_until_disconnected() for client in self.clients.values()]
            if tasks:
                await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in radar loop: {str(e)}")
        finally:
            self.is_running = False
            set_setting('radar_status', 'stopped')
    
    async def stop(self):
        """Stop the radar engine"""
        logger.info("🛑 Stopping Radar Engine...")
        self.is_running = False
        set_setting('radar_status', 'stopped')
        
        # Disconnect all clients
        for phone, client in self.clients.items():
            try:
                await client.disconnect()
                logger.info(f"Client {phone} disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting {phone}: {str(e)}")
        
        self.clients.clear()
        logger.info("Radar Engine stopped")
    
    def is_running_status(self) -> bool:
        """Check if radar is running"""
        return self.is_running
    
    async def get_status(self) -> Dict:
        """Get radar status"""
        return {
            "running": self.is_running,
            "clients_count": len(self.clients),
            "keywords_count": len(self.keywords),
            "ai_enabled": self.ai_enabled,
            "connected_accounts": list(self.clients.keys())
        }

# Global radar engine instance
radar_engine = RadarEngine()
