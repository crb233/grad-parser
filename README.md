# Grad Parser

GRAmmar Definition Parser

A Python module for parsing grammars based on their definitions.

## Example

```python
import grad_parser as grad

text = '{"a":"val", "b":[0,1,2], "c":{}}'

g = grad.Grammar()
g.use(grad.json)
matches = g.parse(text)
obj = matches[0]

def show(match):
  print(text[match.start, match.next])

show(obj.children[1])
# "a":"val"

show(obj.children[1].children[0])
# "a"

show(obj.children[1].children[2])
# "val"
```
