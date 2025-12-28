"""
ITXploreBot - Professional Telegram Broadcast Bot
Built with aiogram 3.x
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Set

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ChatMemberUpdated
from aiogram.enums import ChatType, ChatMemberStatus


# CONFIGURATION

BOT_TOKEN = "8553857292:AAH-zknZ7DnyzaB11mIsvrnePPkXyjmD18s"
ADMIN_GROUP_ID = -1003253050792 

# You can also add individual admin user IDs for DM commands
ADMIN_USER_IDS = [6680395370]  # Replace with your Telegram user ID

DATABASE_FILE = "database.json"

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class Database:
    """Manages local JSON database for storing chat IDs"""
    
    def __init__(self, filepath: str = DATABASE_FILE):
        self.filepath = Path(filepath)
        self.data: Dict[str, Set[int]] = {
            "users": set(),
            "groups": set(),
            "channels": set()
        }
        self.load()
    
    def load(self):
        """Load data from JSON file"""
        if self.filepath.exists():
            try:
                with open(self.filepath, 'r') as f:
                    loaded = json.load(f)
                    # Convert lists back to sets
                    self.data = {
                        key: set(value) for key, value in loaded.items()
                    }
                logger.info(f"Database loaded: {self.get_stats()}")
            except Exception as e:
                logger.error(f"Error loading database: {e}")
        else:
            logger.info("No existing database found. Creating new one.")
            self.save()
    
    def save(self):
        """Save data to JSON file"""
        try:
            # Convert sets to lists for JSON serialization
            serializable = {
                key: list(value) for key, value in self.data.items()
            }
            with open(self.filepath, 'w') as f:
                json.dump(serializable, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving database: {e}")
    
    def add_user(self, user_id: int):
        """Add user ID"""
        self.data["users"].add(user_id)
        self.save()
        logger.info(f"Added user: {user_id}")
    
    def add_group(self, group_id: int):
        """Add group ID"""
        self.data["groups"].add(group_id)
        self.save()
        logger.info(f"Added group: {group_id}")
    
    def add_channel(self, channel_id: int):
        """Add channel ID"""
        self.data["channels"].add(channel_id)
        self.save()
        logger.info(f"Added channel: {channel_id}")
    
    def remove_chat(self, chat_id: int):
        """Remove a chat ID from all categories"""
        removed = False
        for category in self.data.values():
            if chat_id in category:
                category.remove(chat_id)
                removed = True
        if removed:
            self.save()
            logger.info(f"Removed chat: {chat_id}")
        return removed
    
    def get_all_ids(self) -> List[int]:
        """Get all chat IDs"""
        all_ids = []
        for ids in self.data.values():
            all_ids.extend(ids)
        return all_ids
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics"""
        return {
            "users": len(self.data["users"]),
            "groups": len(self.data["groups"]),
            "channels": len(self.data["channels"]),
            "total": sum(len(v) for v in self.data.values())
        }

# ============================================================================
# BOT INITIALIZATION
# ============================================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
db = Database()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_admin(message: Message) -> bool:
    """Check if user is admin"""
    # Check if message is from admin group
    if message.chat.id == ADMIN_GROUP_ID:
        return True
    # Check if user is in admin list (for DM commands)
    if message.from_user and message.from_user.id in ADMIN_USER_IDS:
        return True
    return False

async def check_chat_access(bot: Bot, chat_id: int) -> bool:
    """Check if bot still has access to a chat"""
    try:
        await bot.get_chat(chat_id)
        return True
    except Exception as e:
        logger.warning(f"Lost access to {chat_id}: {e}")
        return False

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command in DMs"""
    if message.chat.type == ChatType.PRIVATE:
        db.add_user(message.from_user.id)
        await message.answer(
            "👋 <b>Welcome to ITXploreBot!</b>\n\n"
            "You've been registered for broadcasts.\n\n"
            "📊 <b>Our Channels:</b>\n"
            "• Data Science: @DataXplore\n"
            "• AI Efficiency: @PromptXplore\n\n"
            "Stay tuned for updates! 🚀",
            parse_mode="HTML"
        )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Show help menu for admins"""
    if not is_admin(message):
        return
    
    help_text = """
📚 <b>ITXploreBot - Admin Commands</b>

<b>Broadcasting:</b>
/broadcast - Reply to any message to broadcast it
  ↳ Supports: Text, Photos, Videos, Documents, Polls

<b>Statistics:</b>
/stat - View current reach statistics

<b>Maintenance:</b>
/check [ID] - Check if bot has access to specific chat
/clean - Remove all inactive chats from database

<b>Information:</b>
/about - Show bot information
/help - Show this menu

<b>💡 Tips:</b>
• Always use /broadcast as a reply
• Run /clean weekly to maintain accurate stats
• Use /check before major broadcasts
"""
    await message.answer(help_text, parse_mode="HTML")

@router.message(Command("about"))
async def cmd_about(message: Message):
    """Show about information"""
    about_text = """
🤖 <b>ITXploreBot</b>

<i>Your Professional Broadcast Assistant</i>

📊 <b>Data Science:</b> @DataXplore
🤖 <b>AI Efficiency:</b> @PromptXplore
💻 <b>Developer:</b> @Xplorium

<b>Features:</b>
✅ Multi-format broadcasting
✅ Auto-registration
✅ Real-time statistics
✅ Smart error handling

Built with ❤️ using aiogram 3.x
"""
    await message.answer(about_text, parse_mode="HTML")

