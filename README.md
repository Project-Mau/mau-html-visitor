# Mau HTML Visitor

This is a plugin for the [Mau](https://github.com/Project-Mau/mau) markup language. The plugin provides the conversion from Mau source to HTML.

You can install this plugin with

```
pip install mau-html-visitor
```

and Mau will automatically be able to load it. To use the visitor you need to load it and to pass it to the class `Mau` when you instantiate it

``` python
from mau import Mau, load_visitors
from mau.message import LogMessageHandler

visitor_classes = load_visitors()

visitors = {i.format_code: i for i in visitor_classes.values()}
visitor_class = visitors["html"]

message_handler = LogMessageHandler()

mau = Mau(message_handler)

result = mau.process(visitor_class, text, "source.mau")
```

The default extension for templates is `.html`. The plugin uses [Pygments](https://pygments.org/) to provide source code highlighting.
