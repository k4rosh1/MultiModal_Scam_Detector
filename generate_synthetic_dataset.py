# =============================================================================
# Synthetic Dataset Generator for Multi-Modal Scam Detection
# Generates 5,000+ balanced (scam/legit) rows in Taglish
# Covers all 6 CICC scam categories + 8 legitimate content categories
# =============================================================================

import pandas as pd
import random
import hashlib
from collections import Counter

# ── REPRODUCIBILITY ───────────────────────────────────────────────────────────
SEED = 2025
random.seed(SEED)

# ── TARGET COUNTS ─────────────────────────────────────────────────────────────
TARGET_SCAM  = 2500
TARGET_LEGIT = 2500

# =============================================================================
# PLACEHOLDER VALUE POOLS
# =============================================================================

amounts_peso = [
    "₱500", "₱1,000", "₱1,500", "₱2,000", "₱2,500", "₱3,000",
    "₱5,000", "₱7,500", "₱10,000", "₱15,000", "₱20,000", "₱25,000",
    "₱50,000", "₱100,000",
]
amounts_dollar = ["$50", "$100", "$200", "$500", "$1,000"]
small_amounts = ["₱100", "₱150", "₱200", "₱250", "₱300", "₱500", "₱750", "₱999"]
big_amounts = ["₱50,000", "₱100,000", "₱200,000", "₱500,000", "₱1,000,000"]
daily_amounts = ["₱500", "₱800", "₱1,000", "₱1,500", "₱2,000", "₱3,000", "₱5,000"]

banks = [
    "BDO", "BPI", "Metrobank", "PNB", "RCBC", "UnionBank",
    "Landbank", "Security Bank", "EastWest Bank", "China Bank",
]
ewallets = ["GCash", "Maya", "Coins.ph", "GrabPay", "ShopeePay"]
platforms = ["GCash", "Maya", "Lazada", "Shopee", "Grab", "Angkas"]

links = [
    "bit.ly/earn{code}", "tinyurl.com/free{code}", "t.me/group{code}",
    "wa.me/{code}", "forms.gle/{code}", "rebrand.ly/{code}",
    "cutt.ly/{code}", "shorturl.at/{code}", "link.ph/{code}",
]
ref_codes = [f"{random.randint(1000,9999)}" for _ in range(200)]
promo_codes = [
    "EARN2024", "FREE500", "RICH101", "VIP2025", "BONUS99",
    "LUCKY777", "CASHBACK", "PAYOUT1", "WINNER01", "TOPUP200",
]

time_frames = [
    "24 hours", "48 hours", "3 days", "5 days", "7 days",
    "isang linggo", "isang araw", "tatlong araw", "isang buwan",
]
time_frames_short = ["today", "ngayon", "mamaya", "bukas", "tonight", "now"]

job_titles = [
    "data encoder", "virtual assistant", "online tutor", "chat support",
    "social media manager", "content moderator", "customer service rep",
    "product reviewer", "ad clicker", "video liker",
]
countries = [
    "Japan", "Korea", "Canada", "Australia", "Dubai", "Singapore",
    "Saudi Arabia", "New Zealand", "Qatar", "Taiwan",
]
crypto_names = ["Bitcoin", "Ethereum", "USDT", "Solana", "BNB", "XRP"]

product_items = [
    "iPhone 15 Pro Max", "Samsung Galaxy S24", "iPad Air", "MacBook",
    "PS5", "Nintendo Switch", "Air Jordan", "branded bag",
    "laptop", "smartwatch", "airpods", "gaming chair",
    "mountain bike", "DSLR camera", "electric scooter",
]
shipping_methods = ["LBC", "J&T", "Flash Express", "Grab Express", "Lalamove"]

food_places = [
    "Jollibee", "McDonald's", "KFC", "Mang Inasal", "Chowking",
    "Greenwich", "Shakey's", "Max's", "Yellow Cab", "Army Navy",
    "Starbucks", "Tim Hortons", "Bo's Coffee",
]
locations = [
    "EDSA", "BGC", "Makati", "Ortigas", "Quezon City", "Alabang",
    "SM North", "MOA", "Trinoma", "Robinsons Galleria", "Ayala",
    "Megamall", "Eastwood", "UP Diliman", "Cebu", "Davao",
]
hobbies = [
    "cooking", "painting", "gardening", "photography", "cycling",
    "running", "yoga", "reading", "gaming", "baking",
    "fishing", "hiking", "drawing", "vlogging", "crocheting",
]
shows_movies = [
    "Netflix", "YouTube", "Disney+", "anime", "K-drama",
    "Marvel movie", "horror movie", "rom-com", "series", "documentary",
]
sports_activities = [
    "basketball", "volleyball", "badminton", "swimming", "jogging",
    "gym", "boxing", "Zumba", "CrossFit", "running",
]


def random_link():
    template = random.choice(links)
    code = random.choice(ref_codes)
    return template.format(code=code)


def random_ref():
    return f"Ref {random.randint(1000,9999)}"


def random_note():
    return f"Note {random.randint(1000,9999)}"


# =============================================================================
# SCAM TEMPLATES — CATEGORY 1: PHISHING
# =============================================================================

phishing_templates = [
    # Bank impersonation — account suspension
    "{bank} notice: Your account has been temporarily suspended. Please verify your identity at {link} to restore access. {ref}.",
    "{bank} ALERT: Unusual login activity detected on your account. Confirm your credentials here: {link}. {ref}.",
    "{bank} Security: Your online banking access will be restricted in {time}. Update your information now: {link}. {ref}.",
    "URGENT — {bank}: We detected unauthorized transactions on your account. Verify immediately: {link}. {ref}.",
    "{bank} notice: Your account may be temporarily locked. Please update your account information using the page sent in this message before your access is restricted. {ref}.",
    "{bank} notice: Your account needs verification. Please verify your login and OTP using the page sent in this message before your access is restricted. {ref}.",
    "{bank} notice: Unusual activity was detected. Please confirm your mobile number using the page sent in this message before your access is restricted. {ref}.",
    "{bank} notice: Unusual activity was detected. Please complete the security form using the page sent in this message before your access is restricted. {ref}.",
    "Your {bank} account has been compromised. Please update your information immediately at {link}. Failure to do so will result in permanent suspension. {ref}.",
    "IMPORTANT: {bank} requires all customers to re-verify their accounts. Click here: {link}. Deadline: {time}. {ref}.",

    # E-wallet impersonation
    "Your {ewallet} account has been flagged for suspicious activity. Verify here to avoid deactivation: {link}. {ref}.",
    "{ewallet} Security Alert: Someone tried to access your account from a new device. Confirm it's you: {link}. {ref}.",
    "NOTICE: Your {ewallet} cash-in limit has been reached. To increase your limit, verify your identity: {link}. {ref}.",
    "{ewallet} Support: We need to verify your account details to process your pending transaction of {amount}. Click: {link}. {ref}.",
    "Hi! This is {ewallet} customer support. Your account will be deactivated in {time} if you don't verify: {link}. {ref}.",
    "Your {ewallet} account is under review. Submit verification documents here: {link} or your balance will be frozen. {ref}.",

    # OTP phishing
    "Your {bank} OTP is needed for a pending transaction of {amount}. If this is not you, verify at {link}. {ref}.",
    "We sent a verification code to your number. Please enter it at {link} to confirm your {bank} transaction. {ref}.",
    "{ewallet}: A cash-out request of {amount} was made. If unauthorized, secure your account: {link}. {ref}.",

    # Fake government / SSS / Pag-IBIG / PhilHealth
    "SSS NOTICE: You have an unclaimed benefit of {amount}. Claim now before it expires: {link}. {ref}.",
    "Pag-IBIG Fund: Your housing loan application requires re-verification. Submit documents here: {link}. {ref}.",
    "PhilHealth advisory: Update your member information to avoid disruption of benefits. Click: {link}. {ref}.",
    "DSWD 4Ps Update: You are eligible for additional cash aid of {amount}. Register here: {link}. {ref}.",
    "BIR Notice: Your tax refund of {amount} is ready for processing. Claim it here: {link}. {ref}.",

    # Delivery / package phishing
    "Your package from {platform} is being held due to incomplete address. Update delivery info: {link}. {ref}.",
    "LBC Express: Your parcel cannot be delivered. Please confirm your address at {link} to reschedule. {ref}.",
    "J&T Express: Package #{ref_code} requires additional shipping fee of {small_amount}. Pay here: {link}.",
    "{platform} delivery update: Your order has been flagged. Verify your account to receive it: {link}. {ref}.",

    # Prize / reward phishing
    "Congratulations! You won {amount} from {bank}'s loyalty program! Claim your prize: {link}. {ref}.",
    "You've been selected for {ewallet}'s cashback promo! Get {amount} now: {link}. Limited time only. {ref}.",
    "{platform} Anniversary Sale: You won a free {item}! Register to claim: {link}. Offer ends {time}. {ref}.",

    # Taglish phishing
    "Grabe! Na-flag yung {bank} account mo. I-verify mo agad dito: {link} para di ma-lock. {ref}.",
    "Uy, may nag-try mag-login sa {ewallet} mo. Hindi ikaw yon? Confirm mo dito: {link}. {ref}.",
    "May pending na {amount} sa {ewallet} account mo. I-claim mo na bago mag-expire: {link}. {ref}.",
    "Ayusin mo na yung {bank} account mo, baka ma-deactivate. Click mo lang to: {link}. {ref}.",
    "Lods, na-hold yung parcel mo. I-verify yung address mo dito: {link}. Bilisan mo lang. {ref}.",
    "Sis/Bro, nag-notify yung {bank} na may unauthorized transaction. Tignan mo: {link}. {ref}.",
    "Attention: Nag-send kami ng OTP sa number mo para sa {bank} verification. I-enter mo dito: {link}. {ref}.",

    # SMS-style short phishing
    "{bank}: Verify acct or it will be closed. {link}. {ref}.",
    "{ewallet} ALERT: Unauthorized cashout detected. Secure now: {link}.",
    "FINAL NOTICE — {bank} acct suspended. Reactivate: {link}. {ref}.",

    # Email-style phishing
    "Dear valued {bank} customer, your account requires immediate attention. Please log in at {link} to review recent activity. {ref}.",
    "This is an automated message from {bank}. Your account security settings need updating. Visit {link} within {time}. {ref}.",
    "Action required: {ewallet} account verification pending. Complete the process at {link} to avoid service interruption. {ref}.",

    # Additional Taglish variations
    "Ay grabe, nagpadala ng notification yung {bank}. Baka ma-lock account mo. Check mo: {link}. {ref}.",
    "Alert sa {ewallet} account mo — may nag-try ng cash-out ng {amount}. I-report mo or i-verify: {link}. {ref}.",
    "Blocked na yung {bank} card mo dahil sa suspicious activity. Unblock dito: {link}. Asap ha! {ref}.",
    "Important po: Na-detect namin na may nag-access sa {ewallet} niyo mula sa ibang device. I-secure: {link}. {ref}.",
    "Di mo ba alam na may {amount} ka na pending sa {bank}? Claim here: {link}. {ref}.",
]

