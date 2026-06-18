import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters,
    PicklePersistence
)
from script_generator import generate_script, format_script_for_telegram
from video_processor import merge_and_process
from publisher import publish_instagram, publish_facebook, publish_youtube
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

WAITING_FOR_VIDEOS = 1


def is_authorized(update: Update) -> bool:
    incoming = str(update.effective_chat.id).strip()
    allowed = str(TELEGRAM_CHAT_ID).strip()
    print(f"AUTH CHECK — Incoming: {incoming} | Allowed: {allowed} | Match: {incoming == allowed}")
    return incoming == allowed


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to ACE Content Studio!\n\n"
        "Here's what I can do:\n\n"
        "📝 /script — Generate a 7-scene video script\n"
        "📤 /upload — Start uploading your recorded clips\n"
        "✅ /done — Process and publish uploaded clips\n"
        "❌ /cancel — Cancel current session\n\n"
        "Start by typing /script to get your script."
    )


async def script_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("Unauthorized.")
        return

    await update.message.reply_text("⏳ Generating your script. Please wait...")

    try:
        script = generate_script()
        context.user_data["current_script"] = script
        context.user_data["uploaded_videos"] = []
        context.user_data["upload_mode"] = False

        formatted = format_script_for_telegram(script)
        await update.message.reply_text(formatted)

    except Exception as e:
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f"Script generation failed: {e}")


async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("Unauthorized.")
        return

    if "current_script" not in context.user_data:
        await update.message.reply_text(
            "No script found. Run /script first."
        )
        return

    context.user_data["uploaded_videos"] = []
    context.user_data["upload_mode"] = True

    script = context.user_data["current_script"]
    total_scenes = len(script["scenes"])

    await update.message.reply_text(
        f"📤 Upload Mode Active\n\n"
        f"Send me your {total_scenes} video clips one by one.\n"
        f"I will number them in the order I receive them.\n\n"
        f"Send /done when all clips are uploaded.\n"
        f"Send /cancel to start over."
    )

    return WAITING_FOR_VIDEOS


async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    if not context.user_data.get("upload_mode"):
        await update.message.reply_text(
            "Send /upload first to start uploading clips."
        )
        return

    video = update.message.video or update.message.document
    if not video:
        await update.message.reply_text("Please send a video file.")
        return

    videos = context.user_data.get("uploaded_videos", [])
    script = context.user_data.get("current_script", {})
    total_scenes = len(script.get("scenes", []))
    current_count = len(videos) + 1

    await update.message.reply_text(f"⬇️ Downloading clip {current_count} of {total_scenes}...")

    try:
        file = await video.get_file()
        file_path = f"/tmp/scene_upload_{current_count}.mp4"
        await file.download_to_drive(file_path)

        file_size = os.path.getsize(file_path)
        videos.append(file_path)
        context.user_data["uploaded_videos"] = videos

        remaining = total_scenes - len(videos)

        if len(videos) >= total_scenes:
            await update.message.reply_text(
                f"✅ Clip {current_count} received! ({file_size:,} bytes)\n\n"
                f"All {total_scenes} clips received!\n"
                f"Send /done to process and publish."
            )
        else:
            await update.message.reply_text(
                f"✅ Clip {current_count} received! ({file_size:,} bytes)\n"
                f"Progress: {len(videos)}/{total_scenes} clips.\n"
                f"{remaining} more to go."
            )

    except Exception as e:
        await update.message.reply_text(f"Error downloading clip: {e}")


async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("Unauthorized.")
        return

    videos = context.user_data.get("uploaded_videos", [])
    script = context.user_data.get("current_script")

    if not videos:
        await update.message.reply_text(
            "No clips uploaded yet. Send /upload first."
        )
        return

    if not script:
        await update.message.reply_text(
            "No script found. Run /script first."
        )
        return

    total_scenes = len(script["scenes"])
    if len(videos) < total_scenes:
        await update.message.reply_text(
            f"Only {len(videos)}/{total_scenes} clips uploaded.\n"
            f"Send remaining clips or /cancel to start over."
        )
        return

    await update.message.reply_text(
        f"🎬 Processing {len(videos)} clips...\n"
        f"Adding captions and background music.\n"
        f"This takes 2-5 minutes. Please wait."
    )

    try:
        final_video = merge_and_process(videos[:total_scenes], script)
        file_size = os.path.getsize(final_video)

        await update.message.reply_text(
            f"✅ Video processed! ({file_size:,} bytes)\n"
            f"Publishing to all platforms now..."
        )

        caption = script["caption"]
        youtube_title = script["youtube_title"]

        ig_result = publish_instagram(final_video, caption)
        fb_result = publish_facebook(final_video, caption)
        yt_result = publish_youtube(final_video, youtube_title, caption)

        results = ["📊 Publishing Results\n"]
        results.append(f"Instagram: {'✅ Published' if ig_result else '❌ Failed'}")
        results.append(f"Facebook: {'✅ Published' if fb_result else '❌ Failed'}")

        if yt_result:
            yt_id = yt_result.get("id", "")
            results.append(f"YouTube: ✅ https://youtube.com/shorts/{yt_id}")
        else:
            results.append("YouTube: ❌ Failed")

        await update.message.reply_text("\n".join(results))

        context.user_data["uploaded_videos"] = []
        context.user_data["upload_mode"] = False

    except Exception as e:
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f"Processing failed: {e}")

    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["uploaded_videos"] = []
    context.user_data["upload_mode"] = False
    await update.message.reply_text(
        "Session cancelled. Run /script to start fresh."
    )
    return ConversationHandler.END


def main():
    persistence = PicklePersistence(filepath="/tmp/bot_persistence.pkl")

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .persistence(persistence)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("upload", upload_command)],
        states={
            WAITING_FOR_VIDEOS: [
                MessageHandler(
                    filters.VIDEO | filters.Document.VIDEO,
                    receive_video
                ),
                CommandHandler("done", done_command),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        persistent=True,
        name="main_conversation"
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("script", script_command))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("done", done_command))
    app.add_handler(
        MessageHandler(
            filters.VIDEO | filters.Document.VIDEO,
            receive_video
        )
    )

    print("ACE Content Studio Bot is running...")
    print(f"Authorized Chat ID: {TELEGRAM_CHAT_ID}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
