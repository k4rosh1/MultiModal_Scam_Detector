import re
import cv2
import numpy as np_cv
import requests as http_requests
from urllib.parse import urlparse, quote
import html as _html_module

MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico',
    '.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v',
    '.mp3', '.wav', '.aac', '.ogg', '.flac', '.m4a',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
}

SOCIAL_PATTERNS = {
    'facebook': [r'facebook\.com', r'fb\.com', r'fb\.watch', r'm\.facebook\.com'],
    'twitter':  [r'twitter\.com', r'x\.com', r't\.co'],
    'instagram':[r'instagram\.com', r'instagr\.am'],
    'tiktok':   [r'tiktok\.com', r'vm\.tiktok\.com'],
    'youtube':  [r'youtube\.com', r'youtu\.be'],
}

# ── PAYMENT / E-WALLET / BANKING APPS ──
# Domains and app deep-link schemes for common PH e-wallets and banks.
# QR codes pointing at these are auto-rejected rather than scanned, since
# a scam-detector scoring a payment redirect for "scam-like text" is not
# a meaningful safety signal here — the risk is the money transfer itself.
PAYMENT_PATTERNS = {
    'gcash':        [r'gcash\.com', r'gcash://'],
    'maya':         [r'paymaya\.com', r'maya\.ph', r'paymaya://', r'maya://'],
    'gotyme':       [r'gotyme\.com\.ph', r'gotyme\.bank', r'gotyme://'],
    'unionbank':    [r'unionbankph\.com', r'unionbank://'],
    'bpi':          [r'bpi\.com\.ph', r'bpi://'],
    'bdo':          [r'bdo\.com\.ph', r'bdo://'],
    'metrobank':    [r'metrobank\.com\.ph', r'metrobank://'],
    'landbank':     [r'landbank\.com', r'landbank://'],
    'rcbc':         [r'rcbc\.com', r'rcbc://'],
    'securitybank': [r'securitybank\.com', r'securitybank://'],
    'coinsph':      [r'coins\.ph', r'coinsph://'],
    'shopeepay':    [r'shopeepay\.ph', r'shopeepay://'],
    'grabpay':      [r'grab\.com/.*(pay|wallet)', r'grabpay://'],
    'palawanpay':   [r'palawanpay\.ph', r'palawanpay://'],
}

_MEDIA_MIME_PREFIXES = ('image/', 'video/', 'audio/')
_MEDIA_MIME_EXACT = {
    'application/pdf', 'application/msword', 'application/vnd.ms-excel',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}

_BOILERPLATE_META_HINTS = (
    'qr code generator', 'make qr code', 'create qr code', 'scan qr code',
    'making free qr', 'qr codes online', 'free qr code',
)

# ── STEALTH HEADERS TO BYPASS ANTI-BOT PROTECTIONS ──
STEALTH_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1'
}

def _upscale_if_small(img, min_dim: int = 400):
    h, w = img.shape[:2]
    scale = max(1.0, min_dim / min(h, w))
    if scale > 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
    return img

def _decode_with_pyzbar(img) -> str:
    try:
        from pyzbar.pyzbar import decode as zbar_decode
    except ImportError:
        return ""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    results = zbar_decode(gray)
    if results: return results[0].data.decode("utf-8", errors="ignore").strip()
    enhanced = cv2.equalizeHist(gray)
    results = zbar_decode(enhanced)
    if results: return results[0].data.decode("utf-8", errors="ignore").strip()
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results = zbar_decode(thresh)
    if results: return results[0].data.decode("utf-8", errors="ignore").strip()
    return ""

def _decode_with_opencv(img) -> str:
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img)
    if data: return data.strip()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enhanced = cv2.equalizeHist(gray)
    data, bbox, _ = detector.detectAndDecode(cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR))
    if data: return data.strip()
    return ""

def decode_qr_from_image(image_bytes: bytes) -> str:
    nparr = np_cv.frombuffer(image_bytes, np_cv.uint8)
    img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not read image. Make sure it is a valid image file (PNG, JPG, etc.).")
    img = _upscale_if_small(img)
    data = _decode_with_pyzbar(img)
    if data: return data
    data = _decode_with_opencv(img)
    if data: return data
    raise ValueError("No QR code detected in this image. Make sure the image is clear and the QR code is fully visible.")

def _resolve_final_url_and_type(url: str, timeout: float = 5.0):
    try:
        resp = http_requests.head(url, headers=STEALTH_HEADERS, timeout=timeout, allow_redirects=True)
        content_type = resp.headers.get('Content-Type', '').lower()
        if resp.status_code >= 400 or resp.url == url or not content_type:
            resp = http_requests.get(url, headers=STEALTH_HEADERS, timeout=timeout, allow_redirects=True, stream=True)
            content_type = resp.headers.get('Content-Type', '').lower()
            resp.close()
        return (resp.url or url), content_type
    except Exception:
        return url, ''

