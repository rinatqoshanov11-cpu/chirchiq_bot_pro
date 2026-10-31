"""Apartment handlers."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.states import ApartmentStates
from app.services import UserService, ApartmentService
from app.keyboards import MainKeyboard, ApartmentKeyboard, InlineKeyboards
from app.models.apartment import ApartmentType
from app.utils import format_apartment_card, format_price, get_logger
from config import settings

logger = get_logger(__name__)
router = Router()


@router.message(F.text == "➕ E'lon qo'shish")
async def start_add_apartment(message: Message, state: FSMContext, session: AsyncSession):
    """Start adding new apartment."""
    user = await UserService.get_by_telegram_id(session, message.from_user.id)

    if not user or not user.is_registered:
        await message.answer(
            "❌ E'lon qo'shish uchun avval ro'yxatdan o'tishingiz kerak.\n\n"
            "📝 'Ro'yxatdan o'tish' tugmasini bosing.",
            reply_markup=MainKeyboard.get_main_menu(is_registered=False)
        )
        return

    if user.is_blocked:
        await message.answer("❌ Siz bloklangansiz. Admin bilan bog'laning.")
        return

    await state.clear()
    await state.update_data(owner_id=user.id, phone_number=user.phone_number)

    await message.answer(
        "🏠 Yangi e'lon qo'shish\n\n"
        "Qaysi turdagi kvartira?",
        reply_markup=ApartmentKeyboard.get_apartment_type()
    )
    await state.set_state(ApartmentStates.waiting_for_type)


@router.message(ApartmentStates.waiting_for_type)
async def process_apartment_type(message: Message, state: FSMContext):
    """Process apartment type."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ E'lon qo'shish bekor qilindi.",
            reply_markup=MainKeyboard.get_main_menu()
        )
        return

    apartment_type = None
    if message.text == "🔑 Ijaraga berish":
        apartment_type = ApartmentType.RENT
    elif message.text == "💰 Sotish":
        apartment_type = ApartmentType.SALE

    if not apartment_type:
        await message.answer("❌ Iltimos, tugmalardan birini tanlang:")
        return

    await state.update_data(type=apartment_type)
    await message.answer(
        "🚪 Necha xonali kvartira?",
        reply_markup=ApartmentKeyboard.get_rooms_keyboard()
    )
    await state.set_state(ApartmentStates.waiting_for_rooms)


@router.message(ApartmentStates.waiting_for_rooms)
async def process_rooms(message: Message, state: FSMContext):
    """Process number of rooms."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.get_main_menu())
        return

    rooms = message.text
    if rooms == "6+":
        rooms = 6
    else:
        try:
            rooms = int(rooms)
            if rooms < 1 or rooms > 10:
                raise ValueError
        except ValueError:
            await message.answer("❌ Noto'g'ri qiymat. Iltimos, 1 dan 6+ gacha raqam kiriting:")
            return

    await state.update_data(rooms=rooms)
    await message.answer(
        "📍 Kvartira manzilini kiriting:\n"
        "(Masalan: Chirchiq, Mustaqillik ko'chasi, 12-uy, 5-kvartira)",
        reply_markup=MainKeyboard.get_cancel_keyboard()
    )
    await state.set_state(ApartmentStates.waiting_for_address)


@router.message(ApartmentStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    """Process apartment address."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.get_main_menu())
        return

    if not message.text or len(message.text) < 5:
        await message.answer("❌ Iltimos, to'liq manzilni kiriting (kamida 5 ta harf):")
        return

    await state.update_data(address=message.text.strip())

    data = await state.get_data()
    price_example = "1000000" if data.get('type') == ApartmentType.RENT else "50000000"

    await message.answer(
        f"💵 Narxini kiriting (so'm):\n"
        f"(Masalan: {price_example})",
        reply_markup=MainKeyboard.get_cancel_keyboard()
    )
    await state.set_state(ApartmentStates.waiting_for_price)


