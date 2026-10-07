"""The word lists of the Zhiyi IME language packs: file layout, rules, and the pack format.

A pack translates candidates of one source language ("zh" Chinese, "en" English) into one target
language. Its translations come from base/<pack>.tsv (generated) with corrections/<pack>.tsv
(edited by people) applied on top: all lines of a key in the corrections replace that key's
lines in the base.

TSV lines, one per sense, in the order shown:
    word <TAB> reading <TAB> part of speech <TAB> translation [<TAB> note]
reading: pinyin syllables joined by ":" for Chinese ("xian:zai", ü as v); empty for English.
part of speech: one of POS below; "-" in the corrections removes the word from the pack.
Lines starting with "#" are comments; the first other line is the column header.
"""
import hashlib
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = {
    "zh": ["en", "ja", "ko", "fr", "de", "es", "ru"],
    "en": ["zh", "ja", "ko", "fr", "de", "es", "ru"],
}
PACKS = [f"{source}-{target}" for source, targets in TARGETS.items() for target in targets]
LANGUAGE_NAMES = {"zh": "Chinese", "en": "English", "ja": "Japanese", "ko": "Korean",
                  "fr": "French", "de": "German", "es": "Spanish", "ru": "Russian"}

# Part of speech labels and their codes in the pack file (engine/include/cxxime/glossary.h).
POS = {"n.": 1, "v.": 2, "adj.": 3, "num.": 4, "mw.": 5, "pron.": 6, "adv.": 7, "prep.": 8,
       "conj.": 9, "part.": 10, "int.": 11, "onom.": 12, "det.": 13}
REMOVE = "-"
MAX_SENSES = 3
HEADER = ["word", "reading", "pos", "translation"]

# What a translation must contain in each target language.
SCRIPT = {
    "zh": re.compile(r"[一-鿿]"),
    "ja": re.compile(r"[぀-ヿ一-鿿0-9]"),
    "ko": re.compile(r"[가-힯0-9]"),
    "ru": re.compile(r"[Ѐ-ӿ0-9]"),
}
LATIN = re.compile(r"[A-Za-zÀ-ɏ0-9]")
HAN = re.compile(r"[一-鿿]")
FORBIDDEN = re.compile(r"[?？—–;；|\t]")
MAX_CHARS = {"zh": 8, "ja": 12, "ko": 14}
DEFAULT_MAX_CHARS = 32
CHINESE_WORD = re.compile(r"^[〇㐀-䶿一-鿿\U00020000-\U0003134f]+$")
ENGLISH_WORD = re.compile(r"^[a-z][a-z'\-]*$")
SYLLABLE = re.compile(r"^[a-z]+$")

MAGIC = b"ZYGLOSS\0"
FORMAT_VERSION = 1
HEADER_SIZE = 96
END_OF_SENSES = 0xFF


def pack_parts(pack):
    source, target = pack.split("-")
    return source, target


def translation_problem(target, text, latin_name=None):
    """Why `text` cannot be shown as a translation into `target`, or None.

    `latin_name`: the word's Latin spelling (its English translation, or the English word);
    a translation equal to it is a name (Tencent, CNN) and allowed in any language."""
    if not text or text != text.strip():
        return "empty or with spaces around it"
    if "  " in text:
        return "double space"
    if FORBIDDEN.search(text):
        return "contains ? — ; | or a tab (one translation per line)"
    if len(text) > MAX_CHARS.get(target, DEFAULT_MAX_CHARS):
        return f"longer than {MAX_CHARS.get(target, DEFAULT_MAX_CHARS)} characters"
    script = SCRIPT.get(target, LATIN)
    is_name = latin_name is not None and text.lower() == latin_name.lower() and LATIN.search(text)
    if not script.search(text) and not is_name:
        return f"not written in {LANGUAGE_NAMES[target]}"
    if target not in ("zh", "ja") and HAN.search(text):
        return "contains Chinese characters"
    return None


def word_problem(source, word, reading, syllables=None):
    """Why (word, reading) is not a valid key for `source`, or None."""
    if source == "zh":
        if not CHINESE_WORD.match(word):
            return "the word must be Chinese characters only"
        parts = reading.split(":") if reading else []
        if len(parts) != len(word):
            return "the reading needs one pinyin syllable per character (xian:zai)"
        for syllable in parts:
            if not SYLLABLE.match(syllable) or (syllables is not None and syllable not in syllables):
                return f"unknown pinyin syllable {syllable!r} (write ü as v)"
        return None
    if not ENGLISH_WORD.match(word):
        return "the word must be lowercase English letters"
    if reading:
        return "English words have no reading"
    return None


def read_tsv(path):
    """[(line number, [cells])] of the data lines; the header and comments are skipped."""
    rows = []
    if not path.exists():
        return rows
    header_seen = False
    with open(path, encoding="utf-8") as f:
        for number, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            cells = line.split("\t")
            if not header_seen:
                header_seen = True
                if cells[:4] == HEADER:
                    continue
            rows.append((number, cells))
    return rows


def entries(path):
    """{(word, reading): [(pos, translation)]} in file order, with the order of first keys."""
    result = {}
    for _, cells in read_tsv(path):
        cells = (cells + [""] * 4)[:4]
        word, reading, pos, text = cells
        result.setdefault((word, reading), []).append((pos, text))
    return result


def merged_entries(pack):
    """The pack's words: base with the corrections applied, in base order (new words last)."""
    merged = entries(ROOT / "base" / f"{pack}.tsv")
    for key, senses in entries(ROOT / "corrections" / f"{pack}.tsv").items():
        if any(pos == REMOVE for pos, _ in senses):
            merged.pop(key, None)
        else:
            merged[key] = senses
    return merged


def known_syllables():
    syllables = set()
    for pack in PACKS:
        if pack.startswith("zh-"):
            for (word, reading) in entries(ROOT / "base" / f"{pack}.tsv"):
                syllables.update(reading.split(":"))
    syllables.discard("")
    return syllables


def pack_bytes(pack, merged, version, built, source_sha256):
    """The .gloss file (engine/include/cxxime/glossary.h) and the sha256 of its contents."""
    source, target = pack_parts(pack)
    first_reading = {}
    for (word, reading) in merged:
        first_reading.setdefault(word, reading)
    items = []
    for (word, reading), senses in merged.items():
        key = f"{word}\t{reading}" if source == "zh" else word
        primary = 1 if source != "zh" or first_reading[word] == reading else 0
        items.append((key.encode("utf-8"), primary, senses[:MAX_SENSES]))
    items.sort(key=lambda item: item[0])
    blob = bytearray()
    index = bytearray()
    for key, primary, senses in items:
        key_offset = len(blob)
        blob += key + b"\0"
        value_offset = len(blob)
        blob.append(primary)
        for pos, text in senses:
            blob.append(POS[pos])
            blob += text.encode("utf-8") + b"\0"
        blob.append(END_OF_SENSES)
        index += struct.pack("<II", key_offset, value_offset)
    content = bytes(index) + bytes(blob)
    header = bytearray(HEADER_SIZE)
    header[0:8] = MAGIC
    struct.pack_into("<HHI", header, 8, FORMAT_VERSION, 0, version)
    header[16:24] = source.encode().ljust(8, b"\0")
    header[24:32] = target.encode().ljust(8, b"\0")
    struct.pack_into("<II", header, 32, len(items), built)
    header[40:72] = source_sha256
    struct.pack_into("<III", header, 72, HEADER_SIZE, HEADER_SIZE + len(index), len(blob))
    return bytes(header) + content, hashlib.sha256(content).hexdigest(), len(items)
