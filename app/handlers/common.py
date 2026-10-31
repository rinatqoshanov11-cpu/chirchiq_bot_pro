"""Common handlers for main menu."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import UserService, ApartmentService
from app.keyboards import MainKeyboard
from app.utils import format_apartment_card, get_logger
from app.models.apartment import ApartmentType

logger = get_logger(__name__)
router = Router()


@router.message(F.text == "🏠 Kvartira qidirish")
async def search_apartments_menu(message: Message, state: FSMContext, session: AsyncSession):
    """Show search menu."""
    await state.clear()

    await message.answer(
        "🏠 Qaysi turdagi kvartira qidiryapsiz?",
        reply_markup=MainKeyboard.get_search_menu()
    )


@router.message(F.text == "🔑 Ijaraga")
async def search_rent(message: Message, session: AsyncSession):
    """Search apartments for rent."""
    await _search_and_send(message, session, ApartmentType.RENT, "🔑 Ijaraga beriladigan kvartiralar:")


@router.message(F.text == "💰 Sotib olish")
async def search_sale(message: Message, session: AsyncSession):
    """Search apartments for sale."""
    await _search_and_send(message, session, ApartmentType.SALE, "💰 Sotiladigan kvartiralar:")


@router.message(F.text == "📋 Barcha e'lonlar")
async def search_all(message: Message, session: AsyncSession):
    """Search all apartments."""
    await _search_and_send(message, session, None, "📋 Barcha e'lonlar:")


@router.message(F.text == "🔙 Orqaga")
async def back_to_main(message: Message, state: FSMContext):
    """Return to main menu."""
    await state.clear()
    await message.answer(
        "🏠 Asosiy menyu:",
        reply_markup=MainKeyboard.get_main_menu()
    )


@router.message(F.text == "📋 Mening e'lonlarim")
async def my_apartments(message: Message, session: AsyncSession):
    """Show user's apartments."""
    user = await UserService.get_by_telegram_id(session, message.from_user.id)

    if not user:
        await message.answer(
            "❌ E'lonlaringizni ko'rish uchun avval ro'yxatdan o'tishingiz kerak.\n\n"
            "📝 'Ro'yxatdan o'tish' tugmasini bosing.",
            reply_markup=MainKeyboard.get_main_menu(is_registered=False)
        )
        return

    apartments = await ApartmentService.get_user_apartments(session, user.id)

    if not apartments:
        await message.answer(
            "😔 Sizda hali e'lonlar yo'q.\n\n"
            "E'lon qo'shish uchun '➕ E'lon qo'shish' tugmasini bosing.",
            reply_markup=MainKeyboard.get_main_menu(is_registered=True)
        )
        return

    await message.answer(f"📋 Sizning {len(apartments)} ta e'loningiz:")

    from app.keyboards import InlineKeyboards

    for apt in apartments:
        text = format_apartment_card(apt, show_contact=True)
        text += f"\n\n📊 Status: {apt.status_emoji} {apt.status.value.title()}"

        if apt.photos:
            await message.answer_photo(
                photo=apt.photos[0],
                caption=text
            )
        else:
            await message.answer(text)


@router.message(F.text == "⚙️ Sozlamalar")
async def settings(message: Message, session: AsyncSession):
    """Show user settings."""
    user = await UserService.get_by_telegram_id(session, message.from_user.id)

    if not user:
        await message.answer(
            "❌ Sozlamalarni ko'rish uchun avval ro'yxatdan o'tishingiz kerak.\n\n"
            "📝 'Ro'yxatdan o'tish' tugmasini bosing.",
            reply_markup=MainKeyboard.get_main_menu(is_registered=False)
        )
        return

    from app.utils import format_user_info

    text = format_user_info(user)
    text += "\n\nMa'lumotlarni o'zgartirish uchun admin bilan bog'laning."

    await message.answer(text, reply_markup=MainKeyboard.get_main_menu(is_registered=True))


PAGE_SIZE = 3

# Short codes for callback_data: "more_<type>_<offset>"
_TYPE_TO_CODE = {ApartmentType.RENT: "rent", ApartmentType.SALE: "sale", None: "all"}
_CODE_TO_TYPE = {code: apt_type for apt_type, code in _TYPE_TO_CODE.items()}


@router.callback_query(F.data.startswith("more_"))
async def show_more_apartments(callback: CallbackQuery, session: AsyncSession):
    """Show the next page of listings when '⬇️ Yana' is pressed."""
    try:
        _, type_code, offset_text = callback.data.split("_")
        apartment_type = _CODE_TO_TYPE[type_code]
        offset = max(0, int(offset_text))
    except (ValueError, KeyError):
        await callback.answer("❌ Xatolik. Qaytadan qidiring.", show_alert=True)
        return

    await callback.answer()

    # Remove the old "Yana" button so it can't be pressed twice
    try:
        await callback.message.delete()
    except Exception:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

    await _search_and_send(callback.message, session, apartment_type, header=None, offset=offset)


async def _search_and_send(
    message: Message,
    session: AsyncSession,
    apartment_type: ApartmentType | None,
    header: str | None,
    offset: int = 0
):
    """Send one page (PAGE_SIZE) of listings, then a '⬇️ Yana' button if more remain."""
    total = await ApartmentService.count_search(session, apartment_type=apartment_type)
    apartments = await ApartmentService.search_apartments(
        session=session,
        apartment_type=apartment_type,
        limit=PAGE_SIZE,
        offset=offset
    )

    if not apartments:
        if offset == 0:
            await message.answer(
                "😔 Hozircha e'lonlar topilmadi.",
                reply_markup=MainKeyboard.get_main_menu()
            )
        else:
            await message.answer("✅ Boshqa e'lon qolmadi.")
        return

    if header:
        await message.answer(f"{header}\n\nTopildi: {total} ta e'lon")

    from app.keyboards import InlineKeyboards

    # Increment view counts once for the whole page
    for apt in apartments:
        apt.view_count += 1
    await session.commit()

    for apt in apartments:
        text = format_apartment_card(apt, show_contact=False)
        keyboard = InlineKeyboards.get_apartment_actions(apt.id)

        if apt.photos:
            try:
                await message.answer_photo(
                    photo=apt.photos[0],
                    caption=text,
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Error sending photo: {e}")
                await message.answer(text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)

    # Footer: progress + "Yana" button (only if more listings remain)
    shown = offset + len(apartments)
    if shown < total:
        next_count = min(PAGE_SIZE, total - shown)
        builder = InlineKeyboardBuilder()
        builder.button(
            text=f"⬇️ Yana {next_count} ta e'lon",
            callback_data=f"more_{_TYPE_TO_CODE[apartment_type]}_{shown}"
        )
        await message.answer(
            f"📄 Ko'rsatildi: {shown} / {total}",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(f"✅ Barcha e'lonlar ko'rsatildi ({total} ta).")