def _is_media_content_type(content_type: str) -> bool:
    ct = content_type.split(';')[0].strip()
    return ct.startswith(_MEDIA_MIME_PREFIXES) or ct in _MEDIA_MIME_EXACT

PAYMENT_DISPLAY_NAMES = {
    'gcash': 'GCash', 'maya': 'Maya (PayMaya)', 'gotyme': 'GoTyme',
    'unionbank': 'UnionBank', 'bpi': 'BPI', 'bdo': 'BDO',
    'metrobank': 'Metrobank', 'landbank': 'Landbank', 'rcbc': 'RCBC',
    'securitybank': 'Security Bank', 'coinsph': 'Coins.ph',
    'shopeepay': 'ShopeePay', 'grabpay': 'GrabPay', 'palawanpay': 'PalawanPay',
}

def _match_payment_provider(*texts) -> str | None:
    """Checks one or more strings against PAYMENT_PATTERNS and returns the
    display name of the first matching provider, or None."""
    for text in texts:
        if not text:
            continue
        for provider, pats in PAYMENT_PATTERNS.items():
            if any(re.search(pat, text, re.IGNORECASE) for pat in pats):
                return PAYMENT_DISPLAY_NAMES.get(provider, provider.title())
    return None

def _is_emvco_payment_qr(content: str) -> bool:
    """
    Detects EMVCo-standard payment QR codes - the raw (non-URL) TLV payload
    format used by GCash, Maya, GoTyme, and virtually all QR Ph / InstaPay-
    compliant e-wallets and banks in the Philippines (and other EMVCo QR
    markets, e.g. Singapore's SGQR, Thailand's PromptPay).

    These always:
      - start with tag "00" (Payload Format Indicator), value "01"
      - end with tag "63" (CRC), length "04", + a 4-hex-char checksum
    That combination is specific enough to reliably fingerprint a payment
    payload without false-positiving on ordinary plain text.
    """
    c = content.strip()
    if len(c) < 20:
        return False
    if not c.startswith("000201"):
        return False
    if not re.search(r'6304[0-9A-Fa-f]{4}$', c):
        return False
    return True

def _looks_like_boilerplate(text: str) -> bool:
    return any(hint in text.lower() for hint in _BOILERPLATE_META_HINTS)

def _extract_body_text(html_src: str, max_len: int = 1000) -> str | None:
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html_src, re.IGNORECASE | re.DOTALL)
    body = body_match.group(1) if body_match else html_src
    body = re.sub(r'<(script|style|noscript|nav|header|footer)[^>]*>.*?</\1>', ' ', body, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', body)
    text = _html_module.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_len] if text else None

