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

## Performance
In version `1.3.0`, we've migrated to `langdetect` to speed up `Scrutineer.analyze()` by more than 300x versus version `1.2.*`!
```cmd
MIN: 1.8852958001662046 seconds
AVG: 2.3002824100200088 seconds
MAX: 4.7612034999765460 seconds
```
We've also seen a 70% import speed increase, in the said profiling.