# =============================================================================
# SCAM TEMPLATES — CATEGORY 2: INVESTMENT FRAUD
# =============================================================================

investment_fraud_templates = [
    # Crypto / trading
    "Invest {small_amount} today and earn {big_amount} in just {time}! 100% legit with SEC registration. {link}. {ref}.",
    "Join our VIP crypto trading group and receive guaranteed daily profits of {amount}! Limited slots. {link}. {ref}.",
    "Guys, nakita ko itong digital investment pool opportunity and ang promise ay earn passive income from your phone. {action}. {ref}.",
    "Double your money in {time}! Our forex trading bot has 99% win rate. Join now: {link}. {ref}.",
    "Invest in {crypto} mining — earn {amount} daily without doing anything! Start with just {small_amount}. {link}. {ref}.",
    "Kumikita na ang mga kasama ko ng {amount} daily sa crypto trading. Gusto mo matuto? DM me or click: {link}. {ref}.",
    "🚀 {crypto} is about to moon! Invest {small_amount} now and get {big_amount} returns. Proven strategy: {link}. {ref}.",
    "Our AI trading bot earned our members {amount} last week alone! Start investing: {link}. Zero risk. {ref}.",
    "Passive income through {crypto} staking — {amount} monthly guaranteed. No experience needed: {link}. {ref}.",
    "Forex trading made easy! Copy our expert trades and earn {amount} weekly. Free trial: {link}. {ref}.",

    # Paluwagan / Ponzi schemes
    "Paluwagan online! Slot 1 to 10 available. Ilagay {small_amount}, makukuha {big_amount}! Tubong lugaw! {link}. {ref}.",
    "Digital paluwagan — 100% payout guaranteed. Nasa slot 3 na kami. Pasok ka na! PM me or {link}. {ref}.",
    "Legit online paluwagan with contract. {small_amount} contribution, {amount} payout sa {time}. Join: {link}. {ref}.",

    # General investment scam
    "Good news! If you want {offer}, they claim you can {reward}. Message me ASAP and don't miss it. {urgency}. {ref}.",
    "Sa mga naghahanap ng extra income, this {job_offer} offer says you can {reward}. {action}, lods. {urgency}. {ref}.",
    "Mga lods, may {program} daw na {promise}. PM me for the registration link; legit daw and maraming payout screenshots. {ref}.",
    "Quick heads-up, may {program} daw na {promise}. Enter your account information; marami na raw kumikita dito. {ref}.",
    "Attention po! If you want {offer}, they claim you can {reward}. Send your details to the coordinator and don't miss it. {urgency}. {ref}.",
    "Isang araw lang may {amount} na ako. Kung gusto mo matuto, click mo to: {link}. Legit yan promise! {ref}.",
    "Earn {amount} instantly by simply signing up! Use my referral code: {promo_code} 🤑. Register: {link}. {ref}.",
    "May bago nanaman na earning app! {amount} sign up bonus. Withdraw agad sa GCash! {link}. {ref}.",

    # Taglish investment pitches
    "Lods, legit to — invest ka lang ng {small_amount} sa platform na to, within {time} may {amount} ka na agad. {link}. {ref}.",
    "Sobrang dali kumita dito! {small_amount} lang starting capital, tapos {amount} ang balik within {time}. Try mo: {link}. {ref}.",
    "Nakaka-{amount} na ako per day dito sa trading. Hindi scam to, may SEC papers. Sama ka na: {link}. {ref}.",
    "Gusto mo kumita ng {amount} habang natutulog? Passive income app to — legit, marami nang proof: {link}. {ref}.",
    "Di ka maniniwala — {small_amount} lang nilagay ko, naging {amount} in {time}! Real talk. PM me or go to {link}. {ref}.",
    "Invest wisely! Our company is SEC-registered and has been paying members for 2 years. Start with {small_amount}: {link}. {ref}.",
    "Libre ang puhunan, kita lang ang hanap! Join our investment community: {link}. Members earning {amount} per week. {ref}.",
    "Grabe, yung friend ko kumita ng {big_amount} sa investment na to! Sama ka na: {link}. Low risk, high reward. {ref}.",
    "Nag-iipon ka pa rin sa bangko? Mag-invest ka na! {amount} monthly returns guaranteed: {link}. {ref}.",
    "Last chance to join our exclusive trading group! Only {small_amount} membership fee. Earn {amount} daily: {link}. {ref}.",

    # Social proof heavy
    "Check mo testimonials ng members namin — {amount} per day ang average! Join: {link}. {ref}.",
    "Screenshot ng payout ko — {amount}! Hindi fake to. Gusto mo rin? DM me: {link}. {ref}.",
    "Tignan mo yung group namin sa Telegram — araw-araw may kumikita ng {amount}. Legit talaga: {link}. {ref}.",
    "Ang dami na naming members na naka-withdraw ng {amount} from this investment platform. Ikaw na lang kulang! {link}. {ref}.",

    # Urgency-heavy
    "TODAY ONLY: Invest {small_amount} and get 3x returns by tomorrow! Slots filling up fast: {link}. {ref}.",
    "⏰ Last 5 slots available for our exclusive investment program! {small_amount} entry, {amount} guaranteed: {link}. {ref}.",
    "Flash investment promo — deposit {small_amount} NOW and withdraw {amount} in {time}. Offer expires tonight: {link}. {ref}.",
    "Limited time! Our trading signals are FREE today. Usual price {small_amount}/month. Join: {link}. {ref}.",

    # Pure Tagalog investment scams
    "Kumita ng malaki sa bahay lang! Walang puhunan, walang risk. Magregister ka lang: {link}. {ref}.",
    "Pera habang natutulog — hindi na bago to! Investment app na legit, SEC-approved: {link}. {ref}.",
    "Ayaw mo na ba ng trabaho? Mag-invest ka at kumita ng {amount} monthly. Libreng seminar: {link}. {ref}.",
]

# =============================================================================
# SCAM TEMPLATES — CATEGORY 3: ACCOUNT TAKEOVER / HACKING
# =============================================================================

