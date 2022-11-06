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

KNOWN_WORDS = STOP_WORDS+ENGLISH_WORDS

RE_DASH = re.compile(r"-")
RE_EN_DASH = re.compile(r"\u2013")
RE_EM_DASH = re.compile(r"\u2014")
RE_N_RANK = re.compile(r"\#[\d]+")
RE_DOLLARS = re.compile(r"\$[\d\,\.]+")
RE_POSSESSIVE = re.compile(r"\b[\w]+[']s\b")
RE_MULTI_SPACE = re.compile(r"\s{2,}")
RE_CLEAN_TITLE = re.compile(r"[^\w\'\,\ ]+")
RE_DELIMITERS = re.compile(r"[\n\.]")
RE_IMAGES = re.compile(r"!\[[\w\"\-\.~!#$%&'()*+,;=:@\/?\ ]*\]\([\w\"\-\.~!#$%&'()*+,;=:@\/?\ ]+\)")
RE_HIVE_SVC = re.compile(r"\[\/\/\]:#[\ ]+\([!][\w\ \.]+\)")
RE_ASTERISKS = re.compile(r"[\*]+")
RE_TILDES = re.compile(r"[~]+")
RE_UNDERSCORES = re.compile(r"[_]+")
RE_HEADERS = re.compile(r"[#]+")
RE_CODE_BLOCKS = re.compile(r"[`]+[\w]*[\ ]*")
RE_TABLE_SEP = re.compile(r"\|[\-]+\|[\-]+\|")
RE_PIPES = re.compile(r"[\ ]*\|[\ ]*")
RE_HTML_TAGS = re.compile(r"<[\/]?[a-zA-Z]+[1-6]?[\w\"\-\.~!#$%&'()*+,;=:@\/?\ ]+>")
RE_LINKS_RIGHT = re.compile(r"\]\([\w\"\-\.~!#$%&'*+,;=:@\/?\ ]+\)")
RE_BLOCKQUOTES = re.compile(r">[\ ]?")
RE_HR = re.compile(r"--[\-]+")
RE_TRAILING_PARENTHESIS = re.compile(r"[\(\[\{\}\]\)]")
RE_USER_TAGS = re.compile(r"@[a-z0-9\-\.]{3,16}")
RE_NON_ASCII = re.compile(r"[^ -~]")
RE_WORDS = re.compile(r"\b\w\w+\b")

class Scrutineer:
    def __init__(
        self, minimum_score=80, max_emojis=0, max_user_tags=5, max_tags=5, retries=1, deep=False
    ):
        self._weights = [1, 1, 1, 1, 1, 1]
        self._minimum_score = float(minimum_score)
        self._max_emojis = int(max_emojis)
        self._max_user_tags = int(max_user_tags)
        self._max_tags = int(max_tags)
        self._retries = int(retries)
        self._deep = isinstance(deep, bool) * bool(deep)
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
        if not isinstance(post, dict):
            post = Waggle(author).get_post(author, permlink, retries=self._retries)
            if not post:
                return {}
        self.analysis["author"] = author
        self.analysis["permlink"] = permlink

        title = post["title"]
        if not len(title):
            return {}
        self.analysis["title"] = _analyze_title(title)
        if auto_skip and (self.analysis["title"]["readability"] < 0.8):
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

        cleaned = _parse_body(body)
        if not len(cleaned):
            return {}
        
        self.analysis["body"] = {}
        self.analysis["emojis"] = _analyze_emojis(body, self._max_emojis)
        if auto_skip and (self.analysis["emojis"]["score"] < 0.8):
            return {}
        
        self.analysis["body"] = _analyze_body(cleaned, self._deep)

        if self._deep:
            keywords = self.analysis["body"]["seo_keywords"]
            self.analysis["title"] = _analyze_title(title, keywords)
        if auto_skip and (self.analysis["title"]["readability"] < 0.8):
            return {}

        word_count = self.analysis["body"]["cleaned"]
        self.analysis["images"] = _analyze_images(body, word_count)
        self.analysis["tagging"] = _analyze_overtagging(body, self._max_user_tags)

        tags = []
        if "tags" in post["json_metadata"]:
            tags = post["json_metadata"]["tags"]
        self.analysis["tags"] = _analyze_tags(tags, self._max_tags)

        score = 0
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