def _extract_page_info(url: str) -> dict:
    # ── YOUTUBE OVERRIDE ──
    is_youtube = bool(re.search(r'(youtube\.com|youtu\.be)', url, re.IGNORECASE))
    if is_youtube:
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={quote(url, safe='')}&format=json"
            yt_resp = http_requests.get(oembed_url, timeout=5)
            if yt_resp.status_code == 200:
                data = yt_resp.json()
                if "title" in data:
                    return {"text": data["title"][:1000], "is_wrapper": False}
        except Exception:
            pass
        return {"text": None, "is_wrapper": False}

    # ── X (TWITTER) OVERRIDE ──
    is_twitter = bool(re.search(r'(twitter\.com|x\.com)', url, re.IGNORECASE))
    if is_twitter:
        try:
            safe_url = url.replace('x.com', 'twitter.com')
            oembed_url = f"https://publish.twitter.com/oembed?url={quote(safe_url, safe='')}"
            tw_resp = http_requests.get(oembed_url, timeout=5)
            if tw_resp.status_code == 200:
                data = tw_resp.json()
                if "html" in data:
                    html_content = data["html"]
                    # Extract ONLY the tweet paragraph, ignoring author and date
                    p_match = re.search(r'<p[^>]*>(.*?)</p>', html_content, re.IGNORECASE | re.DOTALL)
                    if p_match:
                        clean_tweet = p_match.group(1)
                    else:
                        clean_tweet = html_content
                    
                    # Strip tags and pic.twitter.com links
                    clean_tweet = re.sub(r'<[^>]+>', ' ', clean_tweet)
                    clean_tweet = _html_module.unescape(clean_tweet).strip()
                    clean_tweet = re.sub(r'pic\.twitter\.com/\w+', '', clean_tweet).strip()
                    clean_tweet = re.sub(r'\s+', ' ', clean_tweet)
                    
                    return {"text": clean_tweet[:1000], "is_wrapper": False}
        except Exception:
            pass
        return {"text": None, "is_wrapper": False}

    # ── REDDIT OVERRIDE ──
    is_reddit = bool(re.search(r'reddit\.com', url, re.IGNORECASE))
    if is_reddit:
        try:
            base_url = url.split('?')[0].rstrip('/')
            json_url = f"{base_url}.json"
            red_resp = http_requests.get(json_url, headers=STEALTH_HEADERS, timeout=5)
            if red_resp.status_code == 200:
                data = red_resp.json()
                post_data = data[0]['data']['children'][0]['data']
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                combined = f"{title} {selftext}".strip()
                if combined:
                    return {"text": combined[:1000], "is_wrapper": False}
        except Exception:
            pass
        # Fall through to default scraping if JSON fails

    # ── DEFAULT SCRAPING WITH STEALTH HEADERS ──
    try:
        resp = http_requests.get(url, headers=STEALTH_HEADERS, timeout=5, allow_redirects=True)
        if resp.status_code != 200:
            return {"text": None, "is_wrapper": False}
        
        html_src = resp.text
        
        # SAFER DOMAIN-AGNOSTIC MEDIA CHECK
        is_media = bool(re.search(r'<meta[^>]+property=["\']og:(video|audio)["\']', html_src, re.IGNORECASE))
        if bool(re.search(r'<meta[^>]+property=["\']og:type["\'][^>]+content=["\'](video|music)["\']', html_src, re.IGNORECASE)):
            is_media = True
        
        body_text = _extract_body_text(html_src)
        clean_body = body_text if body_text else ""
        
        if len(clean_body) < 50 and re.search(r'<(video|audio)[^>]+>', html_src, re.IGNORECASE):
            is_media = True

        if is_media:
            return {"text": None, "is_wrapper": True}

        # NORMAL TEXT EXTRACTION
        meta_candidate = None
        og_desc = re.search(r"""<meta[^>]+property=["'](og:description)["'][^>]+content=["'](.*?)["']""", html_src, re.IGNORECASE | re.DOTALL)
        if og_desc and og_desc.group(2).strip():
            meta_candidate = _html_module.unescape(og_desc.group(2).strip())[:1000]

        if not meta_candidate:
            meta_desc = re.search(r"""<meta[^>]+name=["'](description)["'][^>]+content=["'](.*?)["']""", html_src, re.IGNORECASE | re.DOTALL)
            if meta_desc and meta_desc.group(2).strip():
                meta_candidate = _html_module.unescape(meta_desc.group(2).strip())[:1000]

        if meta_candidate and not _looks_like_boilerplate(meta_candidate):
            return {"text": meta_candidate, "is_wrapper": False}

        if body_text and not _looks_like_boilerplate(body_text):
            return {"text": body_text, "is_wrapper": False}

        if meta_candidate:
            return {"text": meta_candidate, "is_wrapper": False}
        if body_text:
            return {"text": body_text, "is_wrapper": False}

        title = re.search(r"""<title[^>]*>(.*?)</title>""", html_src, re.IGNORECASE | re.DOTALL)
        if title and title.group(1).strip():
            return {"text": _html_module.unescape(title.group(1).strip())[:1000], "is_wrapper": False}

        return {"text": None, "is_wrapper": False}
    except Exception:
        return {"text": None, "is_wrapper": False}