@router.message(Command("stat"))
async def cmd_stat(message: Message):
    """Show statistics (Admin only)"""
    if not is_admin(message):
        await message.answer("⛔ This command is for admins only.")
        return
    
    stats = db.get_stats()
    stat_text = f"""
📊 <b>ITXploreBot Statistics</b>

👤 <b>Total Users:</b> {stats['users']}
👥 <b>Total Groups:</b> {stats['groups']}
📢 <b>Total Channels:</b> {stats['channels']}

🌍 <b>Total Reach:</b> {stats['total']}
"""
    await message.answer(stat_text, parse_mode="HTML")

@router.message(Command("check"))
async def cmd_check(message: Message):
    """Check if bot has access to specific chat"""
    if not is_admin(message):
        await message.answer("⛔ This command is for admins only.")
        return
    
    # Extract chat ID from command
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("❌ Usage: /check [chat_id]\nExample: /check -1001234567890")
            return
        
        chat_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Invalid chat ID. Must be a number.")
        return
    
    status_msg = await message.answer(f"🔍 Checking access to {chat_id}...")
    
    if await check_chat_access(bot, chat_id):
        await status_msg.edit_text(f"✅ <b>Alive</b>\n\nBot has access to {chat_id}", parse_mode="HTML")
    else:
        db.remove_chat(chat_id)
        await status_msg.edit_text(
            f"❌ <b>Dead</b>\n\nBot lost access to {chat_id}\n"
            f"Removed from database.",
            parse_mode="HTML"
        )

@router.message(Command("clean"))
async def cmd_clean(message: Message):
    """Clean inactive chats from database"""
    if not is_admin(message):
        await message.answer("⛔ This command is for admins only.")
        return
    
    status_msg = await message.answer("🧹 Starting cleanup process...")
    
    all_ids = db.get_all_ids()
    removed = 0
    
    for chat_id in all_ids:
        if not await check_chat_access(bot, chat_id):
            db.remove_chat(chat_id)
            removed += 1
        await asyncio.sleep(0.05)  # Rate limit protection
    
    await status_msg.edit_text(
        f"✅ <b>Cleanup Complete</b>\n\n"
        f"📊 Checked: {len(all_ids)}\n"
        f"🗑️ Removed: {removed}\n"
        f"✨ Active: {len(all_ids) - removed}",
        parse_mode="HTML"
    )

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """Broadcast a message to all users/groups/channels"""
    # Check if admin
    if not is_admin(message):
        await message.answer("⛔ This command can only be used in the Admin HQ group.")
        return
    
    # Check if replying to a message
    if not message.reply_to_message:
        await message.answer("❌ Please reply to a message with /broadcast to broadcast it.")
        return
    
    target_message = message.reply_to_message
    all_ids = db.get_all_ids()
    
    if not all_ids:
        await message.answer("❌ No recipients in database!")
        return
    
    # Start broadcasting
    status_msg = await message.answer(
        f"📡 <b>Broadcasting started...</b>\n\n"
        f"Total recipients: {len(all_ids)}",
        parse_mode="HTML"
    )
    
    success = 0
    failed = 0
    failed_ids = []
    
    for chat_id in all_ids:
        try:
            await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=target_message.chat.id,
                message_id=target_message.message_id
            )
            success += 1
            await asyncio.sleep(0.05)  # Anti-spam delay
        except Exception as e:
            failed += 1
            failed_ids.append(chat_id)
            logger.warning(f"Failed to send to {chat_id}: {e}")
            
            # If forbidden error, remove from database
            if "Forbidden" in str(e) or "blocked" in str(e).lower():
                db.remove_chat(chat_id)
    
    # Final report
    report = (
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"📊 <b>Results:</b>\n"
        f"✅ Successful: {success}\n"
        f"❌ Failed: {failed}\n"
        f"📈 Success Rate: {(success/len(all_ids)*100):.1f}%"
    )
    
    if failed_ids:
        report += f"\n\n🗑️ Auto-removed {len([f for f in failed_ids if not await check_chat_access(bot, f)])} inactive chats"
    
    await status_msg.edit_text(report, parse_mode="HTML")

# ============================================================================
# MY_CHAT_MEMBER HANDLER (Auto-registration for groups/channels)
# ============================================================================

@router.my_chat_member()
async def on_chat_member_update(event: ChatMemberUpdated):
    """Handle bot being added to or removed from chats"""
    
    # Check if bot was added (became a member)
    if event.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
        chat = event.chat
        
        if chat.type == ChatType.GROUP or chat.type == ChatType.SUPERGROUP:
            db.add_group(chat.id)
            logger.info(f"Bot added to group: {chat.title} ({chat.id})")
            
            # Try to send a greeting (may fail if no permissions)
            try:
                await bot.send_message(
                    chat.id,
                    "👋 Thanks for adding me! I'll keep you updated with broadcasts.",
                    parse_mode="HTML"
                )
            except:
                pass
        
        elif chat.type == ChatType.CHANNEL:
            db.add_channel(chat.id)
            logger.info(f"Bot added to channel: {chat.title} ({chat.id})")
    
    # Check if bot was removed
    elif event.new_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
        db.remove_chat(event.chat.id)
        logger.info(f"Bot removed from: {event.chat.title} ({event.chat.id})")

# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Start the bot"""
    dp.include_router(router)
    
    logger.info("ITXploreBot starting...")
    logger.info(f"Admin Group ID: {ADMIN_GROUP_ID}")
    logger.info(f"Database: {db.get_stats()}")
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())