account_takeover_templates = [
    # "Accidental" OTP requests
    "I accidentally used your number for verification. Kindly send me the code. Sorry po!",
    "Ate/Kuya, nagkamali po ako ng number nung nag-register. Paki-send na lang po ng code na na-receive mo. Pasensya na po!",
    "Uy sorry, nalagay ko yung number mo sa registration ko. Pa-send naman ng OTP na narereceive mo. Salamat!",
    "Hi! Mali po ang na-input kong number. Na-receive mo ba yung 6-digit code? Pa-send naman po. Sorry for the trouble!",
    "Bro/Sis, I registered with the wrong number. Can you send me the code you just received? My bad.",
    "Pasensya na po, nag-type ako ng maling number. Yung OTP po na nareceive niyo, paki-forward. Thanks po!",
    "So sorry! Nalagay ko number mo instead of mine sa app. Pwede mo ba i-send sakin yung verification code? Won't happen again.",
    "Hala sorry talaga! Yung 6-digit code na nareceive mo, para sa akin yun. Pwede pa-send back? Nagmamadali kasi ako.",

    # "Hacked account" social engineering
    "Na-hack po yung account ko. Pakisend po ng OTP code na matatanggap ninyo.",
    "Help po! Na-compromise yung {ewallet} account ko. Paki-send ng verification code para ma-recover ko.",
    "Nag-request ako ng account recovery sa {bank}. Pwede mo ba i-forward yung code na matatanggap mo? Wala kasi akong access sa number ko.",
    "Lods, na-hack yung Facebook ko. Ginamit ko number mo for recovery. Pa-send ng code please!",
    "Na-lock yung {ewallet} ko! Nag-send sila ng code sa number mo kasi dati kong number yan. Pa-forward please.",
    "Bro help naman — na-hack yung {bank} online banking ko. Nag-send sila ng OTP sa old number ko na ikaw na gumagamit. Send mo sakin please.",
    "Grabe, na-hack yung Messenger ko! Ginamit ko yung number mo para sa recovery. Paki-send na lang ng code na ma-receive mo.",

    # Impersonating friend/family
    "Hi {name}! Ito si [friend name]. Bagong number ko to. Na-send ko accidentally yung verification code sa number mo. Pa-send back naman?",
    "Tita/Tito, ito po si [name]. Nag-change po ako ng phone. Pa-send po yung OTP na narereceive niyo, need ko po for my new account.",
    "Mama/Papa, ito ako. Nasira phone ko kaya nagtext ako sa ibang number. Pa-send ng code na nareceive mo para makapag-login ako.",
    "Beshie! Ito si [name], new phone. Nag-send ako ng verification sa number mo by mistake. Pa-forward yung code ha?",
    "Lods, ito si [friend]. Lost phone ko kaya gumamit ako ng iba. I need yung code na na-send sa number mo para ma-recover account ko.",

    # Password reset tricks
    "We noticed a login attempt on your account. Send us the code we just sent to verify it was you.",
    "Your {ewallet} account password was changed. If this wasn't you, reply with the verification code we sent.",
    "{bank} Security Team: A password reset was requested. Forward the code you received to cancel this request.",
    "Unauthorized login detected on your {ewallet}. We've sent a security code — please reply with it to block access.",

    # Tech support impersonation
    "This is {bank} IT Support. We need the OTP sent to your number to complete the security patch on your account.",
    "Hi, I'm from {ewallet} customer support. We're fixing a glitch on your account. Please send us the code you received.",
    "{bank} anti-fraud team here. We've detected suspicious activity. Please provide the verification code for your protection.",
    "Good day! {ewallet} tech team. Your account is under maintenance. Kindly share the code we sent for verification purposes.",

    # Taglish account takeover
    "Pre, pautang naman ng OTP mo haha. Joke lang pero seryoso, paki-send lang yung code na nareceive mo. Para sa verification ko lang.",
    "Kuya/Ate, na-link yung number mo sa account ko dati. Pa-send lang ng code na ma-rereceive mo. Kailangan ko lang talaga.",
    "Lods sorry sa abala, nag-send ng code sa number mo yung {ewallet}. Hindi ko sinasadya. Pa-forward lang please.",
    "Uy! May nag-try mag-hack sakin. Ginamit nila yung number mo. Paki-send sakin yung code para ma-block ko sila.",

    # Urgent/threatening account takeover
    "URGENT: Your {bank} account is being accessed right now. Send us the OTP immediately to lock it down.",
    "If you don't send the verification code in 5 minutes, your {ewallet} account will be permanently deleted.",
    "WARNING: Someone is draining your {bank} account. We need the OTP code NOW to stop the transaction!",
    "Alert: {amount} is being transferred from your account. Send us the code to cancel this transaction immediately.",

    # Marketplace / COD OTP scam
    "Hi! I'm the buyer for your item on Marketplace. Shopee/Lazada sent a verification code to your number. Paki-send para ma-process yung payment.",
    "Seller po ako sa Shopee, nag-request ng payout and na-send yung code sa number niyo. Pa-share po para ma-claim ko.",
    "Para sa Lazada order mo — need namin ng confirmation code na na-send sa number mo. Pa-reply ASAP.",
    "Hello po! Yung order niyo sa Shopee, may verification code po na kailangan i-provide para ma-ship. Pa-send po.",

    # Short/casual OTP grabs
    "Pa-send naman ng code bro. Mali kasi yung nalagay kong number.",
    "Ate pa-send lang po ng OTP, nag-register kasi ako sa {ewallet} pero number mo nalagay ko.",
    "Code please! Yung na-receive mo kanina. Kailangan ko lang pandalian.",
    "Sis paki-send yung 6-digit code. Sakin yun promise. Maling number na-input ko.",

    # Additional parametrized account takeover (for diversity)
    "Hi, may nag-try mag-access ng {bank} account ko gamit yung dating number ko. Pa-send ng OTP na na-receive mo. Salamat!",
    "Ate/Kuya, nag-reset ako ng password sa {ewallet}. Yung code na natatanggap mo, paki-send sakin. Need ko ASAP.",
    "Grabe, nag-send ng alert yung {bank} na may nag-try mag-login. Naka-link pa yung old number ko sayo. Pa-forward ng code please.",
    "Help naman! May nag-hack ng {ewallet} ko and nag-try mag-transfer ng {amount}. Paki-send yung code para ma-block ko.",
    "Lods, nag-request ako ng {bank} OTP recovery. Paki-send yung verification code na na-receive mo sa number na yan.",
    "{ewallet} support sent a recovery code to your number. It was my old number. Paki-forward please. Urgent!",
    "Nag-change kasi ako ng phone. Yung {bank} verification code na na-receive mo, para sa account ko yun. Pa-send back?",
    "Bro, yung {ewallet} ko nag-lock. Na-send yung unlock code sa dati kong number na sayo na. Pa-forward naman.",
    "Sorry ha, nag-register ako sa {bank} online pero lumang number ko na sayo na yung nakalagay. Pa-send ng OTP.",
    "Uy, nag-trigger ng security alert yung {bank} ko. Na-send yung code sa old number. Pwede mo ba i-send sakin?",
    "Ate, yung {ewallet} ko need ng verification. Na-send yung code sa number mo kasi dati kong sim yan. Pa-help naman.",
    "Pre, nag-try ako mag-change ng password sa {bank}. Nag-send sila ng OTP sa old number ko. Pa-forward please!",
    "Boss, need ko lang yung {bank} verification code na na-send sa number mo. Lumang account ko kasi yan. Asap!",
    "{bank} security: Nag-flag yung account mo. Pa-send mo yung OTP na nareceive mo para ma-verify namin. {ref}.",
    "Kuya, may nag-request ng {amount} transfer sa {ewallet} ko. Pa-send ng code para ma-cancel ko. Please lang!",
    "I'm from {ewallet} verification team. We sent a code to this number for account #{ref_code}. Kindly provide it.",
    "Nag-link kasi yung {bank} ko sa number mo noon. Ngayon kailangan ko yung OTP. Pa-text back ha?",
    "May {amount} na pending cash-in sa {ewallet} ko. Need yung code na na-send sa number mo para ma-receive ko.",
    "Pare, nag-request ako ng new {bank} debit card. Yung activation code na-send sa old number ko na sayo na. Pa-forward.",
    "This is {bank} anti-fraud unit. A {amount} transaction was flagged. Provide the OTP sent to you to cancel it. {ref}.",
    "Nag-reset ng {ewallet} PIN ko kasi nakalimutan. Yung 4-digit code na nareceive mo, para dun yun. Pa-send please.",
    "Sis, yung {bank} nag-send ng verification code for a {amount} transfer. Kailangan ko yung code para ma-approve. Pa-help.",
    "Lods help — nag-send ng security code yung {ewallet} sa old number ko. Paki-forward before it expires in 5 mins.",
    "May nag-file ng dispute sa {bank} account ko. Kailangan yung OTP na na-send sayo para ma-resolve. Pakisend na!",
    "{ewallet} sent a 6-digit code sa number mo for account recovery. Ito yung account ko. Pa-share naman ng code.",
    "Ate/Kuya, na-compromise yung {bank} account ko. Ginamit ko number mo for recovery request. Pa-send ng code please.",
    "Pa-help naman — may nag-withdraw ng {amount} sa {ewallet} ko. Paki-send yung cancellation code na na-receive mo.",
    "Bro, ang tagal ko na di nagamit yung {bank} account ko. Nag-send sila ng reactivation code sa old number. Pa-forward?",
    "May verification code na na-send yung {ewallet} sa number mo. Para sa {amount} na cash-out ko yun. Paki-send please!",
    "Nag-try mag-access yung kapatid ko ng {bank} account. Na-send yung OTP sa number mo by mistake. Pa-forward lang.",
    "Hi, I need the {bank} verification code sent to this number. It's for my account ending in {ref_code}. Thank you!",
    "Emergency! May nag-hack ng {ewallet} ko and {amount} na ang na-transfer. Pa-send ng OTP para ma-lock ko agad.",
    "Kuya/Ate, nag-update ako ng contact info sa {bank}. Kailangan yung code na na-send sa old number mo. Help naman!",
    "Sorry sa abala — yung {ewallet} ko locked. Nag-send sila ng reset code sa number na to. Pa-send back please.",
    "This is automated {bank} security. Transaction of {amount} initiated. Forward the OTP to block it. {ref}.",
    "Pare, nag-sign up ako sa {ewallet} gamit yung old number ko na sayo na. Pa-forward yung OTP. Last time na to promise!",
    "Need help — nag-change ng password yung {bank} account ko hindi ko ginawa. Pa-send yung code para ma-revert!",
    "{bank} nag-send ng text verification sa number mo for a {amount} fund transfer. Cancel ko sana, pa-send ng code.",
    "Madam/Sir, this is {ewallet} customer care. Verify this number by replying with the OTP code sent. {ref}.",
    "Ay, yung OTP na nareceive mo ngayon lang — para sa {ewallet} login ko yun. Naka-register kasi dati sa number mo.",
    "Lods, need ko yung code na na-send ng {bank} para sa account recovery. Ito yung account number: {ref_code}.",
    "Pasensya na kuya, naka-link yung {ewallet} ko sa sim mo nung lumipat ako ng number. Pa-forward ng verification code?",
    "Hi! {ewallet} nag-send ng code sa number mo for my wallet verification of {amount}. Paki-reply naman. Salamat!",
]

# =============================================================================
# SCAM TEMPLATES — CATEGORY 4: ONLINE LENDING FRAUD
# =============================================================================