def classify_qr_content(content: str) -> dict:
    content = content.strip()

    # ── PAYMENT QR (EMVCo/QR Ph raw payload — GCash, Maya, GoTyme, PH banks) ──
    if _is_emvco_payment_qr(content):
        return {
            'type': 'payment_qr', 'platform': 'qr', 'is_media': False, 'is_payment': True,
            'scan_text': None,
            'note': 'This QR code is a payment/money-transfer QR (EMVCo / QR Ph format used by GCash, Maya, GoTyme, and other PH banks and e-wallets). Payment QR codes are not scanned for scam text — always verify the recipient name directly in your banking or e-wallet app before sending money.',
            'url': None, 'original_url': None, 'used_redirect': False,
        }

    data_uri_match = re.match(r'^data:([\w./+-]+);', content, re.IGNORECASE)
    if data_uri_match and _is_media_content_type(data_uri_match.group(1).lower()):
        return {'type': 'media_file', 'platform': 'qr', 'is_media': True, 'scan_text': None, 'note': f'This QR code embeds a media file directly ({data_uri_match.group(1)}). There is no text content to scan for scams.', 'url': None, 'original_url': None, 'used_redirect': False}

    is_url = content.startswith(('http://', 'https://', 'www.', 'ftp://'))

    # ── PAYMENT QR (custom app deep-link scheme, e.g. gcash://, maya://) ──
    # These use non-http URI schemes, so they must be checked here, before
    # the plain_text fallback below - they'd never reach the later resolved-
    # URL payment check since there's no http(s) URL to resolve.
    if not is_url:
        provider = _match_payment_provider(content)
        if provider:
            return {
                'type': 'payment_qr', 'platform': 'qr', 'is_media': False, 'is_payment': True,
                'scan_text': None,
                'note': f'This QR code opens a payment or e-wallet app ({provider}). Payment links are not scanned for scam text — always verify the recipient directly in your banking or e-wallet app before sending money.',
                'url': None, 'original_url': content, 'used_redirect': False,
            }
        return {'type': 'plain_text', 'platform': 'qr', 'is_media': False, 'scan_text': content, 'note': 'Plain text extracted from QR code.', 'url': None}

    original_content = content
    resolved_url, content_type = _resolve_final_url_and_type(content)
    used_redirect = resolved_url != original_content
    content = resolved_url

    KNOWN_MEDIA_WRAPPERS = [
        r'me-qr\.com/data/image',
        r'me-qr\.com/data/video',
        r'me-qr\.com/data/audio',
        r'me-qr\.com/data/pdf',
        r'me-qr\.com/data/file',
        r'scan\.page',
    ]
    
    for pattern in KNOWN_MEDIA_WRAPPERS:
        if re.search(pattern, content, re.IGNORECASE) or re.search(pattern, original_content, re.IGNORECASE):
            return {
                'type': 'media_file', 
                'platform': 'qr', 
                'is_media': True, 
                'scan_text': None, 
                'note': 'This QR code links to a hosted media page (image/video gallery). There is no text content to scan.', 
                'url': content, 
                'original_url': original_content, 
                'used_redirect': used_redirect
            }

    try:
        parsed = urlparse(content if content.startswith('http') else 'https://' + content)
        path   = parsed.path.lower()
        ext    = '.' + path.split('.')[-1] if '.' in path else ''
    except Exception:
        ext = ''

    redirect_note = f' (resolved from shortener/redirect: {original_content})' if used_redirect else ''

    matched_provider = _match_payment_provider(content, original_content)
    if matched_provider:
        return {
            'type': 'payment_qr', 'platform': 'qr', 'is_media': False, 'is_payment': True,
            'scan_text': None,
            'note': f'This QR code links to a payment or e-wallet app ({matched_provider}){redirect_note}. Payment links are not scanned for scam text — always verify the recipient directly in your banking or e-wallet app before sending money.',
            'url': content, 'original_url': original_content, 'used_redirect': used_redirect,
        }

    is_media_by_ext  = ext in MEDIA_EXTENSIONS
    is_media_by_type = _is_media_content_type(content_type)

    if is_media_by_ext or is_media_by_type:
        detected_as = ext if is_media_by_ext else content_type.split(';')[0]
        return {'type': 'media_file', 'platform': 'qr', 'is_media': True, 'scan_text': None, 'note': f'This QR code links directly to a media file ({detected_as}){redirect_note}. There is no text content to scan for scams.', 'url': content, 'original_url': original_content, 'used_redirect': used_redirect}

    page_info = _extract_page_info(content)
    
    if page_info["is_wrapper"]:
        return {
            'type': 'media_file', 
            'platform': 'qr', 
            'is_media': True, 
            'scan_text': None, 
            'note': 'This QR code links to a hosted media page (video/audio). There is no text content to scan.', 
            'url': content, 
            'original_url': original_content, 
            'used_redirect': used_redirect
        }

    matched_platform = next((p for p, pats in SOCIAL_PATTERNS.items() if any(re.search(pat, content, re.IGNORECASE) for pat in pats)), None)
    extracted_text = page_info["text"]

    if matched_platform:
        return {
            'type': 'social_media_url', 'platform': matched_platform, 'is_media': False,
            'scan_text': extracted_text if extracted_text else content,
            'note': f'Social media link detected ({matched_platform.capitalize()}){redirect_note}. ' + ('Post title extracted from page.' if extracted_text else 'Caption could not be extracted — scanning URL text instead.'),
            'url': content, 'original_url': original_content, 'used_redirect': used_redirect
        }

    return {
        'type': 'url', 'platform': 'qr', 'is_media': False,
        'scan_text': extracted_text if extracted_text else content,
        'note': f'URL extracted from QR code{redirect_note}. ' + ('Page content extracted and scanned for scam indicators.' if extracted_text else 'Could not extract page content — scanning URL text instead.'),
        'url': content, 'original_url': original_content, 'used_redirect': used_redirect
    }