@router.message(ApartmentStates.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    """Process apartment price."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.get_main_menu())
        return

    try:
        price = int(message.text.replace(" ", "").replace(",", ""))
        if price < 1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Noto'g'ri narx. Iltimos, faqat raqam kiriting:")
        return

    await state.update_data(price=price)
    await message.answer(
        "📐 Kvartira maydonini kiriting (m²):\n"
        "(Masalan: 65)",
        reply_markup=MainKeyboard.get_skip_cancel_keyboard()
    )
    await state.set_state(ApartmentStates.waiting_for_area)


@router.message(ApartmentStates.waiting_for_area)
async def process_area(message: Message, state: FSMContext):
    """Process apartment area."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.get_main_menu())
        return

    if message.text == "⏩ O'tkazib yuborish":
        area = None
    else:
        try:
            area = float(message.text.replace(",", "."))
            if area < 1:
                raise ValueError
        except ValueError:
            await message.answer("❌ Noto'g'ri maydon. Iltimos, raqam kiriting yoki o'tkazib yuboring:")
            return

    await state.update_data(area=area)
    await message.answer(
        "🏢 Qavat raqamini kiriting:\n"
        "(Masalan: 5/9 yoki faqat 5)",
        reply_markup=MainKeyboard.get_skip_cancel_keyboard()
    )
    await state.set_state(ApartmentStates.waiting_for_floor)


@router.message(ApartmentStates.waiting_for_floor)
async def process_floor(message: Message, state: FSMContext):
    """Process floor number."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.get_main_menu())
        return

    floor = None
    total_floors = None

    if message.text != "⏩ O'tkazib yuborish":
        try:
            if "/" in message.text:
                parts = message.text.split("/")
                floor = int(parts[0].strip())
                total_floors = int(parts[1].strip())
            else:
                floor = int(message.text.strip())
        except (ValueError, IndexError):
            await message.answer("❌ Noto'g'ri format. Masalan: 5/9 yoki 5\nQaytadan kiriting yoki o'tkazib yuboring:")
            return

    await state.update_data(floor=floor, total_floors=total_floors)
    await message.answer(
        "📝 Qo'shimcha ma'lumot kiriting:\n"
        "(Remont, mebel, jihozlar va hokazo)",
        reply_markup=MainKeyboard.get_skip_cancel_keyboard()
    )
    await state.set_state(ApartmentStates.waiting_for_description)


@router.message(ApartmentStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Process apartment description."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.get_main_menu())
        return

    description = None if message.text == "⏩ O'tkazib yuborish" else message.text.strip()

    if description and len(description) > settings.max_description_length:
        await message.answer(
            f"❌ Tavsif juda uzun. Maksimal {settings.max_description_length} ta belgi.\n"
            f"Qaytadan kiriting:"
        )
        return

    await state.update_data(description=description, photos=[])
    await message.answer(
        f"📸 Kvartira rasmlarini yuboring (maksimal {settings.photos_per_ad} ta):\n\n"
        "Rasmlarni yuborib bo'lgach '✅ Tayyor' tugmasini bosing.",
        reply_markup=ApartmentKeyboard.get_photos_done_keyboard()
    )
    await state.set_state(ApartmentStates.waiting_for_photos)


@router.message(ApartmentStates.waiting_for_photos, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Process apartment photos."""
    data = await state.get_data()
    photos = data.get('photos', [])

    if len(photos) >= settings.photos_per_ad:
        await message.answer(f"❌ Maksimal {settings.photos_per_ad} ta rasm yuklash mumkin!")
        return

    photo = message.photo[-1].file_id
    photos.append(photo)
    await state.update_data(photos=photos)

    await message.answer(f"✅ Rasm qo'shildi ({len(photos)}/{settings.photos_per_ad})")


@router.message(ApartmentStates.waiting_for_photos, F.text == "✅ Tayyor")
async def photos_done(message: Message, state: FSMContext):
    """Finalize photos and show confirmation."""
    data = await state.get_data()

    if not data.get('photos'):
        await message.answer("❌ Kamida 1 ta rasm yuklang!")
        return

    # Show preview
    type_text = "🔑 Ijaraga berish" if data['type'] == ApartmentType.RENT else "💰 Sotish"

    preview = f"📋 E'lon ko'rinishi:\n\n"
    preview += f"Turi: {type_text}\n"
    preview += f"🚪 Xonalar: {data['rooms']}\n"

    if data.get('area'):
        preview += f"📐 Maydon: {data['area']} m²\n"

    if data.get('floor'):
        floor_text = f"{data['floor']}/{data['total_floors']}" if data.get('total_floors') else str(data['floor'])
        preview += f"🏢 Qavat: {floor_text}\n"

    preview += f"📍 Manzil: {data['address']}\n"
    preview += f"💵 Narx: {format_price(data['price'])}\n"

    if data.get('description'):
        preview += f"\n📝 {data['description']}\n"

    preview += f"\n📸 Rasmlar: {len(data['photos'])} ta"

    await message.answer_photo(
        photo=data['photos'][0],
        caption=preview,
        reply_markup=ApartmentKeyboard.get_confirm_keyboard()
    )
    await state.set_state(ApartmentStates.confirm_apartment)


@router.message(ApartmentStates.waiting_for_photos)
async def invalid_photo_input(message: Message):
    """Handle invalid input during photo upload."""
    if message.text == "❌ Bekor qilish":
        await message.reply(
            "❌ Bekor qilindi.",
            reply_markup=MainKeyboard.get_main_menu()
        )
        return

    await message.answer("❌ Iltimos, rasm yuboring yoki '✅ Tayyor' tugmasini bosing.")


@router.message(ApartmentStates.confirm_apartment)
async def confirm_apartment(message: Message, state: FSMContext, session: AsyncSession):
    """Confirm and save apartment."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.get_main_menu())
        return

    if message.text == "✏️ Tahrirlash":
        await message.answer(
            "✏️ Tahrirlamoqchisiz?\n"
            "Afsuski, hozircha bu funksiya mavjud emas.\n"
            "Iltimos, yangi e'lon qo'shing.",
            reply_markup=MainKeyboard.get_main_menu()
        )
        await state.clear()
        return

    if message.text != "✅ Tasdiqlash":
        await message.answer("❌ Iltimos, tugmalardan birini tanlang:")
        return

    data = await state.get_data()

    try:
        # Create apartment
        apartment = await ApartmentService.create_apartment(
            session=session,
            owner_id=data['owner_id'],
            apartment_type=data['type'],
            rooms=data['rooms'],
            address=data['address'],
            price=data['price'],
            phone_number=data['phone_number'],
            area=data.get('area'),
            floor=data.get('floor'),
            total_floors=data.get('total_floors'),
            description=data.get('description'),
            photos=data.get('photos', []),
            source='manual'
        )

        await state.clear()

        type_text = "ijaraga berish" if apartment.type == ApartmentType.RENT else "sotish"

        await message.answer(
            f"✅ E'lon muvaffaqiyatli qo'shildi!\n\n"
            f"🆔 E'lon ID: #{apartment.id}\n"
            f"🏠 Turi: {type_text}\n"
            f"🚪 Xonalar: {apartment.rooms}\n"
            f"💵 Narx: {format_price(apartment.price)}\n\n"
            f"⏳ E'lon admin tomonidan tasdiqlanganidan keyin ko'rsatiladi.",
            reply_markup=MainKeyboard.get_main_menu()
        )

        logger.info(f"New apartment added: #{apartment.id} by user {data['owner_id']}")

        # Notify admins
        await notify_admins_new_apartment(message.bot, session, apartment)

    except Exception as e:
        logger.error(f"Error creating apartment: {e}")
        await message.answer(
            "❌ E'lon qo'shishda xatolik yuz berdi. Qaytadan urinib ko'ring.",
            reply_markup=MainKeyboard.get_main_menu()
        )
        await state.clear()


@router.callback_query(F.data.startswith("contact_"))
async def show_contact(callback: CallbackQuery, session: AsyncSession):
    """Show apartment contact information."""
    apartment_id = int(callback.data.split("_")[1])

    apartment = await ApartmentService.get_by_id(session, apartment_id)

    if not apartment:
        await callback.answer("❌ E'lon topilmadi.", show_alert=True)
        return

    # Increment contact count
    apartment.contact_count += 1
    await session.commit()

    contact_text = f"📞 Bog'lanish ma'lumotlari:\n\n"
    contact_text += f"📱 Telefon: {apartment.phone_number}\n"

    if apartment.contact_name:
        contact_text += f"👤 Ism: {apartment.contact_name}\n"

    await callback.answer(contact_text, show_alert=True)


async def notify_admins_new_apartment(bot, session: AsyncSession, apartment):
    """Notify admins about new apartment."""
    from config import settings

    admin_ids = settings.admin_ids

    if not admin_ids:
        return

    type_text = "Ijaraga" if apartment.type == ApartmentType.RENT else "Sotish"

    text = f"🔔 Yangi e'lon kutmoqda:\n\n"
    text += f"🆔 ID: #{apartment.id}\n"
    text += f"Turi: {type_text}\n"
    text += f"Xonalar: {apartment.rooms}\n"
    text += f"Manzil: {apartment.address}\n"
    text += f"Narx: {format_price(apartment.price)}\n"

    keyboard = InlineKeyboards.get_apartment_actions(
        apartment.id,
        show_admin=True,
        is_pending=True
    )

    for admin_id in admin_ids:
        try:
            if apartment.photos:
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=apartment.photos[0],
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    reply_markup=keyboard
                )
        except Exception as e:
            logger.error(f"Error notifying admin {admin_id}: {e}")
