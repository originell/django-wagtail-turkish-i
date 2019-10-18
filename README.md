# Demo Project for "İstanbul" issue

This is a demonstration to showcase the slugification problem of "İstanbul".

As originally discussed in [a thread in Wagtail's support channel](https://wagtailcms.slack.com/archives/C81FGJR2S/p1570706995063800).

## Setup

Project was created using wagtail's _Getting Started_.

```sh
$ pip install -r requirements.txt
$ ./manage.py migrate
# User to access the CMS Admin
$ ./manage.py createsuperuser
# And off we go!
$ ./manage.py runserver
```

## The issue

When wanting to create a new page with the title `Hello İstanbul`, the slugification
fails. Further analysis is below the _Steps to reproduce_.

## Steps to reproduce

1. Log into the admin with your superuser: [http://localhost:8000/admin/](http://localhost:8000/admin/).
2. Open up Home in the explorer
3. Click _Add Child Page_
4. Set `Hello İstanbul` as title
5. Press _Save Draft_
6. The error message "The page could not be created due to validation errors" appears
   and the `Promote` tab has a badge with a 1 in it.
7. Click on the `Promote` tab
8. You will see an error message: `Enter a valid 'slug' consisting of Unicode letters, numbers, underscores, or hyphens.`.

## Expected behaviour

The lowercased version of the uppercase `İ` (latin capital letter i with dot above)
should work as a slug.

## Analysis

First we analyze the letter, then we try to reason why this fails with wagtail/django.

### Letter

What kind of character is this?

```python
In [1]: import unicodedata
In [2]: unicodedata.name('İ')
Out[2]: 'LATIN CAPITAL LETTER I WITH DOT ABOVE'
```

Also, we can see that this letter only consists of a single unicode character.

```python
In [3]: [unicodedata.name(character) for character in 'İ']
Out[3]: ['LATIN CAPITAL LETTER I WITH DOT ABOVE']
```

Now, we let Python create the lowercase version

```python
In [5]: li = 'İ'.lower()
In [6]: li
Out[6]: 'i̇'
```

Looks good. Let's see what it is called.

```python
In [7]: unicodedata.name(li)
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
<ipython-input-7-70daade6eaaf> in <module>
----> 1 unicodedata.name(li)

TypeError: name() argument 1 must be a unicode character, not str
```

Uh oh. Wait,.. what? So. That means this string consists of two unicode characters.

```python
In [8]: [unicodedata.name(character) for character in li]
Out[8]: ['LATIN SMALL LETTER I', 'COMBINING DOT ABOVE']
```

Indeed it does! So it is a "regular" small "i" with the combining diacritic "dot above".

### Django/Wagtail

So what is going on in Django? As far as I can tell, Wagtail does not have anything
to do with this, as [it simply calls django's slugify()](https://github.com/wagtail/wagtail/blob/e2607f917cc06bdf901ff7a52483ec89ec1115ba/wagtail/core/models.py#L426).

Now, let's go down the rabbit hole.

1. Wagtail calls `slugify("Hello İstanbul")`
2. Django slugifies the title
3. Django's SlugField validates the slug
4. If validation succeeds, Django commits it to the database

#### 1. wagtail calls slugify()

We are going to skip this. Looking [very unsuspicious](https://github.com/wagtail/wagtail/blob/e2607f917cc06bdf901ff7a52483ec89ec1115ba/wagtail/core/models.py#L426).

#### 2. django slugifies the title

We start by taking a look at [django's slugify](https://github.com/django/django/blob/master/django/utils/text.py#L400).

First our string (`"Hello İstanbul"`) is normalized. So it turns each unicode
character into a defined "normalized" form
([python's docs on this explain it well](https://docs.python.org/3.7/library/unicodedata.html#unicodedata.normalize)).

When we `allow_unicode`, django uses the normalized C form:

```python
# https://github.com/django/django/blob/master/django/utils/text.py#L400
# value is always "Hello İstanbul"
if allow_unicode:
    value = unicodedata.normalize('NFKC', value)
```

Doing this, does not change anything for us. As it should be, if I understand
Python's docs on this correctly.

```python
In [20]: unicodedata.normalize('NFKC', "Hello İstanbul")
Out[20]: 'Hello İstanbul'
```

Now, the next step in django's slugification is this line:

```python
# https://github.com/django/django/blob/master/django/utils/text.py#L404
value = re.sub(r'[^\w\s-]', '', value).strip().lower()
```

Splitting it up into three steps:

1. Remove anything that is not a space, a (unicode) character or a hypen
2. Strip leading and trailing whitespace
3. Lowercase the entire string

Again, our `value` would be `Hello İstanbul`. First, we do what the regex does:

```python
In [21]: re.sub(r'[^\w\s-]', '', "Hello İstanbul")
Out[21]: 'Hello İstanbul'
```

That is alright, because every character in our string is either a unicode character
or a space:

```python
In [22]: [(character, unicodedata.name(character), re.match('[\w\s]', character)) for character in "Hello İstanbul"]
Out[22]:
[('H', 'LATIN CAPITAL LETTER H', <re.Match object; span=(0, 1), match='H'>),
 ('e', 'LATIN SMALL LETTER E', <re.Match object; span=(0, 1), match='e'>),
 ('l', 'LATIN SMALL LETTER L', <re.Match object; span=(0, 1), match='l'>),
 ('l', 'LATIN SMALL LETTER L', <re.Match object; span=(0, 1), match='l'>),
 ('o', 'LATIN SMALL LETTER O', <re.Match object; span=(0, 1), match='o'>),
 (' ', 'SPACE', <re.Match object; span=(0, 1), match=' '>),
 ('İ',
  'LATIN CAPITAL LETTER I WITH DOT ABOVE',
  <re.Match object; span=(0, 1), match='İ'>),
 ('s', 'LATIN SMALL LETTER S', <re.Match object; span=(0, 1), match='s'>),
 ('t', 'LATIN SMALL LETTER T', <re.Match object; span=(0, 1), match='t'>),
 ('a', 'LATIN SMALL LETTER A', <re.Match object; span=(0, 1), match='a'>),
 ('n', 'LATIN SMALL LETTER N', <re.Match object; span=(0, 1), match='n'>),
 ('b', 'LATIN SMALL LETTER B', <re.Match object; span=(0, 1), match='b'>),
 ('u', 'LATIN SMALL LETTER U', <re.Match object; span=(0, 1), match='u'>),
 ('l', 'LATIN SMALL LETTER L', <re.Match object; span=(0, 1), match='l'>)]
```

14 characters, 14 matches. All right!

Then, Django calls `strip`, to free the string of extraneous whitespace:

```python
In [24]: re.sub(r'[^\w\s-]', '', "Hello İstanbul").strip()
Out[24]: 'Hello İstanbul'
```

As expected, everything stays the same.

Now the last step in this very line is to lowercase the string:

```python
In [26]: re.sub(r'[^\w\s-]', '', "Hello İstanbul").strip().lower()
Out[26]: 'hello i̇stanbul'
```

After that, the method replaces all spaces with a dash:

```python
In [34]: re.sub(r'[-\s]+', '-', 'hello i̇stanbul')
Out[34]: 'hello-i̇stanbul'
```

And that's that.

#### 3. Django's SlugField validates the value

This is where things "fail". The SlugField is given the result of the slugification:
`'hello-i̇stanbul'`.

Now the SlugField does [it's validation](https://github.com/django/django/blob/a28d1b38e55cf588cfaae97de6a575d5c9f90a96/django/forms/fields.py#L1178).

If we take a look at the SlugField validator being used (with `allow_unicode = True`), we end up with
the [`slug_unicode_re` regular expression, as defined in `django/core/validators.py`](https://github.com/django/django/blob/master/django/core/validators.py#L244).

```python
# allow for unicode words (\w), dashes (-). \Z is for marking the end of the string.
slug_unicode_re = _lazy_re_compile(r'^[-\w]+\Z')
```

From here, things go awry. That regular expression does not match the output
generated by `slugify("Hello İstanbul")`.

```python
In [30]: type(slug_unicode_re.match('hello-i̇stanbul'))
Out[30]: NoneType
```

Why does it fail? Let's repeat the small analysis we did before and remember that the
lowercase version of `İ` consists of two characters:

```python
# Just a quick reminder:
In [10]: [unicodedata.name(character) for character in unicodedata.normalize('NFKC', 'İ'.lower())]
Out[10]: ['LATIN SMALL LETTER I', 'COMBINING DOT ABOVE']

# Now the gory details:
In [36]: [(character, unicodedata.name(character), slug_unicode_re.match(character)) for character in 'hello-i̇stanbul']
Out[36]:
[('h', 'LATIN SMALL LETTER H', <re.Match object; span=(0, 1), match='h'>),
 ('e', 'LATIN SMALL LETTER E', <re.Match object; span=(0, 1), match='e'>),
 ('l', 'LATIN SMALL LETTER L', <re.Match object; span=(0, 1), match='l'>),
 ('l', 'LATIN SMALL LETTER L', <re.Match object; span=(0, 1), match='l'>),
 ('o', 'LATIN SMALL LETTER O', <re.Match object; span=(0, 1), match='o'>),
 ('-', 'HYPHEN-MINUS', <re.Match object; span=(0, 1), match='-'>),
 ('i', 'LATIN SMALL LETTER I', <re.Match object; span=(0, 1), match='i'>),

 # EUREKA!!
 ('̇', 'COMBINING DOT ABOVE', None),

 ('s', 'LATIN SMALL LETTER S', <re.Match object; span=(0, 1), match='s'>),
 ('t', 'LATIN SMALL LETTER T', <re.Match object; span=(0, 1), match='t'>),
 ('a', 'LATIN SMALL LETTER A', <re.Match object; span=(0, 1), match='a'>),
 ('n', 'LATIN SMALL LETTER N', <re.Match object; span=(0, 1), match='n'>),
 ('b', 'LATIN SMALL LETTER B', <re.Match object; span=(0, 1), match='b'>),
 ('u', 'LATIN SMALL LETTER U', <re.Match object; span=(0, 1), match='u'>),
 ('l', 'LATIN SMALL LETTER L', <re.Match object; span=(0, 1), match='l'>)]
```

The combining diacritic does not validate. Which is 100% correct. It should not!
However, that is exactly why the slugification process "fails" in this scenario,
because `slugify()` can be made to produce output that does not validate against
`slug_unicode_re`.

## Summary & Proposed Solution

Summing up: the culprit is the order in which `slugify()` executes the lowercasing.
It does so, _after_ cleaning unwanted characters away. However, as demonstrated,
lowercasing can trigger the creation of unwanted characters. "Unwanted" meaning a
character that can not be validated by the `SlugField`.

There are two ways to solve this:

1. Extend the `slug_unicode_re` to allow for combining diacritics. Or…
2. …change when the lowercasing happens.

Personally I am leaning towards option `2`.

So [this line](https://github.com/django/django/blob/master/django/utils/text.py#L404)
in `django/utils/text.py`'s `slugify`:

```python
value = re.sub(r'[^\w\s-]', '', value).strip().lower()
```

becomes

```python
value = re.sub(r'[^\w\s-]', '', value.lower()).strip()
```

Repeating the proposed solution with our demonstration:

```python
In [37]: re.sub(r'[^\w\s-]', '', 'Hello İstanbul'.lower()).strip()
# Diacritic is now removed, hence we have the lower case latin i
Out[37]: 'hello istanbul'

In [38]: re.sub(r'[-\s]+', '-', 'hello istanbul')
Out[38]: 'hello-istanbul'

In [39]: slug_unicode_re.match('hello-istanbul')
Out[39]: <re.Match object; span=(0, 14), match='hello-istanbul'>
```

### An even deeper dive in

Thanks to [Matt Westcott's suggestion](https://wagtailcms.slack.com/archives/C81FGJR2S/p1571400630283400?thread_ts=1570706995.063800&cid=C81FGJR2S)
that it could also be a bug in Python itself, I took a quick dive into the unicode
plane myself.

-   The `İ` is the _Latin Capital Letter I with Dot Above_. It's codepoint is `U+0130`.
    According to the [chart for the Latin Extended-A set](https://www.unicode.org/charts/PDF/U0100.pdf),
    it's lowercase version is `U+0069`.
-   `U+0069` lives in the [C0 Controls and Basic Latin set](https://www.unicode.org/charts/PDF/U0000.pdf).
    Lo and behold: it is the _Latin small letter I_. So a latin lowercase `i`.

Does this really mean that Python is doing something weird here by adding the
_Combining dot above_?

```python
In [8]: [unicodedata.name(character) for character in 'İ'.lower()]
Out[8]: ['LATIN SMALL LETTER I', 'COMBINING DOT ABOVE']
```

I'm in no way a unicode pro, so my assumption might be very naive and wrong.
