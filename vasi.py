import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    filters, ContextTypes, CallbackQueryHandler
)

load_dotenv()
TOKEN          = os.getenv("TELEGRAM_BOT_TOKEN")
MY_TELEGRAM_ID = os.getenv("MY_TELEGRAM_ID")
WORKSPACE      = Path(os.getenv("WORKSPACE_DIR", "/app/workspace")).resolve()
SKILLS_DIR     = WORKSPACE / "skills"

# ── MODEL KADROSU ──────────────────────────────────────────────────────────────
from ollama import Client as OllamaClient
ollama_client = OllamaClient(host=os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434"))

MODELS = {
    "gatekeeper": os.getenv("OLLAMA_MODEL_GATEKEEPER", "qwen3:30b"),
    "strateji":   os.getenv("OLLAMA_MODEL_STRATEJI",   "command-r"),
    "teknik":     os.getenv("OLLAMA_MODEL_TEKNIK",     "gemma3:27b"),
    "kod":        os.getenv("OLLAMA_MODEL_KOD",        "qwen3-coder:30b"),
    "gorsel":     os.getenv("OLLAMA_MODEL_GORSEL",     "qwen3-vl:30b"),
}


# ══════════════════════════════════════════════════════════════════════════════
# SKILLS SİSTEMİ
# ══════════════════════════════════════════════════════════════════════════════

SKILL_TRIGGERS = {
    "youtube_icerik.md": [
        "youtube", "video", "senaryo", "script", "hook",
        "thumbnail", "başlık", "baslik", "açıklama", "aciklama",
        "etiket", "icerik üret", "kanal"
    ],
    "kod_yardimcisi.md": [
        "kod", "script", "python", "javascript", "hata", "debug",
        "refactor", "fonksiyon", "class", "api", "test",
        "optimize", "review", "incele", "düzelt", "duzelt"
    ],
}


def load_skill(skill_file: str) -> str:
    """Skill dosyasını workspace/skills/ altından okur."""
    path = SKILLS_DIR / skill_file
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return ""


def detect_skill(text: str) -> tuple[str, str]:
    """
    Mesaj metnine göre ilgili skill'i tespit eder.
    (skill_adi, skill_icerigi) döndürür.
    Eşleşme yoksa ("", "") döner.
    """
    t = text.lower()
    for skill_file, triggers in SKILL_TRIGGERS.items():
        if any(trigger in t for trigger in triggers):
            content = load_skill(skill_file)
            if content:
                skill_name = skill_file.replace(".md", "").replace("_", " ").title()
                return skill_name, content
    return "", ""


def list_skills() -> str:
    """Yüklü skill'leri listeler."""
    if not SKILLS_DIR.exists():
        return "Hic skill yuklenmemis. workspace/skills/ klasoru olusturun."
    skill_files = list(SKILLS_DIR.glob("*.md"))
    if not skill_files:
        return "Hic skill yuklenmemis."
    lines = ["Yuklu skill'ler:\n"]
    for f in sorted(skill_files):
        try:
            first_lines = f.read_text(encoding="utf-8").split("\n")
            aciklama = next(
                (l.replace("#", "").replace("SKILL:", "").strip()
                 for l in first_lines if l.strip() and l.startswith("#")),
                f.stem
            )
        except Exception:
            aciklama = f.stem
        lines.append(f"  {f.name} — {aciklama}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# GÜVENLİK KATMANI
# ══════════════════════════════════════════════════════════════════════════════

def is_authorized(update: Update) -> bool:
    """Tüm güvenlik kapılarını tek noktada kontrol eder."""
    user_id = str(update.effective_user.id)
    if MY_TELEGRAM_ID and user_id != MY_TELEGRAM_ID:
        return False
    if update.effective_chat.type != "private":
        return False
    if update.message and update.message.forward_origin:
        return False
    if update.message:
        age = (datetime.now(timezone.utc) - update.message.date).total_seconds()
        if age > 60:
            return False
    return True


def safe_path(filename: str) -> Path | None:
    """
    Path traversal saldırılarını engeller.
    ../../etc/passwd gibi girişler None döndürür.
    """
    try:
        target = (WORKSPACE / filename).resolve()
        if not target.is_relative_to(WORKSPACE):
            return None
        return target
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# DOSYA İŞLEMLERİ
# ══════════════════════════════════════════════════════════════════════════════

def list_workspace_files() -> str:
    files = list(WORKSPACE.rglob("*"))
    if not files:
        return "Workspace bos."
    lines = []
    for f in sorted(files):
        if f.is_file():
            size = f.stat().st_size
            rel  = f.relative_to(WORKSPACE)
            lines.append(f"  {rel}  ({size:,} byte)")
        elif f.is_dir():
            rel = f.relative_to(WORKSPACE)
            lines.append(f"  {rel}/")
    return "Workspace icerigi:\n" + "\n".join(lines)


def read_file(filename: str) -> tuple[str, str]:
    """(icerik, hata) dondurur. Path traversal korumali."""
    path = safe_path(filename)
    if path is None:
        return "", "Guvenlik: Bu dosya yolu workspace disina cikiyor."
    if not path.exists():
        matches = list(WORKSPACE.rglob(filename))
        if not matches:
            return "", f"'{filename}' bulunamadi. /liste ile dosyalari gorebilirsiniz."
        path = matches[0]
    if not path.is_file():
        return "", f"'{filename}' bir klasor."
    try:
        if path.suffix.lower() in {".pdf", ".docx", ".xlsx", ".png", ".jpg", ".jpeg", ".zip"}:
            return "", f"'{path.name}' binary bir dosya ({path.stat().st_size:,} byte)."
        content = path.read_text(encoding="utf-8", errors="replace")
        if len(content) > 12_000:
            content = content[:12_000] + "\n\n[... ilk 12 000 karakter ...]"
        return content, ""
    except Exception as e:
        return "", f"Dosya okunamadi: {e}"


def save_file(filename: str, content: str) -> str:
    """Path traversal korumali dosya yazma."""
    path = safe_path(filename)
    if path is None:
        return "Guvenlik: Bu dosya yolu workspace disina cikiyor."
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(content, encoding="utf-8")
        return f"'{filename}' kaydedildi ({len(content):,} karakter)."
    except Exception as e:
        return f"Kaydetme hatasi: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# MODEL SEÇİCİ & PROMPT
# ══════════════════════════════════════════════════════════════════════════════

def pick_model(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["kod", "script", "python", "docker", "hata", "debug",
                              "fonksiyon", "class", "import", "def ", "```"]):
        return MODELS["kod"]
    if any(k in t for k in ["analiz", "grafik", "gorsel", "tablo", "rapor", "pdf", "excel"]):
        return MODELS["gorsel"]
    if any(k in t for k in ["arastir", "neden", "hesapla", "trend",
                              "istatistik", "karsilastir", "acikla"]):
        return MODELS["teknik"]
    if any(k in t for k in ["e-posta", "yaz", "makale", "icerik", "strateji",
                              "blog", "sosyal medya", "taslak",
                              "youtube", "video", "senaryo", "script", "hook"]):
        return MODELS["strateji"]
    return MODELS["gatekeeper"]


def build_system_prompt(model: str, mode: str = "", skill_content: str = "") -> str:
    base = (
        f"Sen Vasi, {model} modeli uzerinde calisan kisisel bir yapay zeka asistansin. "
        "Turkce veya kullanicinin dilinde cevap ver. Kisa, net ve uygulanabilir ol."
    )
    extras = {
        "analiz": " Dosya icerigini analiz ediyorsun. Onemli bulgulari madde madde ozetle.",
        "rapor":  " Markdown formatinda, basliklar ve alt basliklarla yapilandirilmis rapor yaz.",
        "kod":    " Calisir, test edilebilir kod uret. Aciklamalari yorum satiri olarak ekle.",
    }
    prompt = base + extras.get(mode, "")

    # Skill varsa sistem promptuna ekle
    if skill_content:
        prompt += f"\n\n---\nAKTIF SKILL TALIMATLARI:\n{skill_content}\n---"

    return prompt


# ══════════════════════════════════════════════════════════════════════════════
# TELEGRAM KOMUTLARI
# ══════════════════════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    skill_sayisi = len(list(SKILLS_DIR.glob("*.md"))) if SKILLS_DIR.exists() else 0
    await update.message.reply_text(
        f"Vasi aktif. | Beyin: Ollama (yerel)\n"
        f"Yuklu skill: {skill_sayisi}\n\n"
        "Komutlar:\n"
        "/liste   - workspace dosyalarini goster\n"
        "/skills  - yuklu skill'leri goster\n"
        "/oku     <dosya> - dosya icerigini goster\n"
        "/analiz  <dosya> - dosyayi AI ile analiz et\n"
        "/rapor   <konu>  - rapor yaz ve kaydet\n"
        "/kod     <gorev> - kod yaz ve kaydet\n"
        "/kaydet  <dosya> <icerik> - dosya olustur\n"
        "/sil     <dosya> - dosya sil (onay ister)\n\n"
        "Skill aktifken mesajin basinda [SKILL: ...] gorursun."
    )


async def cmd_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    await update.message.reply_text(list_skills())


async def cmd_liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    await update.message.reply_text(list_workspace_files())


async def cmd_oku(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    if not context.args:
        await update.message.reply_text("Kullanim: /oku dosyaadi.txt")
        return
    filename = " ".join(context.args)
    content, err = read_file(filename)
    if err:
        await update.message.reply_text(err)
        return
    for i in range(0, len(content), 4000):
        await update.message.reply_text(content[i:i+4000])


async def cmd_analiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    if not context.args:
        await update.message.reply_text("Kullanim: /analiz dosyaadi.txt")
        return
    filename = " ".join(context.args)
    content, err = read_file(filename)
    if err:
        await update.message.reply_text(err)
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    model = MODELS["gorsel"]
    try:
        response = ollama_client.chat(
            model=model,
            messages=[
                {"role": "system", "content": build_system_prompt(model, "analiz")},
                {"role": "user",   "content": f"Su dosyayi analiz et:\n\n---\n{content}\n---"}
            ]
        )
        sonuc    = response["message"]["content"]
        out_name = f"analiz_{Path(filename).stem}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        context.user_data["pending_save"] = {
            "filename": out_name,
            "content":  f"# Analiz: {filename}\n\n{sonuc}"
        }
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Kaydet",   callback_data="save_pending:evet"),
            InlineKeyboardButton("Kaydetme", callback_data="save_pending:iptal"),
        ]])
        preview = sonuc[:1000] + ("..." if len(sonuc) > 1000 else "")
        await update.message.reply_text(
            f"[{model.upper()}]\n\n{preview}\n\n---\nKaydetmek istiyor musun? -> {out_name}",
            reply_markup=keyboard
        )
    except Exception as e:
        await update.message.reply_text(f"Analiz hatasi: {e}")