"""
class Analytics:
    def __init__(self, author, limit=100, retries=1):
        self._author = str(author)[:16]
        self._limit = max(min(int(limit), 100), 1)
        self._retries = max(min(int(retries), 5), 1)
        self.analysis = {}
    
    def analyze(self):
        tags = {}
        votes = {}
        post_payouts = []
        post_engagements = []
        
        hive = Waggle(self._author)
        for blog in hive.blogs(limit=self._limit):

            dt = blog["created"][:10]
            self.analysis[dt] = {}
            
            payout = blog["payout"]
            
            # growth[dt]["post"] = blog["title"]
            self.analysis[dt]["payout"] = payout
            self.analysis[dt]["engagements"] = blog["children"]
            self.analysis[dt]["votes"] = len(blog["active_votes"])
            self.analysis[dt]["score"] = scoring(blog)
            
            for vote in blog["active_votes"]:
                voter = vote["voter"]
                votes[voter] = votes.get(voter, []) + [vote["rshares"]]
            
            if "tags" not in blog["json_metadata"]:
                continue
            for tag in blog["json_metadata"]["tags"]:
                tags[tag] = tags.get(tag, []) + [payout]
                
            post_payouts.append([payout, blog["title"]])
            post_engagements.append([blog["children"], blog["title"] + " @" + self._author + "/" + blog["permlink"]])
        
        self.analysis.save()
        
        consistent = []
        high_value = []
        for voter, rshares in votes.items():
            consistent.append([len(rshares), voter])
            high_value.append([sorted(rshares)[-1], voter])

        consistent = list(reversed(sorted(consistent)))
        consistent = [x[1]+"-"+str(x[0]) for x in consistent][:100]
        
        high_value = list(reversed(sorted(high_value)))
        high_value = [x[1] for x in high_value][:100]
        
        high_value_tags = []
        for tag, payouts in tags.items():
            high_value_tags.append([sorted(payouts)[-1], tag])
        
        high_value_tags = list(reversed(sorted(high_value_tags)))
        high_value_tags = [x[1]+str(x[0]) for x in high_value_tags][:10]
        
        post_payouts = list(reversed(sorted(post_payouts)))
        post_payouts = [x[1] for x in post_payouts][:5]
        
        post_engagements = list(reversed(sorted(post_engagements)))
        post_engagements = [x[1] for x in post_engagements][:5]

        
        colors = ("red", "green", "blue", "yellow")
        dates = list(reversed(list(self.analysis.keys())))
        properties = [ x for x in list(self.analysis[dates[0]].keys()) if x != "post" ]
        for i in range(len(properties)):
            values = []
            name = properties[i]
            for j in range(len(dates)):
                adjusted = self.analysis[dates[j]][name]
                if properties[i] == "Upvotes":
                    adjusted /= 10
                values.append(adjusted)
            # plt.plot(list(range(len(dates))), values, color=colors[i], label=name)
          
        # plt.xlabel("Date")
        # plt.ylabel("Properties")
        # plt.title("Hive Content Performance")
        
        # plt.legend()
        # plt.show()
"""

def _analyze_title(title, keywords=None):
    analysis = {}
    # analysis["title"] = title
    
    title = RE_DASH.sub(" ", title)
    title = RE_EN_DASH.sub(" ", title)
    title = RE_EM_DASH.sub(" ", title)
    title = RE_N_RANK.sub(" ", title)
    title = RE_DOLLARS.sub(" ", title)
    title = RE_POSSESSIVE.sub("", title)
    title = RE_MULTI_SPACE.sub(" ", title).strip()
    length = len(title.encode("utf-8"))
    analysis["title"] = title
    
    words = RE_CLEAN_TITLE.sub(" ", title.lower()).split(" ")
    cleaned = " ".join([w for w in words if w in KNOWN_WORDS])
    analysis["cleaned"] = cleaned.strip()
    
    analysis["below_min"] = length < 20
    analysis["above_max"] = length > 60

    analysis["seo_keywords"] = 0
    analysis["readability"] = len(cleaned) / length
    if isinstance(keywords, dict):
        for keyword in keywords.keys():
            if keyword in title.lower():
                analysis["seo_keywords"] = 1
                break
    else:
        analysis["seo_keywords"] = analysis["readability"]

    analysis["score"] = int(not (analysis["below_min"] or analysis["above_max"])) * (
        ((analysis["readability"] * 9) + analysis["seo_keywords"]) / 10
    )
    return analysis


def _parse_body(body):
    # remove images, replace whitespaces
    cleaned = RE_IMAGES.sub("", body).lower()
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

def _analyze_body(cleaned, deep):
    analysis = {}
    corpus = cleaned.split(" ")
    analysis["cleaned"] = len([1 for x in corpus if x.strip()])
    analysis["english"] = len([x for x in corpus if x in KNOWN_WORDS])
    analysis["seo_keywords"] = _get_bigrams(cleaned)
    analysis["above_400"] = analysis["english"] > 400
    analysis["above_800"] = analysis["english"] > 800
    analysis["score"] = (
        (analysis["english"] / analysis["cleaned"])
        + analysis["above_400"]
        + analysis["above_800"]
    ) / 3
    return analysis

def _analyze_emojis(body, limit=0):
    analysis = {}
    analysis["max_emojis"] = limit
    chars = list(RE_NON_ASCII.findall(body))
    analysis["emojis"] = [c for c in chars if c in EMOJIS]
    analysis["count"] = len(analysis["emojis"])
    analysis["score"] = 1
    if analysis["count"] > int(limit):
        analysis["score"] = limit / analysis["count"]
    return analysis
        

def _get_bigrams(contents, occurrence=4, limit=5):
    occurrence = int(occurrence)
    limit = int(limit)

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
    keywords = list(reversed(sorted(keywords)))[:limit]
    return {b: o for b, o in keywords}


def _analyze_images(body, word_count):
    analysis = {}
    ## get image to text ratio
    analysis["count"] = len(list(RE_IMAGES.findall(body)))
    analysis["score"] = 0
    if analysis["count"]:
        scores = [0]
        for image in (1, 2, 3):
            image_ratio = 400 / image
            value = abs(((word_count / analysis["count"]) - image_ratio))
            if 0 <= value <= image_ratio:
                scores.append((1 - (value / image_ratio)))
        analysis["score"] = max(scores)
    return analysis


def _analyze_overtagging(body, max_user_tags):
    analysis = {}
    tags = len(RE_USER_TAGS.findall(body))
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