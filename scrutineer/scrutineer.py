# -*- coding: utf-8 -*-
"""
    scrutineer.*
    ~~~~~~~~~

    Performance and quality analytics on Hive Posts.

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

from json import loads as jloads
from re import compile as rcompile

from nektar import Waggle
from emoji import emoji_list
from langdetect import detect_langs

RE_DASH = rcompile(r"(\-|\u2013|\u2014)")
RE_N_RANK = rcompile(r"\#[\d]+")
RE_DOLLARS = rcompile(r"\$[\d\,\.]+")
RE_POSSESSIVE = rcompile(r"\b[\w]+[']s\b")
RE_MULTI_SPACE = rcompile(r"\s{2,}")
RE_UPPERCASE = rcompile(r"[A-Z]")
RE_CLEAN_TITLE = rcompile(r"[^\w\'\,\-\ ]+")
RE_DELIMITERS = rcompile(r"[\n\.]")
RE_IMAGE = rcompile(r"!\[[^\]]*\]\([^\)]+\)")
RE_IMAGES = rcompile(r"!\[[^\]]*\]\([^\)]+\)\s*!\[[^\]]*\]\([^\)]+\)")
RE_HIVE_SVC = rcompile(r"\[\/\/\]:#[\ ]+\([!][\w\ \.]+\)")
RE_ASTERISKS = rcompile(r"[\*]+")
RE_TILDES = rcompile(r"[~]+")
RE_UNDERSCORES = rcompile(r"[_]+")
RE_HEADERS = rcompile(r"[#][#]+")
RE_CODE_BLOCKS = rcompile(r"[`]+[\w]*[\ ]*")
RE_TABLE_SEP = rcompile(r"\|[\-:]+\|[\-:]+\|")
RE_PIPES = rcompile(r"[\ :]*\|[\ :]*")
RE_HTML_TAGS = rcompile(r"<[\/]?[a-zA-Z]+[1-6]?[^\>]+>")
RE_LINKS_RIGHT = rcompile(r"\]\([^\)]+\)")
RE_BLOCKQUOTES = rcompile(r">[\ ]?")
RE_HR = rcompile(r"--[\-]+")
RE_TRAILING_PARENTHESIS = rcompile(r"[\(\[\{\}\]\)]")
RE_USER_TAGS = rcompile(r"[^\w\/]@[\w\-\.]{3,16}[^\w\/]")
RE_NUMBERS = rcompile(r"\d+\.?\d*")
RE_PUNCTUATIONS = rcompile(r"[\.\,\!\?]")
RE_NON_ASCII = rcompile(r"[^ -~]")
RE_WORD = rcompile(r"\w[^\s]+")

STOP_WORDS = [
    "0s",
    "a",
    "able",
    "about",
    "above",
    "accordance",
    "according",
    "accordingly",
    "across",
    "act",
    "actually",
    "added",
    "adj",
    "af",
    "affected",
    "affecting",
    "affects",
    "after",
    "afterwards",
    "ag",
    "again",
    "against",
    "ain't",
    "all",
    "allow",
    "allows",
    "almost",
    "alone",
    "along",
    "already",
    "also",
    "although",
    "always",
    "am",
    "among",
    "amongst",
    "amoungst",
    "amount",
    "an",
    "and",
    "announce",
    "another",
    "any",
    "anybody",
    "anyhow",
    "anymore",
    "anyone",
    "anything",
    "anyway",
    "anyways",
    "anywhere",
    "apart",
    "apparently",
    "appear",
    "appreciate",
    "appropriate",
    "approximately",
    "are",
    "aren",
    "aren't",
    "arent",
    "arise",
    "around",
    "as",
    "aside",
    "ask",
    "asking",
    "associated",
    "at",
    "available",
    "aw",
    "away",
    "awfully",
    "back",
    "be",
    "became",
    "because",
    "become",
    "becomes",
    "becoming",
    "been",
    "before",
    "beforehand",
    "begin",
    "beginning",
    "beginnings",
    "begins",
    "behind",
    "being",
    "believe",
    "below",
    "beside",
    "besides",
    "best",
    "better",
    "between",
    "beyond",
    "bill",
    "both",
    "bottom",
    "brief",
    "briefly",
    "bs",
    "but",
    "bx",
    "c'mon",
    "call",
    "came",
    "can",
    "can't",
    "cannot",
    "cant",
    "cause",
    "causes",
    "certain",
    "certainly",
    "changes",
    "clearly",
    "co",
    "come",
    "comes",
    "con",
    "concerning",
    "consequently",
    "consider",
    "considering",
    "contain",
    "containing",
    "contains",
    "corresponding",
    "could",
    "couldn",
    "couldn't",
    "couldnt",
    "course",
    "cry",
    "currently",
    "date",
    "definitely",
    "describe",
    "described",
    "despite",
    "detail",
    "did",
    "didn't",
    "different",
    "do",
    "does",
    "doesn",
    "doesn't",
    "doing",
    "don",
    "don't",
    "done",
    "down",
    "downwards",
    "dr",
    "due",
    "during",
    "each",
    "effect",
    "eg",
    "eight",
    "eighty",
    "either",
    "eleven",
    "else",
    "elsewhere",
    "empty",
    "end",
    "ending",
    "enough",
    "entirely",
    "especially",
    "et",
    "et-al",
    "etc",
    "even",
    "ever",
    "every",
    "everybody",
    "everyone",
    "everything",
    "everywhere",
    "exactly",
    "example",
    "except",
    "far",
    "few",
    "ff",
    "fifteen",
    "fifth",
    "fify",
    "fill",
    "find",
    "fire",
    "first",
    "five",
    "fix",
    "followed",
    "following",
    "follows",
    "for",
    "former",
    "formerly",
    "forth",
    "forty",
    "found",
    "four",
    "fr",
    "from",
    "front",
    "ft",
    "full",
    "further",
    "furthermore",
    "gave",
    "ge",
    "get",
    "gets",
    "getting",
    "give",
    "giveaway",
    "given",
    "gives",
    "giving",
    "go",
    "goes",
    "going",
    "gone",
    "got",
    "gotten",
    "greetings",
    "h2",
    "h3",
    "had",
    "hadn",
    "hadn't",
    "happens",
    "hardly",
    "has",
    "hasn",
    "hasn't",
    "hasnt",
    "have",
    "haven",
    "haven't",
    "having",
    "he",
    "he'd",
    "he'll",
    "he's",
    "hello",
    "help",
    "hence",
    "her",
    "here",
    "here's",
    "hereafter",
    "hereby",
    "herein",
    "heres",
    "hereupon",
    "hers",
    "herself",
    "hes",
    "hi",
    "hid",
    "him",
    "himself",
    "his",
    "hither",
    "ho",
    "home",
    "hopefully",
    "how",
    "how's",
    "howbeit",
    "however",
    "http",
    "hundred",
    "i",
    "i'd",
    "i'll",
    "i'm",
    "i've",
    "ie",
    "if",
    "ignored",
    "immediate",
    "immediately",
    "importance",
    "important",
    "in",
    "inasmuch",
    "inc",
    "indeed",
    "index",
    "indicate",
    "indicated",
    "indicates",
    "information",
    "inner",
    "insofar",
    "instead",
    "interest",
    "into",
    "invention",
    "inward",
    "io",
    "is",
    "isn't",
    "it",
    "it'd",
    "it'll",
    "it's",
    "its",
    "itself",
    "just",
    "keep",
    "keeps",
    "kept",
    "kg",
    "km",
    "know",
    "known",
    "knows",
    "largely",
    "last",
    "lately",
    "later",
    "latter",
    "latterly",
    "least",
    "les",
    "less",
    "lest",
    "let",
    "let's",
    "lets",
    "lf",
    "like",
    "liked",
    "likely",
    "line",
    "little",
    "look",
    "looking",
    "looks",
    "ltd",
    "made",
    "mainly",
    "make",
    "makes",
    "many",
    "may",
    "maybe",
    "me",
    "mean",
    "means",
    "meantime",
    "meanwhile",
    "merely",
    "mg",
    "might",
    "mightn",
    "mightn't",
    "mill",
    "million",
    "mine",
    "miss",
    "ml",
    "mn",
    "mo",
    "more",
    "moreover",
    "most",
    "mostly",
    "move",
    "mr",
    "mrs",
    "ms",
    "much",
    "mug",
    "must",
    "mustn't",
    "my",
    "myself",
    "n",
    "na",
    "name",
    "namely",
    "nay",
    "nc",
    "nd",
    "ne",
    "near",
    "nearly",
    "necessarily",
    "necessary",
    "need",
    "needn",
    "needn't",
    "needs",
    "neither",
    "never",
    "nevertheless",
    "new",
    "next",
    "ng",
    "nine",
    "ninety",
    "no",
    "nobody",
    "non",
    "none",
    "nonetheless",
    "noone",
    "nor",
    "normally",
    "nos",
    "not",
    "noted",
    "nothing",
    "novel",
    "now",
    "nowhere",
    "obtain",
    "obtained",
    "obviously",
    "oc",
    "od",
    "of",
    "off",
    "often",
    "oh",
    "ok",
    "okay",
    "old",
    "omitted",
    "on",
    "once",
    "one",
    "ones",
    "only",
    "onto",
    "op",
    "or",
    "other",
    "others",
    "otherwise",
    "ought",
    "our",
    "ours",
    "ourselves",
    "out",
    "outside",
    "over",
    "overall",
    "owing",
    "own",
    "p1",
    "p2",
    "p3",
    "page",
    "pagecount",
    "pages",
    "par",
    "part",
    "particular",
    "particularly",
    "pas",
    "past",
    "per",
    "perhaps",
    "placed",
    "please",
    "plus",
    "poorly",
    "possible",
    "possibly",
    "potentially",
    "predominantly",
    "present",
    "presumably",
    "previously",
    "primarily",
    "probably",
    "promptly",
    "proud",
    "provides",
    "ps",
    "put",
    "que",
    "quickly",
    "quite",
    "ran",
    "rather",
    "re",
    "readily",
    "really",
    "reasonably",
    "recent",
    "recently",
    "ref",
    "refs",
    "regarding",
    "regardless",
    "regards",
    "related",
    "relatively",
    "respectively",
    "resulted",
    "resulting",
    "results",
    "right",
    "run",
    "said",
    "same",
    "saw",
    "say",
    "saying",
    "says",
    "sec",
    "second",
    "secondly",
    "section",
    "see",
    "seeing",
    "seem",
    "seemed",
    "seeming",
    "seems",
    "seen",
    "self",
    "selves",
    "sensible",
    "sent",
    "serious",
    "seriously",
    "seven",
    "several",
    "shall",
    "she",
    "she'd",
    "she'll",
    "she's",
    "shed",
    "shes",
    "should",
    "should've",
    "shouldn",
    "shouldn't",
    "show",
    "showed",
    "shown",
    "showns",
    "shows",
    "side",
    "significant",
    "significantly",
    "similar",
    "similarly",
    "since",
    "sincere",
    "six",
    "sixty",
    "slightly",
    "so",
    "some",
    "somebody",
    "somehow",
    "someone",
    "somethan",
    "something",
    "sometime",
    "sometimes",
    "somewhat",
    "somewhere",
    "soon",
    "sorry",
    "specifically",
    "specified",
    "specify",
    "specifying",
    "still",
    "stop",
    "strongly",
    "sub",
    "substantially",
    "successfully",
    "such",
    "sufficiently",
    "suggest",
    "sup",
    "sure",
    "system",
    "take",
    "taken",
    "taking",
    "tell",
    "ten",
    "tends",
    "than",
    "thank",
    "thanks",
    "thanx",
    "that",
    "that'll",
    "that's",
    "that've",
    "thats",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "thence",
    "there",
    "there'll",
    "there's",
    "there've",
    "thereafter",
    "thereby",
    "thered",
    "therefore",
    "therein",
    "thereof",
    "therere",
    "theres",
    "thereto",
    "thereupon",
    "these",
    "they",
    "they'd",
    "they'll",
    "they're",
    "they've",
    "theyd",
    "theyre",
    "thick",
    "thin",
    "think",
    "third",
    "this",
    "thorough",
    "thoroughly",
    "those",
    "thou",
    "though",
    "thoughh",
    "thousand",
    "three",
    "throug",
    "through",
    "throughout",
    "thru",
    "thus",
    "til",
    "tip",
    "to",
    "together",
    "too",
    "took",
    "top",
    "toward",
    "towards",
    "tried",
    "tries",
    "truly",
    "try",
    "trying",
    "twelve",
    "twenty",
    "twice",
    "two",
    "un",
    "under",
    "unfortunately",
    "unless",
    "unlike",
    "unlikely",
    "until",
    "unto",
    "up",
    "upon",
    "ups",
    "us",
    "use",
    "used",
    "useful",
    "usefully",
    "usefulness",
    "uses",
    "using",
    "usually",
    "value",
    "various",
    "very",
    "via",
    "viz",
    "vol",
    "vols",
    "want",
    "wants",
    "was",
    "wasn",
    "wasn't",
    "wasnt",
    "way",
    "we",
    "we'd",
    "we'll",
    "we're",
    "we've",
    "wed",
    "welcome",
    "well",
    "went",
    "were",
    "weren",
    "weren't",
    "werent",
    "what",
    "what'll",
    "what's",
    "whatever",
    "whats",
    "when",
    "when's",
    "whence",
    "whenever",
    "where",
    "where's",
    "whereafter",
    "whereas",
    "whereby",
    "wherein",
    "wheres",
    "whereupon",
    "wherever",
    "whether",
    "which",
    "while",
    "whim",
    "whither",
    "who",
    "who'll",
    "who's",
    "whod",
    "whoever",
    "whole",
    "whom",
    "whomever",
    "whose",
    "why",
    "why's",
    "widely",
    "will",
    "willing",
    "wish",
    "with",
    "within",
    "without",
    "won't",
    "wonder",
    "wont",
    "words",
    "world",
    "would",
    "wouldn",
    "wouldn't",
    "www",
    "yes",
    "yet",
    "you",
    "you'd",
    "you'll",
    "you're",
    "you've",
    "your",
    "you're",
    "yours",
    "yourself",
    "yourselves",
    "zero",
]

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
        self._permlink = None
        self._previous = None
        self._template = []
        self._analysis = {}
        self._waggle = Waggle("")

    def set_weights(self, title=1, body=1, emojis=1, images=1, tagging=1, tags=1):
        self._weights = [
            float(title),
            float(body),
            float(emojis),
            float(images),
            float(tagging),
            float(tags),
        ]

    def analyze(self, post, permlink=None, auto_skip=False):
        self._analysis = {}
        
        if isinstance(post, dict):
            author = post["author"]
            permlink = post["permlink"]
        if not isinstance(post, dict):
            author = post
            post = self._waggle.get_post(author, permlink, retries=self._retries)
            if not post:
                return {}

        self._analysis["author"] = author
        self._analysis["permlink"] = permlink

        if self._full:
            self._analysis["url"] = post["url"]

        title = post["title"]
        if not len(title):
            return {}

        body = post["body"]
        if self._deep:
            raw_body = body.split("\n")
            if author != self._previous or (permlink == self._permlink and author == self._previous):
                self._previous = author
                for blog in self._waggle.blogs(author, limit=2):
                    if blog["permlink"] == self._permlink:
                        continue
                    self._permlink = blog["permlink"]
                    self._template = blog["body"].split("\n")
                    break
            body = "\n".join([l for l in raw_body
                if l not in self._template])
        cleaned = _parse_body(body)
        if not len(cleaned):
            return {}

        # use keywords instead
        keywords = get_keywords(cleaned) # _get_bigrams(cleaned)
        self._analysis["title"] = _analyze_title(title, keywords, self._full)

        self._analysis["body"] = {}
        self._analysis["emojis"] = _analyze_emojis(body, self._max_emojis, self._full)
        if auto_skip:
            if self._full:
                if (
                    self._analysis["emojis"]["score"] < 0.8
                    or self._analysis["title"]["score"] < 0.8
                ):
                    return {}
            elif self._analysis["emojis"] < 0.8 or self._analysis["title"] < 0.8:
                return {}
        self._analysis["body"] = _analyze_body(cleaned, self._deep, self._full)

        wcount = len(cleaned.split(" "))
        self._analysis["images"] = _analyze_images(body, wcount, self._full)
        self._analysis["tagging"] = _analyze_overtagging(
            body, self._max_user_tags, self._full
        )

        metadata = post["json_metadata"]
        if isinstance(metadata, str):
            metadata = jloads(metadata)
        tags = metadata.get("tags", [])
        self._analysis["tags"] = _analyze_tags(tags, self._max_tags, self._full)

        score = 0
        if not self._full:
            score += self._analysis["title"] * self._weights[0]
            score += self._analysis["body"] * self._weights[1]
            score += self._analysis["emojis"] * self._weights[2]
            score += self._analysis["images"] * self._weights[3]
            score += self._analysis["tagging"] * self._weights[4]
            score += self._analysis["tags"] * self._weights[5]
        else:
            score += self._analysis["title"]["score"] * self._weights[0]
            score += self._analysis["body"]["score"] * self._weights[1]
            score += self._analysis["emojis"]["score"] * self._weights[2]
            score += self._analysis["images"]["score"] * self._weights[3]
            score += self._analysis["tagging"]["score"] * self._weights[4]
            score += self._analysis["tags"]["score"] * self._weights[5]
        score /= sum(self._weights)

        self._analysis["deep"] = self._deep
        self._analysis["score"] = score
        return self._analysis


def _analyze_title(title, keywords, full=False):

    cleaned = title
    cleaned = RE_DASH.sub(" ", cleaned)
    cleaned = RE_N_RANK.sub(" ", cleaned)
    cleaned = RE_DOLLARS.sub(" ", cleaned)
    cleaned = RE_POSSESSIVE.sub("", cleaned)
    cleaned = RE_CLEAN_TITLE.sub(" ", cleaned)
    cleaned = RE_MULTI_SPACE.sub(" ", cleaned).strip()
    length = len(cleaned.encode("utf-8"))

    bmin = length < 20
    amax = length > 80

    score = 0
    skeywords = 0
    readability = 0

    emojis = emoji_list(title)
    if length and not len(emojis):
        uppercase = len(RE_UPPERCASE.findall(cleaned))/length
        adjust = (1, 0.5)[int(bool(uppercase>0.5))]
        
        english = _count_english(cleaned, chars=True)
        readability = (english / len(title)) * adjust
        
        if isinstance(keywords, dict):
            words = title.lower()
            for keyword in keywords:
                if keyword in words:
                    skeywords = 0.5
                    break
        score = int(not (bmin or amax)) * (((readability * 9.5) + skeywords) / 10)

    if not full:
        return score
    return {
        "title": title,
        "cleaned": cleaned,
        "below_min": bmin,
        "above_max": amax,
        "uppercase": uppercase,
        "keywords": keywords,
        "readability": readability,
        "keyword_score": skeywords,
        "emojis": emojis,
        "score": score,
    }

def get_keywords(body, occurrence=4):
    words = RE_WORD.findall(_parse_body(body).lower())
    keywords = {w:words.count(w) for w in set(words) if w not in STOP_WORDS}
    return {k: c for k, c in keywords.items() if c >= int(occurrence)}

def get_bigrams(body, occurrence=4):
    return _get_bigrams(_parse_body(body), occurrence=int(occurrence))

def _parse_body(body):
    # remove images, replace whitespaces
    cleaned = RE_IMAGE.sub("", body).lower()
    cleaned = RE_DELIMITERS.sub(" ", cleaned)

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
    cleaned = RE_USER_TAGS.sub(" ", cleaned)
    cleaned = RE_DASH.sub(" ", cleaned)
    cleaned = RE_PUNCTUATIONS.sub(" ", cleaned)
    cleaned = RE_NUMBERS.sub(" ", cleaned)
    cleaned = RE_MULTI_SPACE.sub(" ", cleaned)

    return cleaned

def _get_bigrams(contents, occurrence=4):
    bigrams = {}
    words = RE_WORD.findall(contents.lower())
    words = [w for w in words if w not in STOP_WORDS]
    for i in range(len(words) - 2):
        bigram = " ".join(words[i : i + 2])
        bigrams[bigram] = bigrams.get(bigram, 0) + 1
    return {b: o for b, o in bigrams.items() if o >= int(occurrence)}


def _analyze_body(words, deep, full=False):
    length = len(words.split(" "))
    english = _count_english(words)
    w400 = english > 400
    w800 = english > 800
    score = (w400 + w800) * (english / length) / 2

    if not full:
        return score
    return {
        "cleaned": length,
        "english": english,
        "400+": w400,
        "800+": w800,
        "score": score,
    }


def _count_english(text, chars=False):
    if not len(text):
        return 0
    try:
        results = str(detect_langs(text))[1:-1].split(",")
    except Exception as e:
        print(f"Scrutineer: {e}")
        return 0
    for lang in results:
        if "en:" not in lang:
            continue
        if chars:
            return float(lang.strip()[3:]) * len(text)
        return float(lang.strip()[3:]) * len(text.split(" "))
    return 0

def _analyze_emojis(body, limit, full=False):
    score = 1
    emojis = emoji_list(body)
    count = len(emojis)
    if count > limit:
        score = (limit / count) * int(bool(limit))

    if not full:
        return score
    return {
        "limit": limit,
        "emojis": [i.get("emoji") for i in emojis if "emoji" in i],
        "count": count,
        "score": score,
    }


def _analyze_images(body, wcount, full=True):
    score = 0
    count = len(RE_IMAGE.findall(body))
    sequences = len(RE_IMAGES.findall(body))
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
    return {"count": count, "sequences": sequences, "score": score}


def _analyze_overtagging(body, limit, full=False):
    tags = len(RE_USER_TAGS.findall(body))
    if tags > limit:
        score = limit / tags
    else:
        score = int((tags <= limit))

    if not full:
        return score
    return {"limit": limit, "count": tags, "score": score}


def _analyze_tags(tags, limit, full=False):
    if limit and len(tags) > limit:
        score = limit / len(tags)
    else:
        score = int((len(tags) <= limit))

    if not full:
        return score
    return {"limit": limit, "count": len(tags), "score": score}