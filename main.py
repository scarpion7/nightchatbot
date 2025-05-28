import random
from dotenv import load_dotenv
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
import re
from aiogram.types import FSInputFile, URLInputFile
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
import asyncio

load_dotenv()

# Sozlamalar
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_SECOND_GROUP_ID = int(os.getenv("ADMIN_SECOND_GROUP_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8000))

# Bot va dispatcher obyektlarini yaratish
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()


# Holatlar klassini aniqlash
class Form(StatesGroup):
    CHOOSE_GENDER = State()
    WAITING_FOR_VOICE_MESSAGE = State() # New state
    VILOYAT = State()
    TUMAN = State()
    AGE_FEMALE = State()
    FEMALE_CHOICE = State()
    POSE_WOMAN = State()
    MJM_EXPERIENCE = State()  # Umumiy MJM tajribasi (Oila uchun)
    MJM_EXPERIENCE_FEMALE = State()  # Ayol uchun MJM tajribasi (Alohida state)
    JMJ_AGE = State()
    JMJ_DETAILS = State()
    FAMILY_HUSBAND_AGE = State()
    FAMILY_WIFE_AGE = State()
    FAMILY_AUTHOR = State()
    FAMILY_HUSBAND_CHOICE = State()
    FAMILY_WIFE_AGREEMENT = State()
    FAMILY_WIFE_CHOICE = State()
    FAMILY_HUSBAND_AGREEMENT = State()
    ABOUT = State()


# New state for admin's reply context
class AdminState(StatesGroup):
    REPLYING_TO_USER = State()


# Viloyatlar ro'yxati
VILOYATLAR = [
    "Andijon", "Buxoro", "Farg'ona", "Jizzax", "Qashqadaryo", "Navoiy", "Namangan",
    "Samarqand", "Sirdaryo", "Surxondaryo", "Toshkent", "Toshkent shahar", "Xorazm",
    "Qoraqalpog'iston Respublikasi",
]

# Tumanlar lug'ati (viloyatlarga bog'langan)
TUMANLAR = {
    "Andijon": ["Andijon shahar", "Asaka", "Baliqchi", "Bo‘ston", "Izboskan", "Qo‘rg‘ontepa", "Shahrixon", "Ulug‘nor",
                "Xo‘jaobod", "Yuzboshilar", "Hokim"],
    "Buxoro": ["Buxoro shahar", "Buxoro tumani", "G‘ijduvon", "Jondor", "Kogon", "Qorako‘l", "Olot", "Peshku",
               "Romitan", "Shofirkon", "Vobkent"],
    "Farg'ona": ["Farg'ona shahar", "Farg'ona tumani", "Beshariq", "Bog‘dod", "Buvayda", "Dang‘ara", "Qo‘qon", "Quva",
                 "Rishton", "Rishton tumani", "Toshloq", "Oltiariq", "Quvasoy shahar"],
    "Jizzax": ["Jizzax shahar", "Arnasoy", "Baxmal", "Dashtobod", "Forish", "G‘allaorol", "Zarbdor", "Zomin",
               "Mirzacho‘l", "Paxtakor", "Sharof Rashidov"],
    "Qashqadaryo": ["Qarshi shahar", "Chiroqchi", "G‘uzor", "Dehqonobod", "Koson", "Kitob", "Mirishkor", "Muborak",
                    "Nishon", "Qarshi tumani", "Shahrisabz", "Yakkabog‘"],
    "Navoiy": ["Navoiy shahar", "Karmana", "Konimex", "Navbahor", "Nurota", "Tomdi", "Uchquduq", "Xatirchi"],
    "Namangan": ["Namangan shahar", "Chust", "Kosonsoy", "Mingbuloq", "Namangan tumani", "Pop", "To‘raqo‘rg‘on",
                 "Uychi", "Yangiqo‘rg‘on"],
    "Samarqand": ["Samarqand shahar", "Bulung‘ur", "Jomboy", "Kattaqo‘rg‘on", "Narpay", "Nurobod", "Oqdaryo", "Payariq",
                  "Pastdarg‘om", "Paxtachi", "Qo‘shrabot", "Samarqand tumani", "Toyloq"],
    "Sirdaryo": ["Guliston shahar", "Boyovut", "Guliston tumani", "Mirzaobod", "Oqoltin", "Sayxunobod", "Sardoba",
                 "Sirdaryo tumani", "Xovos"],
    "Surxondaryo": ["Termiz shahar", "Angor", "Boysun", "Denov", "Jarqo‘rg‘on", "Muzrabot", "Sariosiyo", "Sherobod",
                    "Sho‘rchi", "Termiz tumani"],
    "Toshkent": ["Bekobod", "Bo‘ka", "Ohangaron", "Oqqo‘rg‘on", "Chinoz", "Qibray", "Quyichirchiq", "Toshkent tumani",
                 "Yangiyo‘l", "Zangiota", "Bekobod shahar", "Ohangaron shahar", "Yangiyo‘l shahar"],
    "Toshkent shahar": ["Mirzo Ulug‘bek", "Mirobod", "Sergeli", "Olmazor", "Shayxontohur", "Chilonzor", "Yunusobod",
                        "Uchtepa", "Yashnobod"],
    "Xorazm": ["Urganch shahar", "Bog‘ot", "Gurlan", "Xiva shahar", "Qo‘shko‘pir", "Shovot", "Urganch tumani", "Xonqa",
               "Yangiariq"],
    "Qoraqalpog'iston Respublikasi": ["Nukus shahar", "Amudaryo", "Beruniy", "Bo‘zatov", "Kegayli", "Qonliko‘l",
                                      "Qo‘ng‘irot",
                                      "Qorao‘zak", "Shumanay", "Taxtako‘pir", "To‘rtko‘l", "Xo‘jayli",
                                      "Chimboy", "Mo‘ynoq", "Ellikqal‘a"],
}

# Ayollar uchun pozitsiyalar ro'yxati
POSES_WOMAN = [
    "Rakom", "Chavandoz(Ustizda sakrab)", "Oyolarimni yelkezga qo'yib", "Romantik/Erkalab",
    "BSDM / Qiynab", "Hamma pozada", "Kunillingus / Minet / 69 / Lazzatli seks", "Anal/Romantik"
]

# MJM tajribasi variantlari (Oila uchun)
MJM_EXPERIENCE_OPTIONS = [
    "Hali bo'lmagan",
    "1-marta bo'lgan",
    "2-3 marta bo'lgan",
    "5 martadan ko'p (MJMni sevamiz)"
]

# MJM tajribasi variantlari (Ayol uchun)
MJM_EXPERIENCE_FEMALE_OPTIONS = [
    "Hali bo'lmagan",
    "1-marta bo'lgan",
    "2-3 marta bo'lgan",
    "5 martadan ko'p (MJMni sevaman)"
]

# Random phrases for voice message
RANDOM_PHRASES = [
    "Salom, bugun ajoyib kun!",
    "Hayot go'zal, uni qadrlaylik.",
    "Har bir kuningiz mazmunli o'tsin!",
    "Omad sizga kulib boqsin!",
    "Orzularingizga erishing!",
    "Tabassum qiling, hayot go'zal!",
    "Yaxshi kayfiyat tilayman!",
    "Baxt har doim yoningizda bo'lsin!"
]

# Suhbat rejimida bo'lgan foydalanuvchilar IDsi
chat_mode_users = set()


# Umumiy navigatsiya tugmalarini qo'shish funksiyasi (Vertical)
def add_navigation_buttons(builder: InlineKeyboardBuilder, back_state: str):
    builder.row(
        types.InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"back_{back_state}"),
        types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")
    )


# Jinsni tanlash klaviaturasi (Vertical)
def gender_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👨 Erkak", callback_data="gender_male"))
    builder.row(types.InlineKeyboardButton(text="👩 Ayol", callback_data="gender_female"))
    builder.row(types.InlineKeyboardButton(text="👨‍👩‍👧 Oilaman", callback_data="gender_family"))
    builder.row(
        types.InlineKeyboardButton(text="ℹ️ Bot haqida", callback_data="about_bot"))
    add_navigation_buttons(builder, "start")
    return builder.as_markup()


# Viloyatlar klaviaturasi (Vertical)
def viloyat_keyboard():
    builder = InlineKeyboardBuilder()
    for vil in VILOYATLAR:
        builder.row(types.InlineKeyboardButton(text=vil, callback_data=f"vil_{vil}"))
    add_navigation_buttons(builder, "gender")
    return builder.as_markup()


# Tumanlar klaviaturasi (Vertical)
def tuman_keyboard(viloyat):
    builder = InlineKeyboardBuilder()
    for tuman in TUMANLAR.get(viloyat, []):
        builder.row(types.InlineKeyboardButton(text=tuman, callback_data=f"tum_{tuman}"))
    add_navigation_buttons(builder, "viloyat")
    return builder.as_markup()


# Ayolning yoshini tanlash klaviaturasi (Vertical)
def age_female_keyboard():
    builder = InlineKeyboardBuilder()
    ranges = ["18-25", "26-35", "36-45", "45+"]
    for r in ranges:
        builder.row(types.InlineKeyboardButton(text=r, callback_data=f"age_{r}"))
    add_navigation_buttons(builder, "tuman")
    return builder.as_markup()


# Ayolning tanlov klaviaturasi (Vertical)
def female_choice_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👨 Erkak bilan", callback_data="choice_1"))
    builder.row(types.InlineKeyboardButton(text="👥 MJM (2ta erkak)", callback_data="choice_2"))
    builder.row(types.InlineKeyboardButton(text="👭 JMJ (Dugonam bor)", callback_data="choice_3"))
    add_navigation_buttons(builder, "age_female")
    return builder.as_markup()


# Ayollar uchun pozitsiyalar klaviaturasi (Vertical)
def poses_keyboard():
    builder = InlineKeyboardBuilder()
    for idx, pose in enumerate(POSES_WOMAN, 1):
        builder.row(types.InlineKeyboardButton(text=f"{idx}. {pose}", callback_data=f"pose_{idx}"))
    add_navigation_buttons(builder, "female_choice")
    return builder.as_markup()


# MJM tajribasini tanlash klaviaturasi (Vertical)
def mjm_experience_keyboard(is_female=False):
    builder = InlineKeyboardBuilder()
    options = MJM_EXPERIENCE_FEMALE_OPTIONS if is_female else MJM_EXPERIENCE_OPTIONS

    for idx, option in enumerate(options):
        callback_prefix = "mjm_exp_female_" if is_female else "mjm_exp_family_"
        builder.row(types.InlineKeyboardButton(text=option, callback_data=f"{callback_prefix}{idx}"))

    if is_female:
        add_navigation_buttons(builder, "female_choice")
    else:
        add_navigation_buttons(builder, "family_husband_choice")

    return builder.as_markup()


# Oila: Kim yozmoqda klaviaturasi (Vertical)
def family_author_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👨 Erkak yozmoqda", callback_data="author_husband"))
    builder.row(types.InlineKeyboardButton(text="👩 Ayol yozmoqda", callback_data="author_wife"))
    add_navigation_buttons(builder, "family_wife_age")
    return builder.as_markup()


# Oila: Erkakning tanlovi klaviaturasi (Vertical)
def family_husband_choice_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👥 MJM", callback_data="h_choice_mjm"))
    builder.row(types.InlineKeyboardButton(text="👨 Erkak (ayolim uchun)", callback_data="h_choice_erkak"))
    add_navigation_buttons(builder, "family_author")
    return builder.as_markup()


# Oila: Ayolning roziligi klaviaturasi (Erkak tanlovidan keyin) (Vertical)
def family_wife_agreement_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Ha rozi", callback_data="wife_agree_yes"))
    builder.row(
        types.InlineKeyboardButton(text="🔄 Yo'q, lekin men istayman (kondiraman)", callback_data="wife_agree_convince"))
    builder.row(
        types.InlineKeyboardButton(text="❓ Bilmayman, hali aytib ko'rmadim", callback_data="wife_agree_unknown"))
    add_navigation_buttons(builder, "family_husband_choice")
    return builder.as_markup()


# Oila: Ayolning tanlovi klaviaturasi (Vertical)
def family_wife_choice_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👥 MJM (erim bilan)", callback_data="w_choice_mjm_husband"))
    builder.row(types.InlineKeyboardButton(text="👥 MJM (begona 2 erkak bilan)", callback_data="w_choice_mjm_strangers"))
    builder.row(types.InlineKeyboardButton(text="👨 Erkak (erimdan qoniqmayapman)", callback_data="w_choice_erkak"))
    add_navigation_buttons(builder, "family_author")
    return builder.as_markup()


# Oila: Erkakning roziligi klaviaturasi (Ayol tanlovidan keyin) (Vertical)
def family_husband_agreement_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Ha rozi", callback_data="husband_agree_yes"))
    builder.row(types.InlineKeyboardButton(text="🔄 Yo'q, lekin men istayman (kondiraman)",
                                           callback_data="husband_agree_convince"))
    builder.row(
        types.InlineKeyboardButton(text="❓ Bilmayman, hali aytib ko'rmadim", callback_data="husband_agree_unknown"))
    add_navigation_buttons(builder, "family_wife_choice")
    return builder.as_markup()


# Admin panelga va kanalga ma'lumotlarni yuborish funksiyasi (Uch manzilga)
async def send_application_to_destinations(data: dict, user: types.User):
    admin_message_text = (
        f"📊 **Yangi ariza qabul qilindi**\n\n"
        f"👤 **Profilga havola:** "
    )
    if user.username:
        admin_message_text += f"[@{user.username}](tg://user?id={user.id}) (ID: `{user.id}`)\n"
    else:
        admin_message_text += f"[{user.full_name}](tg://user?id={user.id}) (ID: `{user.id}`)\n"

    admin_message_text += (
        f"📝 **Ism:** {user.full_name}\n"
        f"🚻 **Jins:** {data.get('gender', 'None1')}\n"
        f"🗺️ **Viloyat:** {data.get('viloyat', 'None1')}\n"
        f"🏘️ **Tuman:** {data.get('tuman', 'None1')}\n"
    )

    if data.get('gender') == 'female':
        admin_message_text += (
            f"🎂 **Yosh:** {data.get('age', 'None1')}\n"
            f"🤝 **Tanlov:** {'Erkak bilan' if data.get('choice') == '1' else ('👥 MJM (2ta erkak)' if data.get('choice') == '2' else ('👭 JMJ (Dugonam bor)' if data.get('choice') == '3' else 'None1'))}\n"
        )
        if data.get('choice') == '1':
            admin_message_text += f"🤸 **Pozitsiya:** {data.get('pose', 'None1')}\n"
        elif data.get('choice') == '2':
            admin_message_text += f"👥 **MJM tajriba:** {data.get('mjm_experience_female', 'None1')}\n"
        elif data.get('choice') == '3':
            admin_message_text += (
                f"🎂 **Dugona yoshi:** {data.get('jmj_age', 'None1')}\n"
                f"ℹ️ **Dugona haqida:** {data.get('jmj_details', 'None1')}\n"
            )

    elif data.get('gender') == 'family':
        admin_message_text += (
            f"👨 **Erkak yoshi:** {data.get('husband_age', 'None1')}\n"
            f"👩 **Ayol yoshi:** {data.get('wife_age', 'None1')}\n"
            f"✍️ **Yozmoqda:** {'Erkak' if data.get('author') == 'husband' else ('Ayol' if data.get('author') == 'wife' else 'None1')}\n"
        )
        if data.get('author') == 'husband':
            h_choice_text = {'mjm': '👥 MJM', 'erkak': '👨 Erkak (ayoli uchun)'}.get(data.get('h_choice'), 'None1')
            admin_message_text += f"🎯 **Erkak tanlovi:** {h_choice_text}\n"
            if data.get('h_choice') == 'mjm':
                admin_message_text += f"👥 **MJM tajriba:** {data.get('mjm_experience', 'None1')}\n"
            admin_message_text += f"👩‍⚕️ **Ayol roziligi:** {data.get('wife_agreement', 'None1')}\n"

        elif data.get('author') == 'wife':
            w_choice_text = {'mjm_husband': '👥 MJM (erim bilan)', 'mjm_strangers': '👥 MJM (begona 2 erkak bilan)',
                             'erkak': '👨 Erkak (erimdan qoniqmayapman)'}.get(data.get('w_choice'), 'None1')
            admin_message_text += f"🎯 **Ayol tanlovi:** {w_choice_text}\n"
            if data.get('w_choice') == 'mjm_husband':
                admin_message_text += f"👨‍⚕️ **Erkak roziligi:** {data.get('husband_agreement', 'None1')}\n"

    if data.get('about'):
        admin_message_text += f"ℹ️ **Qo'shimcha / Kutilayotgan natija:** {data.get('about', 'None1')}\n"

    voice_phrase = data.get('voice_phrase')
    voice_message_file_id = data.get('voice_message_file_id')

    if voice_message_file_id and voice_phrase:
        admin_message_text += f"🎤 **Ovozli tasdiqlash:** {voice_phrase}\n"


    builder = InlineKeyboardBuilder()
    builder.button(text="✉️ Javob yozish", callback_data=f"admin_initiate_reply_{user.id}")
    reply_markup = builder.as_markup()

    target_chat_ids = [ADMIN_USER_ID, ADMIN_GROUP_ID, ADMIN_SECOND_GROUP_ID]

    for chat_id in target_chat_ids:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=admin_message_text,
                reply_markup=reply_markup if chat_id in [ADMIN_USER_ID, ADMIN_GROUP_ID] else None, # Only for admin and main group
                parse_mode="Markdown"
            )
            if voice_message_file_id:
                await bot.send_voice(chat_id=chat_id, voice=voice_message_file_id)
            logging.info(f"Application sent to chat {chat_id} for user {user.id}")
        except Exception as e:
            logging.error(f"Failed to send application to chat {chat_id} for user {user.id}: {e}")
            try:
                await bot.send_message(ADMIN_USER_ID,
                                       f"⚠️ Ogohlantirish: Foydalanuvchi `{user.id}` arizasini {chat_id} chatiga yuborishda xatolik: {e}",
                                       parse_mode="Markdown")
            except Exception as e_admin:
                logging.error(f"Failed to send error notification to admin user: {e_admin}")

    channel_text = f"📊 **Yangi ariza**\n\n📝 **Ism:** {user.full_name}\n"

    if data.get('gender'):
        channel_text += f"🚻 **Jins:** {data['gender']}\n"
    if data.get('viloyat'):
        channel_text += f"🗺️ **Viloyat:** {data['viloyat']}\n"
    if data.get('tuman'):
        channel_text += f"🏘️ **Tuman:** {data['tuman']}\n"
    if data.get('gender') == 'female':
        if data.get('age'):
            channel_text += f"🎂 **Yosh:** {data['age']}\n"
        if data.get('choice'):
            choice_text = {'1': 'Erkak bilan', '2': '👥 MJM (2ta erkak)', '3': '👭 JMJ (Dugonam bor)'}.get(data['choice'],
                                                                                                         'None1')
            channel_text += f"🤝 **Tanlov:** {choice_text}\n"
        if data.get('pose'):
            channel_text += f"🤸 **Pozitsiya:** {data['pose']}\n"
        if data.get('mjm_experience_female') and data.get('choice') == '2':
            channel_text += f"👥 **MJM tajriba:** {data['mjm_experience_female']}\n"
        if data.get('jmj_age') and data.get('choice') == '3':
            channel_text += f"🎂 **Dugona yoshi:** {data['jmj_age']}\n"
        if data.get('jmj_details') and data.get('choice') == '3':
            channel_text += f"ℹ️ **Dugona haqida:** {data['jmj_details']}\n"
    elif data.get('gender') == 'family':
        if data.get('husband_age'):
            channel_text += f"👨 **Erkak yoshi:** {data['husband_age']}\n"
        if data.get('wife_age'):
            channel_text += f"👩 **Ayol yoshi:** {data['wife_age']}\n"
        if data.get('author'):
            author_text = {'husband': 'Erkak', 'wife': 'Ayol'}.get(data['author'], 'None1')
            channel_text += f"✍️ **Yozmoqda:** {author_text}\n"
        if data.get('h_choice') and data.get('author') == 'husband':
            h_choice_text = {'mjm': '👥 MJM', 'erkak': '👨 Erkak (ayoli uchun)'}.get(data['h_choice'], 'None1')
            channel_text += f"🎯 **Erkak tanlovi:** {h_choice_text}\n"
        if data.get('mjm_experience') and data.get('author') == 'husband' and data.get(
                'h_choice') == 'mjm':
            channel_text += f"👥 **MJM tajriba:** {data['mjm_experience']}\n"
        if data.get('wife_agreement') and data.get('author') == 'husband':
            wife_agree_text = {'yes': '✅ Ha rozi', 'convince': '🔄 Yo\'q, lekin men istayman',
                               'unknown': '❓ Bilmayman, hali aytmadim'}.get(data['wife_agreement'], 'None1')
            channel_text += f"👩‍⚕️ **Ayol roziligi:** {wife_agree_text}\n"
        if data.get('w_choice') and data.get('author') == 'wife':
            w_choice_text = {'mjm_husband': '👥 MJM (erim bilan)', 'mjm_strangers': '👥 MJM (begona 2 erkak bilan)',
                             'erkak': '👨 Erkak (erimdan qoniqmayapman)'}.get(data['w_choice'], 'None1')
            channel_text += f"🎯 **Ayol tanlovi:** {w_choice_text}\n"
        if data.get('husband_agreement') and data.get('author') == 'wife' and data.get('w_choice') == 'mjm_husband':
            husband_agree_text = {'yes': '✅ Ha rozi', 'convince': '🔄 Yo\'q, lekin men istayman',
                                  'unknown': '❓ Bilmayman, hali aytmadim'}.get(
                data['husband_agreement'], 'None1')
            channel_text += f"👨‍⚕️ **Erkak roziligi:** {husband_agree_text}\n"

    if data.get('about'):
        channel_text += f"ℹ️ **Qo'shimcha / Kutilayotgan natija:** {data['about']}\n"

    if voice_message_file_id and voice_phrase:
        channel_text += f"🎤 **Ovozli tasdiqlash:** {voice_phrase}\n"

    channel_text += "\n---\nBu ariza kanalga avtomatik joylandi."

    try:
        await bot.send_message(
            CHANNEL_ID,
            channel_text,
            parse_mode="Markdown"
        )
        if voice_message_file_id:
            await bot.send_voice(chat_id=CHANNEL_ID, voice=voice_message_file_id)
        logging.info(f"Application sent to channel {CHANNEL_ID} for user {user.id}")
    except Exception as e:
        logging.error(f"Failed to send application to channel {CHANNEL_ID} for user {user.id}: {e}")
        try:
            await bot.send_message(ADMIN_USER_ID,
                                   f"⚠️ Ogohlantirish: Foydalanuvchi `{user.id}` arizasini kanalga yuborishda xatolik: {e}",
                                   parse_mode="Markdown")
        except Exception as e_admin:
            logging.error(f"Failed to send error notification to admin user about channel error: {e_admin}")


