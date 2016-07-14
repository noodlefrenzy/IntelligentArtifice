Title: Python List Comprehensions Gone Crazy
Date: 2016-01-27 15:48
Author: noodlefrenzy
Category: Software
Tags: Python
Slug: python-list-comprehensions-gone-crazy
Status: published

Recently, I was messing around with some image recognition tasks in
Python, and wanted to take a look at some of the images in my training
set. At first, I was tempted to go open file explorer and walk around
the directory tree spot-checking a few, but then I remembered that it
was easy to display images in an [IPython](http://ipython.org/) notebook
using \`IPython.display\`.

Perhaps I could write some code to walk the tree and show a few random
images from each directory. Surely it couldn't be that hard. I wrote a
simple method to do so:

```python
import os
import random
from IPython.display import display, Image

def select_rand(num, dirname, filenames):
    files = [file for file in filenames if file.endswith(('.jpg','.png'))]
    if len(files) > 0:
        print('Found ' + str(len(files)) + ' files in ' + dirname)
        files = random.sample(files, min(len(files), num))
        for filename in files:
            display(Image(os.path.join(dirname, filename)))
    else:
        print('Found no files for ' + dirname)

os.path.walk(root_dir, select_rand, 2)
```

Probably not the most efficient in the world, but it did exactly what I
wanted. Of course, at this point I was basically procrastinating from
what I was actually supposed to be doing, so decided to take it further.

Could I reduce this whole shebang to a single list comprehension? Is
this good programming? Nope, definitely not, but it's a fun way to test
your understanding of a language, so let's do it.

First, let's find a method that returns all of the files in a directory
tree, walking the tree like \`os.path.walk\` but returning the results
instead of visiting them - \`os.walk\` should do the trick. Why is
\`os.path.walk\` a visitor pattern and \`os.walk\` a generator? No clue,
let's move on.

```python
[t for t in os.walk(root_dir)]
```

Second, we'll filter the files to images only:

```python
[img
 for t in os.walk(root_dir)
 for img in t[2] if img.endswith(('.png', '.jpg'))]
```

Now let's turn these into actual Image objects by replacing \`img\` with
\`Image(os.path.join(t[0], img))\`. Okay, we now have Image objects for
*all* images, but that's too many to display in our notebook. We should
limit to three random ones from each directory:

```python
[Image(os.path.join(t[0], img))
 for t in os.walk(root_dir) 
 for img in random.sample([f for f in t[2] if f.endswith(('.png','.jpg'))], 3)]
```

We replace our \`t[2]\` with a random sample based on an inner
comprehension, and move our "is it an image" test into that
comprehension. This, however, explodes in my example with

    ValueError: sample larger than population

Boom! I apparently have some subdirectory in there with only one or two
images. Rather than try for some even crazier nested inner lambda, I'll
just define a simple specialization of \`sample\` that's protected
against too few results, and replace \`random.sample\` with that. We
then \`map\` each result to the \`display\` method to show it in the
notebook:

```python
sample = lambda l, n: l if len(l) < n else random.sample(l, n)
map(display, [Image(os.path.join(t[0], img))
 for t in os.walk(root_dir) 
 for img in sample([f for f in t[2] if f.endswith(('.png','.jpg'))], 3)])
```