async def cmd_rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    if not context.args:
        await update.message.reply_text("Kullanim: /rapor yapay zeka guvenligi 2026")
        return
    konu = " ".join(context.args)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    model = MODELS["strateji"]
    try:
        response = ollama_client.chat(
            model=model,
            messages=[
                {"role": "system", "content": build_system_prompt(model, "rapor")},
                {"role": "user",   "content": f"Su konu hakkinda detayli rapor/makale yaz: {konu}"}
            ]
        )
        sonuc    = response["message"]["content"]
        out_name = f"rapor_{konu[:30].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        context.user_data["pending_save"] = {"filename": out_name, "content": sonuc}
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Kaydet",   callback_data="save_pending:evet"),
            InlineKeyboardButton("Kaydetme", callback_data="save_pending:iptal"),
        ]])
        await update.message.reply_text(
            f"[{model.upper()}] Rapor hazir.\n\nOnizleme:\n{sonuc[:600]}...\n\n"
            f"Kaydetmek istiyor musun? -> {out_name}",
            reply_markup=keyboard
        )
    except Exception as e:
        await update.message.reply_text(f"Rapor hatasi: {e}")


async def cmd_kod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    if not context.args:
        await update.message.reply_text("Kullanim: /kod CSV oku ve istatistik hesapla")
        return
    gorev = " ".join(context.args)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    model = MODELS["kod"]

    # Kod skill'i her zaman aktif et
    _, skill_content = detect_skill("kod yaz")

    try:
        response = ollama_client.chat(
            model=model,
            messages=[
                {"role": "system", "content": build_system_prompt(model, "kod", skill_content)},
                {"role": "user",   "content": f"Su gorevi yerine getiren Python kodu yaz: {gorev}"}
            ]
        )
        sonuc    = response["message"]["content"]
        out_name = f"kod_{gorev[:25].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.py"
        context.user_data["pending_save"] = {"filename": out_name, "content": sonuc}
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Kaydet",   callback_data="save_pending:evet"),
            InlineKeyboardButton("Kaydetme", callback_data="save_pending:iptal"),
        ]])
        await update.message.reply_text(
            f"[{model.upper()}] Kod hazir.\n\n{sonuc[:600]}...\n\n"
            f"Kaydetmek istiyor musun? -> {out_name}",
            reply_markup=keyboard
        )
    except Exception as e:
        await update.message.reply_text(f"Kod hatasi: {e}")