online_lending_fraud_templates = [
    # Processing fee scams
    "Congratulations! Your loan of {big_amount} has been approved! Kindly pay the processing fee of {small_amount} to release your proceeds. {link}. {ref}.",
    "Loan approved po! {big_amount} ang amount. I-deposit mo lang yung {small_amount} processing fee sa {ewallet} para ma-release agad. {ref}.",
    "Good news — pre-approved ka for a personal loan of {big_amount}! Processing fee lang ng {small_amount}, release within {time}. {link}. {ref}.",
    "Ma'am/Sir, approved na po yung loan application niyo ng {big_amount}. Kailangan lang po ng {small_amount} processing fee bago ma-release. {ref}.",
    "Your fast cash loan of {big_amount} is ready for disbursement. Complete the {small_amount} processing fee here: {link}. {ref}.",

    # Security deposit scams
    "The security deposit is refundable and will be returned with your loan. Kindly pay {small_amount} to proceed. {link}. {ref}.",
    "Para ma-release yung {big_amount} loan mo, kailangan muna ng refundable security deposit na {small_amount}. I-send sa {ewallet}: {ref}.",
    "Insurance fee of {small_amount} is required before we can release your {big_amount} loan. This is standard procedure. {link}. {ref}.",
    "Your loan requires a collateral deposit of {small_amount}. Don't worry — it will be deducted from your first release. {link}. {ref}.",
    "For compliance purposes, a one-time verification fee of {small_amount} is needed for your {big_amount} loan. {ewallet} transfer to: {ref}.",

    # Fake lending apps
    "Download our lending app and get instant approval for up to {big_amount}! No collateral needed. {link}. {ref}.",
    "Bagong lending app — 0% interest for the first month! Loan up to {big_amount}. Download na: {link}. {ref}.",
    "Instant cash loan in 5 minutes! Up to {big_amount}, walang guarantor. Just download: {link}. {ref}.",
    "Need emergency cash? Borrow up to {big_amount} with our app — no credit check required! {link}. {ref}.",
    "Fast loan approval! 30 minutes lang and {big_amount} na agad sa account mo. Apply here: {link}. {ref}.",

    # Escalating fee scams
    "Update po: May additional insurance fee pa po ng {small_amount} para ma-finalize yung loan niyo. Kailangan po today. {ref}.",
    "Sir/Ma'am, may documentary stamp tax pa po na {small_amount} na hindi kasama sa initial processing fee. Required po before release. {ref}.",
    "Your loan release was delayed due to a system upgrade. Pay the re-processing fee of {small_amount} to expedite. {link}. {ref}.",
    "May BIR withholding tax pa po na {small_amount}. Last payment na po to before release ng {big_amount}. {ref}.",

    # Loan shark masquerading as legit
    "Need cash? We offer salary loans up to {big_amount} with easy payment terms! No hidden fees. PM me to apply. {ref}.",
    "Emergency loan — released within the day! {big_amount} max amount, flexible payment. Just pay {small_amount} enrollment fee. {ref}.",
    "Low-interest personal loan available! {big_amount} limit. 1% monthly interest, walang fine print. Apply: {link}. {ref}.",
    "May kilala ako na legit na lender. {big_amount} loan, {small_amount} lang processing. Walang collateral, walang CI. PM lang. {ref}.",

    # Taglish lending scams
    "Lods, legit lending yan. {big_amount} agad ma-aapprove ka basta magbayad ka lang ng {small_amount} processing fee. Try mo: {link}. {ref}.",
    "Naka-loan na ako dyan ng {big_amount}. {small_amount} lang binayad ko na processing fee tapos released agad. Totoo lods! {link}. {ref}.",
    "Grabe, ang bilis ma-approve! {big_amount} loan ko, {small_amount} lang binayad ko. Legit talaga: {link}. {ref}.",
    "Uy may bago akong nadiscover na lending app. {big_amount} agad released sakin! Need mo lang mag-deposit ng {small_amount}. {link}. {ref}.",
    "Mga lods, kung kailangan niyo ng pera, I-try niyo to — {big_amount} instant approval. {small_amount} lang processing fee: {link}. {ref}.",
    "Boss, approved ka na for {big_amount}! Proceed ka lang ng payment ng {small_amount} sa account na to para ma-release na. {ref}.",

    # Text-message style lending scams
    "APPROVED: Loan #{ref_code} for {big_amount}. Pay {small_amount} via {ewallet} to release. Reply YES to confirm.",
    "Reminder: Your {big_amount} loan is ready. Settle the {small_amount} processing fee today to avoid cancellation. {link}.",
    "Pre-approved loan: {big_amount}. Requirements: Valid ID + {small_amount} processing fee. Apply: {link}. {ref}.",

    # "Government-affiliated" lending scams
    "SSS Salary Loan: You're eligible for up to {big_amount}. Processing fee of {small_amount} is required. Apply: {link}. {ref}.",
    "Pag-IBIG Multi-Purpose Loan: Pre-approved for {big_amount}. Pay {small_amount} admin fee to process. {link}. {ref}.",
    "GSIS member? You qualify for an emergency loan of {big_amount}. One-time fee of {small_amount}: {link}. {ref}.",

    # Zero-capital / no-risk promises
    "Zero capital loan! Borrow {big_amount} and start your business. No collateral, no co-maker. Just {small_amount} processing fee: {link}. {ref}.",
    "Walang guarantor? Walang problema! Loan of {big_amount} available for everyone. {small_amount} registration fee lang: {link}. {ref}.",
    "No credit history needed! Get {big_amount} approved today. Simple requirements + {small_amount} fee: {link}. {ref}.",

    # Additional variations
    "Instant cash advance up to {big_amount}! Get funds within the hour. Sign up fee: {small_amount}. {link}. {ref}.",
    "Payroll loan available for employed and self-employed! {big_amount} max. {small_amount} one-time fee. {link}. {ref}.",
    "Your credit limit has been increased to {big_amount}. Activate now by paying {small_amount}: {link}. {ref}.",
    "Kindly pay the processing fee to release your loan proceeds. Amount: {small_amount}. Send to {ewallet} acct. {ref}.",
]

# =============================================================================
# SCAM TEMPLATES — CATEGORY 5: EMPLOYMENT / RECRUITMENT FRAUD
# =============================================================================

employment_fraud_templates = [
    # Liking / task-based scams
    "Earn {daily_amount} per day by liking products online! No experience needed. Start here: {link}. {ref}.",
    "Complete simple tasks and receive commissions immediately! {daily_amount} daily potential. Join: {link}. {ref}.",
    "Work from home opportunity — like and review products for {daily_amount}/day! Free training provided. {link}. {ref}.",
    "Mag-like lang ng videos, kikita ka na ng {daily_amount} daily! Legit paying app to. Download: {link}. {ref}.",
    "Earn {amount} weekly just by watching ads and completing surveys! Register: {link}. {ref}.",
    "{daily_amount} per task — just rate products on our app! Payout via {ewallet}. Start: {link}. {ref}.",
    "Gusto mo kumita habang naka-phone lang? Like products and earn {daily_amount} daily. Proven: {link}. {ref}.",
    "Simple online tasks = big money! {daily_amount}/day, no boss, no schedule. Join our team: {link}. {ref}.",

    # Fake hiring
    "Hiring ASAP! Factory worker in {country}, no placement fee! Message me for details. {ref}.",
    "Looking for {job_title}? We're hiring — {amount} monthly salary! Apply now: {link}. {ref}.",
    "WE ARE HIRING: {job_title} position available! Work from home, {daily_amount} per day. Send resume to: {link}. {ref}.",
    "URGENT HIRING: {job_title} needed for our office in {country}. {amount} monthly + free housing. Apply: {link}. {ref}.",
    "Now hiring {job_title}s! No experience required, training provided. Salary: {amount}/month. {link}. {ref}.",
    "Job opening: {job_title} — work from home! {daily_amount} daily, payout via {ewallet}. Apply here: {link}. {ref}.",

    # Deposit-required jobs
    "Congrats! You passed our initial screening for {job_title}. Please pay the {small_amount} training fee to start. {link}. {ref}.",
    "Welcome to our team! To activate your {job_title} account, deposit {small_amount} as starting capital. Refundable after 1 month. {ref}.",
    "Hired! As a {job_title}, you need to deposit {small_amount} for your starter kit. This will be returned on your first payout. {ref}.",
    "Your {job_title} application is approved! Pay the {small_amount} orientation fee via {ewallet} to proceed. {ref}.",
    "You're in! {small_amount} lang ang registration fee for the {job_title} position. Deducted sa first salary mo. {ref}.",

    # Reseller / networking scams
    "Looking for active resellers! No capital needed. Kikita ka ng {amount} weekly. PM is the key 🔑. {ref}.",
    "Be your own boss! Join our reseller program — {amount} weekly income, no inventory needed. PM me. {ref}.",
    "Earn {amount} monthly as our brand ambassador! Just recruit 3 people to join. {link}. {ref}.",
    "Free mentorship + {daily_amount} daily income! Join our network marketing team. Limited slots: {link}. {ref}.",
    "Start your online business with us! {small_amount} capital lang, earn up to {amount} per month. {link}. {ref}.",

    # Overseas job scams
    "POEA-accredited agency hiring for {country}! {job_title} position, {amount}/month salary. No placement fee. PM me. {ref}.",
    "Direct hire sa {country}! {job_title} needed ASAP. Free visa, free ticket, free accommodation. Message me: {ref}.",
    "Hiring {job_title} for {country} — process within {time}! All expenses paid. Legit agency. {link}. {ref}.",
    "OFW opportunity! {country} is hiring {job_title}s. Salary: {amount}/month + benefits. Apply before deadline: {link}. {ref}.",
    "Walk-in interview for {country} jobs! {job_title} — {amount}/month. Bring 2 valid IDs. Address: [meeting place]. {ref}.",

    # Taglish employment scams
    "Lods, legit to! Nag-earn ako ng {daily_amount} kahapon lang sa pag-like ng products. Try mo: {link}. {ref}.",
    "Hiring kami ng {job_title}! {amount} ang salary per month. Walang experience needed. Apply na: {link}. {ref}.",
    "Sobrang dali ng trabaho — like lang ng like, tapos {daily_amount} agad sa {ewallet}! Download: {link}. {ref}.",
    "Pre, may alam akong legit na sideline — {daily_amount} per day. Gamit lang ng phone mo. PM me for details. {ref}.",
    "Naghahanap ka ba ng extra income? {daily_amount} per day lang sa pag-complete ng online tasks. Walang capital: {link}. {ref}.",
    "Sa lahat ng naghahanap ng work from home — try niyo to! {daily_amount} daily, payout sa {ewallet}. Legit: {link}. {ref}.",
    "Walang trabaho? Walang problema! Earn {daily_amount}/day online. No interview, no resume needed. Start: {link}. {ref}.",
    "Tara sideline! {job_title} position — part-time lang pero {daily_amount} ang kita per day. Apply: {link}. {ref}.",

    # Short recruitment scam messages
    "Hiring {job_title}. DM for details. {daily_amount}/day.",
    "WFH opportunity. {daily_amount} daily. No exp needed. {link}.",
    "Part-time online job. {amount}/month. PM is the key. {ref}.",

    # Additional variations
    "Looking for people interested in {job_title}? Sabi nila {reward}, kahit beginner puwede. {action}. {ref}.",
    "Crypto mining gamit ang phone! Earn {crypto} passively. Download here: {link}. {ref}.",
    "Be a mystery shopper! Get paid {daily_amount}/day to shop and review stores. Register: {link}. {ref}.",
    "Content creator wanted! Earn {amount}/month posting on social media. No followers needed. Apply: {link}. {ref}.",
]

