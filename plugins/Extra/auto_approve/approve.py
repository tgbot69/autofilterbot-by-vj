import os, string, logging, random, asyncio, time, datetime, re, sys, json, base64
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import *
from database.ia_filterdb import get_file_details, unpack_new_file_id, get_bad_files
from database.users_chats_db import db, delete_all_referal_users, get_referal_users_count, get_referal_all_users, referal_add_user
from database.join_reqs import JoinReqs
from info import *
from utils import get_settings, pub_is_subscribed, get_size, is_subscribed, save_group_settings, temp, verify_user, check_token, check_verification, get_token, get_shortlink, get_tutorial, get_seconds
from database.connections_mdb import active_connection
from urllib.parse import quote_plus
from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size
logger = logging.getLogger(__name__)

BATCH_FILES = {}
join_db = JoinReqs

@Client.on_chat_join_request((filters.group | filters.channel))
async def auto_approve(client, message: ChatJoinRequest):
    if message.chat.id == AUTH_CHANNEL and join_db().isActive():
        if REQUEST_TO_JOIN_MODE == False:
            return 
        ap_user_id = message.from_user.id
        first_name = message.from_user.first_name
        username = message.from_user.username
        date = message.date
        await join_db().add_user(user_id=ap_user_id, first_name=first_name, username=username, date=date)
        if TRY_AGAIN_BTN == True:
            return 
        data = await db.get_msg_command(ap_user_id)
        
        if data.split("-", 1)[0] == "VJ":
            user_id = int(data.split("-", 1)[1])
            vj = await referal_add_user(user_id, message.from_user.id)
            if vj and PREMIUM_AND_REFERAL_MODE == True:
                await client.send_message(message.from_user.id, f"<b>You have joined using the referral link of user with ID {user_id}\n\nSend /start again to use the bot</b>")
                num_referrals = await get_referal_users_count(user_id)
                await client.send_message(chat_id = user_id, text = "<b>{} start the bot with your referral link\n\nTotal Referals - {}</b>".format(message.from_user.mention, num_referrals))
                if num_referrals == REFERAL_COUNT:
                    time = REFERAL_PREMEIUM_TIME       
                    seconds = await get_seconds(time)
                    if seconds > 0:
                        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
                        user_data = {"id": user_id, "expiry_time": expiry_time} 
                        await db.update_user(user_data)  # Use the update_user method to update or insert user data
                        await delete_all_referal_users(user_id)
                        await client.send_message(chat_id = user_id, text = "<b>You Have Successfully Completed Total Referal.\n\nYou Added In Premium For {}</b>".format(REFERAL_PREMEIUM_TIME))
                        return 
            else:
                if PREMIUM_AND_REFERAL_MODE == True:
                    buttons = [[
                        InlineKeyboardButton('⤬ Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ ⤬', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
                    ],[
                      #  InlineKeyboardButton('Eᴀʀɴ Mᴏɴᴇʏ 💸', callback_data="shortlink_info"),
                        InlineKeyboardButton('⌬ Mᴏᴠɪᴇ Gʀᴏᴜᴘ', url=GRP_LNK)
                    ],[
                        InlineKeyboardButton('〄 Hᴇʟᴘ', callback_data='help'),
                      #  InlineKeyboardButton('⍟ Aʙᴏᴜᴛ', callback_data='about')
                    ],[
                        InlineKeyboardButton('🔻 ɢᴇᴛ ғʀᴇᴇ/ᴘᴀɪᴅ sᴜʙsᴄʀɪᴘᴛɪᴏɴ 🔻', callback_data='subscription')
                    ],[
                        InlineKeyboardButton('✇ Jᴏɪɴ Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ ✇', url=CHNL_LNK)
                    ]]
                else:
                    buttons = [[
                        InlineKeyboardButton('⤬ Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ ⤬', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
                    ],[
                      #  InlineKeyboardButton('Eᴀʀɴ Mᴏɴᴇʏ 💸', callback_data="shortlink_info"),
                        InlineKeyboardButton('⌬ Mᴏᴠɪᴇ Gʀᴏᴜᴘ', url=GRP_LNK)
                    ],[
                        InlineKeyboardButton('〄 Hᴇʟᴘ', callback_data='help'),
                      #  InlineKeyboardButton('⍟ Aʙᴏᴜᴛ', callback_data='about')
                    ],[
                        InlineKeyboardButton('✇ Jᴏɪɴ Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ ✇', url=CHNL_LNK)
                    ]]
                reply_markup = InlineKeyboardMarkup(buttons)
                m=await client.send_sticker(chat_id = message.from_user.id, sticker = "CAACAgUAAxkBAAEKVaxlCWGs1Ri6ti45xliLiUeweCnu4AACBAADwSQxMYnlHW4Ls8gQMAQ") 
                await asyncio.sleep(1)
                await m.delete()
                await client.send_photo(
                    chat_id=message.from_user.id,
                    photo=random.choice(PICS),
                    caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
                    reply_markup=reply_markup,
                    parse_mode=enums.ParseMode.HTML
                )
                return 
        try:
            pre, file_id = data.split('_', 1)
        except:
            file_id = data
            pre = ""
        if data.split("-", 1)[0] == "BATCH":
            sts = await client.send_message(message.from_user.id, "<b>Please wait...</b>")
            file_id = data.split("-", 1)[1]
            msgs = BATCH_FILES.get(file_id)
            if not msgs:
                file = await client.download_media(file_id)
                try: 
                    with open(file) as file_data:
                        msgs=json.loads(file_data.read())
                except:
                    await sts.edit("FAILED")
                    return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
                os.remove(file)
                BATCH_FILES[file_id] = msgs

            filesarr = []
            for msg in msgs:
                title = msg.get("title")
                size=get_size(int(msg.get("size", 0)))
                f_caption=msg.get("caption", "")
                if BATCH_FILE_CAPTION:
                    try:
                        f_caption=BATCH_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                    except Exception as e:
                        logger.exception(e)
                        f_caption=f_caption
                if f_caption is None:
                    f_caption = f"{title}"
                try:
                    if STREAM_MODE == True:
                        # Create the inline keyboard button with callback_data
                        user_id = message.from_user.id
                        username =  message.from_user.mention 

                        try:
                            log_msg = await client.send_cached_media(
                                chat_id=LOG_CHANNEL,
                                file_id=msg.get("file_id"),
                            )
                        except FloodWait as e:
                            k = await sts.reply(f"Waiting For {e.value} Seconds.")
                            await asyncio.sleep(e.value)
                            log_msg = await client.send_cached_media(
                                chat_id=LOG_CHANNEL,
                                file_id=msg.get("file_id"),
                            )
                            await k.delete()
                        fileName = {quote_plus(get_name(log_msg))}
                        stream = f"{URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                        download = f"{URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
 
                        await log_msg.reply_text(
                            text=f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id} \n•• ᴜꜱᴇʀɴᴀᴍᴇ : {username} \n\n•• ᖴᎥᒪᗴ Nᗩᗰᗴ : {fileName}",
                            quote=True,
                            disable_web_page_preview=True,
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Fast Download 🚀", url=download),  # we download Link
                                                                InlineKeyboardButton('🖥️ Watch online 🖥️', url=stream)]])  # web stream Link
                        )
                    if STREAM_MODE == True:
                        button = [[
                            InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
                            InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
                        ],[
                            InlineKeyboardButton('𝗕𝗢𝗧 𝗢𝗪𝗡𝗘𝗥', url=OWNER_LNK)
                        ],[
                            InlineKeyboardButton("🚀 Fast Download 🚀", url=download),
                            InlineKeyboardButton('🖥️ Watch online 🖥️', url=stream)
                        ],[
                            InlineKeyboardButton("• ᴡᴀᴛᴄʜ ɪɴ ᴡᴇʙ ᴀᴘᴘ •", web_app=WebAppInfo(url=stream))
                        ]]
                    else:
                        button = [[
                            InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
                            InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
                        ],[
                            InlineKeyboardButton('𝗕𝗢𝗧 𝗢𝗪𝗡𝗘𝗥', url=OWNER_LNK)
                        ]]
                    msg = await client.send_cached_media(
                        chat_id=message.from_user.id,
                        file_id=msg.get("file_id"),
                        caption=f_caption,
                        protect_content=msg.get('protect', False),
                        reply_markup=InlineKeyboardMarkup(button)
                    )
                    filesarr.append(msg)
                
                except FloodWait as e:
                    k = await sts.reply(f"Waiting For {e.value} Seconds.")
                    await asyncio.sleep(e.value)
                    msg = await client.send_cached_media(
                        chat_id=message.from_user.id,
                        file_id=msg.get("file_id"),
                        caption=f_caption,
                        protect_content=msg.get('protect', False),
                        reply_markup=InlineKeyboardMarkup(button)
                    )
                    filesarr.append(msg)
                    await k.delete()
                except Exception as e:
                    logger.warning(e)
                    continue
                await asyncio.sleep(1) 
            await sts.delete()
            k = await client.send_message(chat_id = message.from_user.id, text=f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis Movie Files/Videos will be deleted in <b><u>10 mins</u> 🫥 <i></b>(Due to Copyright Issues)</i>.\n\n<b><i>Please forward this ALL Files/Videos to your Saved Messages and Start Download there</i></b>")
            await asyncio.sleep(600)
            for x in filesarr:
                await x.delete()
            await k.edit_text("<b>Your All Files/Videos is successfully deleted!!!</b>")  
            return
        elif data.split("-", 1)[0] == "DSTORE":
            sts = await client.send_message(message.from_user.id, "<b>Please wait...</b>")
            b_string = data.split("-", 1)[1]
            decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("ascii")
            try:
                f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
            except:
                f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
                protect = "/pbatch" if PROTECT_CONTENT else "batch"
            diff = int(l_msg_id) - int(f_msg_id)
            filesarr = []
            async for msg in client.iter_messages(int(f_chat_id), int(l_msg_id), int(f_msg_id)):
                if msg.media:
                    media = getattr(msg, msg.media.value)
                    file_type = msg.media
                    file = getattr(msg, file_type.value)
                    size = get_size(int(file.file_size))
                    if BATCH_FILE_CAPTION:
                        try:
                            f_caption=BATCH_FILE_CAPTION.format(file_name=getattr(media, 'file_name', ''), file_size='' if size is None else size, file_caption=getattr(msg, 'caption', ''))
                        except Exception as e:
                            logger.exception(e)
                            f_caption = getattr(msg, 'caption', '')
                    else:
                        media = getattr(msg, msg.media.value)
                        file_name = getattr(media, 'file_name', '')
                        f_caption = getattr(msg, 'caption', file_name)
                    file_id = file.file_id
                    if STREAM_MODE == True:
                        # Create the inline keyboard button with callback_data
                        user_id = message.from_user.id
                        username =  message.from_user.mention 

                        try:
                            log_msg = await client.send_cached_media(
                                chat_id=LOG_CHANNEL,
                                file_id=file_id,
                            )
                        except FloodWait as e:
                            k = await sts.reply(f"Waiting For {e.value} Seconds.")
                            await asyncio.sleep(e.value)
                            log_msg = await client.send_cached_media(
                                chat_id=LOG_CHANNEL,
                                file_id=file_id,
                            )
                            await k.delete()
                        fileName = {quote_plus(get_name(log_msg))}
                        stream = f"{URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                        download = f"{URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
 
                        await log_msg.reply_text(
                            text=f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id} \n•• ᴜꜱᴇʀɴᴀᴍᴇ : {username} \n\n•• ᖴᎥᒪᗴ Nᗩᗰᗴ : {fileName}",
                            quote=True,
                            disable_web_page_preview=True,
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Fast Download 🚀", url=download),  # we download Link
                                                                InlineKeyboardButton('🖥️ Watch online 🖥️', url=stream)]])  # web stream Link
                        )
                    if STREAM_MODE == True:
                        button = [[
                            InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
                            InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
                        ],[
                            InlineKeyboardButton('𝗕𝗢𝗧 𝗢𝗪𝗡𝗘𝗥', url=OWNER_LNK)
                        ],[
                            InlineKeyboardButton("🚀 Fast Download 🚀", url=download),
                            InlineKeyboardButton('🖥️ Watch online 🖥️', url=stream)
                        ],[
                            InlineKeyboardButton("• ᴡᴀᴛᴄʜ ɪɴ ᴡᴇʙ ᴀᴘᴘ •", web_app=WebAppInfo(url=stream))
                        ]]
                    else:
                        button = [[
                            InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
                            InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
                        ],[
                            InlineKeyboardButton('𝗕𝗢𝗧 𝗢𝗪𝗡𝗘𝗥', url=OWNER_LNK)
                        ]]
                    try:
                        p = await msg.copy(message.from_user.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False, reply_markup=InlineKeyboardMarkup(button))
                        filesarr.append(p)
                    except FloodWait as e:
                        k = await sts.reply(f"Waiting For {e.value} Seconds.")
                        await asyncio.sleep(e.value)
                        p = await msg.copy(message.from_user.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False, reply_markup=InlineKeyboardMarkup(button))
                        filesarr.append(p)
                        await k.delete()
                    except Exception as e:
                        logger.exception(e)
                        continue
                elif msg.empty:
                    continue
                else:
                    try:
                        p = await msg.copy(message.from_user.id, protect_content=True if protect == "/pbatch" else False)
                        filesarr.append(p)
                    except FloodWait as e:
                        k = await sts.reply(f"Waiting For {e.value} Seconds.")
                        await asyncio.sleep(e.value)
                        p = await msg.copy(message.from_user.id, protect_content=True if protect == "/pbatch" else False)
                        filesarr.append(p)
                        await k.delete()
                    except Exception as e:
                        logger.exception(e)
                        continue
                await asyncio.sleep(1)
            await sts.delete()
            k = await client.send_message(chat_id = message.from_user.id, text=f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis Movie Files/Videos will be deleted in <b><u>10 mins</u> 🫥 <i></b>(Due to Copyright Issues)</i>.\n\n<b><i>Please forward this ALL Files/Videos to your Saved Messages and Start Download there</i></b>")
            await asyncio.sleep(600)
            for x in filesarr:
                await x.delete()
            await k.edit_text("<b>Your All Files/Videos is successfully deleted!!!</b>")
            return
        elif data.split("-", 1)[0] == "verify":
            userid = data.split("-", 2)[1]
            token = data.split("-", 3)[2]
            if str(message.from_user.id) != str(userid):
                return await client.send_message(
                    chat_id=message.from_user.id,
                    text="<b>Invalid link or Expired link !</b>",
                    protect_content=True
                )
            is_valid = await check_token(client, userid, token)
            if is_valid == True:
                await client.send_message(
                    chat_id=message.from_user.id,
                    text=f"<b>Hey {message.from_user.mention}, You are successfully verified !\nNow you have unlimited access for all movies till today midnight.</b>",
                    protect_content=True
                )
                await verify_user(client, userid, token)
            else:
                return await client.send_message(
                    chat_id=message.from_user.id,
                    text="<b>Invalid link or Expired link !</b>",
                    protect_content=True
                )
        if data.startswith("sendfiles"):
            chat_id = int("-" + file_id.split("-")[1])
            userid = message.from_user.id if message.from_user else None
            settings = await get_settings(chat_id)
            pre = 'allfilesp' if settings['file_secure'] else 'allfiles'
            g = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start={pre}_{file_id}")
            btn = [[
                InlineKeyboardButton('📂 Dᴏᴡɴʟᴏᴀᴅ Nᴏᴡ 📂', url=g)
            ]]
            if settings['tutorial']:
                btn.append([InlineKeyboardButton('⁉️ Hᴏᴡ Tᴏ Dᴏᴡɴʟᴏᴀᴅ ⁉️', url=await get_tutorial(chat_id))])
            k = await client.send_message(chat_id=message.from_user.id,text=f"<b>Get All Files in a Single Click!!!\n\n📂 ʟɪɴᴋ ➠ : {g}\n\n<i>Note: This message is deleted in 5 mins to avoid copyrights. Save the link to Somewhere else</i></b>", reply_markup=InlineKeyboardMarkup(button))
            await asyncio.sleep(300)
            await k.edit("<b>Your message is successfully deleted!!!</b>")
            return   
    
        elif data.startswith("short"):
            user = message.from_user.id
            chat_id = temp.SHORT.get(user)
            settings = await get_settings(chat_id)
            pre = 'filep' if settings['file_secure'] else 'file'
            files_ = await get_file_details(file_id)
            files = files_
            g = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start={pre}_{file_id}")
            btn = [[
                InlineKeyboardButton('📂 Dᴏᴡɴʟᴏᴀᴅ Nᴏᴡ 📂', url=g)
            ]]
            if settings['tutorial']:
                btn.append([InlineKeyboardButton('⁉️ Hᴏᴡ Tᴏ Dᴏᴡɴʟᴏᴀᴅ ⁉️', url=await get_tutorial(chat_id))])
            k = await client.send_message(chat_id=user,text=f"<b>📕Nᴀᴍᴇ ➠ : <code>{files['file_name']}</code> \n\n🔗Sɪᴢᴇ ➠ : {get_size(files['file_size'])}\n\n📂Fɪʟᴇ ʟɪɴᴋ ➠ : {g}\n\n<i>Note: This message is deleted in 20 mins to avoid copyrights. Save the link to Somewhere else</i></b>", reply_markup=InlineKeyboardMarkup(button))
            await asyncio.sleep(1200)
            await k.edit("<b>Your message is successfully deleted!!!</b>")
            return
        
        elif data.startswith("all"):
            files = temp.GETALL.get(file_id)
            if not files:
                return await client.send_message(chat_id=message.from_user.id, text='<b><i>No such file exist.</b></i>')
            filesarr = []
            for file in files:
                file_id = file["file_id"]
                files_ = await get_file_details(file_id)
                files1 = files_
                title = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files1["file_name"].split()))
                size=get_size(files1["file_size"])
                f_caption=files1["caption"]
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                    except Exception as e:
                        logger.exception(e)
                        f_caption=f_caption
                if f_caption is None:
                    f_caption = f"{' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files1['file_name'].split()))}"
                if not await db.has_premium_access(message.from_user.id):
                    if not await check_verification(client, message.from_user.id) and VERIFY == True:
                        btn = [[
                            InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start="))
                        ],[
                            InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)
                        ]]
                        await client.send_message(
                            chat_id=message.from_user.id,
                            text="<b>You are not verified !\nKindly verify to continue !</b>",
                            protect_content=True,
                            reply_markup=InlineKeyboardMarkup(btn)
                        )
                        return
                if STREAM_MODE == True:
                    button = [[
                        InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
                        InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
                    ],[
                        InlineKeyboardButton("𝗕𝗢𝗧 𝗢𝗪𝗡𝗘𝗥", url=OWNER_LNK)
                    ],[
                        InlineKeyboardButton('🚀 Fast Download / Watch Online🖥️', callback_data=f'generate_stream_link:{file_id}') #Don't change anything without contacting me @KingVJ01
                    ]]
                else:
                    button = [[
                        InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
                        InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
                    ],[
                        InlineKeyboardButton("𝗕𝗢𝗧 𝗢𝗪𝗡𝗘𝗥", url=OWNER_LNK)
                    ]]
                msg = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    protect_content=True if pre == 'filep' else False,
                    reply_markup=InlineKeyboardMarkup(button)
                )
                filesarr.append(msg)
            k = await client.send_message(chat_id = message.from_user.id, text=f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis Movie Files/Videos will be deleted in <b><u>10 mins</u> 🫥 <i></b>(Due to Copyright Issues)</i>.\n\n<b><i>Please forward this ALL Files/Videos to your Saved Messages and Start Download there</i></b>")
            await asyncio.sleep(600)
            for x in filesarr:
                await x.delete()
            await k.edit_text("<b>Your All Files/Videos is successfully deleted!!!</b>")
            return
        elif data.startswith("files"):
            user = message.from_user.id
            if temp.SHORT.get(user)==None:
                await client.send_message(chat_id=message.from_user.id, text="<b>Please Search Again in Group</b>")
            else:
                chat_id = temp.SHORT.get(user)
            settings = await get_settings(chat_id)
            pre = 'filep' if settings['file_secure'] else 'file'
            if settings['is_shortlink'] and not await db.has_premium_access(user):
                files_ = await get_file_details(file_id)
                files = files_
                g = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start={pre}_{file_id}")
                button = [[
                    InlineKeyboardButton('📂 Dᴏᴡɴʟᴏᴀᴅ Nᴏᴡ 📂', url=g)
                ]]
                if settings['tutorial']:
                    btn.append([InlineKeyboardButton('⁉️ Hᴏᴡ Tᴏ Dᴏᴡɴʟᴏᴀᴅ ⁉️', url=await get_tutorial(chat_id))])
                k = await client.send_message(chat_id=message.from_user.id,text=f"<b>📕Nᴀᴍᴇ ➠ : <code>{files['file_name']}</code> \n\n🔗Sɪᴢᴇ ➠ : {get_size(files['file_size'])}\n\n📂Fɪʟᴇ ʟɪɴᴋ ➠ : {g}\n\n<i>Note: This message is deleted in 20 mins to avoid copyrights. Save the link to Somewhere else</i></b>", reply_markup=InlineKeyboardMarkup(button))
                await asyncio.sleep(1200)
                await k.edit("<b>Your message is successfully deleted!!!</b>")
                return
        user = message.from_user.id
        files_ = await get_file_details(file_id)           
        if not files_:
            pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
            try:
                if not await db.has_premium_access(message.from_user.id):
                    if not await check_verification(client, message.from_user.id) and VERIFY == True:
                        btn = [[
                            InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start="))
                        ],[
                            InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)
                        ]]
                        await client.send_message(
                            chat_id=message.from_user.id,
                            text="<b>You are not verified !\nKindly verify to continue !</b>",
                            protect_content=True,
                            reply_markup=InlineKeyboardMarkup(btn)
                        )
                        return
                if STREAM_MODE == True:
                    button = [[
                        InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
                        InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
                    ],[
                        InlineKeyboardButton("𝗕𝗢𝗧 𝗢𝗪𝗡𝗘𝗥", url=OWNER_LNK)
                    ],[
                        InlineKeyboardButton('🚀 Fast Download / Watch Online🖥️', callback_data=f'generate_stream_link:{file_id}') #Don't change anything without contacting me @KingVJ01
                    ]]
                else:
                    button = [[
                        InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
                        InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
                    ],[
                        InlineKeyboardButton("𝗕𝗢𝗧 𝗢𝗪𝗡𝗘𝗥", url=OWNER_LNK)
                    ]]
                msg = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=file_id,
                    protect_content=True if pre == 'filep' else False,
                    reply_markup=InlineKeyboardMarkup(button)
                )
                filetype = msg.media
                file = getattr(msg, filetype.value)
                title = '@VJ_Bots  ' + ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), file.file_name.split()))
                size=get_size(file.file_size)
                f_caption = f"<code>{title}</code>"
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                    except:
                        return
                await msg.edit_caption(
                    caption=f_caption,
                    reply_markup=InlineKeyboardMarkup(button)
                )
                btn = [[
                    InlineKeyboardButton("Get File Again", callback_data=f'del#{file_id}')
                ]]
                k = await client.send_message(message.from_user.id,"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis Movie File/Video will be deleted in <b><u>10 mins</u> 🫥 <i></b>(Due to Copyright Issues)</i>.\n\n<b><i>Please forward this File/Video to your Saved Messages and Start Download there</i></b>")
                await asyncio.sleep(600)
                await msg.delete()
                await k.edit_text("<b>Your File/Video is successfully deleted!!!\n\nClick below button to get your deleted file 👇</b>",reply_markup=InlineKeyboardMarkup(btn))
                return
            except:
                pass
            return await client.send_message(message.from_user.id, '**No such file exist.**')
        files = files_
        title = '@VJ_Bots  ' + ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files["file_name"].split()))
        size=get_size(files["file_size"])
        f_caption=files["caption"]
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption=f_caption
        if f_caption is None:
            f_caption = f"@VJ_Bots  {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files['file_name'].split()))}"
        if not await db.has_premium_access(message.from_user.id):
            if not await check_verification(client, message.from_user.id) and VERIFY == True:
                btn = [[
                    InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start="))
                ],[
                    InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)
                ]]
                await client.send_message(
                    chat_id=message.from_user.id,
                    text="<b>You are not verified !\nKindly verify to continue !</b>",
                    protect_content=True,
                    reply_markup=InlineKeyboardMarkup(btn)
                )
                return
        if STREAM_MODE == True:
            button = [[
                InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
                InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
            ],[
                InlineKeyboardButton("𝗕𝗢𝗧 𝗢𝗪𝗡𝗘𝗥", url=OWNER_LNK)
            ],[
                InlineKeyboardButton('🚀 Fast Download / Watch Online🖥️', callback_data=f'generate_stream_link:{file_id}') #Don't change anything without contacting me @KingVJ01
            ]]
        else:
            button = [[
                InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
                InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
            ],[
                InlineKeyboardButton("𝗕𝗢𝗧 𝗢𝗪𝗡𝗘𝗥", url=OWNER_LNK)
            ]]
        msg = await client.send_cached_media(
            chat_id=message.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if pre == 'filep' else False,
            reply_markup=InlineKeyboardMarkup(button)
        )
        btn = [[
            InlineKeyboardButton("Get File Again", callback_data=f'del#{file_id}')
        ]]
        k = await client.send_message(message.from_user.id, "<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis Movie File/Video will be deleted in <b><u>10 mins</u> 🫥 <i></b>(Due to Copyright Issues)</i>.\n\n<b><i>Please forward this File/Video to your Saved Messages and Start Download there</i></b>")
        await asyncio.sleep(600)
        await msg.delete()
        await k.edit_text("<b>Your File/Video is successfully deleted!!!\n\nClick below button to get your deleted file 👇</b>",reply_markup=InlineKeyboardMarkup(btn))
        return
    if AUTO_APPROVE_MODE == True:
        if not await db.is_user_exist(message.from_user.id):
            await db.add_user(message.from_user.id, message.from_user.first_name)
        if message.chat.id == AUTH_CHANNEL:
            return 
        chat = message.chat 
        user = message.from_user  
        await client.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
        text = f"<b>ʜᴇʟʟᴏ {message.from_user.mention} 👋,\n\nʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {message.chat.title} ɪs ᴀᴘᴘʀᴏᴠᴇᴅ.\n\nᴘᴏᴡᴇʀᴇᴅ ʙʏ - {CHNL_LNK}</b>"
        await client.send_message(chat_id=user.id, text=text)
