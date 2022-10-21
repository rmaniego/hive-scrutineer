# -*- coding: utf-8 -*-
"""
    scrutineer.*
    ~~~~~~~~~

    Performance and quality analytics on Hive Posts.

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

import re
from nektar import Waggle

class Scrutineer:
    def __init__(self, minimum_score=80, max_user_tagging=5, retries=1, deep=False):
        self._weights = [1, 1, 1, 1]
        self._minimum_score = float(minimum_score)
        self._max_user_tagging = int(max_user_tagging)
        self._retries = int(retries)
        self._deep = isinstance(deep, bool) * bool(deep)
        self.analysis = {}

    def set_weights(self, title, body, images, tagging):
        self._weights = [float(title), float(body), float(images), float(tagging)]

    def analyze(self, author, permlink, skip_bad_title=False):
        hive = Waggle(author)
        post = hive.get_post(author, permlink, retries=self._retries)
        if not post:
            return {}

        self.analysis["title"] = _analyze_title(post["title"])
        
        if self.analysis["title"]["score"] < (self._minimum_score/100):
            return {}

        body = post["body"]
        if self._deep:
            unique_lines = []
            raw_body = body.split("\n")
            blogs = hive.blogs(author, limit=3)
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
        self.analysis["body"] = _analyze_body(cleaned, stripped)

        word_count = self.analysis["body"]["stripped"]
        self.analysis["images"] = _analyze_images(body, word_count)

        self.analysis["tagging"] = _analyze_overtagging(stripped, self._max_user_tagging)
        
        score = 0
        score += self.analysis["title"]["score"] * self._weights[0]
        score += self.analysis["body"]["score"] * self._weights[1]
        score += self.analysis["images"]["score"] * self._weights[2]
        score += self.analysis["tagging"]["score"] * self._weights[3]
        score /= sum(self._weights)
        
        self.analysis["deep"] = self._deep
        self.analysis["total_score"] = score
        return self.analysis

def _analyze_title(title):
    analysis = {}
    length = len(title.encode("utf-8"))
    analysis["below_min"] = length < 30
    analysis["above_max"] = length > 60
    analysis["readability"] = len(re.sub(r"[^\w\'\,\-\ ]+", "", title)) / length
    analysis["score"] = (
        int(not (analysis["below_min"] or analysis["above_max"]))
        * analysis["readability"]
    )
    return analysis


def _analyze_overtagging(body, max_user_tagging):
    analysis = {}
    tags = len(re.findall(r"[\ ]?@[a-z0-9\-\.]{3,16}[\ ]?", body))
    analysis["max_user_tagging"] = max_user_tagging
    analysis["count"] = tags
    analysis["score"] = 1
    if tags > max_user_tagging:
        analysis["score"] = 1 / tags
    return analysis


def _parse_body(body):
    # remove images, replace whitespaces
    pattern = r"!\[[\w\ \-\._~!$&'()*+,;=:@#\/?]*\]\([\w\-\.~!$%&'()*+,;=:@\/?]+\)"
    cleaned = re.sub(pattern, "", body)
    cleaned = cleaned.replace("\n", " ")

    ## remove other formatting codes
    ## do not change order of patterns !!
    patterns = [
        r"\[\/\/\]:#[\ ]+\([!][\w\ \.]+\)" r"#+",  # hive services codes
        r"[*]+",
        r"[~]+",
        r"[_]+",
        r"[`]+[\w]*[\ ]?",  # headers, text formatting
        r"\|[\-]+\|[\-]+\|",  # table separator
        r"[\ ]*\|[\ ]*",  # remove pipe symbols
        r"<[\/]?[a-zA-Z]+[1-6]?[\ \w\=\"\']+>",  # html tags
        r"\]\([\w\d\-._~!$&'()*+,;=:@#\/?]+\)",  # links, right-side
        r">[\ ]?",
        r"--[\-]+",  # blocks, horizontal rule
        r"[\(\[\{\}\]\)]",
    ]  # trailing parentheses, brackets, and braces
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned)
    cleaned = re.sub(r"[\s]+", " ", cleaned)

    ## strip non-ascii characters
    stripped = re.sub(r"[^\ -~]", "", cleaned)
    
    return cleaned, stripped

def _analyze_body(cleaned, stripped):
    analysis = {}
    analysis["cleaned"] = len(cleaned.split(" "))
    analysis["stripped"] = len(stripped.split(" "))

    analysis["above_499"] = analysis["stripped"] > 499
    analysis["above_999"] = analysis["stripped"] > 999

    analysis["score"] = ((analysis["stripped"] / analysis["cleaned"]) + analysis["above_499"] + analysis["above_999"]) / 3
    return analysis


def _analyze_images(body, word_count):
    analysis = {}
    ## get image to text ratio
    image_ratio = 400 / 1
    pattern = r"!\[[\w\ \-\._~!$&'()*+,;=:@#\/?]*\]\([\w\-\.~!$%&'()*+,;=:@\/?]+\)"
    analysis["count"] = len(list(re.findall(pattern, body)))
    analysis["score"] = 0
    if analysis["count"]:
        value = abs(((word_count / analysis["count"]) - image_ratio))
        if 0 <= value <= image_ratio:
            analysis["score"] = 1 - (value / image_ratio)
    return analysis