# =============================================================================
# SCAM TEMPLATES — CATEGORY 6: CONSUMER PRODUCTS & SERVICES FRAUD
# =============================================================================

consumer_fraud_templates = [
    # Fake product listings
    "Selling brand new {item} — only {amount}! Limited stocks. PM to order. First come, first served! {ref}.",
    "SALE! {item} for only {amount}! Original, sealed, with warranty. Order now: {link}. {ref}.",
    "Flash sale: {item} at {amount} only! Regular price is triple. Grab yours: {link}. {ref}.",
    "Legit seller here! {item} brand new for {amount}. DM to reserve. Can ship via {shipping}. {ref}.",
    "Clearance sale! {item} — {amount} na lang! Last {qty} units. PM to order. {ref}.",

    # Advance payment pressure
    "Please pay first to reserve the item. Limited stocks only. Kindly settle payment immediately. {ref}.",
    "PM sent! Para ma-reserve yung {item}, need ko ng {small_amount} down payment. Balance upon delivery. {ref}.",
    "Pa-deposit na lang po ng {small_amount} para ma-hold yung {item}. Madami pong nag-iinquire. {ref}.",
    "Sir/Ma'am, limited stocks na po yung {item}. Pwede po ba mag-full payment muna? Ship ko agad pagkareceive. {ref}.",
    "Kindly settle the full amount of {amount} before we ship. We don't offer COD for this item. {ref}.",

    # COD-to-prepay switch
    "Sorry po, hindi na po available yung COD option. Pwede po ba GCash/Maya payment na lang? Ship within {time}. {ref}.",
    "Update: Our rider said your area is non-COD. Please transfer {amount} via {ewallet} for delivery. {ref}.",
    "Ma'am/Sir, nag-change na po ng policy yung courier — prepaid na lang po. I-send niyo na lang po yung {amount} sa {ewallet}. {ref}.",
    "J&T declined COD for your area. Kindly pay via {ewallet} — {amount}. Will ship same day. {ref}.",

    # Fake giveaway / freebies
    "Free {item} giveaway! Just share this post and register here: {link}. Winners announced in {time}! {ref}.",
    "🎉 GIVEAWAY: Win a brand new {item}! Like + Share + Comment DONE. Register: {link}. {ref}.",
    "Congratulations! You won a free {item} from our raffle! Claim it here: {link}. Pay {small_amount} shipping only. {ref}.",
    "Free {item} for the first 50 registrants! Sign up now: {link}. Shipping fee of {small_amount} lang. {ref}.",

    # Fake ticket / service scams
    "Concert tickets available! {amount} each. Limited supply. PM to reserve. GCash payment only. {ref}.",
    "Selling event tickets at discounted price — {amount}! Transfer payment first, will send e-ticket after. {ref}.",
    "Promo airfare! Manila to {country} — {amount} only! Book now: {link}. Limited slots. {ref}.",
    "Passport renewal fast-track service! Only {amount}. Skip the line. Message me for details. {ref}.",
    "Visa assistance for {country} — guaranteed approval! Service fee: {amount}. PM me. {ref}.",

    # Taglish consumer fraud
    "Lods, legit seller ako. {item} for {amount}. Sealed, brand new. Shipping via {shipping}. PM to order! {ref}.",
    "Grabe, ang mura! {item} — {amount} na lang! Last stocks na. Reserve na: {link}. {ref}.",
    "Sis/Bro, pa-reserve na kayo. {item} — {amount}. Marami nang nag-inquire. First come, first served! {ref}.",
    "Selling preloved {item} — {amount} na lang. Slightly used, good condition. GCash/Maya payment. PM me. {ref}.",
    "Brand new {item}, direct from supplier! Only {amount}. Full payment muna bago ship. {ref}.",
    "May {item} ako for sale — {amount}. Meetup or ship, pero need deposit {small_amount} muna para sure. {ref}.",
    "Pa-order na po! {item} — {amount}. COD available pero need {small_amount} reservation fee muna. {ref}.",

    # Pressure tactics
    "Limited stocks only. Kindly settle payment immediately. {ref}.",
    "Last 3 stocks na lang po ng {item}! {amount} — first to pay, first to ship. No reservation without payment. {ref}.",
    "Sale ends today! {item} for {amount}. After today, back to original price. Order: {link}. {ref}.",
    "Maraming nag-iinquire sa {item}. If you're serious, deposit {small_amount} now. {ref}.",
    "Uy lods, last piece na ng {item} — {amount}. Kung gusto mo, bayaran mo na agad. Pa-GCash na lang. {ref}.",

    # Dropship / wholesale scams
    "Wholesale {item} — {small_amount} per unit! Minimum order 10 pcs. Full payment before shipping. {link}. {ref}.",
    "Supplier direct! {item} for resellers — {small_amount} lang per piece. MOQ 20. PM for price list. {ref}.",
    "Dropshipping opportunity! Sell {item} for {amount} — your cost is only {small_amount}. Start now: {link}. {ref}.",

    # Additional variations
    "Gadget sale! {item} — {amount}! Nationwide delivery. Order here: {link}. GCash/Maya accepted. {ref}.",
    "Pre-order na! {item} arriving in {time}. Slot payment: {small_amount}. Balance upon arrival. {ref}.",
    "Imported {item} from {country}! Only {amount}. Authentic, with receipt. Full payment = priority shipping. {ref}.",
    "May nag-cancel na order kaya extra stock kami ng {item}. {amount} discounted price. PM asap. {ref}.",
]

# =============================================================================
# LEGITIMATE TEMPLATES — 8 CATEGORIES
# =============================================================================

# ── CATEGORY 1: DAILY LIFE ───────────────────────────────────────────────────
daily_life_templates = [
    "Kumain kami ni {name} sa {food} kanina. Masarap pa rin ang pagkain! 😄 {note}.",
    "Grabe ang traffic sa {location} ngayon! Late nanaman ako sa trabaho 😭 {note}.",
    "Ang init ng panahon ngayon! Gusto ko mag swimming ☀️🏖️ {note}.",
    "Sino gusto mag kape? Tara {food} tayo! ☕ {note}.",
    "Nag-grocery ako sa {location} kanina. Ang daming tao. {note}.",
    "Looking forward to the weekend! Pahinga din pag may time. {note}.",
    "Ang sarap ng ulam namin ngayon — sinigang! Best comfort food talaga. {note}.",
    "Random update: nag-grocery ako pagkatapos ng work. {filler}. {note}.",
    "Today felt simple: {simple_activity}. {filler}. {note}.",
    "After a busy day, nag-set aside ako ng Sunday para magpahinga. {filler}. {note}.",
    "Small win today! {simple_activity}, then naglaan ako ng time para magpahinga. {filler}. {note}.",
    "Finally! {simple_activity}, then naglaan ako ng time para magpahinga. {filler}. {note}.",
    "Late-night thoughts, {simple_activity}. {filler}. {note}.",
    "Grabe, natapos ko rin yung report. Ang simple ng araw pero okay lang. {filler}. {note}.",
    "Mga lods, {simple_activity}. Needed that break today. {filler}. {note}.",
    "Random thought! {simple_activity}, then naglaan ako ng time para magpahinga. {filler}. {note}.",
    "Just woke up and the weather is so nice today. Perfect para mag-{hobby}! {note}.",
    "Nagluto ako ng breakfast today — pancakes and eggs! Simple joys. {note}.",
    "Nag-commute ako kanina and ang chill ng byahe for once. Sana lagi ganito! {note}.",
    "Ang relaxing ng araw na to. Walang ginawa kundi mag-chill sa bahay. {note}.",
    "Ang lamig ng hangin ngayon! Perfect weather for hot choco ☕ {note}.",
    "Bumili ako ng ice cream kanina dahil ang init. Best decision ever! {note}.",
    "Cleaned my room today and it feels so satisfying. Productive Sunday! {note}.",
    "Random cravings: gusto ko ng pizza and {food} combo haha. {note}.",
    "Ang ganda ng sunset kanina! Nag-picture ako sa rooftop. {note}.",
    "Tried a new coffee shop sa {location}. Hindi naman masama yung latte nila. {note}.",
    "May ulan na naman! At least hindi ko na kailangan mag-dilig ng garden. {note}.",
    "Ang saya ng araw — walang traffic pauwi! Miracle talaga. {note}.",
    "Nag-jogging ako kanina sa park. Ang refreshing ng morning air. {note}.",
    "Nag-swimming kami sa beach. Ang ganda ng tubig! Perfect getaway. {note}.",
    "Ang sarap ng tulog ko kagabi. 8 hours solid! Feeling recharged. {note}.",
    "Nagising ako nang maaga today. First time in a long time! {note}.",
    "Nag-bike ride kami ni {name} sa {location}. Ang saya! {note}.",
    "Bumili ako ng bagong sapatos! Pinag-ipunan ko talaga to. {note}.",
    "Nag-try ako ng samgyupsal for the first time. Worth the hype! {note}.",
]