@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    if message.from_user.id in chat_mode_users:
        await message.answer("Siz suhbat rejimidasiz. Suhbatni tugatish uchun /endchat buyrug'ini bosing. \n\n"
                             "Agar suhbat tugasa admin sizga yoza olmaydi.\n\n"
                             "Istasangiz suhbatni tugatishdan oldin siz bilan bog'lanish uchun\n\n"
                             " raqam yoki username qoldiring ")
        return

    await state.clear()
    await message.answer("Salom! Iltimos, jinsingizni tanlang:", reply_markup=gender_keyboard())
    await state.set_state(Form.CHOOSE_GENDER)
    logging.info(f"User {message.from_user.id} started the bot.")


@dp.callback_query(F.data == "cancel")
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id in chat_mode_users:
        await callback.answer("Siz suhbat rejimidasiz. Suhbatni tugatish uchun /endchat ni bosing.", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text("Suhbat bekor qilindi. Yangidan boshlash uchun /start ni bosing.")
    await callback.answer()
    logging.info(f"User {callback.from_user.id} cancelled the form.")


@dp.callback_query(F.data == "about_bot")
async def about_bot_handler(callback: types.CallbackQuery):
    about_text = (
        "Bu bot orqali siz o'zingizga mos juftlikni topishingiz mumkin.\n"
        "Anonimlik kafolatlanadi.\n"
        "Qoidalar:\n"
        "- Faqat 18+ foydalanuvchilar uchun.\n"
        "- Haqiqiy ma'lumotlarni kiriting.\n"
        "- Hurmat doirasidan chiqmaslik.\n"
        "Qayta boshlash uchun /start buyrug'ini bosing."
    )
    await callback.message.edit_text(about_text, reply_markup=InlineKeyboardBuilder().button(text="◀️ Orqaga",
                                                                                             callback_data="back_start").as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("back_"))
async def back_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id in chat_mode_users:
        await callback.answer("Siz suhbat rejimidasiz. Suhbatni tugatish uchun /endchat buyrug'ini bosing. \n\n"
                              "Agar suhbat tugasa admin sizga yoza olmaydi.\n\n"
                              "Istasangiz suhbatni tugatishdan oldin siz bilan bog'lanish uchun\n\n"
                              " raqam yoki username qoldiring ", show_alert=True)
        return

    target_state_name = callback.data.split("_")[1]
    data = await state.get_data()

    logging.info(f"User {callback.from_user.id} going back to {target_state_name}")
    logging.info(f"Current state data: {data}")

    if target_state_name == "start":
        await start_handler(callback.message, state)
    elif target_state_name == "gender":
        await state.set_state(Form.CHOOSE_GENDER)
        await callback.message.edit_text("Iltimos, jinsingizni tanlang:", reply_markup=gender_keyboard())
    elif target_state_name == "viloyat":
        await state.set_state(Form.VILOYAT)
        await callback.message.edit_text("Viloyatingizni tanlang:", reply_markup=viloyat_keyboard())
    elif target_state_name == "tuman":
        viloyat = data.get('viloyat')
        if viloyat:
            await state.set_state(Form.TUMAN)
            await callback.message.edit_text("Tumaningizni tanlang:", reply_markup=tuman_keyboard(viloyat))
        else:
            await state.set_state(Form.VILOYAT)
            await callback.message.edit_text("Viloyatingizni tanlang:", reply_markup=viloyat_keyboard())
    elif target_state_name == "age_female":
        await state.set_state(Form.AGE_FEMALE)
        await callback.message.edit_text("Yoshingizni tanlang:", reply_markup=age_female_keyboard())
    elif target_state_name == "female_choice":
        await state.set_state(Form.FEMALE_CHOICE)
        await callback.message.edit_text("Tanlang:", reply_markup=female_choice_keyboard())
    elif target_state_name == "pose_woman":
        await state.set_state(Form.POSE_WOMAN)
        await callback.message.edit_text("Iltimos, pozitsiyalardan birini tanlang:", reply_markup=poses_keyboard())
    elif target_state_name == "mjm_experience":
        await callback.message.edit_text("MJM tajribangizni tanlang:", reply_markup=mjm_experience_keyboard(is_female=False))
        await state.set_state(Form.MJM_EXPERIENCE)
    elif target_state_name == "mjm_experience_female":
        await callback.message.edit_text("MJM tajribangizni tanlang:", reply_markup=mjm_experience_keyboard(is_female=True))
        await state.set_state(Form.MJM_EXPERIENCE_FEMALE)
    elif target_state_name == "jmj_age":
        await state.set_state(Form.JMJ_AGE)
        await callback.message.edit_text("Dugonangizning yoshini kiriting (faqat raqamda, 18-60 yosh):")
    elif target_state_name == "jmj_details":
        await state.set_state(Form.JMJ_DETAILS)
        await callback.message.edit_text("Dugonangiz haqida qo'shimcha ma'lumot kiriting:")
    elif target_state_name == "family_husband_age":
        await state.set_state(Form.FAMILY_HUSBAND_AGE)
        await callback.message.edit_text("Eringizning yoshini kiriting (faqat raqamda, 18-60 yosh):")
    elif target_state_name == "family_wife_age":
        await state.set_state(Form.FAMILY_WIFE_AGE)
        await callback.message.edit_text("Ayolingizning yoshini kiriting (faqat raqamda, 18-60 yosh):")
    elif target_state_name == "family_author":
        await state.set_state(Form.FAMILY_AUTHOR)
        await callback.message.edit_text("Kim yozmoqda:", reply_markup=family_author_keyboard())
    elif target_state_name == "family_husband_choice":
        await state.set_state(Form.FAMILY_HUSBAND_CHOICE)
        await callback.message.edit_text("Tanlang:", reply_markup=family_husband_choice_keyboard())
    elif target_state_name == "family_wife_agreement":
        await state.set_state(Form.FAMILY_WIFE_AGREEMENT)
        await callback.message.edit_text("Ayolning roziligi:", reply_markup=family_wife_agreement_keyboard())
    elif target_state_name == "family_wife_choice":
        await state.set_state(Form.FAMILY_WIFE_CHOICE)
        await callback.message.edit_text("Tanlang:", reply_markup=family_wife_choice_keyboard())
    elif target_state_name == "family_husband_agreement":
        await state.set_state(Form.FAMILY_HUSBAND_AGREEMENT)
        await callback.message.edit_text("Erkakning roziligi:", reply_markup=family_husband_agreement_keyboard())
    elif target_state_name == "about":
        # 'About' sahifasidan orqaga qaytishda oldingi statega o'tish logikasi
        gender = data.get('gender')
        prev_state_for_about = None
        if gender == 'female':
            choice = data.get('choice')
            if choice == '1':
                prev_state_for_about = Form.POSE_WOMAN
            elif choice == '2':
                prev_state_for_about = Form.MJM_EXPERIENCE_FEMALE
            elif choice == '3':
                prev_state_for_about = Form.JMJ_DETAILS
        elif gender == 'family':
            author = data.get('author')
            if author == 'husband':
                h_choice = data.get('h_choice')
                if h_choice == 'mjm':
                    prev_state_for_about = Form.MJM_EXPERIENCE
                elif h_choice == 'erkak':
                    prev_state_for_about = Form.FAMILY_WIFE_AGREEMENT
            elif author == 'wife':
                w_choice = data.get('w_choice')
                if w_choice == 'mjm_husband':
                    prev_state_for_about = Form.FAMILY_HUSBAND_AGREEMENT
                elif w_choice in ['mjm_strangers', 'erkak']:
                    prev_state_for_about = Form.FAMILY_WIFE_CHO

        if prev_state_for_about:
            await state.set_state(prev_state_for_about)
            if prev_state_for_about == Form.POSE_WOMAN:
                await callback.message.edit_text("Iltimos, pozitsiyalardan birini tanlang:", reply_markup=poses_keyboard())
            elif prev_state_for_about == Form.MJM_EXPERIENCE_FEMALE:
                await callback.message.edit_text("MJM tajribangizni tanlang:", reply_markup=mjm_experience_keyboard(is_female=True))
            elif prev_state_for_about == Form.MJM_EXPERIENCE:
                await callback.message.edit_text("MJM tajribangizni tanlang:", reply_markup=mjm_experience_keyboard(is_female=False))
            elif prev_state_for_about == Form.JMJ_DETAILS:
                await callback.message.edit_text("Dugonangiz haqida qo'shimcha ma'lumot kiriting:")
            elif prev_state_for_about == Form.FAMILY_WIFE_AGREEMENT:
                await callback.message.edit_text("Ayolning roziligi:", reply_markup=family_wife_agreement_keyboard())
            elif prev_state_for_about == Form.FAMILY_WIFE_CHOICE:
                await callback.message.edit_text("Tanlang:", reply_markup=family_wife_choice_keyboard())
            elif prev_state_for_about == Form.FAMILY_HUSBAND_AGREEMENT:
                await callback.message.edit_text("Erkakning roziligi:", reply_markup=family_husband_agreement_keyboard())
            else:
                await state.set_state(Form.CHOOSE_GENDER)
                await callback.message.edit_text("Iltimos, jinsingizni tanlang:", reply_markup=gender_keyboard())
            logging.warning(f"User {callback.from_user.id} back from ABOUT to unhandled previous state.")
        else:
            await state.set_state(Form.CHOOSE_GENDER)
            await callback.message.edit_text("Iltimas, jinsingizni tanlang:", reply_markup=gender_keyboard())
            logging.warning(f"User {callback.from_user.id} back from ABOUT with no determined previous state.")
    await callback.answer()


@dp.callback_query(F.data.startswith("gender_"), Form.CHOOSE_GENDER)
async def gender_handler(callback: types.CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    logging.info(f"User {callback.from_user.id} chose gender: {gender}")

    if gender == "male":
        await callback.message.edit_text(
            "Kechirasiz, bu xizmat faqat ayollar va oilalar uchun.\n"
            "Agar oila bo'lsangiz iltimos «Oilaman» bo'limini tanlang.",
            reply_markup=InlineKeyboardBuilder().button(
                text="Qayta boshlash", callback_data="back_start"
            ).as_markup()
        )
        await state.clear()
        await callback.answer("Erkaklar uchun ro'yxatdan o'tish mumkin emas.", show_alert=True)
    else:
        random_phrase = random.choice(RANDOM_PHRASES)
        await state.update_data(voice_phrase=random_phrase)
        await callback.message.edit_text(f"Iltimos, ushbu jumlani ovozli xabar qilib yuboring:\n\n*\"{random_phrase}\"*\n\nOvozli xabar yuborgandan so'ng keyingi bosqichga o'tasiz.", parse_mode="Markdown")
        await state.set_state(Form.WAITING_FOR_VOICE_MESSAGE)
        await callback.answer()

@dp.message(F.voice, Form.WAITING_FOR_VOICE_MESSAGE)
async def voice_message_handler(message: types.Message, state: FSMContext):
    file_id = message.voice.file_id
    await state.update_data(voice_message_file_id=file_id)
    data = await state.get_data()
    voice_phrase = data.get('voice_phrase', 'Noma\'lum jumla')

    await message.answer(
        f"Ovozli xabaringiz qabul qilindi! Siz \"{voice_phrase}\" deb aytdingiz. Rahmat! Endi viloyatingizni tanlang:",
        reply_markup=viloyat_keyboard()
    )
    await state.set_state(Form.VILOYAT)
    logging.info(f"User {message.from_user.id} sent voice message with file_id: {file_id}")


@dp.callback_query(F.data.startswith("vil_"), Form.VILOYAT)
async def viloyat_handler(callback: types.CallbackQuery, state: FSMContext):
    viloyat = callback.data.split("_")[1]
    await state.update_data(viloyat=viloyat)
    logging.info(f"User {callback.from_user.id} chose viloyat: {viloyat}")
    await callback.message.edit_text("Tumaningizni tanlang:", reply_markup=tuman_keyboard(viloyat))
    await state.set_state(Form.TUMAN)
    await callback.answer()


@dp.callback_query(F.data.startswith("tum_"), Form.TUMAN)
async def tuman_handler(callback: types.CallbackQuery, state: FSMContext):
    tuman = callback.data.split("_")[1]
    await state.update_data(tuman=tuman)
    logging.info(f"User {callback.from_user.id} chose tuman: {tuman}")

    data = await state.get_data()
    gender = data.get('gender')

    if gender == "female":
        await callback.message.edit_text("Yoshingizni tanlang:", reply_markup=age_female_keyboard())
        await state.set_state(Form.AGE_FEMALE)
    elif gender == "family":
        await callback.message.edit_text("Eringizning yoshini kiriting (faqat raqamda, 18-60 yosh):")
        await state.set_state(Form.FAMILY_HUSBAND_AGE)
    await callback.answer()


@dp.callback_query(F.data.startswith("age_"), Form.AGE_FEMALE)
async def age_female_handler(callback: types.CallbackQuery, state: FSMContext):
    age = callback.data.split("_")[1]
    await state.update_data(age=age)
    logging.info(f"User {callback.from_user.id} chose age (female): {age}")
    await callback.message.edit_text("Tanlang:", reply_markup=female_choice_keyboard())
    await state.set_state(Form.FEMALE_CHOICE)
    await callback.answer()


@dp.callback_query(F.data.startswith("choice_"), Form.FEMALE_CHOICE)
async def female_choice_handler(callback: types.CallbackQuery, state: FSMContext):
    choice = callback.data.split("_")[1]
    await state.update_data(choice=choice)
    logging.info(f"User {callback.from_user.id} chose female choice: {choice}")

    if choice == "1":  # Erkak bilan
        await callback.message.edit_text("Iltimos, pozitsiyalardan birini tanlang:", reply_markup=poses_keyboard())
        await state.set_state(Form.POSE_WOMAN)
    elif choice == "2":  # MJM (2ta erkak)
        await callback.message.edit_text("MJM tajribangizni tanlang:", reply_markup=mjm_experience_keyboard(is_female=True))
        await state.set_state(Form.MJM_EXPERIENCE_FEMALE)
    elif choice == "3":  # JMJ (Dugonam bor)
        await callback.message.edit_text("Dugonangizning yoshini kiriting (faqat raqamda, 18-60 yosh):")
        await state.set_state(Form.JMJ_AGE)
    await callback.answer()


@dp.message(F.text, Form.JMJ_AGE)
async def jmj_age_handler(message: types.Message, state: FSMContext):
    age_input = message.text.strip()
    if age_input.isdigit() and 18 <= int(age_input) <= 60:
        await state.update_data(jmj_age=age_input)
        logging.info(f"User {message.from_user.id} entered JMJ age: {age_input}")
        await message.answer("Dugonangiz haqida qo'shimcha ma'lumot kiriting:")
        await state.set_state(Form.JMJ_DETAILS)
    else:
        await message.answer("Iltimos, dugonangizning yoshini 18 yoshdan 60 yoshgacha bo'lgan raqamda kiriting.")


@dp.message(F.text, Form.JMJ_DETAILS)
async def jmj_details_handler(message: types.Message, state: FSMContext):
    details = message.text.strip()
    await state.update_data(jmj_details=details)
    logging.info(f"User {message.from_user.id} entered JMJ details: {details}")
    await message.answer(
        "Bu uchrashuvdan nimalarni kutyapsiz va sizga nimalar yoqadi(hohlayapsiz) \n\n Ko’rishish uchun sizda joy mavjudmi(batafsil yozing)??:")
    await state.set_state(Form.ABOUT)


@dp.callback_query(F.data.startswith("pose_"), Form.POSE_WOMAN)
async def pose_woman_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        pose_index = int(callback.data.split("_")[1])
        if 0 < pose_index <= len(POSES_WOMAN):
            pose = POSES_WOMAN[pose_index - 1]  # List index is 0-based
            await state.update_data(pose=pose)
            logging.info(f"User {callback.from_user.id} chose female pose: {pose}")
            await callback.message.edit_text(
                "Bu uchrashuvdan nimalarni kutyapsiz va sizga nimalar yoqadi(hohlayapsiz) \n\n Ko’rishish uchun sizda joy mavjudmi(batafsil yozing)??:")
            await state.set_state(Form.ABOUT)
        else:
            await callback.message.edit_text("Noto'g'ri pozitsiya tanlandi. Iltimos, qaytadan tanlang.", reply_markup=poses_keyboard())
    except ValueError:
        await callback.message.edit_text("Noto'g'ri ma'lumot qabul qilindi. Iltimos, tugmalardan birini bosing.", reply_markup=poses_keyboard())
    await callback.answer()


@dp.callback_query(F.data.startswith("mjm_exp_family_"), Form.MJM_EXPERIENCE)
async def mjm_experience_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        exp_index = int(callback.data.split("_")[-1])
        if 0 <= exp_index < len(MJM_EXPERIENCE_OPTIONS):
            original_option_text = MJM_EXPERIENCE_OPTIONS[exp_index]
            await state.update_data(mjm_experience=original_option_text)
            logging.info(f"User {callback.from_user.id} chose MJM experience (family): {original_option_text}")
            await callback.message.edit_text("Ayolning roziligi:", reply_markup=family_wife_agreement_keyboard())
            await state.set_state(Form.FAMILY_WIFE_AGREEMENT)
        else:
            await callback.message.edit_text("Noto'g'ri tanlov. Iltimos, qaytadan tanlang.", reply_markup=mjm_experience_keyboard(is_female=False))
    except ValueError:
        await callback.message.edit_text("Noto'g'ri ma'lumot qabul qilindi. Iltimos, tugmalardan birini bosing.", reply_markup=mjm_experience_keyboard(is_female=False))
    await callback.answer()


@dp.callback_query(F.data.startswith("mjm_exp_female_"), Form.MJM_EXPERIENCE_FEMALE)
async def mjm_experience_female_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        exp_index = int(callback.data.split("_")[-1])
        if 0 <= exp_index < len(MJM_EXPERIENCE_FEMALE_OPTIONS):
            original_option_text = MJM_EXPERIENCE_FEMALE_OPTIONS[exp_index]
            await state.update_data(mjm_experience_female=original_option_text)
            logging.info(f"User {callback.from_user.id} chose MJM experience (female): {original_option_text}")
            await callback.message.edit_text(
                "Bu uchrashuvdan nimalarni kutyapsiz va sizga nimalar yoqadi(hohlayapsiz) \n\n Ko’rishish uchun sizda joy mavjudmi(batafsil yozing)??:")
            await state.set_state(Form.ABOUT)
        else:
            await callback.message.edit_text("Noto'g'ri tanlov. Iltimos, qaytadan tanlang.", reply_markup=mjm_experience_keyboard(is_female=True))
    except ValueError:
        await callback.message.edit_text("Noto'g'ri ma'lumot qabul qilindi. Iltimos, tugmalardan birini bosing.", reply_markup=mjm_experience_keyboard(is_female=True))
    await callback.answer()


@dp.message(F.text, Form.FAMILY_HUSBAND_AGE)
async def family_husband_age_handler(message: types.Message, state: FSMContext):
    age_input = message.text.strip()
    if age_input.isdigit() and 18 <= int(age_input) <= 60:
        await state.update_data(husband_age=age_input)
        logging.info(f"User {message.from_user.id} entered husband age: {age_input}")
        await message.answer("Ayolingizning yoshini kiriting (faqat raqamda, 18-60 yosh):")
        await state.set_state(Form.FAMILY_WIFE_AGE)
    else:
        await message.answer("Iltimos, eringizning yoshini 18 yoshdan 60 yoshgacha bo'lgan raqamda kiriting.")


@dp.message(F.text, Form.FAMILY_WIFE_AGE)
async def family_wife_age_handler(message: types.Message, state: FSMContext):
    age_input = message.text.strip()
    if age_input.isdigit() and 18 <= int(age_input) <= 60:
        await state.update_data(wife_age=age_input)
        logging.info(f"User {message.from_user.id} entered wife age: {age_input}")
        await message.answer("Kim yozmoqda:", reply_markup=family_author_keyboard())
        await state.set_state(Form.FAMILY_AUTHOR)
    else:
        await message.answer("Iltimos, ayolning yoshini 18 yoshdan 60 yoshgacha bo'lgan raqamda kiriting.")


@dp.callback_query(F.data.startswith("author_"), Form.FAMILY_AUTHOR)
async def family_author_handler(callback: types.CallbackQuery, state: FSMContext):
    author = callback.data.split("_")[1]
    await state.update_data(author=author)
    logging.info(f"User {callback.from_user.id} chose family author: {author}")
    if author == "husband":
        await callback.message.edit_text("Tanlang:", reply_markup=family_husband_choice_keyboard())
        await state.set_state(Form.FAMILY_HUSBAND_CHOICE)
    elif author == "wife":
        await callback.message.edit_text("Tanlang:", reply_markup=family_wife_choice_keyboard())
        await state.set_state(Form.FAMILY_WIFE_CHOICE)
    await callback.answer()


@dp.callback_query(F.data.startswith("h_choice_"), Form.FAMILY_HUSBAND_CHOICE)
async def family_husband_choice_handler(callback: types.CallbackQuery, state: FSMContext):
    h_choice = callback.data.split("_")[2]
    await state.update_data(h_choice=h_choice)
    logging.info(f"User {callback.from_user.id} chose husband choice: {h_choice}")
    if h_choice == "mjm":
        await callback.message.edit_text("MJM tajribangizni tanlang:", reply_markup=mjm_experience_keyboard(is_female=False))
        await state.set_state(Form.MJM_EXPERIENCE)
    elif h_choice == "erkak":
        await callback.message.edit_text("Ayolning roziligi:", reply_markup=family_wife_agreement_keyboard())
        await state.set_state(Form.FAMILY_WIFE_AGREEMENT)
    await callback.answer()


@dp.callback_query(F.data.startswith("wife_agree_"), Form.FAMILY_WIFE_AGREEMENT)
async def family_wife_agreement_handler(callback: types.CallbackQuery, state: FSMContext):
    wife_agreement = callback.data.split("_")[2]
    await state.update_data(wife_agreement=wife_agreement)
    logging.info(f"User {callback.from_user.id} chose wife agreement: {wife_agreement}")
    await callback.message.edit_text(
        "Bu uchrashuvdan nimalarni kutyapsiz va sizga nimalar yoqadi(hohlayapsiz) \n\n Ko’rishish uchun sizda joy mavjudmi(batafsil yozing)??:")
    await state.set_state(Form.ABOUT)
    await callback.answer()


@dp.callback_query(F.data.startswith("w_choice_"), Form.FAMILY_WIFE_CHOICE)
async def family_wife_choice_handler(callback: types.CallbackQuery, state: FSMContext):
    w_choice = callback.data.split("_")[2]
    await state.update_data(w_choice=w_choice)
    logging.info(f"User {callback.from_user.id} chose wife choice: {w_choice}")
    if w_choice == "mjm_husband":
        await callback.message.edit_text("Erkakning roziligi:", reply_markup=family_husband_agreement_keyboard())
        await state.set_state(Form.FAMILY_HUSBAND_AGREEMENT)
    elif w_choice in ["mjm_strangers", "erkak"]:
        await callback.message.edit_text(
            "Bu uchrashuvdan nimalarni kutyapsiz va sizga nimalar yoqadi(hohlayapsiz) \n\n Ko’rishish uchun sizda joy mavjudmi(batafsil yozing)??:")
        await state.set_state(Form.ABOUT)
    await callback.answer()


@dp.callback_query(F.data.startswith("husband_agree_"), Form.FAMILY_HUSBAND_AGREEMENT)
async def family_husband_agreement_handler(callback: types.CallbackQuery, state: FSMContext):
    husband_agreement = callback.data.split("_")[2]
    await state.update_data(husband_agreement=husband_agreement)
    logging.info(f"User {callback.from_user.id} chose husband agreement: {husband_agreement}")
    await callback.message.edit_text(
        "Bu uchrashuvdan nimalarni kutyapsiz va sizga nimalar yoqadi(hohlayapsiz) \n\n Ko’rishish uchun sizda joy mavjudmi(batafsil yozing)??:")
    await state.set_state(Form.ABOUT)
    await callback.answer()


@dp.message(F.text, Form.ABOUT)
async def about_handler(message: types.Message, state: FSMContext):
    about_text = message.text.strip()
    await state.update_data(about=about_text)
    logging.info(f"User {message.from_user.id} entered about text.")

    data = await state.get_data()
    user = message.from_user

    await send_application_to_destinations(data, user)
    await message.answer("Arizangiz qabul qilindi. Tez orada siz bilan bog'lanamiz!")
    await state.clear()


@dp.message(F.chat.id.in_([ADMIN_USER_ID, ADMIN_GROUP_ID]), Command("reply"))
async def admin_initiate_reply_command(message: types.Message, state: FSMContext):
    # Bu buyruq faqat shaxsiy chatda ishlaydi, guruhda emas
    if message.chat.type != types.ChatType.PRIVATE:
        await message.answer("Bu buyruq faqat shaxsiy chatda ishlaydi.")
        return

    try:
        user_id_to_reply = int(message.text.split(" ", 1)[1].strip())
        await state.set_state(AdminState.REPLYING_TO_USER)
        await state.update_data(target_user_id=user_id_to_reply)
        await message.answer(f"Foydalanuvchi `{user_id_to_reply}` ga javob yozishingiz mumkin. "
                             "Suhbatni tugatish uchun /endreply buyrug'ini bosing.", parse_mode="Markdown")
        logging.info(f"Admin {message.from_user.id} initiated reply to user {user_id_to_reply}")
    except (IndexError, ValueError):
        await message.answer("Noto'g'ri format. Foydalanish: `/reply <user_id>`")


@dp.callback_query(F.data.startswith("admin_initiate_reply_"), F.chat.id.in_([ADMIN_USER_ID, ADMIN_GROUP_ID]))
async def admin_initiate_reply_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id_to_reply = int(callback.data.split("_")[-1])

    # Agar guruhda bo'lsa, shaxsiy chatda davom ettirishni so'raymiz
    if callback.message.chat.type != types.ChatType.PRIVATE:
        await callback.answer("Javob yozishni shaxsiy chatda davom ettiring.", show_alert=True)
        # Admins will get a message in their private chat
        try:
            builder = InlineKeyboardBuilder()
            builder.button(text="✉️ Javob yozishni boshlash", callback_data=f"admin_initiate_reply_private_{user_id_to_reply}")
            await bot.send_message(
                chat_id=callback.from_user.id,
                text=f"Foydalanuvchi `{user_id_to_reply}` ga javob yozish uchun quyidagi tugmani bosing "
                     "yoki shaxsiy chatda `/reply {user_id}` buyrug'ini ishlating:",
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Failed to send private reply initiation to admin {callback.from_user.id}: {e}")
        return

    await state.set_state(AdminState.REPLYING_TO_USER)
    await state.update_data(target_user_id=user_id_to_reply)
    await callback.message.edit_text(f"Foydalanuvchi `{user_id_to_reply}` ga javob yozishingiz mumkin. "
                                     "Suhbatni tugatish uchun /endreply buyrug'ini bosing.", parse_mode="Markdown")
    await callback.answer()
    logging.info(f"Admin {callback.from_user.id} initiated reply via callback to user {user_id_to_reply}")


@dp.callback_query(F.data.startswith("admin_initiate_reply_private_"), AdminState.REPLYING_TO_USER)
async def admin_initiate_reply_private_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id_to_reply = int(callback.data.split("_")[-1])
    await state.set_state(AdminState.REPLYING_TO_USER)
    await state.update_data(target_user_id=user_id_to_reply)
    await callback.message.edit_text(f"Foydalanuvchi `{user_id_to_reply}` ga javob yozishingiz mumkin. "
                                     "Suhbatni tugatish uchun /endreply buyrug'ini bosing.", parse_mode="Markdown")
    await callback.answer()
    logging.info(f"Admin {callback.from_user.id} initiated private reply via callback to user {user_id_to_reply}")


@dp.message(F.chat.id.in_([ADMIN_USER_ID, ADMIN_GROUP_ID]), AdminState.REPLYING_TO_USER)
async def admin_reply_to_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    if not target_user_id:
        await message.answer("Javob beriladigan foydalanuvchi topilmadi. Qayta urinib ko'ring yoki /start bosing.")
        await state.clear()
        return

    try:
        if message.text:
            await bot.send_message(target_user_id, message.text, parse_mode="Markdown")
            logging.info(f"Admin {message.from_user.id} replied text message to user {target_user_id}")
        elif message.photo:
            await bot.send_photo(target_user_id, message.photo[-1].file_id, caption=message.caption, parse_mode="Markdown")
            logging.info(f"Admin {message.from_user.id} replied photo message to user {target_user_id}")
        elif message.video:
            await bot.send_video(target_user_id, message.video.file_id, caption=message.caption, parse_mode="Markdown")
            logging.info(f"Admin {message.from_user.id} replied video message to user {target_user_id}")
        elif message.animation:
            await bot.send_animation(target_user_id, message.animation.file_id, caption=message.caption, parse_mode="Markdown")
            logging.info(f"Admin {message.from_user.id} replied animation (GIF) message to user {target_user_id}")
        elif message.sticker:
            await bot.send_sticker(target_user_id, message.sticker.file_id)
            logging.info(f"Admin {message.from_user.id} replied sticker message to user {target_user_id}")
        elif message.document:
            await bot.send_document(target_user_id, message.document.file_id, caption=message.caption, parse_mode="Markdown")
            logging.info(f"Admin {message.from_user.id} replied document message to user {target_user_id}")
        elif message.audio:
            await bot.send_audio(target_user_id, message.audio.file_id, caption=message.caption, parse_mode="Markdown")
            logging.info(f"Admin {message.from_user.id} replied audio message to user {target_user_id}")
        elif message.voice:
            await bot.send_voice(target_user_id, message.voice.file_id, caption=message.caption, parse_mode="Markdown")
            logging.info(f"Admin {message.from_user.id} replied voice message to user {target_user_id}")
        else:
            await message.answer("Kechirasiz, bu turdagi xabarni hozircha yubora olmayman.")
            logging.warning(
                f"Admin {message.from_user.id} tried to reply with unhandled message type to user {target_user_id}")
            return
        await message.answer("Xabar foydalanuvchiga yuborildi.")
    except Exception as e:
        logging.error(f"Error replying to user {target_user_id} from admin {message.from_user.id}: {e}")
        await message.answer(f"Xabar yuborishda xatolik yuz berdi: {e}")


@dp.message(Command("endreply"), F.chat.id.in_([ADMIN_USER_ID, ADMIN_GROUP_ID]))
async def admin_end_reply_command(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == AdminState.REPLYING_TO_USER:
        data = await state.get_data()
        target_user_id = data.get("target_user_id")
        await state.clear()
        await message.answer(f"Foydalanuvchi `{target_user_id}` bilan suhbat tugatildi.", parse_mode="Markdown")
        logging.info(f"Admin {message.from_user.id} ended reply session with user {target_user_id}")
    else:
        await message.answer("Siz hozir suhbat rejimida emassiz.")


@dp.message(F.chat.id.not_in([ADMIN_USER_ID, ADMIN_GROUP_ID, CHANNEL_ID]))
async def forward_to_admin(message: types.Message):
    user = message.from_user
    user_info = (
        f"**Yangi xabar:**\n"
        f"Foydalanuvchi: [{user.full_name}](tg://user?id={user.id})"
    )
    if user.username:
        user_info += f" (@{user.username})"
    user_info += f" (ID: `{user.id}`)\n"

    builder = InlineKeyboardBuilder()
    builder.button(text="✉️ Javob yozish", callback_data=f"admin_initiate_reply_{user.id}")
    reply_markup = builder.as_markup()

    try:
        if message.text:
            text_to_send = f"{user_info}\n\n*Matn xabar:*\n{message.text}"
            await bot.send_message(ADMIN_USER_ID, text_to_send, reply_markup=reply_markup, parse_mode="Markdown")
            await bot.send_message(ADMIN_GROUP_ID, text_to_send, reply_markup=reply_markup, parse_mode="Markdown")
            logging.info(f"Forwarded text message from user {user.id}")
        elif message.photo:
            caption_text = f"{user_info}\n\n*Rasm xabar:*\n{message.caption if message.caption else ''}"
            await bot.send_photo(ADMIN_USER_ID, message.photo[-1].file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            await bot.send_photo(ADMIN_GROUP_ID, message.photo[-1].file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            logging.info(f"Forwarded photo message from user {user.id}")
        elif message.video:
            caption_text = f"{user_info}\n\n*Video xabar:*\n{message.caption if message.caption else ''}"
            await bot.send_video(ADMIN_USER_ID, message.video.file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            await bot.send_video(ADMIN_GROUP_ID, message.video.file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            logging.info(f"Forwarded video message from user {user.id}")
        elif message.animation:
            caption_text = f"{user_info}\n\n*GIF xabar:*\n{message.caption if message.caption else ''}"
            await bot.send_animation(ADMIN_USER_ID, message.animation.file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            await bot.send_animation(ADMIN_GROUP_ID, message.animation.file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            logging.info(f"Forwarded animation (GIF) message from user {user.id}")
        elif message.sticker:
            text_to_send = f"{user_info}\n\n*Stiker xabar:*"
            await bot.send_sticker(ADMIN_USER_ID, message.sticker.file_id, reply_markup=reply_markup)
            await bot.send_message(ADMIN_USER_ID, text_to_send, parse_mode="Markdown")
            await bot.send_sticker(ADMIN_GROUP_ID, message.sticker.file_id, reply_markup=reply_markup)
            await bot.send_message(ADMIN_GROUP_ID, text_to_send, parse_mode="Markdown")
            logging.info(f"Forwarded sticker message from user {user.id}")
        elif message.document:
            caption_text = f"{user_info}\n\n*Hujjat xabar:*\n{message.caption if message.caption else ''}"
            await bot.send_document(ADMIN_USER_ID, message.document.file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            await bot.send_document(ADMIN_GROUP_ID, message.document.file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            logging.info(f"Forwarded document message from user {user.id}")
        elif message.audio:
            caption_text = f"{user_info}\n\n*Audio xabar:*\n{message.caption if message.caption else ''}"
            await bot.send_audio(ADMIN_USER_ID, message.audio.file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            await bot.send_audio(ADMIN_GROUP_ID, message.audio.file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            logging.info(f"Forwarded audio message from user {user.id}")
        elif message.voice:
            caption_text = f"{user_info}\n\n*Ovozli xabar:*\n{message.caption if message.caption else ''}"
            await bot.send_voice(ADMIN_USER_ID, message.voice.file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            await bot.send_voice(ADMIN_GROUP_ID, message.voice.file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            logging.info(f"Forwarded voice message from user {user.id}")
        else:
            await bot.send_message(ADMIN_USER_ID, f"{user_info}\n\n*Noma'lum turdagi xabar qabul qilindi.*", reply_markup=reply_markup, parse_mode="Markdown")
            await bot.send_message(ADMIN_GROUP_ID, f"{user_info}\n\n*Noma'lum turdagi xabar qabul qilindi.*", reply_markup=reply_markup, parse_mode="Markdown")
            logging.warning(f"Forwarded unhandled message type from user {user.id}")
    except Exception as e:
        logging.error(f"Error forwarding message from user {user.id} to admin/group: {e}")
        # Optionally, notify the admin about the forwarding error
        try:
            await bot.send_message(ADMIN_USER_ID,
                                   f"⚠️ Ogohlantirish: Foydalanuvchi `{user.id}` dan xabar yuborishda xatolik: {e}",
                                   parse_mode="Markdown")
        except Exception as e_admin:
            logging.error(f"Failed to send error notification to admin user: {e_admin}")


async def main():
    # Webhook sozlamalari
    dispatcher = dp
    bot_instance = bot
    await bot_instance.set_webhook(WEBHOOK_URL)

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot_instance,
        secret_token=TOKEN  # set secret_token to avoid unwanted requests
    )
    webhook_requests_handler.register(app, "/webhook")
    setup_application(app, dispatcher, bot=bot_instance)

    # Register handlers
    dp.message.register(start_handler, Command("start"))
    dp.callback_query.register(cancel_handler, F.data == "cancel")
    dp.callback_query.register(about_bot_handler, F.data == "about_bot")
    dp.callback_query.register(back_handler, F.data.startswith("back_"))
    dp.callback_query.register(gender_handler, F.data.startswith("gender_"), Form.CHOOSE_GENDER)
    dp.message.register(voice_message_handler, F.voice, Form.WAITING_FOR_VOICE_MESSAGE) # Register new voice handler
    dp.callback_query.register(viloyat_handler, F.data.startswith("vil_"), Form.VILOYAT)
    dp.callback_query.register(tuman_handler, F.data.startswith("tum_"), Form.TUMAN)
    dp.callback_query.register(age_female_handler, F.data.startswith("age_"), Form.AGE_FEMALE)
    dp.callback_query.register(female_choice_handler, F.data.startswith("choice_"), Form.FEMALE_CHOICE)
    dp.message.register(jmj_age_handler, F.text, Form.JMJ_AGE)
    dp.message.register(jmj_details_handler, F.text, Form.JMJ_DETAILS)
    dp.callback_query.register(pose_woman_handler, F.data.startswith("pose_"), Form.POSE_WOMAN)
    dp.callback_query.register(mjm_experience_handler, F.data.startswith("mjm_exp_family_"), Form.MJM_EXPERIENCE)
    dp.callback_query.register(mjm_experience_female_handler, F.data.startswith("mjm_exp_female_"), Form.MJM_EXPERIENCE_FEMALE)
    dp.message.register(family_husband_age_handler, F.text, Form.FAMILY_HUSBAND_AGE)
    dp.message.register(family_wife_age_handler, F.text, Form.FAMILY_WIFE_AGE)
    dp.callback_query.register(family_author_handler, F.data.startswith("author_"), Form.FAMILY_AUTHOR)
    dp.callback_query.register(family_husband_choice_handler, F.data.startswith("h_choice_"), Form.FAMILY_HUSBAND_CHOICE)
    dp.callback_query.register(family_wife_agreement_handler, F.data.startswith("wife_agree_"), Form.FAMILY_WIFE_AGREEMENT)
    dp.callback_query.register(family_wife_choice_handler, F.data.startswith("w_choice_"), Form.FAMILY_WIFE_CHOICE)
    dp.callback_query.register(family_husband_agreement_handler, F.data.startswith("husband_agree_"), Form.FAMILY_HUSBAND_AGREEMENT)
    dp.message.register(about_handler, F.text, Form.ABOUT)

    # Admin reply handlers
    dp.message.register(admin_initiate_reply_command, Command("reply"))
    dp.callback_query.register(admin_initiate_reply_callback, F.data.startswith("admin_initiate_reply_"))
    dp.callback_query.register(admin_initiate_reply_private_callback, F.data.startswith("admin_initiate_reply_private_"), AdminState.REPLYING_TO_USER)
    dp.message.register(admin_reply_to_user, AdminState.REPLYING_TO_USER)
    dp.message.register(admin_end_reply_command, Command("endreply"))

    # Forwarding unhandled messages to admin
    dp.message.register(forward_to_admin)

    # Start the application
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


def setup_application(app, dispatcher, *, bot):
    # This function is usually used for webhook setup in aiogram.
    # It sets up the dispatcher to handle incoming webhook updates.
    # The SimpleRequestHandler already registers the handler.
    # We mainly need to ensure the bot and dispatcher are correctly linked.
    pass


if __name__ == "__main__":
    logging.info("Starting bot in webhook mode...")
    # As per aiogram documentation and common deployment practices for webhooks,
    # the web server should be run directly.
    # asyncio.run(main()) # No need to run this as web.run_app is blocking
    # We call main() directly here, which will start the aiohttp web server.
    # This is for local testing or environments where aiohttp is expected to manage the event loop.
    # In some production environments (e.g., Render.com), `web.run_app` might not be
    # directly called if the platform handles the ASGI server.
    # However, for aiogram webhooks, `web.run_app` is standard.
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main())
