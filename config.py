import os

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Meta
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
INSTAGRAM_USER_ID = os.environ.get("INSTAGRAM_USER_ID")
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")

# YouTube
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")

# Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Brand
BRAND_NAME = "Ace Digitals Global"
BRAND_HANDLE = "@DigitalUche"
BRAND_NICHE = "business growth, digital marketing, AI automation, websites, revenue systems"
BRAND_AUDIENCE = "Nigerian entrepreneurs and SME owners aged 18-35"

# Video
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# Content topics
TOPICS = [
    "Why Most Businesses Don't Have a Marketing Problem They Have a Sales Problem",
    "5 Reasons Customers Visit Your Website But Never Contact You",
    "Why You're Getting Traffic But No Sales",
    "The Hidden Cost of Running a Business Without Systems",
    "How to Know Where Your Next Customer Will Come From",
    "The Customer Journey Every Small Business Must Understand",
    "Why Referrals Alone Are Dangerous for Business Growth",
    "The Biggest Mistakes Small Businesses Make Online",
    "How Businesses Lose Customers Before They Ever Reach Out",
    "The Difference Between Busy Businesses and Profitable Businesses",
    "What a Website Should Actually Do for a Business",
    "Why Most Nigerian Business Websites Fail",
    "7 Website Features That Increase Customer Enquiries",
    "Landing Page vs Website Which One Do You Need",
    "How to Turn Website Visitors into Paying Customers",
    "Signs Your Website Is Costing You Money",
    "The Psychology Behind High Converting Websites",
    "10 Tasks AI Can Do for Your Business Today",
    "How AI Can Help Small Businesses Compete With Bigger Brands",
    "The Difference Between AI Tools and AI Systems",
    "How to Automate Customer Follow Ups",
    "AI Mistakes Business Owners Make",
    "Building a Business That Runs Even When You Are Sleeping",
    "Why Posting Every Day Does Not Guarantee Sales",
    "The Truth About Going Viral",
    "What Businesses Should Post If They Want More Customers",
    "The Difference Between Content That Gets Likes and Content That Gets Sales",
    "Why Most Facebook Ads Fail",
    "The Marketing Funnel Explained Simply",
    "I Analyzed 100 Small Businesses Here Is What They All Got Wrong",
]

ANGLES = [
    "direct_explanation",
    "mistake_angle",
    "case_study",
    "myth_busting",
    "fix_how_to",
    "pain_emotional"
]

# Music moods mapped to royalty free tracks from pixabay
MUSIC_MOODS = {
    "educational": "https://cdn.pixabay.com/audio/2024/03/12/audio_2dde668d38.mp3",
    "motivational": "https://cdn.pixabay.com/audio/2024/01/29/audio_855508f0ab.mp3",
    "corporate": "https://cdn.pixabay.com/audio/2023/10/30/audio_7f256c3fba.mp3",
    "calm": "https://cdn.pixabay.com/audio/2024/02/15/audio_c8f4b82f5e.mp3",
}
