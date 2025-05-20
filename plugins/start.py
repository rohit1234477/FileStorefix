# Don't Remove Credit @CodeFlix_Bots, @clutch008
# Ask Doubt on telegram @CodeflixSupport
#
# Copyright (C) 2025 by Codeflix-Bots@Github, < https://github.com/Codeflix-Bots >.
#
# This file is part of < https://github.com/Codeflix-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/Codeflix-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatInviteLink, ChatPrivileges
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant
from bot import Bot
from config import *
from helper_func import *
from database.database import *

BAN_SUPPORT = f"{BAN_SUPPORT}"

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id

    # Check if user is banned
    banned_users = await db.get_ban_users()
    if user_id in banned_users:
        return await message.reply_text(
            "<b>⛔️ You are Bᴀɴɴᴇᴅ from using this bot.</b>\n\n"
            "<i>Contact support if you think this is a mistake.</i>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Contact Support", url=BAN_SUPPORT)]]
            )
        )

    # ✅ Check Force Subscription
    if not await is_subscribed(client, user_id):
        return await not_joined(client, message)

    # File auto-delete time in seconds
    FILE_AUTO_DELETE = await db.get_del_timer() or 600  # Default to 10 minutes (600 seconds)

    # Add user if not already present
    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except:
            pass

    # Handle normal message flow
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except IndexError:
            return

        string = await decode(base64_string)
        argument = string.split("-")

        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                print(f"Error decoding IDs: {e}")
                return

        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                print(f"Error decoding ID: {e}")
                return

        temp_msg = await message.reply("<b>Please wait...</b>")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("Something went wrong! Please try again or contact support.")
            print(f"Error getting messages: {e}")
            return
        finally:
            await temp_msg.delete()

        codeflix_msgs = []
        sent_ids = set()  # Track sent message IDs to prevent duplicates
        for msg in messages:
            # Skip if message ID was already processed
            if msg.id in sent_ids:
                print(f"Skipping duplicate message ID {msg.id}")
                continue

            # Log message details for debugging
            caption_content = msg.caption.html if msg.caption else ""
            text_content = msg.text.html if msg.text else ""
            filename = msg.document.file_name if msg.document else msg.video.file_name if msg.video else ""
            has_sticker = bool(msg.sticker)
            print(f"Processing message ID {msg.id}: Caption={caption_content}, Text={text_content}, Filename={filename}, Sticker={has_sticker}, ReplyTo={msg.reply_to_message_id}")

            try:
                # Construct caption for videos/documents
                if msg.video or msg.document:
                    description = caption_content or filename or "<b>Video from @Anime_Telugu_English_VS</b>"
                    caption = f"{description}\n{CUSTOM_CAPTION}"
                else:
                    caption = caption_content or text_content  # Use original caption/text for non-media

                # Copy the main message based on content type
                if msg.video or msg.document:
                    copied_msg = await msg.copy(
                        chat_id=message.from_user.id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=msg.reply_markup if DISABLE_CHANNEL_BUTTON else None,
                        protect_content=PROTECT_CONTENT
                    )
                    codeflix_msgs.append(copied_msg)
                    sent_ids.add(msg.id)
                    print(f"Copied main message ID {msg.id} with caption: {caption}")
                elif msg.sticker:
                    copied_msg = await client.send_sticker(
                        chat_id=message.from_user.id,
                        sticker=msg.sticker.file_id
                    )
                    codeflix_msgs.append(copied_msg)
                    sent_ids.add(msg.id)
                    print(f"Copied sticker message ID {msg.id}")
                elif msg.text or caption_content:
                    copied_msg = await client.send_message(
                        chat_id=message.from_user.id,
                        text=caption,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    codeflix_msgs.append(copied_msg)
                    sent_ids.add(msg.id)
                    print(f"Copied text message ID {msg.id}: {caption}")
                else:
                    print(f"Skipping message ID {msg.id}: No valid content to copy")
                    continue

                # Check for reply message (additional description)
                if msg.reply_to_message_id and msg.reply_to_message_id not in sent_ids:
                    reply_msg = await client.get_messages(client.db_channel.id, msg.reply_to_message_id)
                    if reply_msg:
                        reply_caption = reply_msg.caption.html if reply_msg.caption else reply_msg.text.html if reply_msg.text else ""
                        if reply_msg.video or reply_msg.document:
                            copied_reply = await reply_msg.copy(
                                chat_id=message.from_user.id,
                                caption=reply_caption,
                                parse_mode=ParseMode.HTML,
                                reply_markup=reply_msg.reply_markup if DISABLE_CHANNEL_BUTTON else None,
                                protect_content=PROTECT_CONTENT
                            )
                            codeflix_msgs.append(copied_reply)
                            sent_ids.add(reply_msg.id)
                            print(f"Copied additional description (reply message ID {msg.reply_to_message_id}) for main message ID {msg.id}: {reply_caption}")
                        elif reply_msg.sticker:
                            copied_reply = await client.send_sticker(
                                chat_id=message.from_user.id,
                                sticker=reply_msg.sticker.file_id
                            )
                            codeflix_msgs.append(copied_reply)
                            sent_ids.add(reply_msg.id)
                            print(f"Copied sticker reply message ID {msg.reply_to_message_id} for main message ID {msg.id}")
                        elif reply_msg.text or reply_caption:
                            copied_reply = await client.send_message(
                                chat_id=message.from_user.id,
                                text=reply_caption,
                                parse_mode=ParseMode.HTML,
                                disable_web_page_preview=True
                            )
                            codeflix_msgs.append(copied_reply)
                            sent_ids.add(reply_msg.id)
                            print(f"Copied text reply message ID {msg.reply_to_message_id} for main message ID {msg.id}: {reply_caption}")
                    else:
                        print(f"Additional description (reply message ID {msg.reply_to_message_id}) not found for main message ID {msg.id}")

                # Add delay to avoid rate limits
                await asyncio.sleep(0.5)

            except FloodWait as e:
                await asyncio.sleep(e.x)
                if msg.id not in sent_ids:
                    if msg.video or msg.document:
                        copied_msg = await msg.copy(
                            chat_id=message.from_user.id,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            reply_markup=msg.reply_markup if DISABLE_CHANNEL_BUTTON else None,
                            protect_content=PROTECT_CONTENT
                        )
                        codeflix_msgs.append(copied_msg)
                        sent_ids.add(msg.id)
                        print(f"Copied main message ID {msg.id} with caption after FloodWait: {caption}")
                    elif msg.sticker:
                        copied_msg = await client.send_sticker(
                            chat_id=message.from_user.id,
                            sticker=msg.sticker.file_id
                        )
                        codeflix_msgs.append(copied_msg)
                        sent_ids.add(msg.id)
                        print(f"Copied sticker message ID {msg.id} after FloodWait")
                    elif msg.text or caption_content:
                        copied_msg = await client.send_message(
                            chat_id=message.from_user.id,
                            text=caption,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                        codeflix_msgs.append(copied_msg)
                        sent_ids.add(msg.id)
                        print(f"Copied text message ID {msg.id} after FloodWait: {caption}")
                    if msg.reply_to_message_id and msg.reply_to_message_id not in sent_ids:
                        reply_msg = await client.get_messages(client.db_channel.id, msg.reply_to_message_id)
                        if reply_msg:
                            reply_caption = reply_msg.caption.html if reply_msg.caption else reply_msg.text.html if reply_msg.text else ""
                            if reply_msg.video or reply_msg.document:
                                copied_reply = await reply_msg.copy(
                                    chat_id=message.from_user.id,
                                    caption=reply_caption,
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=reply_msg.reply_markup if DISABLE_CHANNEL_BUTTON else None,
                                    protect_content=PROTECT_CONTENT
                                )
                                codeflix_msgs.append(copied_reply)
                                sent_ids.add(reply_msg.id)
                                print(f"Copied additional description (reply message ID {msg.reply_to_message_id}) for main message ID {msg.id} after FloodWait: {reply_caption}")
                            elif reply_msg.sticker:
                                copied_reply = await client.send_sticker(
                                    chat_id=message.from_user.id,
                                    sticker=reply_msg.sticker.file_id
                                )
                                codeflix_msgs.append(copied_reply)
                                sent_ids.add(reply_msg.id)
                                print(f"Copied sticker reply message ID {msg.reply_to_message_id} for main message ID {msg.id} after FloodWait")
                            elif reply_msg.text or reply_caption:
                                copied_reply = await client.send_message(
                                    chat_id=message.from_user.id,
                                    text=reply_caption,
                                    parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True
                                )
                                codeflix_msgs.append(copied_reply)
                                sent_ids.add(reply_msg.id)
                                print(f"Copied text reply message ID {msg.reply_to_message_id} for main message ID {msg.id} after FloodWait: {reply_caption}")
                        else:
                            print(f"Additional description (reply message ID {msg.reply_to_message_id}) not found for main message ID {msg.id} after FloodWait")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Failed to copy message ID {msg.id} or its description: {e}")
                await message.reply_text(f"⚠️ Failed to send message ID {msg.id}. Please try again or contact support.")
                continue

        if FILE_AUTO_DELETE > 0 and codeflix_msgs:  # Only send notification if messages were copied
            try:
                notification_msg = await message.reply(
                    f"<b>Tʜɪs Fɪʟᴇ ᴡɪʟʟ ʙᴇ Dᴇʟᴇᴛᴇᴅ ɪɴ {get_exp_time(FILE_AUTO_DELETE)}. Pʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ғᴏʀᴡᴀʀᴅ ɪᴛ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇғᴏʀᴇ ɪᴛ ɢᴇᴛs Dᴇʟᴇᴛᴇᴅ.</b>",
                    quote=True
                )

                await asyncio.sleep(FILE_AUTO_DELETE)

                for snt_msg in codeflix_msgs:
                    if snt_msg:
                        try:
                            await snt_msg.delete()
                            print(f"Deleted message ID {snt_msg.id}")
                        except Exception as e:
                            print(f"Error deleting message {snt_msg.id}: {e}")

                try:
                    reload_url = (
                        f"https://t.me/{client.username}?start={message.command[1]}"
                        if message.command and len(message.command) > 1
                        else None
                    )
                    keyboard = InlineKeyboardMarkup(
                        [[InlineKeyboardButton("ɢᴇᴛ ғɪʟᴇ ᴀɢᴀɪɴ!", url=reload_url)]]
                    ) if reload_url else None

                    await notification_msg.edit(
                        "<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜀ɪʟᴇ 👇</b>",
                        reply_markup=keyboard
                    )
                    print("Updated auto-delete notification with 'Get File Again' button")
                except Exception as e:
                    print(f"Error updating notification with 'Get File Again' button: {e}")
            except Exception as e:
                print(f"Error sending auto-delete notification: {e}")
                await message.reply_text("⚠️ Failed to send auto-delete notification. Files may still be deleted.")
    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• ᴍᴏʀᴇ ᴄʜᴀɴɴᴇʟs •", url="https://t.me/koianimes")],
                [
                    InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="about"),
                    InlineKeyboardButton('ʜᴇʟᴘ •', callback_data="help")
                ]
            ]
        )
        reply_kwargs = {
            "photo": START_PIC,
            "caption": START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            "reply_markup": reply_markup
        }
        if hasattr(Message, "reply_photo") and "message_effect_id" in Message.reply_photo.__code__.co_varnames:
            reply_kwargs["message_effect_id"] = 5104841245755180586

        await message.reply_photo(**reply_kwargs)
        return