# ── CATEGORY 2: FINANCE — HARD NEGATIVES ─────────────────────────────────────
finance_legit_templates = [
    "Received my salary today and immediately set aside money for rent and utilities. Adulting talaga. {note}.",
    "Finally paid my credit card bill in full. Ang sarap sa feeling na zero balance ulit. {note}.",
    "I checked my bank balance today and finally hit my small savings goal. One step at a time. {note}.",
    "Nag-open ako ng separate account for travel savings. Hopefully enough na by next year. {note}.",
    "Bought a secondhand laptop using money I saved for months. Super happy with the purchase. {note}.",
    "Reading about personal finance lately, especially emergency funds and responsible budgeting. {note}.",
    "Crypto prices are interesting to watch, but I'm only reading about the market for now. {note}.",
    "Thank God, approved na yung scholarship allowance ko. Huge help for my school expenses. {note}.",
    "Finally got my first paycheck! Time to budget this money wisely. {note}.",
    "Praise God for the financial breakthrough! Finally paid off all my debts. 🙏 {note}.",
    "Working hard today so I can save money for our family trip next year. 💪 {note}.",
    "Investing in myself is the best decision I've made. Attending a seminar today! {note}.",
    "Just opened a new bank account today. Remembering to save money for the future! {note}.",
    "Nag-compute ako ng expenses ko this month. Medyo sumobra pero okay lang, next month mas magiging disciplined ako. {note}.",
    "Received my 13th month pay! Going straight to savings. Wag na mag-shopping haha. {note}.",
    "Nagtitipid talaga ako ngayon kasi gusto ko mag-invest sa mutual fund next year. {note}.",
    "Na-approve na yung SSS loan ko! At least may panggastos sa emergency. {note}.",
    "Bought stocks for the first time today. Small amount lang pero excited pa rin. Long-term investment naman. {note}.",
    "Nag-open ako ng digital bank account. Ang ganda ng interest rate compared sa traditional. {note}.",
    "Flex ko lang — zero credit card debt for 6 months straight! Discipline is key. {note}.",
    "Paid off my car loan finally! Financial freedom is the best feeling ever. {note}.",
    "Ang mahal ng bilihin ngayon. Good thing may meal plan ako to save on food expenses. {note}.",
    "Nag-withdraw ako ng pera sa ATM kanina. Grabe, ang haba ng pila. {note}.",
    "Bumili ako ng insurance sa wakas. Better late than never, diba? {note}.",
    "Nag-apply ako for Pag-IBIG housing loan. Excited for our future home! {note}.",
    "Finally set up my emergency fund — 6 months worth of expenses. Feels secure! {note}.",
    "Nag-try ako mag-compute ng retirement savings. Ang layo pa pero at least nag-start na. {note}.",
    "Masaya ako kasi naka-save ako ng {amount_legit} this month. Small progress pa rin! {note}.",
    "Na-refund na yung overcharge sa electric bill ko. At least honest yung company. {note}.",
    "Nag-update ako ng budget spreadsheet ko. Excel is my best friend this 2025. {note}.",
    "May bagong promo yung bank ko for savings account. Okay naman yung terms. {note}.",
    "Na-reach ko na yung savings goal ko for this quarter! Treat yourself naman konti. {note}.",
    "Ang hirap mag-budget pag May — graduation, Mother's Day, bills. Pero kaya naman. {note}.",
    "Nag-enroll ako sa financial literacy seminar. Free lang, sponsored ng LGU. {note}.",
    "Kinakaltas na yung HMO contribution ko sa salary. At least covered na ang health. {note}.",
]

# ── CATEGORY 3: RELIGIOUS / INSPIRATIONAL ─────────────────────────────────────
religious_templates = [
    "Thank you Lord for another year of life and countless blessings! 🙏🎂 {note}.",
    "Blessed Sunday everyone! Remember to go to church and thank Him for everything. {note}.",
    "Salamat sa Diyos sa lahat ng biyaya. Hindi madali pero kinakaya. {note}.",
    "Maturity is realizing what truly makes you rich — not money, not status, but faith. 🙏 {note}.",
    "God is good all the time! Despite the challenges, He never leaves us. {note}.",
    "Sunday well spent brings a week of content. Happy Sabbath everyone! {note}.",
    "Lord, thank you for the strength to face another week. Guide us always. 🙏 {note}.",
    "I love you guys! Thank you for the continuous support and love. {note}.",
    "Praying for everyone going through tough times. God has a plan for you. 🙏 {note}.",
    "Counting my blessings today: health, family, friends. What more can I ask for? {note}.",
    "Went to church today and the sermon was exactly what I needed to hear. {note}.",
    "His grace is sufficient. Whatever you're going through, trust the process. 🙏 {note}.",
    "Happy Easter everyone! Let us celebrate the risen King! 🐣✝️ {note}.",
    "Keep the faith, lods. Hindi tayo pinababayaan ng Diyos. Laban lang! {note}.",
    "Nag-rosary kami ng family kagabi. Ang peaceful ng feeling. {note}.",
    "Jeremiah 29:11 — For I know the plans I have for you. Claim it! 🙏 {note}.",
    "Ang ganda ng praise and worship kanina. Na-touch talaga ako. {note}.",
    "Thankful for another day of life. Not everyone gets this chance. {note}.",
    "Bible reading before bed — best habit I've developed this year. {note}.",
    "May God bless our hardworking frontliners and healthcare workers. 🙏 {note}.",
    "Hindi lahat ng biyaya pera. Minsan ang pinakamalaking blessing ay peace of mind. {note}.",
    "Nag-volunteer kami sa outreach program ng church. Sobrang fulfilling! {note}.",
    "Thank you Lord for the gift of family. Walang katumbas ang love nila. {note}.",
    "Everything happens for a reason. Trust His timing. 🙏 {note}.",
    "Ang galing ng Diyos — just when I thought I couldn't, He made a way. {note}.",
]

# ── CATEGORY 4: SOCIAL MEDIA / ENTERTAINMENT ──────────────────────────────────
entertainment_templates = [
    "Watching {show} all day. Perfect rest day! 🍿 {note}.",
    "Grabe yung ending ng {show}! No spoilers pero must-watch talaga! {note}.",
    "Bagong episode ng {show} — ang ganda! Sino pa nakapanood? {note}.",
    "Ang galing ng soundtrack ng {show}! On repeat sa playlist ko. 🎵 {note}.",
    "Nag-binge watch kami ng {show} buong weekend. Worth it naman! {note}.",
    "Sino nakakita nung viral video sa {location}? Ang funny talaga! 😂 {note}.",
    "New album ni [artist] ang ganda! Pang-whole day replay. 🎶 {note}.",
    "Finally watched that {show} everyone's been talking about. Medyo overhyped pero okay naman. {note}.",
    "Nag-concert kami kagabi! Ang saya ng experience! Best night ever! {note}.",
    "May bago na namang meme trend. Ang witty ng mga Pilipino talaga haha. {note}.",
    "Naglaro kami ng board games ng barkada. Ang saya! Walang phones allowed. {note}.",
    "Downloaded a new game on my phone. Ang addicting pero fun! {note}.",
    "Nag-karaoke kami sa bahay. Sino ang best singer? Syempre ako haha! 🎤 {note}.",
    "Tried a new playlist on Spotify. Perfect vibe for working from home. {note}.",
    "Ang ganda ng exhibit sa {location}! Highly recommended for art lovers. {note}.",
    "Nag-marathon ng Harry Potter movies buong holiday. Classic talaga! {note}.",
    "Sumakit mata ko kakabrowse ng social media. Time to rest na siguro. {note}.",
    "Sana may season 2 yung {show}. Ang bitin ng ending eh! {note}.",
    "Reading a new book today — finally something productive this weekend! {note}.",
    "Nag-try mag-vlog pero ang awkward ko on camera haha. Practice makes perfect! {note}.",
    "Ang ganda ng podcast na na-discover ko. Perfect for commute listening. {note}.",
    "Binili ko yung merch ng favorite band ko! Mahal pero worth it. {note}.",
    "Nag-gaming buong gabi. Di ko namalayan late na pala. Oops! {note}.",
    "Movie night with the family — popcorn, blankets, and {show}. Perfect! {note}.",
    "Ang viral nung dance challenge sa TikTok. Na-try ko pero fail haha. {note}.",
]

# ── CATEGORY 5: WORK / SCHOOL ────────────────────────────────────────────────
work_school_templates = [
    "Ang daming deadline this week. Sana matapos ko lahat on time! {note}.",
    "Nakakastress ang exam kanina. Sana pumasa ako! 📚 {note}.",
    "Finally finished my thesis! Years of hard work paid off. 🎓 {note}.",
    "First day at my new job! Excited and nervous at the same time. {note}.",
    "Got promoted today! All the hard work and late nights were worth it. 💪 {note}.",
    "Nag-submit ako ng project proposal kanina. Sana ma-approve! {note}.",
    "Working overtime again tonight. Pagod pero kailangan talaga. {note}.",
    "Had a great meeting with my team today. We're making real progress. {note}.",
    "Ang hirap mag-aral while working. But I know it'll be worth it someday. {note}.",
    "Board exam results are out next week. Lord, please! 🙏 {note}.",
    "Nag-attend ako ng company training today. Ang dami kong natutunan! {note}.",
    "Stressful day at work pero at least productive naman. {note}.",
    "Just passed my certification exam! One step closer to my dream career. {note}.",
    "Nagpresent ako sa meeting kanina. Super kaba pero nag-go well naman. {note}.",
    "Remote work setup talaga ang best. No commute, more time with family. {note}.",
    "Submitted my resignation today. Time for a new chapter! {note}.",
    "Ang saya — na-regularize na ako sa company! 6 months of probation done. {note}.",
    "Group project na naman. Sana cooperative lahat ng members this time. {note}.",
    "Had my annual performance review — nag-exceed expectations! Bonus loading? {note}.",
    "Nag-aral ako buong gabi for the midterms. Coffee is my best friend. {note}.",
    "Graduation day na bukas! Di pa rin ako makapaniwala. Sobrang thankful. {note}.",
    "New semester, new goals. This time mas magiging focused ako. {note}.",
    "Ang dami kong backlogs sa work. Need to catch up this weekend. {note}.",
    "Finished a big client project today. Time to celebrate with pizza! {note}.",
    "Nag-apply ako sa scholarship. Sana makapasa para makatipid sa tuition. {note}.",
]