async def cmd_kaydet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Kullanim: /kaydet notlar.md Bu dosyaya yazilacak icerik")
        return
    filename = args[0]
    icerik   = " ".join(args[1:])
    context.user_data["pending_save"] = {"filename": filename, "content": icerik}
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Kaydet", callback_data="save_pending:evet"),
        InlineKeyboardButton("Iptal",  callback_data="save_pending:iptal"),
    ]])
    await update.message.reply_text(
        f"'{filename}' dosyasina {len(icerik):,} karakter yazilacak. Onayliyor musun?",
        reply_markup=keyboard
    )


async def cmd_sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return
    if not context.args:
        await update.message.reply_text("Kullanim: /sil dosyaadi.txt")
        return
    filename = " ".join(context.args)
    path = safe_path(filename)
    if path is None:
        await update.message.reply_text("Guvenlik: Bu dosya yolu workspace disina cikiyor.")
        return
    if not path.exists():
        await update.message.reply_text(f"'{filename}' bulunamadi.")
        return
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Evet, sil", callback_data=f"sil_evet|{filename}"),
        InlineKeyboardButton("Iptal",     callback_data="sil_iptal"),
    ]])
    await update.message.reply_text(
        f"'{filename}' kalici olarak silinecek. Onayliyor musun?",
        reply_markup=keyboard
    )


