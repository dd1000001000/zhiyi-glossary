"""Checks the word lists (base/ and corrections/); exits with 1 when something must be fixed.

  python tools/check.py            every pack
  python tools/check.py zh-ja      one pack

On GitHub the problems are shown on the changed lines of the pull request.
"""
import os
import sys

from glossary_format import (MAX_SENSES, PACKS, POS, REMOVE, ROOT, entries, known_syllables,
                             pack_parts, read_tsv, translation_problem, word_problem)


def main():
    packs = sys.argv[1:] or PACKS
    unknown = [pack for pack in packs if pack not in PACKS]
    if unknown:
        sys.exit(f"unknown packs: {', '.join(unknown)} (known: {', '.join(PACKS)})")
    github = os.environ.get("GITHUB_ACTIONS") == "true"
    syllables = known_syllables()
    problems = 0

    def report(path, number, message):
        nonlocal problems
        problems += 1
        relative = path.relative_to(ROOT).as_posix()
        if github:
            print(f"::error file={relative},line={number}::{message}")
        else:
            print(f"{relative}:{number}: {message}")

    # Brand names may stay in Latin letters when the English translation is the same.
    english_names = {key: {text for _, text in senses}
                     for key, senses in entries(ROOT / "base" / "zh-en.tsv").items()}
    for key, senses in entries(ROOT / "corrections" / "zh-en.tsv").items():
        english_names[key] = {text for _, text in senses}

    for pack in packs:
        source, target = pack_parts(pack)
        for folder in ("base", "corrections"):
            path = ROOT / folder / f"{pack}.tsv"
            if folder == "base" and not path.exists():
                report(path, 1, "missing")
                continue
            seen_lines = set()
            senses_per_key = {}
            removed = set()
            for number, cells in read_tsv(path):
                if len(cells) < 4 or (folder == "base" and len(cells) > 4) or len(cells) > 5:
                    report(path, number, "expected word, reading, pos, translation"
                           + (" and an optional note" if folder == "corrections" else ""))
                    continue
                word, reading, pos, text = cells[:4]
                key = (word, reading)
                problem = word_problem(source, word, reading, syllables)
                if problem:
                    report(path, number, problem)
                if (word, reading, pos, text) in seen_lines:
                    report(path, number, "repeated line")
                seen_lines.add((word, reading, pos, text))
                if pos == REMOVE:
                    if folder == "base":
                        report(path, number, "'-' is for the corrections only")
                    elif text:
                        report(path, number, "a '-' line removes the word: leave the translation empty")
                    removed.add(key)
                    continue
                if pos not in POS:
                    report(path, number, f"part of speech must be one of {' '.join(POS)} or -")
                senses_per_key[key] = senses_per_key.get(key, 0) + 1
                if senses_per_key[key] == MAX_SENSES + 1:
                    report(path, number, f"at most {MAX_SENSES} senses per word")
                latin_name = word if source == "en" else None
                names = english_names.get(key, set()) if source == "zh" else set()
                problem = translation_problem(target, text, latin_name)
                if problem and any(translation_problem(target, text, name) is None
                                   for name in names):
                    problem = None
                if problem:
                    report(path, number, f"{text!r}: {problem}")
            for key in removed & set(senses_per_key):
                report(path, 1, f"{key[0]} is both removed ('-') and translated")
    if problems:
        print(f"{problems} problem(s)", file=sys.stderr)
        sys.exit(1)
    print(f"checked {len(packs)} pack(s): OK")


if __name__ == "__main__":
    main()
