# -*- coding: utf-8 -*-
"""
    scrutineer.*
    ~~~~~~~~~

    Performance and quality analytics on Hive Posts.

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

import re
from .constants import STOP_WORDS, ENGLISH_WORDS
from nektar import Waggle

KNOWN_WORDS = STOP_WORDS+ENGLISH_WORDS

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
        if not (len(cleaned) and len(stripped)):
            return {}

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
    analysis["title"] = title
    length = len(title.encode("utf-8"))
    
    analysis["below_min"] = length < 20
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
        ((analysis["readability"] * 9) + analysis["seo_keywords"]) / 10
    )
    return analysis


def _parse_body(body):
    # remove images, replace whitespaces
    pattern = (
        r"!\[[\w\"\-\.~!#$%&'()*+,;=:@\/?\ ]*\]\([\w\"\-\.~!#$%&'()*+,;=:@\/?\ ]+\)"
    )
    cleaned = re.sub(pattern, "", body).lower()
    cleaned = re.sub(r"[\n\.]", " ", cleaned)
    cleaned = re.sub(r"\u2013", " ", cleaned)
    cleaned = re.sub(r"\u2014", " ", cleaned)

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
    ]  
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned)
    cleaned = re.sub(r"[\s]+", " ", cleaned)

    ## strip non-ascii characters
    stripped = re.sub(r"[^'\w\-\s]", "", cleaned)
    stripped = re.sub(r"[^\ -~]", "", stripped)
    return cleaned, stripped

def _analyze_body(cleaned, stripped, deep):
    analysis = {}
    analysis["cleaned"] = len([1 for x in cleaned.split(" ") if x.strip()])
    analysis["stripped"] = len([1 for x in stripped.split(" ") if x.strip()])
    
    corpus = stripped.split(" ")
    analysis["english"] = len([x for x in corpus if x in KNOWN_WORDS])
    
    analysis["seo_keywords"] = _get_bigrams(stripped)

    analysis["above_400"] = analysis["stripped"] > 400
    analysis["above_800"] = analysis["stripped"] > 800

    analysis["score"] = (
        (analysis["english"] / analysis["cleaned"])
        + analysis["above_400"]
        + analysis["above_800"]
    ) / 3
    return analysis


def _get_bigrams(contents, occurrence=4, limit=5):
    occurrence = int(occurrence)
    limit = int(limit)

    bigrams = {}
    words = list(re.findall(r"\b\w\w+\b", contents.lower()))
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