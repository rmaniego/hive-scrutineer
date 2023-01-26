# -*- coding: utf-8 -*-
"""
    scrutineer.*
    ~~~~~~~~~

    Performance and quality analytics on Hive Posts.

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

import re
import json

from nektar import Waggle
from emoji import emoji_list
from langdetect import detect_langs

RE_DASH = re.compile(r"-")
RE_EN_DASH = re.compile(r"\u2013")
RE_EM_DASH = re.compile(r"\u2014")
RE_N_RANK = re.compile(r"\#[\d]+")
RE_DOLLARS = re.compile(r"\$[\d\,\.]+")
RE_POSSESSIVE = re.compile(r"\b[\w]+[']s\b")
RE_MULTI_SPACE = re.compile(r"\s{2,}")
RE_UPPERCASE = re.compile(r"[A-Z]")
RE_CLEAN_TITLE = re.compile(r"[^\w\'\,\-\ ]+")
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
RE_USER_TAGS = re.compile(r"[^\w\/]@[\w\-\.]{3,16}[^\w\/]")
RE_NON_ASCII = re.compile(r"[^ -~]")

STOP_WORDS = [
    "0s",
    "3a",
    "3b",
    "3d",
    "6b",
    "6o",
    "a",
    "a's",
    "a1",
    "a2",
    "a3",
    "a4",
    "ab",
    "able",
    "about",
    "above",
    "abst",
    "ac",
    "accordance",
    "according",
    "accordingly",
    "across",
    "act",
    "actually",
    "ad",
    "added",
    "adj",
    "ae",
    "af",
    "affected",
    "affecting",
    "affects",
    "after",
    "afterwards",
    "ag",
    "again",
    "against",
    "ah",
    "ain",
    "ain't",
    "aj",
    "al",
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
    "ao",
    "ap",
    "apart",
    "apparently",
    "appear",
    "appreciate",
    "appropriate",
    "approximately",
    "ar",
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
    "au",
    "auth",
    "av",
    "available",
    "aw",
    "away",
    "awfully",
    "ax",
    "ay",
    "az",
    "b",
    "b1",
    "b2",
    "b3",
    "ba",
    "back",
    "bc",
    "bd",
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
    "bi",
    "bill",
    "biol",
    "bj",
    "bk",
    "bl",
    "bn",
    "both",
    "bottom",
    "bp",
    "br",
    "brief",
    "briefly",
    "bs",
    "bt",
    "bu",
    "but",
    "bx",
    "by",
    "c",
    "c'mon",
    "c's",
    "c1",
    "c2",
    "c3",
    "ca",
    "call",
    "came",
    "can",
    "can't",
    "cannot",
    "cant",
    "cause",
    "causes",
    "cc",
    "cd",
    "ce",
    "certain",
    "certainly",
    "cf",
    "cg",
    "ch",
    "changes",
    "ci",
    "cit",
    "cj",
    "cl",
    "clearly",
    "cm",
    "cn",
    "co",
    "com",
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
    "cp",
    "cq",
    "cr",
    "cry",
    "cs",
    "ct",
    "cu",
    "currently",
    "cv",
    "cx",
    "cy",
    "cz",
    "d",
    "d2",
    "da",
    "date",
    "dc",
    "dd",
    "definitely",
    "describe",
    "described",
    "despite",
    "detail",
    "df",
    "di",
    "did",
    "didn",
    "didn't",
    "different",
    "dj",
    "dk",
    "dl",
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
    "dp",
    "dr",
    "ds",
    "dt",
    "du",
    "due",
    "during",
    "dx",
    "dy",
    "e",
    "e2",
    "e3",
    "ea",
    "each",
    "ec",
    "ed",
    "edu",
    "ee",
    "ef",
    "effect",
    "eg",
    "ei",
    "eight",
    "eighty",
    "either",
    "ej",
    "eleven",
    "else",
    "elsewhere",
    "em",
    "empty",
    "end",
    "ending",
    "enough",
    "entirely",
    "eo",
    "ep",
    "eq",
    "er",
    "es",
    "especially",
    "est",
    "et",
    "et-al",
    "etc",
    "eu",
    "ev",
    "even",
    "ever",
    "every",
    "everybody",
    "everyone",
    "everything",
    "everywhere",
    "ex",
    "exactly",
    "example",
    "except",
    "ey",
    "f",
    "f2",
    "fa",
    "far",
    "fc",
    "few",
    "ff",
    "fi",
    "fifteen",
    "fifth",
    "fify",
    "fill",
    "find",
    "fire",
    "first",
    "five",
    "fix",
    "fj",
    "fl",
    "fn",
    "fo",
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
    "fs",
    "ft",
    "fu",
    "full",
    "further",
    "furthermore",
    "fy",
    "g",
    "ga",
    "gave",
    "ge",
    "get",
    "gets",
    "getting",
    "gi",
    "give",
    "giveaway",
    "given",
    "gives",
    "giving",
    "gj",
    "gl",
    "go",
    "goes",
    "going",
    "gone",
    "got",
    "gotten",
    "gr",
    "greetings",
    "gs",
    "gy",
    "h",
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
    "hed",
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
    "hh",
    "hi",
    "hid",
    "him",
    "himself",
    "his",
    "hither",
    "hj",
    "ho",
    "home",
    "hopefully",
    "how",
    "how's",
    "howbeit",
    "however",
    "hr",
    "hs",
    "http",
    "hu",
    "hundred",
    "hy",
    "i",
    "i'd",
    "i'll",
    "i'm",
    "i've",
    "i2",
    "i3",
    "i4",
    "i6",
    "i7",
    "i8",
    "ia",
    "ib",
    "ibid",
    "ic",
    "id",
    "ie",
    "if",
    "ig",
    "ignored",
    "ih",
    "ii",
    "ij",
    "il",
    "im",
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
    "ip",
    "iq",
    "ir",
    "is",
    "isn",
    "isn't",
    "it",
    "it'd",
    "it'll",
    "it's",
    "itd",
    "its",
    "itself",
    "iv",
    "ix",
    "iy",
    "iz",
    "j",
    "jj",
    "jr",
    "js",
    "jt",
    "ju",
    "just",
    "k",
    "ke",
    "keep",
    "keeps",
    "kept",
    "kg",
    "kj",
    "km",
    "know",
    "known",
    "knows",
    "ko",
    "l",
    "l2",
    "la",
    "largely",
    "last",
    "lately",
    "later",
    "latter",
    "latterly",
    "lb",
    "lc",
    "le",
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
    "lj",
    "ll",
    "ln",
    "lo",
    "look",
    "looking",
    "looks",
    "los",
    "lr",
    "ls",
    "lt",
    "ltd",
    "m",
    "m2",
    "ma",
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
    "mt",
    "mu",
    "much",
    "mug",
    "must",
    "mustn't",
    "my",
    "myself",
    "n",
    "n2",
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
    "ni",
    "nine",
    "ninety",
    "nj",
    "nl",
    "nn",
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
    "nr",
    "ns",
    "nt",
    "ny",
    "o",
    "oa",
    "ob",
    "obtain",
    "obtained",
    "obviously",
    "oc",
    "od",
    "of",
    "off",
    "often",
    "og",
    "oh",
    "oi",
    "oj",
    "ok",
    "okay",
    "ol",
    "old",
    "om",
    "omitted",
    "on",
    "once",
    "one",
    "ones",
    "only",
    "onto",
    "oo",
    "op",
    "oq",
    "or",
    "ord",
    "os",
    "ot",
    "other",
    "others",
    "otherwise",
    "ou",
    "ought",
    "our",
    "ours",
    "ourselves",
    "out",
    "outside",
    "over",
    "overall",
    "ow",
    "owing",
    "own",
    "ox",
    "oz",
    "p",
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
    "pc",
    "pd",
    "pe",
    "per",
    "perhaps",
    "pf",
    "ph",
    "pi",
    "pj",
    "pk",
    "pl",
    "placed",
    "please",
    "plus",
    "pm",
    "pn",
    "po",
    "poorly",
    "possible",
    "possibly",
    "potentially",
    "pp",
    "pq",
    "pr",
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
    "pt",
    "pu",
    "put",
    "py",
    "q",
    "qj",
    "qu",
    "que",
    "quickly",
    "quite",
    "qv",
    "r",
    "r2",
    "ra",
    "ran",
    "rather",
    "rc",
    "rd",
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
    "research",
    "research-articl",
    "respectively",
    "resulted",
    "resulting",
    "results",
    "rf",
    "rh",
    "ri",
    "right",
    "rj",
    "rl",
    "rm",
    "rn",
    "ro",
    "rq",
    "rr",
    "rs",
    "rt",
    "ru",
    "run",
    "rv",
    "ry",
    "s",
    "s2",
    "sa",
    "said",
    "same",
    "saw",
    "say",
    "saying",
    "says",
    "sc",
    "sd",
    "se",
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
    "sf",
    "shall",
    "shan",
    "shan't",
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
    "si",
    "side",
    "significant",
    "significantly",
    "similar",
    "similarly",
    "since",
    "sincere",
    "six",
    "sixty",
    "sj",
    "sl",
    "slightly",
    "sm",
    "sn",
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
    "sp",
    "specifically",
    "specified",
    "specify",
    "specifying",
    "sq",
    "sr",
    "ss",
    "st",
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
    "sy",
    "system",
    "sz",
    "t",
    "t's",
    "t1",
    "t2",
    "t3",
    "take",
    "taken",
    "taking",
    "tb",
    "tc",
    "td",
    "te",
    "tell",
    "ten",
    "tends",
    "tf",
    "th",
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
    "thickv",
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
    "ti",
    "til",
    "tip",
    "tj",
    "tl",
    "tm",
    "tn",
    "to",
    "together",
    "too",
    "took",
    "top",
    "toward",
    "towards",
    "tp",
    "tq",
    "tr",
    "tried",
    "tries",
    "truly",
    "try",
    "trying",
    "ts",
    "tt",
    "tv",
    "twelve",
    "twenty",
    "twice",
    "two",
    "tx",
    "u",
    "u201d",
    "ue",
    "ui",
    "uj",
    "uk",
    "um",
    "un",
    "under",
    "unfortunately",
    "unless",
    "unlike",
    "unlikely",
    "until",
    "unto",
    "uo",
    "up",
    "upon",
    "ups",
    "ur",
    "us",
    "use",
    "used",
    "useful",
    "usefully",
    "usefulness",
    "uses",
    "using",
    "usually",
    "ut",
    "v",
    "va",
    "value",
    "various",
    "vd",
    "ve",
    "very",
    "via",
    "viz",
    "vj",
    "vo",
    "vol",
    "vols",
    "volumtype",
    "vq",
    "vs",
    "vt",
    "vu",
    "w",
    "wa",
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
    "well-b",
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
    "whos",
    "whose",
    "why",
    "why's",
    "wi",
    "widely",
    "will",
    "willing",
    "wish",
    "with",
    "within",
    "without",
    "wo",
    "won",
    "won't",
    "wonder",
    "wont",
    "words",
    "world",
    "would",
    "wouldn",
    "wouldn't",
    "wouldnt",
    "www",
    "x",
    "x1",
    "x2",
    "x3",
    "xf",
    "xi",
    "xj",
    "xk",
    "xl",
    "xn",
    "xo",
    "xs",
    "xt",
    "xv",
    "xx",
    "y",
    "y2",
    "yes",
    "yet",
    "yj",
    "yl",
    "you",
    "you'd",
    "you'll",
    "you're",
    "you've",
    "youd",
    "your",
    "youre",
    "yours",
    "yourself",
    "yourselves",
    "yr",
    "ys",
    "yt",
    "z",
    "zero",
    "zi",
    "zz",
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
        self.analysis = {}
        self._blogs = []
        self._previous = ""

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
            if author == self._previous:
                blogs = self._blogs
            else:
                self._previous = author
                blogs = account.blogs(author, limit=2)
                self._blogs = [b for b in blogs]
            for blog in blogs:
                if blog["permlink"] == permlink:
                    continue
                raw_blog_body = blog["body"].split("\n")
                unique_lines = [l for l in raw_body if l not in raw_blog_body]
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

        metadata = post["json_metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        tags = metadata.get("tags", [])
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
        english = _to_english(cleaned, chars=True)
        readability = (english / len(title)) * adjust
        if isinstance(keywords, dict):
            words = title.lower()
            for keyword in keywords.keys():
                if keyword in words:
                    skeywords = 1
                    break
        score = int(not (bmin or amax)) * (
            ((readability * 9.5) + (skeywords * 0.5)) / 10
        )

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
    occurrence = int(occurrence)
    if not body:
        return {}
     
    keywords = {}
    cleaned = _parse_body(body)
    words = cleaned.lower().split(" ")
    words = [w for w in words if w not in STOP_WORDS]
    for word in set(words):
        count = words.count(word)
        if count < occurrence:
            continue
        keywords[word] = count
    return keywords

def get_bigrams(body, occurrence=4):
    occurrence = int(occurrence)
    if not body:
        return {}
    cleaned = _parse_body(body)
    return _get_bigrams(cleaned, occurrence=4)

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
    cleaned = RE_DASH.sub(" ", cleaned)
    cleaned = RE_MULTI_SPACE.sub(" ", cleaned)

    return cleaned

def _get_bigrams(contents, occurrence=4):
    occurrence = int(occurrence)

    bigrams = {}
    words = contents.lower().split(" ")
    words = [w for w in words if w not in STOP_WORDS]
    for i in range(len(words) - 2):
        bigram = " ".join(words[i : i + 2])
        bigrams[bigram] = bigrams.get(bigram, 0) + 1
    return {b: o for b, o in bigrams.items() if o >= occurrence}


def _analyze_body(words, deep, full=False):
    length = len(words.split(" "))
    english = _to_english(words)
    w400 = english > 400
    w800 = english > 800
    score = ((english / length) + (w400 * 2) + w800) / 4

    if not full:
        return score
    return {
        "cleaned": length,
        "english": english,
        "400+": w400,
        "800+": w800,
        "score": score,
    }


def _to_english(words, chars=False):
    if not len(words):
        return 0
    try:
        results = str(detect_langs(words))[1:-1].split(",")
    except Exception as e:
        print(f"Scrutineer: {e}")
        return 0
    for lang in results:
        if "en:" in lang:
            if chars:
                return float(lang.strip()[3:]) * len(words)
            return float(lang.strip()[3:]) * len(words.split(" "))
    return 0


def _analyze_emojis(body, limit, full=False):
    emojis = emoji_list(body)

    score = 1
    count = len(emojis)
    if count > limit:
        score = 0
        if limit:
            score = limit / count

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
    return {"count": count, "sequences": sequences, "score": score}


def _analyze_overtagging(body, limit, full=False):
    tags = len(RE_USER_TAGS.findall(body))
    score = int((tags <= limit))
    if tags > limit:
        score = limit / tags

    if not full:
        return score
    return {"limit": limit, "count": tags, "score": score}


def _analyze_tags(tags, limit, full=False):
    score = int((len(tags) <= limit))
    if limit and len(tags) > limit:
        score = limit / len(tags)

    if not full:
        return score
    return {"limit": limit, "count": len(tags), "score": score}