# ── CATEGORY 6: FAMILY / RELATIONSHIPS ────────────────────────────────────────
family_templates = [
    "Happy birthday sa aking bestfriend! Sana marami pang blessings ang dumating sayo. {note}.",
    "Family dinner tonight! Ang saya pag kumpleto ang pamilya. {note}.",
    "Celebrated our anniversary today. Grateful for this person. ❤️ {note}.",
    "Missing my family back home. Video call na lang muna natin mamaya. {note}.",
    "Surprise birthday party for mama! Ang saya ng reaction niya! 🎂 {note}.",
    "Road trip with the barkada next weekend! Can't wait! 🚗 {note}.",
    "Ang cute ng pamangkin ko! Bagong tawa niya ang highlight ng araw ko. {note}.",
    "Mother's Day is coming! Time to plan something special for mama. {note}.",
    "Reunion with college friends after so many years. Parang kahapon lang! {note}.",
    "Nag-bond kami ng family sa {location}. Best weekend ever! {note}.",
    "Congratulations sa kapatid ko na nag-graduate today! Proud tito/tita here! 🎓 {note}.",
    "First time ko mag-cook para sa family. Medyo burnt pero appreciate nila effort haha. {note}.",
    "Nag-date kami ni hubby/wifey sa {food}. Simple pero sweet. {note}.",
    "Bagong baby sa family! Welcome to the world, little one! 👶 {note}.",
    "Father's Day greetings to all the hardworking dads out there! 💪 {note}.",
    "Nag-surprise visit sa parents. Ang saya ng faces nila! {note}.",
    "Group chat ng family never gets boring. Ang kukulit ng mga kapatid ko! {note}.",
    "Celebrated my grandparent's anniversary. 50 years together — true love! {note}.",
    "Nag-picnic kami sa park ng buong family. Simple but memorable. {note}.",
    "Ang hirap mag-LDR pero worth it naman pag nagkita na. {note}.",
    "Nag-shopping kami ng mama para sa holiday preparations. {note}.",
    "Thankful for friends who became family. You know who you are! {note}.",
    "Barkada reunion at {food}! Ang tanda na natin pero same energy pa rin. {note}.",
    "Welcome home sa ate/kuya ko from abroad! Missed you so much! {note}.",
    "Nag-videocall kami ng buong family kagabi. Connection ang pinaka-importante. {note}.",
]

# ── CATEGORY 7: HEALTH / FITNESS ─────────────────────────────────────────────
health_templates = [
    "Started going to the gym again today. Ang sakit ng legs ko! {note}.",
    "Day 30 of my running challenge — 5km today! Getting stronger. 🏃 {note}.",
    "Nag-try ako ng {sport} for the first time. Ang hirap pero ang saya! {note}.",
    "Morning yoga is the best way to start the day. Ang peaceful. 🧘 {note}.",
    "Finally hit my weight goal after months of discipline! {note}.",
    "Mental health reminder: It's okay to rest. You don't have to be productive every day. {note}.",
    "Started meal prepping this week. Healthier choices, happier body. {note}.",
    "Ang sakit ng katawan ko from yesterday's workout pero no pain no gain! {note}.",
    "Went for a run sa {location} this morning. Ang refreshing! {note}.",
    "Nag-try ako ng intermittent fasting. Day 3 palang pero feeling ko effective na. {note}.",
    "Regular checkup today — all results normal! Thank God for good health. {note}.",
    "Hydration reminder: Drink your water! 💧 Hindi joke yung 8 glasses a day. {note}.",
    "Ang ganda ng pakiramdam ko after weeks of consistent exercise. Confidence boost! {note}.",
    "Started taking vitamins regularly. Better late than never sa health. {note}.",
    "Nag-{sport} kami ng barkada. Ang saya kahit pawisan na lahat! {note}.",
    "Recovery day today — stretching and light walking lang. Rest is part of the process. {note}.",
    "Bumili ako ng new running shoes. Motivation to keep going! {note}.",
    "Joined a {sport} club sa barangay namin. Great way to meet new people! {note}.",
    "Cooked a healthy meal today — grilled fish and salad. Ang sarap pala! {note}.",
    "Ang importante ng sleep. 7-8 hours talaga ang kailangan. {note}.",
    "Started a 30-day fitness challenge. Day 1 done! Sana kayanin hanggang end. {note}.",
    "Nag-swimming sa public pool. Ang refreshing! Perfect exercise for summer. {note}.",
    "Annual physical exam today. Prevention is better than cure! {note}.",
    "Ang stress reliever ko ngayon is {hobby}. Better than scrolling endlessly. {note}.",
    "Nag-hike kami sa {location} — ang ganda ng view sa top! Worth the climb. {note}.",
]

# ── CATEGORY 8: E-COMMERCE — HARD NEGATIVES ──────────────────────────────────
ecommerce_legit_templates = [
    "Dumating na yung order ko sa Shopee! Ang bilis ng delivery. Happy customer! {note}.",
    "Nag-review ako ng products before buying. Research talaga bago checkout. {note}.",
    "Lazada sale ngayon! Naka-add to cart na ako ng marami pero di ko i-checkout lahat haha. {note}.",
    "Finally bought the {item} I've been eyeing for months. Reward ko sa sarili ko! {note}.",
    "COD order arrived today. Exactly as described — honest seller! 5 stars. {note}.",
    "Nag-return ako ng product sa Shopee. Smooth naman yung return process. {note}.",
    "May bagong Shopee voucher! Mag-check out na ba ako o mag-tiis? Decisions, decisions. {note}.",
    "Bought a gift for my friend online. Sana magustuhan niya! {note}.",
    "Nag-compare ako ng prices sa Lazada at Shopee. Shopee won this time! {note}.",
    "Sobrang reliable nung seller — fast shipping, good packaging, legit item. {note}.",
    "Ang hirap mag-pigil pag sale season. Add to cart game is strong! {note}.",
    "Na-deliver na yung online order ko. Quality is good for the price! {note}.",
    "Nag-sell ako ng preloved items online. Decluttering while earning! {note}.",
    "Checked the reviews first before buying. 4.8 stars with 10k+ sold — okay na yan! {note}.",
    "Nag-order ako ng groceries online. Ang convenient! Di na kailangan pumila. {note}.",
    "Flash sale alert pero di ko na-checkout on time. Sayang! Next time na lang. {note}.",
    "Nag-unbox ng Shopee haul — lahat ng items legit! Good finds for affordable prices. {note}.",
    "Bought school supplies online for my kids. Ang mura compared sa physical store! {note}.",
    "May ongoing promo sa GCash — cashback sa bills payment. Nag-avail na ako. {note}.",
    "Na-receive ko na yung GCash cashback from the promo. Legit naman pala! {note}.",
    "Nag-sell ako ng homemade pastries online. Ang daming orders! Grateful for the support. {note}.",
    "Waiting for my Lazada delivery — sana dumating today! Track ko na lang. {note}.",
    "Nag-order ng birthday cake online. Ang ganda ng reviews so excited na ako! {note}.",
    "Bought a phone case sa Shopee — {small_amount_legit} lang! Good quality naman. {note}.",
    "Nag-avail kami ng promo sa {food} — buy 1 take 1! Sulit talaga. {note}.",
]


# =============================================================================
# PLACEHOLDER FILL POOLS FOR LEGITIMATE TEMPLATES
# =============================================================================

names = ["Maria", "Juan", "Anna", "Mark", "Kat", "Carlo", "Jhay", "Mae", "Bea", "Paulo"]
simple_activities = [
    "naglinis ako ng garden", "nagluto ako ng ulam", "nag-ayos ako ng kwarto",
    "bumalik ako sa gym", "nag-shoot ako ng photos sa hapon",
    "nag-try ako ng bagong recipe", "paulit-ulit kong pinapakinggan yung bagong playlist",
    "nag-lunch kami ng family", "finally napanood ko yung movie",
    "ang daming deadline this week", "busy yung small shop this morning",
    "nag-laro ng basketball sa court", "naglakad kami sa park",
    "bumili ako ng bagong libro", "nag-drawing ako buong hapon",
]
fillers = [
    "Tomorrow ulit", "Worth it yung effort", "Small progress is still progress",
    "Need ko talaga ng rest after that", "Back to reality tomorrow haha",
    "Sulit naman kahit pagod", "At least productive ang araw",
    "Sana mas relaxed ang next few days", "Walang grand plan, enjoy lang muna",
    "Simple things pero nakaka-good mood",
]
amounts_legit = ["₱500", "₱1,000", "₱2,000", "₱3,000", "₱5,000"]
small_amounts_legit = ["₱99", "₱150", "₱200", "₱350", "₱499"]


# =============================================================================
# SCAM TEMPLATE FILL POOLS
# =============================================================================

offers = [
    "crypto airdrop", "shopping voucher promo", "mobile earning app",
    "cashback reward", "online raffle", "free data promo",
    "government cash assistance", "digital wallet bonus",
]
rewards = [
    "get paid for simple tasks", "earn passive income from your phone",
    "get a commission for every successful invite",
    "unlock a bonus after three referrals",
    "receive a large shopping voucher",
    "make dollars without experience",
    "secure a high-paying slot",
    "claim a limited cash reward",
    "turn ₱500 into a bigger payout",
    "receive a crypto bonus instantly",
    "withdraw earnings every afternoon",
]
promises = [
    "turn ₱500 into a bigger payout",
    "make dollars without experience",
    "earn passive income daily",
    "double your money in days",
    "get guaranteed returns",
    "receive crypto bonuses",
]
programs = [
    "referral program", "cashback program", "investment pool",
    "online commission job", "affiliate marketing system",
    "digital earning platform", "crypto mining network",
]
job_offers = [
    "online chat support", "data entry", "product review",
    "social media moderator", "commission job", "virtual assistant",
    "ad viewing", "video watching",
]
actions = [
    "click the link in the post", "reserve your slot today",
    "submit the online form", "pay the activation fee first",
    "connect your wallet for verification",
    "send the required deposit",
    "enter your account information",
    "message me ASAP",
    "send your details to the coordinator",
]
urgencies = [
    "sayang kung ma-late ka",
    "mabilis lang ang process",
    "first come, first served",
    "limited slots lang kaya bilisan",
    "open until midnight only",
    "huwag palampasin kung kailangan mo ng extra income",
    "no experience needed, perfect for beginners",
    "tested na raw ng mga kakilala ko",
    "legit daw and maraming payout screenshots",
]
qtys = ["2", "3", "5", "10", "15", "20"]


