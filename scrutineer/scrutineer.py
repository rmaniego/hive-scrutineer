# -*- coding: utf-8 -*-
"""
    scrutineer.*
    ~~~~~~~~~

    Performance and quality analytics on Hive Posts.

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

import re
from .constants import ENGLISH_STOP_WORDS, ENGLISH_10K_WORDS #, LANGUAGE_MODEL
from nektar import Waggle


class Scrutineer:
    def __init__(
        self, minimum_score=80, max_user_tags=5, max_tags=5, retries=1, deep=False
    ):
        self._weights = [1, 1, 1, 1, 1]
        self._minimum_score = float(minimum_score)
        self._max_user_tags = int(max_user_tags)
        self._max_tags = int(max_tags)
        self._retries = int(retries)
        self._deep = isinstance(deep, bool) * bool(deep)
        self.analysis = {}

    def set_weights(self, title, body, images, tagging, tags):
        self._weights = [
            float(title),
            float(body),
            float(images),
            float(tagging),
            float(tags),
        ]

    def analyze(self, post, permlink=None, skip_bad_title=True):
        author = post
        if isinstance(post, dict):
            author = post["author"]
            permlink = post["permlink"]
        if not isinstance(post, dict):
            post = Waggle(author).get_post(author, permlink, retries=self._retries)
            if not post:
                return {}

        title = post["title"]
        if not len(title):
            return {}
        self.analysis["title"] = _analyze_title(title)
        if self.analysis["title"]["readability"] < (self._minimum_score / 100):
            return {}

        body = post["body"]
        if self._deep:
            unique_lines = []
            raw_body = body.split("\n")
            blogs = Waggle(author).blogs(author, limit=2)
            for blog in blogs:
                if blog["permlink"] == permlink:
                    continue
                raw_blog_body = blog["body"].split("\n")
                for line in raw_body:
                    if line not in raw_blog_body:
                        unique_lines.append(line)
                break
            body = "\n".join(unique_lines)
        

        cleaned, stripped = _parse_body(body)
        self.analysis["body"] = _analyze_body(cleaned, stripped, self._deep)

        if self._deep:
            keywords = self.analysis["body"]["seo_keywords"]
            self.analysis["title"] = _analyze_title(title, keywords)

        word_count = self.analysis["body"]["stripped"]
        self.analysis["images"] = _analyze_images(body, word_count)
        self.analysis["tagging"] = _analyze_overtagging(body, self._max_user_tags)

        tags = []
        if "tags" in post["json_metadata"]:
            tags = post["json_metadata"]["tags"]
        self.analysis["tags"] = _analyze_tags(tags, self._max_tags)

        score = 0
        score += self.analysis["title"]["score"] * self._weights[0]
        score += self.analysis["body"]["score"] * self._weights[1]
        score += self.analysis["images"]["score"] * self._weights[2]
        score += self.analysis["tagging"]["score"] * self._weights[3]
        score += self.analysis["tags"]["score"] * self._weights[4]
        score /= sum(self._weights)

        self.analysis["deep"] = self._deep
        self.analysis["score"] = score
        return self.analysis


def _analyze_title(title, keywords=None):
    analysis = {}
    length = len(title.encode("utf-8"))
    
    analysis["below_min"] = length < 30
    analysis["above_max"] = length > 60

    analysis["seo_keywords"] = 0
    analysis["readability"] = len(re.sub(r"[^\w\'\,\-\ ]+", "", title)) / length
    if isinstance(keywords, dict):
        for keyword in keywords.keys():
            if keyword in title.lower():
                analysis["seo_keywords"] = 1
                break
    else:
        analysis["seo_keywords"] = analysis["readability"]

    analysis["score"] = int(not (analysis["below_min"] or analysis["above_max"])) * (
        ((analysis["readability"] * 2) + analysis["seo_keywords"]) / 3
    )
    return analysis


def _parse_body(body):
    # remove images, replace whitespaces
    pattern = (
        r"!\[[\w\"\-\.~!#$%&'()*+,;=:@\/?\ ]*\]\([\w\"\-\.~!#$%&'()*+,;=:@\/?\ ]+\)"
    )
    cleaned = re.sub(pattern, "", body)
    cleaned = cleaned.replace("\n", " ")

    ## remove other formatting codes
    ## do not change order of patterns !!
    patterns = [
        r"\[\/\/\]:#[\ ]+\([!][\w\ \.]+\)" r"#+",  # hive services codes
        r"[*]+",
        r"[~]+",
        r"[_]+",
        r"[#]+",  # code blocks
        r"[`]+[\w]*[\ ]?",  # code blocks
        r"\|[\-]+\|[\-]+\|",  # table separator
        r"[\ ]*\|[\ ]*",  # remove pipe symbols
        r"<[\/]?[a-zA-Z]+[1-6]?[\w\"\-\.~!#$%&'()*+,;=:@\/?\ ]+>",  # html tags
        r"\]\([\w\"\-\.~!#$%&'*+,;=:@\/?\ ]+\)",  # links, right-side
        r">[\ ]?",
        r"--[\-]+",  # blocks, horizontal rule
        r"[\(\[\{\}\]\)]",  # trailing parentheses, brackets, and braces
        r"@[a-z0-9\-\.]{3,16}",  # user tags
        r"[^\w\s]",
    ]  
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned)
    cleaned = re.sub(r"[\s]+", " ", cleaned)

    ## strip non-ascii characters
    stripped = re.sub(r"[^\ -~]", "", cleaned)
    return cleaned, stripped

def _analyze_body(cleaned, stripped, deep):
    analysis = {}
    analysis["cleaned"] = len(cleaned.split(" "))
    analysis["stripped"] = len(stripped.split(" "))
    analysis["seo_keywords"] = _get_bigrams(stripped)

    """
    
    analysis["languages"] = {}
    if deep:
        guesses = []
        chunks = list(re.findall(r".{50}", stripped))
        normalized = [_normalize(x.ljust(50, " ")) for x in chunks]
        for chunk in normalized:
            languages = []
            for lang, weights in LANGUAGE_MODEL.items():
                likelihood = _resultant(chunk, weights)
                languages.append([likelihood, lang])
            guess = list(reversed(sorted(languages)))[0][1]
            guesses.append(guess)
        lines = len(guesses)
        for lang in set(guesses):
            analysis["languages"][lang] = guesses.count(lang) / lines
    """

    words = list(re.findall(r"\b\w\w+\b", stripped.lower()))
    words = len([x for x in words if x not in ENGLISH_10K_WORDS])
    if words > 50:
        analysis["stripped"] -= words
        analysis["cleaned"] -= words

    analysis["above_499"] = analysis["stripped"] > 499
    analysis["above_999"] = analysis["stripped"] > 999

    analysis["score"] = (
        (analysis["stripped"] / analysis["cleaned"])
        + analysis["above_499"]
        + analysis["above_999"]
    ) / 3
    return analysis


def _get_bigrams(contents, occurrence=4, limit=5):
    occurrence = int(occurrence)
    limit = int(limit)

    bigrams = {}
    words = list(re.findall(r"\b\w\w+\b", contents.lower()))
    words = [x for x in words if x not in ENGLISH_STOP_WORDS]
    for i in range(len(words) - 2):
        bigram = " ".join(words[i : i + 2])
        bigrams[bigram] = bigrams.get(bigram, 0) + 1

    keywords = []
    for b, o in bigrams.items():
        if o >= occurrence:
            keywords.append([b, o])
    keywords = list(reversed(sorted(keywords)))[:limit]
    return {b: o for b, o in keywords}


def _analyze_images(body, word_count):
    analysis = {}
    ## get image to text ratio
    image_ratio = 400 / 3
    pattern = r"!\[[\w\ \-\._~!$&'()*+,;=:@#\/?]*\]\([\w\-\.~!$%&'()*+,;=:@\/?]+\)"
    analysis["count"] = len(list(re.findall(pattern, body)))
    analysis["score"] = 0
    if analysis["count"]:
        value = abs(((word_count / analysis["count"]) - image_ratio))
        if 0 <= value <= image_ratio:
            analysis["score"] = 1 - (value / image_ratio)
    return analysis


def _analyze_overtagging(body, max_user_tags):
    analysis = {}
    tags = len(re.findall(r"@[a-z0-9\-\.]{3,16}", body))
    analysis["max_user_tags"] = max_user_tags
    analysis["count"] = tags
    analysis["score"] = 1
    if tags > max_user_tags:
        analysis["score"] = 1 / tags
    return analysis


def _analyze_tags(tags, max_tags):
    analysis = {}
    analysis["max_tags"] = max_tags
    analysis["count"] = len(tags)
    analysis["score"] = 0
    if analysis["count"]:
        analysis["score"] = 1
        if analysis["count"] > max_tags:
            analysis["score"] = 1 / (analysis["count"] - 5)
    return analysis

def _normalize(pattern, value=None):
    mx = 1114111
    pattern = [(ord(item)/mx) for item in pattern]
    if value is not None:
        return pattern + [value]
    return pattern

def _resultant(x, w):
    """
        x: inputs
        w: weights
    """
    v = x[0] * w[0]
    for i in range(1, len(x)):
        v += x[i] * w[i]
    return (v + w[-1])