import pandas as pd
import random

scam_templates = [
    "GRABE! Kumita ako ng {amount} pesos sa loob ng {time}! DM mo ko! 💰 {link}",
    "Gusto mo ba ng extra income? Walang ilalabas na pera, just watch videos and earn up to {amount} a day! Legit paying app. {link}",
    "Need mo ba ng work from home? We are hiring part time data encoders! {amount} daily. PM me how.",
    "Congratulations! You have been selected to receive {amount}. Click here to claim your prize {link}",
    "Invest {small_amount} and get {amount} back in 24 hours! 100% legit company with SEC registration. {link}",
    "Double your money in just {time}! Join our trading group now! Limited slots only. 💸 {link}",
    "Click the link to get free {small_amount} pesos GCash! Legit to guys kakakuha ko lang. {link}",
    "Looking for active resellers! No capital needed. Kikita ka ng {amount} weekly. PM is the key 🔑",
    "Paluwagan online! Slot 1 to 10 available. Tubong lugaw! {link}",
    "Earn {amount} instantly by simply signing up! Use my referral code: {code} 🤑",
    "May bago nanaman paying app! {amount} sign up bonus. Withdraw agad sa Gcash! {link}",
    "Crypto mining gamit ang phone! Earn bitcoin passively. Download here: {link}",
    "Hiring ASAP! Factory worker abroad, no placement fee! Message me for details.",
    "Free iPhone 14 Pro Max giveaway! Just share this post and register here: {link}",
    "Isang araw lang may {amount} na ako. Kung gusto mo matuto, click mo to {link}",
]

legit_templates = [
    "Kumain kami ni Maria sa Jollibee kanina. Masarap pa rin ang Chickenjoy! 😄",
    "Maturity is realizing what truly makes you rich. 🤍 Not money, not status, but having someone who loves Jesus. 🙏 A relationship rooted in Christ is a blessing. 🌱",
    "Just opened a new bank account today. Remembering to save money for the future! It's a true blessing to be financially stable.",
    "Grabe ang traffic sa EDSA ngayon! Late nanaman ako sa trabaho 😭",
    "Watching Netflix all day. Perfect rest day! 🍿",
    "Thank you Lord for another year of life and countless blessings! 🙏🎂",
    "Happy birthday sa aking bestfriend! Sana marami pang pera at blessings ang dumating sayo.",
    "Saan kaya magandang kumain sa BGC mamaya? Any recommendations?",
    "Nakakastress ang exam kanina. Sana pumasa ako! 📚",
    "Flex ko lang ang bago kong sapatos! Pinag-ipunan ko talaga to gamit ang sweldo ko.",
    "Praise God for the financial breakthrough! Finally paid off all my debts. 🙏",
    "Investing in myself is the best decision I've made. Attending a seminar today!",
    "Ang init ng panahon ngayon! Gusto ko mag swimming ☀️🏖️",
    "Sino gusto mag kape? Tara Starbucks tayo!",
    "Looking forward to the weekend! Pahinga din pag may time.",
    "Blessed Sunday everyone! Remember to go to church and thank Him for everything.",
    "Working hard today so I can save money for our family trip next year. 💪",
    "Finally got my first paycheck! Time to budget this money wisely.",
    "I love you guys! Thank you for the continuous support and love.",
    "Salamat sa Diyos sa lahat ng biyaya. Hindi madali pero kinakaya."
]

amounts = ["5,000", "10,000", "50,000", "$100", "$500", "100k"]
small_amounts = ["500", "1,000", "2,500"]
times = ["7 araw", "24 hours", "isang buwan", "3 days"]
links = ["bit.ly/earn123", "tinyurl.com/freecash", "www.legitearn.ph/register", "t.me/cryptogroup"]
codes = ["EARN2024", "FREE500", "RICH101"]

data = []

# Generate 500 Scams
for _ in range(500):
    text = random.choice(scam_templates).format(
        amount=random.choice(amounts),
        small_amount=random.choice(small_amounts),
        time=random.choice(times),
        link=random.choice(links),
        code=random.choice(codes)
    )
    age = random.randint(1, 60)
    freq = round(random.uniform(5.0, 30.0), 2)
    data.append({"text": text, "account_age": age, "posting_frequency": freq, "label": 1})

# Generate 500 Legits (Many containing money/religion keywords as Hard Negatives)
for _ in range(500):
    text = random.choice(legit_templates)
    age = random.randint(300, 3000)
    freq = round(random.uniform(0.1, 3.0), 2)
    data.append({"text": text, "account_age": age, "posting_frequency": freq, "label": 0})

# Shuffle the dataset
random.shuffle(data)

df = pd.DataFrame(data)
df.to_csv("hard_test_dataset.csv", index=False)
print(f"Generated hard_test_dataset.csv with {len(df)} rows.")