chat_data_cache = {}

async def not_joined(client: Client, message: Message):
    temp = await message.reply("<b><i>ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>")

    user_id = message.from_user.id
    buttons = []
    count = 0

    try:
        all_channels = await db.show_channels()
        for total, chat_id in enumerate(all_channels, start=1):
            mode = await db.get_channel_mode(chat_id)

            await message.reply_chat_action(ChatAction.TYPING)

            if not await is_sub(client, user_id, chat_id):
                try:
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]
                    else:
                        data = await client.get_chat(chat_id)
                        chat_data_cache[chat_id] = data

                    name = data.title

                    if mode == "on" and not data.username:
                        invite = await client.create_chat_invite_link(
                            chat_id=chat_id,
                            creates_join_request=True,
                            expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                        )
                        link = invite.invite_link
                    else:
                        if data.username:
                            link = f"https://t.me/{data.username}"
                        else:
                            invite = await client.create_chat_invite_link(
                                chat_id=chat_id,
                                expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                            )
                            link = invite.invite_link

                    buttons.append([InlineKeyboardButton(text=name, url=link)])
                    count += 1
                    await temp.edit(f"<b>{'! ' * count}</b>")

                except Exception as e:
                    print(f"Error with chat {chat_id}: {e}")
                    return await temp.edit(
                        f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @clutch008</i></b>\n"
                        f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
                    )

        try:
            buttons.append([
                InlineKeyboardButton(
                    text='♻️ Tʀʏ Aɢᴀɪɴ',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ])
        except IndexError:
            pass

        await message.reply_photo(
            photo=FORCE_PIC,
            caption=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        print(f"Final Error: {e}")
        await temp.edit(
            f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @clutch008</i></b>\n"
            f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
        )

@Bot.on_message(filters.command('commands') & filters.private & admin)
async def bcmd(bot: Bot, message: Message):
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data="close")]])
    await message.reply(text=CMD_TXT, reply_markup=reply_markup, quote=True)
