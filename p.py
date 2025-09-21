"""
WhatsApp AI Agent - ULTRA STABLE VERSION
✅ Enhanced DOM detection with multiple strategies
✅ Real-time message monitoring
✅ Bulletproof automatic chat detection
✅ Fixed API response issues
✅ Zero manual intervention needed
"""

import os
import time
import pyperclip
import logging
import sys
import hashlib
import random
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from openai import OpenAI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("whatsapp_agent.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class WhatsAppAgent:
    def __init__(self):
        load_dotenv()
        self.setup_config()
        
        # Test OpenAI connection immediately
        logger.info("🔑 Testing OpenAI API connection...")
        try:
            self.client = OpenAI(api_key=self.OPENAI_API_KEY)
            # Test with a simple call
            test_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            logger.info("✅ OpenAI API connection successful")
        except Exception as e:
            logger.error(f"❌ OpenAI API test failed: {e}")
            logger.error("Please check your OPENAI_API_KEY in .env file")
            sys.exit(1)

        # Enhanced state tracking with contact history
        self.driver = None
        self.processed_messages = set()
        self.processed_chats = set()  # Track processed chats to avoid duplicates
        self.intro_sent_by_chat = {}
        self.last_message_timestamps = {}
        self.chat_cooldowns = {}  # Separate cooldown tracking
        self.current_chat_name = None
        self.running = False
        self.last_scan_time = time.time()
        self.scan_count = 0
        
        # NEW: Contact tracking for "busy" message logic
        self.known_contacts = set()  # Contacts we've interacted with before
        self.busy_message_sent = set()  # Contacts who received the "busy" message
        self.new_contact_detected = {}  # Track when new contacts are first detected

    def setup_config(self):
        """Enhanced configuration"""
        # API Key check
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not self.OPENAI_API_KEY:
            logger.error("❌ OPENAI_API_KEY not found in .env file")
            logger.error("Please create a .env file with: OPENAI_API_KEY=your_api_key_here")
            sys.exit(1)

        # Chrome paths
        self.CHROME_DRIVER_PATH = os.getenv(
            "CHROME_DRIVER_PATH", r"C:\chromedriver-win64\chromedriver.exe"
        )
        self.CHROME_PROFILE_PATH = os.getenv(
            "CHROME_PROFILE_PATH", r"C:/Temp/ChromeProfile"
        )
        
        # Test ChromeDriver path
        if not os.path.exists(self.CHROME_DRIVER_PATH):
            logger.error(f"❌ ChromeDriver not found at: {self.CHROME_DRIVER_PATH}")
            logger.error("Please download ChromeDriver and update the path in .env file")
            sys.exit(1)

        # Timing config - Optimized to prevent duplicates
        self.CHECK_INTERVAL = 3.0  # Slower to prevent duplicates
        self.MESSAGE_COOLDOWN = 15  # Longer cooldown per chat
        self.STABILITY_DELAY = 2.0  # More stability time
        self.SCAN_COOLDOWN = 5.0   # Minimum time between full scans

        # Enhanced WhatsApp selectors - Updated for 2025
        self.CHAT_LIST_SELECTORS = [
            '//div[@id="pane-side"]//div[@role="grid"]//div[@role="gridcell"]',
            '//div[contains(@class, "_2nY6U")]',  # Chat list items
            '//div[@data-testid="cell-frame-container"]',
            '//div[contains(@class, "_1i0i5")]',  # Individual chat rows
        ]

        # Unread message indicators
        self.UNREAD_INDICATORS = [
            './/span[contains(@class, "_38M1B")]',  # Unread count badge
            './/div[contains(@class, "_2EXPL")]',   # Unread dot
            './/span[contains(@aria-label, "unread")]',
            './/span[contains(@class, "unread")]',
        ]

        # Message input selectors
        self.MESSAGE_INPUT_SELECTORS = [
            '//div[@contenteditable="true"][@data-tab="10"]',
            '//div[@contenteditable="true"][@data-testid="conversation-compose-box-input"]',
            '//div[@role="textbox"][@contenteditable="true"]',
        ]

        # Enhanced message detection - Updated selectors for 2025
        self.INCOMING_MSG_SELECTORS = [
            '//div[@data-testid="conversation-panel-messages"]//div[contains(@class, "message-in")]//span[contains(@class, "selectable-text")]',
            '//div[contains(@class, "_1beEj") and contains(@class, "message-in")]//span[contains(@class, "selectable-text")]',
            '//div[contains(@class, "copyable-text")][@data-pre-plain-text and not(ancestor::div[contains(@class, "message-out")])]//span[@dir="ltr"]',
        ]
        
        # Outgoing message selectors to avoid replying to own messages
        self.OUTGOING_MSG_SELECTORS = [
            '//div[contains(@class, "message-out")]//span[contains(@class, "selectable-text")]',
            '//div[contains(@class, "_1beEj") and contains(@class, "message-out")]//span[contains(@class, "selectable-text")]',
        ]

        # Chat header selectors
        self.CHAT_HEADER_SELECTORS = [
            '//header[@data-testid="conversation-header"]//span[@title]',
            '//div[@data-testid="conversation-header"]//span[@title]',
            '//header//span[contains(@class, "copyable-text")][@title]',
        ]

    def setup_chrome(self):
        """Enhanced Chrome setup with debugging"""
        logger.info("🚀 Setting up Chrome...")
        try:
            chrome_options = Options()
            
            # Profile setup
            chrome_options.add_argument(f"--user-data-dir={self.CHROME_PROFILE_PATH}")
            chrome_options.add_argument("--profile-directory=Default")
            
            # Anti-detection measures
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Stability options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            
            # Create profile directory if it doesn't exist
            os.makedirs(self.CHROME_PROFILE_PATH, exist_ok=True)
            
            service = Service(self.CHROME_DRIVER_PATH)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Anti-detection script
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.maximize_window()
            logger.info("✅ Chrome setup successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Chrome setup failed: {e}")
            return False

    def wait_for_whatsapp(self):
        """Wait for WhatsApp Web to load with better detection"""
        logger.info("🌐 Opening WhatsApp Web...")
        try:
            self.driver.get("https://web.whatsapp.com")
            logger.info("⏳ Waiting for WhatsApp Web to load...")
            
            # Check current status every 5 seconds
            max_wait_time = 120  # 2 minutes total
            check_interval = 5
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                try:
                    # Check for QR code
                    qr_elements = self.driver.find_elements(By.XPATH, '//div[@data-testid="qr-code"]')
                    if qr_elements and qr_elements[0].is_displayed():
                        logger.info("📱 QR Code detected - Please scan with your phone to continue")
                        time.sleep(check_interval)
                        elapsed_time += check_interval
                        continue
                    
                    # Check for "Keep me signed in" checkbox
                    keep_signed_elements = self.driver.find_elements(By.XPATH, '//input[@type="checkbox"]')
                    if keep_signed_elements:
                        logger.info("✅ Checking 'Keep me signed in' option")
                        try:
                            if not keep_signed_elements[0].is_selected():
                                keep_signed_elements[0].click()
                        except:
                            pass
                    
                    # Check for main chat interface
                    chat_found = False
                    for selector in self.CHAT_LIST_SELECTORS:
                        try:
                            elements = self.driver.find_elements(By.XPATH, selector)
                            if elements and any(elem.is_displayed() for elem in elements):
                                logger.info("✅ WhatsApp Web loaded successfully!")
                                logger.info(f"📋 Found {len(elements)} chat elements")
                                time.sleep(3)
                                return True
                        except:
                            continue
                    
                    # Check for loading indicators
                    loading_elements = self.driver.find_elements(By.XPATH, '//*[contains(text(), "Loading")]')
                    if loading_elements:
                        logger.info("⏳ WhatsApp still loading...")
                    
                    logger.info(f"⏱️ Waiting... ({elapsed_time}/{max_wait_time}s)")
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                    
                except Exception as e:
                    logger.debug(f"Status check error: {e}")
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                    
            logger.error("❌ WhatsApp Web loading timeout - please check your internet connection or try refreshing")
            return False
            
        except Exception as e:
            logger.error(f"❌ WhatsApp loading error: {e}")
            return False

    def get_chat_name_from_element(self, chat_element):
        """Extract chat name from chat element with better reliability"""
        try:
            # Multiple strategies to get chat name
            name_selectors = [
                './/span[@title]',
                './/div[@title]',
                './/span[contains(@class, "_21S-L")]',  # Chat name class
                './/div[contains(@class, "copyable-text")]//span',
                './/span[not(@aria-label)]',  # Non-aria spans often contain names
            ]
            
            for selector in name_selectors:
                try:
                    name_elements = chat_element.find_elements(By.XPATH, selector)
                    for elem in name_elements:
                        name = elem.get_attribute('title') or elem.text
                        if name and name.strip() and len(name.strip()) > 2:
                            # Avoid common non-name text
                            exclude_words = ['online', 'last seen', 'typing', 'unread', 'new message']
                            if not any(word in name.lower() for word in exclude_words):
                                return name.strip()[:50]  # Limit length
                except:
                    continue
            
            # Fallback to a more stable identifier
            try:
                # Use element location as backup identifier
                location = chat_element.location
                return f"Chat_{location['x']}_{location['y']}"
            except:
                return f"Chat_{int(time.time())}"
                
        except Exception as e:
            logger.debug(f"Error getting chat name: {e}")
            return f"Unknown_{int(time.time())}"

    def scan_for_unread_chats(self):
        """Scan for unread chats with duplicate prevention"""
        # Prevent too frequent scanning
        current_time = time.time()
        if current_time - self.last_scan_time < self.SCAN_COOLDOWN:
            return []
        
        self.last_scan_time = current_time
        self.scan_count += 1
        
        unread_chats = []
        
        try:
            # Get all chat elements
            all_chats = []
            for selector in self.CHAT_LIST_SELECTORS:
                try:
                    chats = self.driver.find_elements(By.XPATH, selector)
                    if chats:
                        all_chats.extend(chats)
                        logger.debug(f"Found {len(chats)} elements with selector")
                        break  # Use first working selector only
                except Exception as e:
                    logger.debug(f"Selector failed: {e}")
                    continue
            
            if not all_chats:
                logger.warning("❌ No chat elements found")
                return []
            
            logger.debug(f"🔍 Scan #{self.scan_count}: Checking {len(all_chats)} chats...")
            
            # Check each chat for unread indicators
            for i, chat in enumerate(all_chats[:20]):  # Limit to first 20 chats for performance
                try:
                    if not chat.is_displayed() or chat.size['height'] <= 10:
                        continue
                    
                    # Generate chat identifier
                    chat_location = chat.location
                    chat_id = f"{chat_location['x']}_{chat_location['y']}"
                    
                    # Skip if already processed recently
                    if chat_id in self.processed_chats:
                        continue
                        
                    # Check for unread indicators
                    has_unread = False
                    for indicator in self.UNREAD_INDICATORS:
                        try:
                            unread_elem = chat.find_element(By.XPATH, indicator)
                            if unread_elem.is_displayed() and unread_elem.size['width'] > 0:
                                has_unread = True
                                break
                        except:
                            continue
                    
                    if has_unread:
                        chat_name = self.get_chat_name_from_element(chat)
                        
                        # Check cooldown for this specific chat
                        if chat_name in self.chat_cooldowns:
                            if current_time - self.chat_cooldowns[chat_name] < self.MESSAGE_COOLDOWN:
                                logger.debug(f"⏰ Chat {chat_name} in cooldown")
                                continue
                        
                        unread_chats.append((chat, chat_name, chat_id))
                        logger.info(f"📩 New unread chat: {chat_name}")
                        
                        # Mark as processed to avoid immediate re-detection
                        self.processed_chats.add(chat_id)
                        
                        # Only process one unread chat at a time
                        break
                        
                except Exception as e:
                    logger.debug(f"Error checking chat {i}: {e}")
                    continue
            
            # Clean old processed chats every 10 scans
            if self.scan_count % 10 == 0:
                self.processed_chats.clear()
                logger.debug("🧹 Cleared processed chats cache")
                    
        except Exception as e:
            logger.error(f"❌ Error scanning chats: {e}")
            
        return unread_chats

    def click_chat_element(self, chat_element):
        """Click on a chat element reliably"""
        methods = [
            lambda: ActionChains(self.driver).move_to_element(chat_element).click().perform(),
            lambda: chat_element.click(),
            lambda: self.driver.execute_script("arguments[0].click();", chat_element),
        ]
        
        for i, method in enumerate(methods, 1):
            try:
                method()
                time.sleep(self.STABILITY_DELAY)
                logger.debug(f"✅ Chat clicked using method {i}")
                return True
            except Exception as e:
                logger.debug(f"Method {i} failed: {e}")
                continue
                
        return False

    def get_current_chat_name(self):
        """Get the name of currently opened chat"""
        try:
            for selector in self.CHAT_HEADER_SELECTORS:
                try:
                    elem = self.driver.find_element(By.XPATH, selector)
                    name = elem.get_attribute('title') or elem.text
                    if name and name.strip():
                        return name.strip()
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error getting current chat name: {e}")
            
        return f"Chat_{int(time.time())}"

    def get_latest_incoming_message(self):
        """Get the latest INCOMING message (not from AI) from current chat"""
        try:
            # Get all incoming messages (excluding outgoing)
            incoming_messages = []
            
            for selector in self.INCOMING_MSG_SELECTORS:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        msg_text = elem.text.strip()
                        if msg_text and len(msg_text) > 0:
                            incoming_messages.append(msg_text)
                    if incoming_messages:
                        break  # Use first working selector
                except Exception as e:
                    logger.debug(f"Incoming message selector failed: {e}")
                    continue
            
            if not incoming_messages:
                logger.debug("No incoming messages found")
                return None
            
            # Get the latest message
            latest_message = incoming_messages[-1]
            
            # Filter out AI's own messages (check if it starts with our intro)
            ai_indicators = [
                "Hey! Akash is busy right now, but I'm his AI assistant",
                "I'm Akash's AI assistant",
                "🤖",
                "AI assistant"
            ]
            
            # Check if this looks like our own message
            for indicator in ai_indicators:
                if indicator in latest_message:
                    logger.debug(f"Skipping AI's own message: {latest_message[:50]}...")
                    return None
            
            # Additional check - if message is too long and repetitive, likely our own
            if len(latest_message) > 100 and "assistant" in latest_message.lower():
                logger.debug(f"Skipping likely AI message: {latest_message[:50]}...")
                return None
                
            return latest_message
            
        except Exception as e:
            logger.debug(f"Error getting incoming messages: {e}")
            
        return None

    def is_new_contact(self, chat_name):
        """Determine if this is a new contact (never interacted before)"""
        # Clean chat name for comparison
        clean_chat_name = chat_name.strip().lower()
        
        # Check if we've seen this contact before
        if clean_chat_name in self.known_contacts:
            return False
        
        # Check if this looks like a system-generated chat name (not a real contact)
        if clean_chat_name.startswith('chat_') or clean_chat_name.startswith('unknown_'):
            return False
            
        return True

    def mark_contact_as_known(self, chat_name):
        """Mark a contact as known (we've interacted with them)"""
        clean_chat_name = chat_name.strip().lower()
        self.known_contacts.add(clean_chat_name)

    def has_busy_message_been_sent(self, chat_name):
        """Check if busy message was already sent to this contact"""
        clean_chat_name = chat_name.strip().lower()
        return clean_chat_name in self.busy_message_sent

    def mark_busy_message_sent(self, chat_name):
        """Mark that busy message was sent to this contact"""
        clean_chat_name = chat_name.strip().lower()
        self.busy_message_sent.add(clean_chat_name)

    def generate_ai_response(self, message, chat_name):
        """Generate AI response with smart contact detection"""
        try:
            # Check contact status
            is_new = self.is_new_contact(chat_name)
            busy_sent = self.has_busy_message_been_sent(chat_name)
            
            logger.debug(f"Contact analysis for {chat_name}: new={is_new}, busy_sent={busy_sent}")
            
            # RULE 1: New contact - send busy message once
            if is_new and not busy_sent:
                logger.info(f"🆕 New contact detected: {chat_name} - sending busy message")
                self.mark_busy_message_sent(chat_name)
                self.mark_contact_as_known(chat_name)
                return "Hi, Akash is busy."
            
            # RULE 2 & 3: Follow-up from new contact OR existing contact - respond normally
            else:
                # Mark as known if not already
                self.mark_contact_as_known(chat_name)
                
                # Generate normal response
                system_prompt = (
                    "You are Akash's AI assistant. "
                    "Respond naturally and helpfully in 1-2 sentences max. "
                    "Be conversational, friendly, and use emojis appropriately like a human would. "
                    "Use casual language, contractions, and chat like you're texting a friend. "
                    "Do not mention that Akash is busy - just respond to their message naturally."
                )
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Someone sent: '{message}'. Respond appropriately."}
                ]
                
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    max_tokens=80,
                    temperature=0.8,
                    presence_penalty=0.6,
                    frequency_penalty=0.3
                )
                
                reply = response.choices[0].message.content.strip()
                logger.info(f"💬 Normal response to {chat_name}: {reply[:50]}...")
                return reply
                
        except Exception as e:
            logger.error(f"❌ AI response generation failed: {e}")
            # Fallback based on contact type
            if self.is_new_contact(chat_name) and not self.has_busy_message_been_sent(chat_name):
                self.mark_busy_message_sent(chat_name)
                self.mark_contact_as_known(chat_name)
                return "Hi, Akash is busy."
            else:
                self.mark_contact_as_known(chat_name)
                return "I'm here to help! What do you need? 😊"

    def send_message(self, text):
        """Send message with enhanced reliability"""
        try:
            # Find input box
            input_box = None
            for selector in self.MESSAGE_INPUT_SELECTORS:
                try:
                    elem = self.driver.find_element(By.XPATH, selector)
                    if elem.is_displayed():
                        input_box = elem
                        break
                except:
                    continue
            
            if not input_box:
                logger.error("❌ Could not find message input")
                return False
            
            # Focus on input
            ActionChains(self.driver).move_to_element(input_box).click().perform()
            time.sleep(0.5)
            
            # Clear existing content
            input_box.send_keys(Keys.CONTROL + "a")
            input_box.send_keys(Keys.DELETE)
            time.sleep(0.3)
            
            # Send via clipboard (best for special characters)
            pyperclip.copy(text)
            input_box.send_keys(Keys.CONTROL + "v")
            time.sleep(0.8)
            
            # Send message
            input_box.send_keys(Keys.ENTER)
            time.sleep(1)
            
            logger.info(f"✅ Sent: {text[:60]}{'...' if len(text) > 60 else ''}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return False

    def is_message_from_user(self, message_text):
        """Check if message is from user (not from AI)"""
        ai_signatures = [
            "Hey! Akash is busy right now, but I'm his AI assistant",
            "I'm Akash's AI assistant",
            "Hi! Akash is busy right now - I'm his AI assistant",
            "I'm here to help! What do you need?",
            "🤖",
        ]
        
        # Check if message contains AI signatures
        for signature in ai_signatures:
            if signature in message_text:
                return False
                
        # Check length - AI messages tend to be longer
        if len(message_text) > 120:
            return False
            
        return True

    def create_message_id(self, message, chat_name):
        """Create unique ID for message with timestamp grouping"""
        # Group messages by minute to avoid processing rapid duplicates
        timestamp_group = int(time.time()) // 60  # Group by minute
        return hashlib.md5(f"{chat_name}::{message[:50]}::{timestamp_group}".encode()).hexdigest()[:12]

    def leave_current_chat(self):
        """Leave current chat and go back to main WhatsApp interface"""
        try:
            # Method 1: Press Escape key to go back
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
            logger.debug("📤 Left chat using Escape key")
            return True
        except:
            try:
                # Method 2: Click on WhatsApp logo/header to go to main view
                whatsapp_header = self.driver.find_element(By.XPATH, '//header[@data-testid="chatlist-header"]')
                whatsapp_header.click()
                time.sleep(1)
                logger.debug("📤 Left chat by clicking header")
                return True
            except:
                try:
                    # Method 3: Click on chat list area
                    chat_list = self.driver.find_element(By.XPATH, '//div[@id="pane-side"]')
                    ActionChains(self.driver).move_to_element(chat_list).click().perform()
                    time.sleep(1)
                    logger.debug("📤 Left chat by clicking chat list")
                    return True
                except:
                    logger.debug("⚠️ Could not leave chat - continuing anyway")
                    return False

    def is_message_from_user(self, message_text):
        """Check if message is from user (not from AI)"""
        ai_signatures = [
            "Hey! Akash is busy right now, but I'm his AI assistant",
            "I'm Akash's AI assistant",
            "Hi! Akash is busy right now - I'm his AI assistant",
            "I'm here to help! What do you need?",
            "🤖",
        ]
        
        # Check if message contains AI signatures
        for signature in ai_signatures:
            if signature in message_text:
                return False
                
        # Check length - AI messages tend to be longer
        if len(message_text) > 120:
            return False
            
        return True

    def main_monitoring_loop(self):
        """Simple monitoring loop - reply and leave chat immediately"""
        logger.info("🤖 AI Agent is now monitoring for messages!")
        logger.info("💬 Send a message to any chat to test automatic replies")
        
        self.running = True
        error_count = 0
        
        while self.running:
            try:
                start_time = time.time()
                
                # Scan for unread chats (with built-in cooldown)
                unread_chats = self.scan_for_unread_chats()
                
                if unread_chats:
                    # Process only the first unread chat
                    chat_element, chat_name, chat_id = unread_chats[0]
                    
                    logger.info(f"📱 Processing new unread chat: {chat_name}")
                    
                    try:
                        # Click on the chat
                        if not self.click_chat_element(chat_element):
                            logger.warning(f"⚠️ Could not click chat: {chat_name}")
                            continue
                        
                        # Wait for chat to load
                        time.sleep(self.STABILITY_DELAY)
                        
                        # Verify we're in the right chat
                        actual_chat_name = self.get_current_chat_name()
                        
                        # Get latest message
                        latest_message = self.get_latest_incoming_message()
                        
                        if latest_message and len(latest_message.strip()) > 0:
                            # Additional check to ensure it's from user
                            if not self.is_message_from_user(latest_message):
                                logger.debug(f"🤖 Skipping AI's own message: {latest_message[:30]}...")
                                # Leave chat even if skipping message
                                self.leave_current_chat()
                                continue
                            
                            # Create unique message identifier
                            message_id = self.create_message_id(latest_message, actual_chat_name)
                            
                            # Check if already processed
                            if message_id in self.processed_messages:
                                logger.debug(f"🔄 Message already processed: {message_id}")
                                # Leave chat even if already processed
                                self.leave_current_chat()
                                continue
                            
                            logger.info(f"📩 New USER message from {actual_chat_name}: {latest_message[:50]}...")
                            
                            # Smart contact detection and response
                            ai_reply = self.generate_ai_response(latest_message, actual_chat_name)
                            
                            # Send reply
                            if self.send_message(ai_reply):
                                # Mark as processed
                                self.processed_messages.add(message_id)
                                self.chat_cooldowns[actual_chat_name] = time.time()
                                
                                logger.info(f"✅ Successfully replied to {actual_chat_name}")
                                logger.info(f"💬 Reply sent: {ai_reply}")
                                error_count = 0
                                
                                # IMPORTANT: Leave chat immediately after replying
                                time.sleep(1)  # Brief pause to ensure message is sent
                                self.leave_current_chat()
                                logger.info(f"📤 Left {actual_chat_name} chat - ready for new messages")
                                
                                # Short wait before next scan
                                time.sleep(2)
                            else:
                                logger.error(f"❌ Failed to send reply to {actual_chat_name}")
                                # Leave chat even if send failed
                                self.leave_current_chat()
                        else:
                            logger.debug(f"📭 No valid user message found in {actual_chat_name}")
                            # Leave chat if no valid message
                            self.leave_current_chat()
                                
                    except Exception as e:
                        logger.error(f"❌ Error processing chat {chat_name}: {e}")
                        # Leave chat on any error
                        try:
                            self.leave_current_chat()
                        except:
                            pass
                        continue
                else:
                    logger.debug("✅ No unread chats found")
                
                # Cleanup old data periodically
                if len(self.processed_messages) > 100:
                    old_messages = list(self.processed_messages)[:50]
                    for old_msg in old_messages:
                        self.processed_messages.discard(old_msg)
                
                # Clean old cooldowns
                current_time = time.time()
                expired_cooldowns = [
                    chat for chat, timestamp in self.chat_cooldowns.items()
                    if current_time - timestamp > self.MESSAGE_COOLDOWN * 2
                ]
                for chat in expired_cooldowns:
                    del self.chat_cooldowns[chat]
                
                # Dynamic sleep
                elapsed = time.time() - start_time
                sleep_time = max(1.0, self.CHECK_INTERVAL - elapsed)
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                logger.info("🛑 Stopping agent...")
                break
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Loop error #{error_count}: {e}")
                
                # Try to go back to main interface on error
                try:
                    self.leave_current_chat()
                except:
                    pass
                
                if error_count > 5:
                    logger.warning("⚠️ Multiple errors, taking a longer break...")
                    time.sleep(30)
                    error_count = 0
                else:
                    time.sleep(10)

    def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up...")
        self.running = False
        try:
            if self.driver:
                self.driver.quit()
            logger.info("✅ Cleanup completed")
        except:
            pass


def main():
    """Main function"""
    logger.info("🚀 Starting WhatsApp AI Agent...")
    
    # Check environment
    if not os.path.exists('.env'):
        logger.error("❌ .env file not found!")
        logger.error("Create a .env file with:")
        logger.error("OPENAI_API_KEY=your_api_key_here")
        logger.error("CHROME_DRIVER_PATH=C:\\chromedriver-win64\\chromedriver.exe")
        return False
    
    agent = WhatsAppAgent()
    
    try:
        # Setup Chrome
        if not agent.setup_chrome():
            return False
            
        # Setup WhatsApp
        if not agent.wait_for_whatsapp():
            return False
            
        # Start monitoring
        agent.main_monitoring_loop()
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        agent.cleanup()
    
    return True


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Program crashed: {e}")
    finally:
        logger.info("👋 Program ended")