# ══════════════════════════════════════════════════════════════════════════════
# CALLBACK HANDLER
# ══════════════════════════════════════════════════════════════════════════════

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if str(query.from_user.id) != MY_TELEGRAM_ID: return

    data = query.data
    if data.startswith("save_pending:"):
        action = data.split(":")[1]
        if action == "iptal":
            await query.edit_message_text("Iptal edildi. Dosya kaydedilmedi.")
            context.user_data.pop("pending_save", None)
            return
        pending = context.user_data.get("pending_save")
        if not pending:
            await query.edit_message_text("Bekleyen kayit bulunamadi.")
            return
        sonuc = save_file(pending["filename"], pending["content"])
        context.user_data.pop("pending_save", None)
        await query.edit_message_text(sonuc)
        return

    if data == "sil_iptal":
        await query.edit_message_text("Iptal edildi.")
        return
    if data.startswith("sil_evet|"):
        _, filename = data.split("|", 1)
        path = safe_path(filename)
        if path is None:
            await query.edit_message_text("Guvenlik hatasi.")
            return
        try:
            path.unlink()
            await query.edit_message_text(f"'{filename}' silindi.")
        except Exception as e:
            await query.edit_message_text(f"Silinemedi: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# SERBEST MESAJ — Skills Destekli Smart Router
# ══════════════════════════════════════════════════════════════════════════════

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update): return

    metin = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # 1. Skill tespiti
    skill_adi, skill_content = detect_skill(metin)

    # 2. Dosya baglamı
    extra_context = ""
    found_file    = None
    for word in metin.split():
        if "." in word and len(word) > 3 and not word.startswith("http"):
            content, err = read_file(word)
            if content:
                extra_context = f"\n\n[Baglam - {word}]:\n{content[:4000]}"
                found_file = word
                break

    # 3. Model secimi
    model = pick_model(metin)

    try:
        response = ollama_client.chat(
            model=model,
            messages=[
                {"role": "system", "content": build_system_prompt(model, skill_content=skill_content)},
                {"role": "user",   "content": metin + extra_context}
            ]
        )
        yanit = response["message"]["content"]

        # Yanit etiketi
        bilgi = f"[{model.upper()}]"
        if skill_adi:
            bilgi += f" [SKILL: {skill_adi}]"
        if found_file:
            bilgi += f" ('{found_file}' okundu)"
        bilgi += "\n\n"

        for i in range(0, len(yanit), 4000):
            prefix = bilgi if i == 0 else ""
            await update.message.reply_text(prefix + yanit[i:i+4000])

    except Exception:
        await update.message.reply_text("SISTEM UYARISI: Baglanti hatasi. Ollama calisiyor mu?")


# ══════════════════════════════════════════════════════════════════════════════
# ANA DÖNGÜ
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Skills klasorunu otomatik olustur
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    skill_sayisi = len(list(SKILLS_DIR.glob("*.md")))

    print("Vasi basladi. Provider: OLLAMA")
    print(f"Yuklu skill: {skill_sayisi}")
    print("Veri yerel kaliyor. Ollama aktif.")
    print("Path traversal korumasi ve onay mekanizmasi aktif.")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("skills", cmd_skills))
    app.add_handler(CommandHandler("liste",  cmd_liste))
    app.add_handler(CommandHandler("oku",    cmd_oku))
    app.add_handler(CommandHandler("analiz", cmd_analiz))
    app.add_handler(CommandHandler("rapor",  cmd_rapor))
    app.add_handler(CommandHandler("kod",    cmd_kod))
    app.add_handler(CommandHandler("kaydet", cmd_kaydet))
    app.add_handler(CommandHandler("sil",    cmd_sil))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.run_polling()
