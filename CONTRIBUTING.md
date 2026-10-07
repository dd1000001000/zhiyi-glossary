# 参与改进 / Contributing

谢谢你帮忙改进翻译！English below.

## 报告错误（不需要会 Git）

在 [Issues](https://github.com/dd1000001000/zhiyi-glossary/issues/new/choose) 里选“翻译纠错”，填上：
词、读音（中文词，可不填）、语言包、现在的翻译、建议改成什么。维护者或这门语言的审核人会整理进修订文件。

## 直接修改（Pull Request）

只改 `corrections/` 下的文件，不要改 `base/`（底稿会被重新生成）。

修订文件里，**一个词的所有行一起替换底稿里这个词的全部义项**：

```
# 词	读音	词性	译文	备注（可选）
行	hang	n.	row
行	hang	n.	bank	银行的“行”
意思	yi:si	n.	meaning
意思	yi:si	n.	intention
好像在	hao:xiang:zai	-		不是一个词：不显示翻译
```

（列之间用 Tab 分隔。）

- 改一个翻译：把这个词想保留的义项全部写进修订文件（包括没改的那些）。
- 删掉一个词的翻译：词性写 `-`，译文留空。
- 加新词：直接加，底稿里没有也可以。中文词必须写读音，每个字一个拼音音节，用 `:` 隔开，ü 写作 v（`lv:se`）。
- 英文词只用小写字母（以及 `'` 和 `-`），读音留空。

### 写法

- 词性只能用这些：`n.` 名词、`v.` 动词、`adj.` 形容词、`num.` 数词、`mw.` 量词、`pron.` 代词、`adv.` 副词、
  `prep.` 介词、`conj.` 连词、`part.` 助词、`int.` 叹词、`onom.` 拟声词、`det.` 限定词。
- 每个词最多 3 个义项，最常用的放第一个。只有意思确实不同、或者同一个意思常用作别的词性时才多写一个义项，
  不要把同义词拆成几个义项。
- 译文是目标语言的词典词形，1–3 个词：动词用原形（英语不加 to），小写，德语名词和专有名词按规则大写。
- 一行只写一个译文，不要用 `;`、`/`、`或` 列举同义词；不要加解释和问号。
- 数字用阿拉伯数字（万 → 10,000）。
- 助词这类没有对应词的，写简短的功能说明（吗 → question particle）。

### 提交前检查

```
python tools/check.py zh-ja        # 只检查改过的语言包；不带参数检查全部
```

不需要安装任何依赖（Python 3.8+）。PR 会自动运行同样的检查，不通过不能合并。

### Pull Request

- 每个 PR 只改一个主题（比如“修正日语里的量词”），说明改了什么、为什么。
- 提交时加 `-s` 签名（`git commit -s`），表示你有权按 GPL-3.0 贡献这些内容。
- 至少一位懂这门语言的审核人同意后合并。

## 发布（维护者）

1. `python tools/check.py`，然后 `python tools/build.py`：内容变了的语言包版本号加一，写入 `versions.json`。
2. 用软件更新的私钥给 `packs/glossary.json` 签名，得到 `glossary.json.sig`。
3. 把 `glossary.json`、`glossary.json.sig` 和变了的 `<语言包>.v<版本>.gloss` 上传到
   `dd1000001000/zhiyi_ime` 的 `glossary` Release（不覆盖旧版本的文件）。
4. 提交 `versions.json`，在 Release 说明里写上这次的改动和贡献者。

---

## Contributing (English)

**Report a mistake** without Git: open a *Translation fix* issue with the word, its reading
(Chinese, optional), the pack, the current and the suggested translation.

**Edit** only `corrections/`; `base/` is regenerated. All lines of a word in a corrections file
replace all its senses in the base, so list every sense you want to keep. `-` as the part of
speech (with an empty translation) removes the word; new words can be added (Chinese words need
the pinyin reading, one syllable per character joined by `:`, ü written as v; English words are
lowercase).

Rules: parts of speech `n. v. adj. num. mw. pron. adv. prep. conj. part. int. onom. det.`;
at most 3 senses, the most common first, only for clearly different meanings or another common
part of speech; dictionary forms of 1–3 words (verbs without "to", lowercase except German nouns
and names); one translation per line, no `;` `/` lists, notes or question marks; numerals as
digits; a short gloss for function words.

Run `python tools/check.py <pack>` before opening a pull request (no dependencies). Sign off your
commits (`git commit -s`) to confirm you may contribute them under GPL-3.0. A reviewer who knows
the language approves before merging.
