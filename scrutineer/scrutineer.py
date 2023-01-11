# -*- coding: utf-8 -*-
"""
    scrutineer.*
    ~~~~~~~~~

    Performance and quality analytics on Hive Posts.

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

import re
from .constants import EMOJIS, STOP_WORDS, ENGLISH_WORDS
from nektar import Waggle

KNOWN_WORDS = STOP_WORDS + ENGLISH_WORDS

RE_DASH = re.compile(r"-")
RE_EN_DASH = re.compile(r"\u2013")
RE_EM_DASH = re.compile(r"\u2014")
RE_N_RANK = re.compile(r"\#[\d]+")
RE_DOLLARS = re.compile(r"\$[\d\,\.]+")
RE_POSSESSIVE = re.compile(r"\b[\w]+[']s\b")
RE_MULTI_SPACE = re.compile(r"\s{2,}")
RE_CLEAN_TITLE = re.compile(r"[^\w\'\,\ ]+")
RE_DELIMITERS = re.compile(r"[\n\.]")
RE_IMAGE = re.compile(r"!\[[^\]]*\]\([^\)]+\)")
RE_IMAGES = re.compile(r"!\[[^\]]*\]\([^\)]+\)[\s]{0,}!\[[^\]]*\]\([^\)]+\)")
RE_HIVE_SVC = re.compile(r"\[\/\/\]:#[\ ]+\([!][\w\ \.]+\)")
RE_ASTERISKS = re.compile(r"[\*]+")
RE_TILDES = re.compile(r"[~]+")
RE_UNDERSCORES = re.compile(r"[_]+")
RE_HEADERS = re.compile(r"[#][#]+")
RE_CODE_BLOCKS = re.compile(r"[`]+[\w]*[\ ]*")
RE_TABLE_SEP = re.compile(r"\|[\-]+\|[\-]+\|")
RE_PIPES = re.compile(r"[\ ]*\|[\ ]*")
RE_HTML_TAGS = re.compile(r"<[\/]?[a-zA-Z]+[1-6]?[^\>]+>")
RE_LINKS_RIGHT = re.compile(r"\]\([^\)]+\)")
RE_BLOCKQUOTES = re.compile(r">[\ ]?")
RE_HR = re.compile(r"--[\-]+")
RE_TRAILING_PARENTHESIS = re.compile(r"[\(\[\{\}\]\)]")
RE_USER_TAGS = re.compile(r"@[a-z0-9\-\.]{3,16}")
RE_NON_ASCII = re.compile(r"[^ -~]")
RE_WORDS = re.compile(r"\b\w\w+\b")


class Scrutineer:
    def __init__(
        self,
        minimum_score=80,
        max_emojis=0,
        max_user_tags=5,
        max_tags=5,
        retries=1,
        deep=False,
        full=False,
    ):
        self._weights = [1, 1, 1, 1, 1, 1]
        self._minimum_score = float(minimum_score)
        self._max_emojis = int(max_emojis)
        self._max_user_tags = int(max_user_tags)
        self._max_tags = int(max_tags)
        self._retries = int(retries)
        self._deep = isinstance(deep, bool) * bool(deep)
        self._full = isinstance(full, bool) * bool(full)
        self.analysis = {}

    def set_weights(self, title, body, emojis, images, tagging, tags):
        self._weights = [
            float(title),
            float(body),
            float(emojis),
            float(images),
            float(tagging),
            float(tags),
        ]

    def analyze(self, post, permlink=None, auto_skip=False):
        author = post
        if isinstance(post, dict):
            author = post["author"]
            permlink = post["permlink"]
        account = Waggle(author)
        if not isinstance(post, dict):
            post = account.get_post(author, permlink, retries=self._retries)
            if not post:
                return {}

        self.analysis["author"] = author
        self.analysis["permlink"] = permlink

        if self._full:
            self.analysis["url"] = post["url"]

        title = post["title"]
        if not len(title):
            return {}
        self.analysis["title"] = {}

        body = post["body"]
        if self._deep:
            unique_lines = []
            raw_body = body.split("\n")
            blogs = account.blogs(author, limit=2)
            for blog in blogs:
                if blog["permlink"] == permlink:
                    continue
                raw_blog_body = blog["body"].split("\n")
                for line in raw_body:
                    if line not in raw_blog_body:
                        unique_lines.append(line)
                break
            body = "\n".join(unique_lines)

        cleaned = _parse_body(body)
        if not len(cleaned):
            return {}

        keywords = _get_bigrams(cleaned)
        self.analysis["title"] = _analyze_title(title, keywords, self._full)

        self.analysis["body"] = {}
        self.analysis["emojis"] = _analyze_emojis(body, self._max_emojis, self._full)
        if auto_skip:
            if self._full:
                if (
                    self.analysis["emojis"]["score"] < 0.8
                    or self.analysis["title"]["score"] < 0.8
                ):
                    return {}
            elif self.analysis["emojis"] < 0.8 or self.analysis["title"] < 0.8:
                return {}
        self.analysis["body"] = _analyze_body(cleaned, self._deep, self._full)

        wcount = len(cleaned.split(" "))
        self.analysis["images"] = _analyze_images(body, wcount, self._full)
        self.analysis["tagging"] = _analyze_overtagging(
            body, self._max_user_tags, self._full
        )

        tags = []
        if "tags" in post["json_metadata"]:
            tags = post["json_metadata"]["tags"]
        self.analysis["tags"] = _analyze_tags(tags, self._max_tags, self._full)

        score = 0
        if not self._full:
            score += self.analysis["title"] * self._weights[0]
            score += self.analysis["body"] * self._weights[1]
            score += self.analysis["emojis"] * self._weights[2]
            score += self.analysis["images"] * self._weights[3]
            score += self.analysis["tagging"] * self._weights[4]
            score += self.analysis["tags"] * self._weights[5]
        else:
            score += self.analysis["title"]["score"] * self._weights[0]
            score += self.analysis["body"]["score"] * self._weights[1]
            score += self.analysis["emojis"]["score"] * self._weights[2]
            score += self.analysis["images"]["score"] * self._weights[3]
            score += self.analysis["tagging"]["score"] * self._weights[4]
            score += self.analysis["tags"]["score"] * self._weights[5]
        score /= sum(self._weights)

        self.analysis["deep"] = self._deep
        self.analysis["score"] = score
        return self.analysis


def _analyze_title(title, keywords, full=False):

    cleaned = title
    cleaned = RE_DASH.sub(" ", cleaned)
    cleaned = RE_EN_DASH.sub(" ", cleaned)
    cleaned = RE_EM_DASH.sub(" ", cleaned)
    cleaned = RE_N_RANK.sub(" ", cleaned)
    cleaned = RE_DOLLARS.sub(" ", cleaned)
    cleaned = RE_POSSESSIVE.sub("", cleaned)
    cleaned = RE_MULTI_SPACE.sub(" ", cleaned).strip()
    length = len(cleaned.encode("utf-8"))

    words = RE_CLEAN_TITLE.sub(" ", title.lower()).split(" ")
    cleaned = " ".join([w for w in words if w in KNOWN_WORDS])
    cleaned = cleaned.strip()

    bmin = length < 20
    amax = length > 80

    score = 0
    skeywords = 0
    readability = 0
    
    if length:
        readability = len(cleaned) / length
        if isinstance(keywords, dict):
            words = title.lower()
            for keyword in keywords.keys():
                if keyword in words:
                    skeywords = 1
                    break
        score = int(not (bmin or amax)) * (((readability * 9.5) + (skeywords * 0.5)) / 10)

    if not full:
        return score

    analysis = {}
    analysis["title"] = title
    analysis["cleaned"] = cleaned
    analysis["below_min"] = bmin
    analysis["above_max"] = amax
    analysis["keywords"] = keywords
    analysis["readability"] = readability
    analysis["keyword_score"] = skeywords
    analysis["score"] = score
    return analysis


def _parse_body(body):
    # remove images, replace whitespaces
    cleaned = RE_IMAGE.sub("", body).lower()
    cleaned = RE_DELIMITERS.sub(" ", cleaned)
    cleaned = RE_EN_DASH.sub(" ", cleaned)
    cleaned = RE_EM_DASH.sub(" ", cleaned)

    ## remove other formatting codes
    ## do not change order of patterns !!
    cleaned = RE_HIVE_SVC.sub("", cleaned)
    cleaned = RE_ASTERISKS.sub("", cleaned)
    cleaned = RE_TILDES.sub("", cleaned)
    cleaned = RE_UNDERSCORES.sub("", cleaned)
    cleaned = RE_HEADERS.sub("", cleaned)
    cleaned = RE_CODE_BLOCKS.sub("", cleaned)
    cleaned = RE_TABLE_SEP.sub("", cleaned)
    cleaned = RE_PIPES.sub("", cleaned)
    cleaned = RE_HTML_TAGS.sub("", cleaned)
    cleaned = RE_LINKS_RIGHT.sub("", cleaned)
    cleaned = RE_BLOCKQUOTES.sub("", cleaned)
    cleaned = RE_HR.sub("", cleaned)
    cleaned = RE_TRAILING_PARENTHESIS.sub("", cleaned)
    cleaned = RE_USER_TAGS.sub("", cleaned)
    cleaned = RE_MULTI_SPACE.sub(" ", cleaned)

    return cleaned


def _get_bigrams(contents, occurrence=4):
    occurrence = int(occurrence)

    bigrams = {}
    words = list(RE_WORDS.findall(contents.lower()))
    words = [x for x in words if x not in STOP_WORDS]
    for i in range(len(words) - 2):
        bigram = " ".join(words[i : i + 2])
        bigrams[bigram] = bigrams.get(bigram, 0) + 1

    keywords = []
    for b, o in bigrams.items():
        if o >= occurrence:
            keywords.append([b, o])
    keywords = list(reversed(sorted(keywords)))
    return {b: o for b, o in keywords}


def _analyze_body(words, deep, full=False):
    corpus = words.split(" ")
    cleaned = len([1 for x in corpus])
    english = len([x for x in corpus if x in KNOWN_WORDS])
    w400 = english > 400
    w800 = english > 800
    score = ((english / cleaned) + w400 + w800) / 3
    if not full:
        return score

    analysis = {}
    analysis["cleaned"] = cleaned
    analysis["english"] = english
    analysis["400+"] = w400
    analysis["800+"] = w800
    analysis["score"] = score
    return analysis


def _analyze_emojis(body, limit, full=False):
    chars = list(RE_NON_ASCII.findall(body))
    emojis = [c for c in chars if c in EMOJIS]

    count = len(emojis)
    score = int((count <= limit))
    if count > limit:
        score = limit / count
    if not full:
        return score

    analysis = {}
    analysis["limit"] = limit
    analysis["emojis"] = emojis
    analysis["count"] = count
    analysis["score"] = score
    return analysis


def _analyze_images(body, wcount, full=True):
    score = 0
    count = len(list(RE_IMAGE.findall(body)))
    sequences = len(list(RE_IMAGES.findall(body)))
    if count:
        scores = [0]
        for image in (1, 2, 3):
            image_ratio = 400 / image
            value = abs(((wcount / count) - image_ratio))
            if 0 <= value <= image_ratio:
                scores.append((1 - (value / image_ratio)))
        score = max(scores)
        if sequences:
            score = (score + (1 / sequences)) / 2
    if not full:
        return score

    analysis = {}
    analysis["count"] = count
    analysis["sequences"] = sequences
    analysis["score"] = score
    return analysis


def _analyze_overtagging(body, limit, full=False):
    tags = len(RE_USER_TAGS.findall(body))
    score = int((tags <= limit))
    if tags > limit:
        score = limit / tags
    if not full:
        return score

    analysis = {}
    analysis["limit"] = limit
    analysis["count"] = tags
    analysis["score"] = score
    return analysis


def _analyze_tags(tags, limit, full=False):
    score = int((len(tags) <= limit))
    if limit and len(tags) > limit:
        score = limit / len(tags)
    if not full:
        return score

    analysis = {}
    analysis["limit"] = limit
    analysis["count"] = len(tags)
    analysis["score"] = score
    return analysis
