# scrutineer
Hive Post performance and quality analytics.

## Installation

```cmd
$ pip install hive-scrutineer
```

Supported Python versions 3.10+.

## Blockchain Support
Limited support to Hive Blockchain HF27.

## Basic usage

```python
from scrutineer import Scrutineer

analyzer = Scrutineer()
analyzer.set_weights()
analysis = analyzer.analyze("author", "post-permlink")
```

## Customizations

```python
import json
from nektar import Waggle
from scrutineer import Scrutineer

hive = Waggle("username")

analyzer = Scrutineer(minimum_score=10, max_emojis=0, deep=True, full=False)
analyzer.set_weights(title=5, body=6, emojis=4, images=2, tagging=3, tags=1)

for blog in hive.blogs(limit=5)
    analysis = analyzer.analyze(blog)
    print(json.dumps(analysis, indent=2))
```

## Keywords

```python
import json
from nektar import Waggle
from scrutineer import get_keywords, get_bigrams

hive = Waggle("username")
for blog in hive.blogs(limit=5)
    keywords = get_keywords(blog["body"])
    print("\nget_keywords" + json.dumps(keywords))
    
    keywords = get_bigrams(blog["body"])
    print("\nget_bigrams:" + json.dumps(keywords))
```

## Performance
In version `1.3.0`, we've migrated to `langdetect` to speed up `Scrutineer.analyze()` by more than 300x versus version `1.2.*`!
```cmd
MIN: 0.02782490011304617
AVG: 0.13722777900053187
MAX: 4.033556599984877
```
We've also seen a 70% import speed increase, in the said profiling.