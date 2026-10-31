"""Registration handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from app.states import RegistrationStates
from app.services import UserService
from app.keyboards import MainKeyboard
from app.utils import validate_phone_number, get_logger

logger = get_logger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    """Handle /start command."""
    telegram_id = message.from_user.id
    await state.clear()

    # Check if user is already registered
    user = await UserService.get_by_telegram_id(session, telegram_id)

    if user and user.is_registered:
        await message.answer(
            f"👋 Xush kelibsiz, {user.full_name}!\n\n"
            "🏠 Chirchiq shahri kvartira ijarasi va sotish boti.\n\n"
            "📱 Kvartiralarni ko'rish uchun 'Kvartira qidirish' tugmasini bosing.\n"
            "➕ E'lon qo'shish uchun 'E'lon qo'shish' tugmasini bosing.",
            reply_markup=MainKeyboard.get_main_menu(is_registered=True)
        )
        return

    # Show main menu without registration
    await message.answer(
        "👋 Xush kelibsiz!\n\n"
        "🏠 Chirchiq shahri kvartira ijarasi va sotish boti.\n\n"
        "📱 Kvartiralarni darhol ko'rishingiz mumkin - 'Kvartira qidirish' tugmasini bosing.\n\n"
        "➕ E'lon qo'shmoqchi bo'lsangiz, avval 'Ro'yxatdan o'tish' tugmasini bosing.",
        reply_markup=MainKeyboard.get_main_menu(is_registered=False)
    )


@router.message(F.text == "📝 Ro'yxatdan o'tish")
async def start_registration(message: Message, state: FSMContext, session: AsyncSession):
    """Start registration process."""
    telegram_id = message.from_user.id

    # Check if already registered
    user = await UserService.get_by_telegram_id(session, telegram_id)
    if user and user.is_registered:
        await message.answer(
            "✅ Siz allaqachon ro'yxatdan o'tgansiz!",
            reply_markup=MainKeyboard.get_main_menu(is_registered=True)
        )
        return

    await message.answer(
        "📝 Ro'yxatdan o'tish jarayoni boshlanadi.\n\n"
        "Ism-familiyangizni kiriting:",
        reply_markup=MainKeyboard.get_cancel_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_full_name)


@router.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    """Process full name input."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Ro'yxatdan o'tish bekor qilindi.\n"
            "Qaytadan boshlash uchun /start ni bosing.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if not message.text or len(message.text) < 3:
        await message.answer("❌ Iltimos, to'liq ism-familiyangizni kiriting (kamida 3 ta harf):")
        return

    await state.update_data(full_name=message.text.strip())
    await message.answer(
        "📱 Telefon raqamingizni kiriting yoki tugmani bosing:\n"
        "(Masalan: +998901234567)",
        reply_markup=MainKeyboard.get_phone_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Process phone number from contact."""
    phone = message.contact.phone_number
    validated_phone = validate_phone_number(phone)

    if not validated_phone:
        await message.answer(
            "❌ Noto'g'ri telefon raqam. Iltimos, qaytadan kiriting:",
            reply_markup=MainKeyboard.get_phone_keyboard()
        )
        return

    await state.update_data(phone_number=validated_phone)
    await message.answer(
        "📍 Manzilingizni kiriting:\n"
        "(Masalan: Chirchiq shahar, Mustaqillik ko'chasi, 25-uy)",
        reply_markup=MainKeyboard.get_cancel_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_address)


@router.message(RegistrationStates.waiting_for_phone)
async def process_phone_text(message: Message, state: FSMContext):
    """Process phone number from text."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Ro'yxatdan o'tish bekor qilindi.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if not message.text:
        await message.answer("❌ Iltimos, telefon raqamingizni kiriting:")
        return

    validated_phone = validate_phone_number(message.text)

    if not validated_phone:
        await message.answer(
            "❌ Noto'g'ri telefon raqam formati.\n"
            "To'g'ri format: +998901234567 yoki 998901234567\n\n"
            "Qaytadan kiriting:",
            reply_markup=MainKeyboard.get_phone_keyboard()
        )
        return

    await state.update_data(phone_number=validated_phone)
    await message.answer(
        "📍 Manzilingizni kiriting:\n"
        "(Masalan: Chirchiq shahar, Mustaqillik ko'chasi, 25-uy)",
        reply_markup=MainKeyboard.get_cancel_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_address)


@router.message(RegistrationStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext, session: AsyncSession):
    """Process address and complete registration."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Ro'yxatdan o'tish bekor qilindi.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if not message.text or len(message.text) < 5:
        await message.answer("❌ Iltimos, to'liq manzilingizni kiriting (kamida 5 ta harf):")
        return

    # Get all registration data
    data = await state.get_data()

    try:
        # Create user in database
        user = await UserService.create_user(
            session=session,
            telegram_id=message.from_user.id,
            full_name=data['full_name'],
            phone_number=data['phone_number'],
            address=message.text.strip(),
            username=message.from_user.username
        )

        await state.clear()

        await message.answer(
            f"✅ Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!\n\n"
            f"👤 Ism: {user.full_name}\n"
            f"📱 Telefon: {user.phone_number}\n"
            f"📍 Manzil: {user.address}\n\n"
            f"Endi siz e'lon qo'shishingiz va barcha imkoniyatlardan foydalanishingiz mumkin!",
            reply_markup=MainKeyboard.get_main_menu(is_registered=True)
        )

        logger.info(f"New user registered: {user.telegram_id} - {user.full_name}")

    except Exception as e:
        logger.error(f"Registration error: {e}")
        await message.answer(
            "❌ Ro'yxatdan o'tishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.\n"
            "/start ni bosing.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