# =============================================================================
# GENERATION FUNCTIONS
# =============================================================================

def fill_scam_template(template):
    """Fill a scam template with random placeholder values."""
    result = template
    replacements = {
        "{bank}": random.choice(banks),
        "{ewallet}": random.choice(ewallets),
        "{platform}": random.choice(platforms),
        "{amount}": random.choice(amounts_peso + amounts_dollar),
        "{small_amount}": random.choice(small_amounts),
        "{big_amount}": random.choice(big_amounts),
        "{daily_amount}": random.choice(daily_amounts),
        "{link}": random_link(),
        "{ref}": random_ref(),
        "{ref_code}": random.choice(ref_codes),
        "{time}": random.choice(time_frames),
        "{time_short}": random.choice(time_frames_short),
        "{promo_code}": random.choice(promo_codes),
        "{job_title}": random.choice(job_titles),
        "{country}": random.choice(countries),
        "{crypto}": random.choice(crypto_names),
        "{item}": random.choice(product_items),
        "{shipping}": random.choice(shipping_methods),
        "{offer}": random.choice(offers),
        "{reward}": random.choice(rewards),
        "{promise}": random.choice(promises),
        "{program}": random.choice(programs),
        "{job_offer}": random.choice(job_offers),
        "{action}": random.choice(actions),
        "{urgency}": random.choice(urgencies),
        "{name}": random.choice(names),
        "{qty}": random.choice(qtys),
    }
    for key, val in replacements.items():
        result = result.replace(key, val)
    return result


def fill_legit_template(template):
    """Fill a legitimate template with random placeholder values."""
    result = template
    replacements = {
        "{name}": random.choice(names),
        "{food}": random.choice(food_places),
        "{location}": random.choice(locations),
        "{hobby}": random.choice(hobbies),
        "{show}": random.choice(shows_movies),
        "{sport}": random.choice(sports_activities),
        "{item}": random.choice(product_items),
        "{note}": random_note(),
        "{filler}": random.choice(fillers),
        "{simple_activity}": random.choice(simple_activities),
        "{amount_legit}": random.choice(amounts_legit),
        "{small_amount_legit}": random.choice(small_amounts_legit),
    }
    for key, val in replacements.items():
        result = result.replace(key, val)
    return result


def generate_scam_metadata():
    """Generate metadata for a scam account."""
    # ~55% typical scam (new account, high frequency)
    # ~15% medium-age accounts (could be either class)
    # ~15% old/hacked accounts (legitimate-looking age)
    # ~15% low posting frequency (stealthy scammers)
    roll = random.random()
    if roll < 0.55:
        age = random.randint(1, 60)
        freq = round(random.uniform(5.0, 30.0), 2)
    elif roll < 0.70:
        age = random.randint(60, 365)
        freq = round(random.uniform(3.0, 20.0), 2)
    elif roll < 0.85:
        age = random.randint(365, 2000)
        freq = round(random.uniform(5.0, 25.0), 2)
    else:
        age = random.randint(1, 120)
        freq = round(random.uniform(0.5, 4.0), 2)
    return age, freq


def generate_legit_metadata():
    """Generate metadata for a legitimate account."""
    # ~55% typical legit (old account, low frequency)
    # ~15% medium-age accounts (could be either class)
    # ~15% brand new legit users (just joined)
    # ~15% high posting frequency (active but legit users)
    roll = random.random()
    if roll < 0.55:
        age = random.randint(300, 3000)
        freq = round(random.uniform(0.1, 3.0), 2)
    elif roll < 0.70:
        age = random.randint(60, 365)
        freq = round(random.uniform(0.5, 5.0), 2)
    elif roll < 0.85:
        age = random.randint(1, 60)
        freq = round(random.uniform(0.1, 3.0), 2)
    else:
        age = random.randint(300, 2000)
        freq = round(random.uniform(5.0, 20.0), 2)
    return age, freq


# =============================================================================
# MAIN GENERATION PIPELINE
# =============================================================================

def generate_dataset():
    """Generate the full synthetic dataset."""
    data = []
    seen_texts = set()

    # ── SCAM DATA ─────────────────────────────────────────────────────────────
    scam_categories = {
        "Phishing": phishing_templates,
        "Investment Fraud": investment_fraud_templates,
        "Account Takeover": account_takeover_templates,
        "Online Lending Fraud": online_lending_fraud_templates,
        "Employment Fraud": employment_fraud_templates,
        "Consumer Fraud": consumer_fraud_templates,
    }

    total_scam_templates = sum(len(t) for t in scam_categories.values())
    print(f"\n📋 Total unique scam templates: {total_scam_templates}")

    # Distribute scam rows across categories
    scam_per_category = TARGET_SCAM // len(scam_categories)
    scam_remainder = TARGET_SCAM % len(scam_categories)

    scam_counts = {}
    for i, (cat_name, templates) in enumerate(scam_categories.items()):
        target = scam_per_category + (1 if i < scam_remainder else 0)
        count = 0
        attempts = 0
        max_attempts = target * 10  # Safety limit

        while count < target and attempts < max_attempts:
            template = random.choice(templates)
            text = fill_scam_template(template)
            text_hash = hashlib.md5(text.encode()).hexdigest()

            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                age, freq = generate_scam_metadata()
                data.append({
                    "text": text,
                    "account_age": age,
                    "posting_frequency": freq,
                    "label": 1
                })
                count += 1
            attempts += 1

        scam_counts[cat_name] = count
        print(f"   ✅ {cat_name}: {count} rows generated")

    total_scams = sum(scam_counts.values())
    print(f"   📊 Total scam rows: {total_scams}")

    # ── LEGITIMATE DATA ───────────────────────────────────────────────────────
    legit_categories = {
        "Daily Life": daily_life_templates,
        "Finance (Hard Negatives)": finance_legit_templates,
        "Religious / Inspirational": religious_templates,
        "Social Media / Entertainment": entertainment_templates,
        "Work / School": work_school_templates,
        "Family / Relationships": family_templates,
        "Health / Fitness": health_templates,
        "E-commerce (Hard Negatives)": ecommerce_legit_templates,
    }

    total_legit_templates = sum(len(t) for t in legit_categories.values())
    print(f"\n📋 Total unique legitimate templates: {total_legit_templates}")

    legit_per_category = TARGET_LEGIT // len(legit_categories)
    legit_remainder = TARGET_LEGIT % len(legit_categories)

    legit_counts = {}
    for i, (cat_name, templates) in enumerate(legit_categories.items()):
        target = legit_per_category + (1 if i < legit_remainder else 0)
        count = 0
        attempts = 0
        max_attempts = target * 10

        while count < target and attempts < max_attempts:
            template = random.choice(templates)
            text = fill_legit_template(template)
            text_hash = hashlib.md5(text.encode()).hexdigest()

            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                age, freq = generate_legit_metadata()
                data.append({
                    "text": text,
                    "account_age": age,
                    "posting_frequency": freq,
                    "label": 0
                })
                count += 1
            attempts += 1

        legit_counts[cat_name] = count
        print(f"   ✅ {cat_name}: {count} rows generated")

    total_legits = sum(legit_counts.values())
    print(f"   📊 Total legitimate rows: {total_legits}")

    # ── SHUFFLE AND SAVE ──────────────────────────────────────────────────────
    random.shuffle(data)
    df = pd.DataFrame(data)
    df.to_csv("synthetic_dataset.csv", index=False)

    # ── VALIDATION REPORT ─────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  SYNTHETIC DATASET GENERATION REPORT")
    print(f"{'='*60}")
    print(f"  Total rows:        {len(df)}")
    print(f"  Scam rows (1):     {(df['label']==1).sum()}")
    print(f"  Legit rows (0):    {(df['label']==0).sum()}")
    print(f"  Balance ratio:     {(df['label']==1).sum() / len(df) * 100:.1f}% scam / {(df['label']==0).sum() / len(df) * 100:.1f}% legit")
    print(f"  Unique texts:      {df['text'].nunique()} / {len(df)}")
    print(f"  Duplicate texts:   {len(df) - df['text'].nunique()}")
    print()
    print(f"  --- Scam Metadata Stats ---")
    scam_df = df[df['label']==1]
    print(f"  account_age:       min={scam_df['account_age'].min()}, max={scam_df['account_age'].max()}, mean={scam_df['account_age'].mean():.1f}")
    print(f"  posting_frequency: min={scam_df['posting_frequency'].min()}, max={scam_df['posting_frequency'].max()}, mean={scam_df['posting_frequency'].mean():.1f}")
    print()
    print(f"  --- Legit Metadata Stats ---")
    legit_df = df[df['label']==0]
    print(f"  account_age:       min={legit_df['account_age'].min()}, max={legit_df['account_age'].max()}, mean={legit_df['account_age'].mean():.1f}")
    print(f"  posting_frequency: min={legit_df['posting_frequency'].min()}, max={legit_df['posting_frequency'].max()}, mean={legit_df['posting_frequency'].mean():.1f}")
    print()

    # Category breakdown
    print(f"  --- Scam Category Breakdown ---")
    for cat, count in scam_counts.items():
        print(f"    {cat}: {count} rows ({count/total_scams*100:.1f}%)")
    print()
    print(f"  --- Legit Category Breakdown ---")
    for cat, count in legit_counts.items():
        print(f"    {cat}: {count} rows ({count/total_legits*100:.1f}%)")

    print(f"\n✅ Dataset saved to: synthetic_dataset.csv")
    print(f"{'='*60}")

    return df


if __name__ == "__main__":
    df = generate_dataset()
