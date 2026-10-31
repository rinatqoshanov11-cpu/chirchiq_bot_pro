"""Admin handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import UserService, ApartmentService
from app.keyboards import InlineKeyboards, MainKeyboard
from app.models.apartment import ApartmentStatus
from app.utils import format_apartment_card, format_user_info, get_logger

logger = get_logger(__name__)
router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message, session: AsyncSession):
    """Show admin panel."""
    if not await UserService.is_admin(session, message.from_user.id):
        await message.answer("❌ Sizda admin huquqlari yo'q.")
        return

    stats = await ApartmentService.get_statistics(session)
    user_count = await UserService.get_user_count(session)

    text = f"🔐 Admin Panel\n\n"
    text += f"📊 Statistika:\n"
    text += f"👥 Foydalanuvchilar: {user_count}\n"
    text += f"🏠 Jami e'lonlar: {stats['total']}\n"
    text += f"✅ Aktiv: {stats['active']}\n"
    text += f"⏳ Kutilayotgan: {stats['pending']}\n"
    text += f"🔑 Ijaraga: {stats['rent']}\n"
    text += f"💰 Sotish: {stats['sale']}\n"
    text += f"👁 Jami ko'rishlar: {stats['total_views']}\n\n"
    text += f"Quyidagi amallarni tanlang:"

    await message.answer(text, reply_markup=InlineKeyboards.get_admin_menu())


@router.callback_query(F.data == "admin_pending")
async def show_pending_apartments(callback: CallbackQuery, session: AsyncSession):
    """Show pending apartments for approval."""
    if not await UserService.is_admin(session, callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqlari yo'q.", show_alert=True)
        return

    apartments = await ApartmentService.get_pending_apartments(session, limit=10)

    if not apartments:
        await callback.answer("✅ Kutilayotgan e'lonlar yo'q.", show_alert=True)
        return

    await callback.message.answer(f"⏳ {len(apartments)} ta e'lon kutmoqda:\n")

    for apt in apartments:
        text = format_apartment_card(apt, show_contact=True)
        text = f"🆔 ID: #{apt.id}\n\n" + text

        keyboard = InlineKeyboards.get_apartment_actions(
            apt.id,
            show_admin=True,
            is_pending=True
        )

        if apt.photos:
            await callback.message.answer_photo(
                photo=apt.photos[0],
                caption=text,
                reply_markup=keyboard
            )
        else:
            await callback.message.answer(text, reply_markup=keyboard)

    await callback.answer()


@router.callback_query(F.data == "admin_active")
async def show_active_apartments(callback: CallbackQuery, session: AsyncSession):
    """Show active apartments."""
    if not await UserService.is_admin(session, callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqlari yo'q.", show_alert=True)
        return

    apartments = await ApartmentService.search_apartments(
        session=session,
        status=ApartmentStatus.APPROVED,
        limit=10
    )

    if not apartments:
        await callback.answer("😔 Aktiv e'lonlar yo'q.", show_alert=True)
        return

    await callback.message.answer(f"✅ {len(apartments)} ta aktiv e'lon:\n")

    for apt in apartments:
        text = format_apartment_card(apt, show_contact=True)
        text = f"🆔 ID: #{apt.id}\n\n" + text

        keyboard = InlineKeyboards.get_apartment_actions(
            apt.id,
            show_admin=True,
            is_pending=False
        )

        if apt.photos:
            await callback.message.answer_photo(
                photo=apt.photos[0],
                caption=text,
                reply_markup=keyboard
            )
        else:
            await callback.message.answer(text, reply_markup=keyboard)

    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def show_users(callback: CallbackQuery, session: AsyncSession):
    """Show users list."""
    if not await UserService.is_admin(session, callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqlari yo'q.", show_alert=True)
        return

    users = await UserService.get_all_users(session, limit=20)

    if not users:
        await callback.answer("😔 Foydalanuvchilar yo'q.", show_alert=True)
        return

    text = f"👥 Ro'yxatdan o'tgan foydalanuvchilar ({len(users)} ta):\n\n"

    for i, user in enumerate(users, 1):
        status = "🚫" if user.is_blocked else "✅"
        admin_mark = " 🔐" if user.is_admin else ""
        text += f"{i}. {status} {user.full_name}{admin_mark}\n"
        text += f"   📱 {user.phone_number}\n"
        text += f"   🆔 ID: {user.telegram_id}\n\n"

    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def show_detailed_stats(callback: CallbackQuery, session: AsyncSession):
    """Show detailed statistics."""
    if not await UserService.is_admin(session, callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqlari yo'q.", show_alert=True)
        return

    stats = await ApartmentService.get_statistics(session)
    user_count = await UserService.get_user_count(session)

    text = f"📊 To'liq statistika\n\n"
    text += f"👥 Foydalanuvchilar\n"
    text += f"├─ Jami: {user_count}\n\n"

    text += f"🏠 E'lonlar\n"
    text += f"├─ Jami: {stats['total']}\n"
    text += f"├─ ✅ Aktiv: {stats['active']}\n"
    text += f"├─ ⏳ Kutilmoqda: {stats['pending']}\n"
    text += f"├─ 🔑 Ijaraga: {stats['rent']}\n"
    text += f"└─ 💰 Sotish: {stats['sale']}\n\n"

    text += f"📈 Statistika\n"
    text += f"└─ 👁 Jami ko'rishlar: {stats['total_views']}\n"

    if stats['active'] > 0:
        avg_views = stats['total_views'] / stats['active']
        text += f"└─ 📊 O'rtacha ko'rishlar: {avg_views:.1f}\n"

    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_approve_"))
async def approve_apartment(callback: CallbackQuery, session: AsyncSession):
    """Approve apartment listing."""
    if not await UserService.is_admin(session, callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqlari yo'q.", show_alert=True)
        return

    apartment_id = int(callback.data.split("_")[2])
    apartment = await ApartmentService.get_by_id(session, apartment_id)

    if not apartment:
        await callback.answer("❌ E'lon topilmadi.", show_alert=True)
        return

    await ApartmentService.approve_apartment(session, apartment)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"✅ E'lon #{apartment_id} tasdiqlandi!")
    await callback.answer("✅ Tasdiqlandi!")

    # Notify owner
    try:
        await callback.bot.send_message(
            apartment.owner.telegram_id,
            f"✅ Sizning e'loningiz #{apartment_id} tasdiqlandi va endi ko'rsatilmoqda!"
        )
    except Exception as e:
        logger.error(f"Error notifying owner: {e}")

    logger.info(f"Apartment #{apartment_id} approved by admin {callback.from_user.id}")


@router.callback_query(F.data.startswith("admin_reject_"))
async def reject_apartment(callback: CallbackQuery, session: AsyncSession):
    """Reject apartment listing."""
    if not await UserService.is_admin(session, callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqlari yo'q.", show_alert=True)
        return

    apartment_id = int(callback.data.split("_")[2])
    apartment = await ApartmentService.get_by_id(session, apartment_id)

    if not apartment:
        await callback.answer("❌ E'lon topilmadi.", show_alert=True)
        return

    await ApartmentService.reject_apartment(session, apartment)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"❌ E'lon #{apartment_id} rad etildi!")
    await callback.answer("❌ Rad etildi!")

    # Notify owner
    try:
        await callback.bot.send_message(
            apartment.owner.telegram_id,
            f"❌ Afsuski, sizning e'loningiz #{apartment_id} admin tomonidan rad etildi.\n"
            "Iltimos, ma'lumotlarni tekshirib qaytadan urinib ko'ring."
        )
    except Exception as e:
        logger.error(f"Error notifying owner: {e}")

    logger.info(f"Apartment #{apartment_id} rejected by admin {callback.from_user.id}")


@router.callback_query(F.data.startswith("admin_archive_"))
async def archive_apartment(callback: CallbackQuery, session: AsyncSession):
    """Archive apartment listing."""
    if not await UserService.is_admin(session, callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqlari yo'q.", show_alert=True)
        return

    apartment_id = int(callback.data.split("_")[2])
    apartment = await ApartmentService.get_by_id(session, apartment_id)

    if not apartment:
        await callback.answer("❌ E'lon topilmadi.", show_alert=True)
        return

    await ApartmentService.archive_apartment(session, apartment)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("📦 Arxivlandi!")

    logger.info(f"Apartment #{apartment_id} archived by admin {callback.from_user.id}")


@router.callback_query(F.data.startswith("admin_delete_"))
async def delete_apartment(callback: CallbackQuery, session: AsyncSession):
    """Delete apartment listing."""
    if not await UserService.is_admin(session, callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqlari yo'q.", show_alert=True)
        return

    apartment_id = int(callback.data.split("_")[2])
    apartment = await ApartmentService.get_by_id(session, apartment_id)

    if not apartment:
        await callback.answer("❌ E'lon topilmadi.", show_alert=True)
        return

    await ApartmentService.delete_apartment(session, apartment)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("🗑 O'chirildi!")

    logger.info(f"Apartment #{apartment_id} deleted by admin {callback.from_user.id}")


@router.callback_query(F.data.startswith("admin_block_"))
async def block_user(callback: CallbackQuery, session: AsyncSession):
    """Block user."""
    if not await UserService.is_admin(session, callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqlari yo'q.", show_alert=True)
        return

    user_id = int(callback.data.split("_")[2])
    user = await UserService.get_by_id(session, user_id)

    if not user:
        await callback.answer("❌ Foydalanuvchi topilmadi.", show_alert=True)
        return

    await UserService.block_user(session, user)
    await callback.answer("🚫 Foydalanuvchi bloklandi!")

    logger.info(f"User {user_id} blocked by admin {callback.from_user.id}")


@router.callback_query(F.data.startswith("admin_unblock_"))
async def unblock_user(callback: CallbackQuery, session: AsyncSession):
    """Unblock user."""
    if not await UserService.is_admin(session, callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqlari yo'q.", show_alert=True)
        return

    user_id = int(callback.data.split("_")[2])
    user = await UserService.get_by_id(session, user_id)

    if not user:
        await callback.answer("❌ Foydalanuvchi topilmadi.", show_alert=True)
        return

    await UserService.unblock_user(session, user)
    await callback.answer("✅ Foydalanuvchi blokdan chiqarildi!")

    logger.info(f"User {user_id} unblocked by admin {callback.from_user.id}")


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_prompt(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Prompt for broadcast message."""
    if not await UserService.is_admin(session, callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqlari yo'q.", show_alert=True)
        return

    from app.states import AdminStates

    await callback.message.answer(
        "📢 Barcha foydalanuvchilarga yuborish uchun xabar yozing:\n\n"
        "❌ Bekor qilish uchun /cancel ni yuboring.",
        reply_markup=MainKeyboard.get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_broadcast_message)
    await callback.answer()


@router.message(F.text, F.from_user.func(lambda u: True))
async def process_broadcast_message(message: Message, state: FSMContext, session: AsyncSession):
    """Process broadcast message."""
    from app.states import AdminStates

    current_state = await state.get_state()
    if current_state != AdminStates.waiting_for_broadcast_message:
        return

    if not await UserService.is_admin(session, message.from_user.id):
        return

    if message.text == "❌ Bekor qilish" or message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=MainKeyboard.get_main_menu())
        return

    users = await UserService.get_all_users(session, limit=1000)

    sent = 0
    failed = 0

    status_msg = await message.answer("📤 Xabarlar yuborilmoqda...")

    for user in users:
        try:
            await message.bot.send_message(
                user.telegram_id,
                f"📢 Admin xabari:\n\n{message.text}"
            )
            sent += 1
        except Exception as e:
            logger.error(f"Error sending broadcast to {user.telegram_id}: {e}")
            failed += 1

    await status_msg.edit_text(
        f"✅ Xabar yuborish tugadi!\n\n"
        f"✅ Yuborildi: {sent}\n"
        f"❌ Xato: {failed}"
    )

    await state.clear()
    logger.info(f"Broadcast sent by admin {message.from_user.id}: {sent} sent, {failed} failed")
