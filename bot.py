import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# Configuration
BOT_TOKEN = "8892597337:AAEv14-HlLgfbbfT7qwOs2MicHVHB0kxxyI"
USDT_ADDRESS = "TRzb358csuzX2niyt4PvGoKntgYovUk7JH"
EA_NAME = "Alfa Fx Pruning"

# IMPORTANT: Put your personal Telegram User ID here to receive order alerts
ADMIN_CHAT_ID = 6987325782  

# Conversation States
WAITING_SCREENSHOT = 1
WAITING_ACCOUNT_ID = 2

# Logging configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Pricing Plans Definition
PLANS = {
    "trial": {"name": "15-Day Free Trial", "price": "$0 (Free)"},
    "monthly": {"name": "Monthly Subscription", "price": "$30 / month"},
    "quarterly": {"name": "Quarterly Subscription", "price": "$70 for 3 months"},
    "yearly": {"name": "Yearly Subscription", "price": "$249 for 1 year"},
    "lifetime": {"name": "Lifetime Access", "price": "$349 Lifetime"}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        f"🤖 **Welcome to {EA_NAME} Official Bot!**\n\n"
        f"Automate your Forex trading with maximum efficiency.\n\n"
        f"📌 **License Policy:** 1 MT4/MT5 account per license.\n\n"
        f"Please select your desired plan below:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎁 15-Day Free Trial ($0)", callback_data="plan_trial")],
        [InlineKeyboardButton("🗓️ Monthly ($30)", callback_data="plan_monthly")],
        [InlineKeyboardButton("📅 Quarterly ($70)", callback_data="plan_quarterly")],
        [InlineKeyboardButton("🚀 Yearly ($249)", callback_data="plan_yearly")],
        [InlineKeyboardButton("💎 Lifetime ($349)", callback_data="plan_lifetime")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    plan_key = query.data.replace("plan_", "")
    selected_plan = PLANS[plan_key]
    context.user_data['selected_plan'] = selected_plan['name']
    
    if plan_key == "trial":
        await query.message.reply_text(
            f"✅ You selected **{selected_plan['name']}**.\n\n"
            f"Please send your **MT4 or MT5 Account Number** now:"
        )
        return WAITING_ACCOUNT_ID
    else:
        payment_text = (
            f"🛒 **Selected Plan:** {selected_plan['name']} ({selected_plan['price']})\n\n"
            f"💳 **USDT TRC20 Deposit Address:**\n"
            f"`{USDT_ADDRESS}`\n\n"
            f"⚠️ **Instruction:** Send the payment to the address above, then **upload the payment screenshot (Photo)** in this chat."
        )
        await query.message.reply_text(payment_text, parse_mode="Markdown")
        return WAITING_SCREENSHOT

async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = update.message.photo[-1].file_id
    context.user_data['photo_id'] = photo_file
    
    await update.message.reply_text(
        "✅ Screenshot received successfully!\n\n"
        "Now please send your **MT4 or MT5 Account Number**:"
    )
    return WAITING_ACCOUNT_ID

async def receive_account_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account_id = update.message.text
    user = update.message.from_user
    plan = context.user_data.get('selected_plan', 'Unknown Plan')
    photo_id = context.user_data.get('photo_id', None)
    
    await update.message.reply_text(
        "🙌 **Thank you!** Your order details have been submitted.\n"
        "The admin will verify your payment and release your EA files shortly."
    )
    
    # Notify Admin
    admin_text = (
        f"🔔 **NEW ORDER RECEIVED!**\n\n"
        f"👤 **User:** {user.full_name} (@{user.username})\n"
        f"🆔 **User ID:** `{user.id}`\n"
        f"📦 **Plan:** {plan}\n"
        f"🔢 **MT4/MT5 Account:** `{account_id}`"
    )
    
    admin_keyboard = [
        [
            InlineKeyboardButton("✅ Approve & Send EA", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
        ]
    ]
    admin_markup = InlineKeyboardMarkup(admin_keyboard)
    
    if photo_id:
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo_id,
            caption=admin_text,
            reply_markup=admin_markup,
            parse_mode="Markdown"
        )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"🎁 **FREE TRIAL REQUEST**\n\n{admin_text}",
            reply_markup=admin_markup,
            parse_mode="Markdown"
        )
        
    return ConversationHandler.END

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, user_id = query.data.split("_")
    user_id = int(user_id)
    
    if action == "approve":
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ **APPROVED & SENT**")
        
        # Message to customer
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 **Your payment has been approved!**\n\nFind your **{EA_NAME}** `.ex4` and `.ex5` files below:"
        )
        
        # Send EA files to customer
        try:
            await context.bot.send_document(
                chat_id=user_id, 
                document=open('Alfa_Fx_Pruning.ex4', 'rb'), 
                caption="Alfa Fx Pruning MT4 Version"
            )
            await context.bot.send_document(
                chat_id=user_id, 
                document=open('Alfa_Fx_Pruning.ex5', 'rb'), 
                caption="Alfa Fx Pruning MT5 Version"
            )
        except Exception as e:
            await context.bot.send_message(
                chat_id=user_id, 
                text="An error occurred while sending files. The admin will contact you directly."
            )
            print(f"Error sending files: {e}")
            
    elif action == "reject":
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ **REJECTED**")
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Your payment could not be verified. Please contact support."
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(plan_selected, pattern="^plan_")],
        states={
            WAITING_SCREENSHOT: [MessageHandler(filters.PHOTO, receive_screenshot)],
            WAITING_ACCOUNT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_account_id)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(approve|reject)_"))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()