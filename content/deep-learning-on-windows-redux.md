Title: Deep Learning on Windows, Redux
Date: 2017-06-27 12:34
Author: noodlefrenzy
Category: Machine Learning
Tags: Windows, Deep Learning, Machine Learning, Cognitive Toolkit, CNTK, TensorFlow, Keras
Slug: deep-learning-on-windows-redux
Status: draft
Summary: An updated primer on how to get deep learning frameworks up and running on Windows, with examples.

## Why the Rewrite?

When I wrote my initial [Deep Learning on Windows](./deep-learning-on-windows.html) guide, it was a year ago - TensorFlow was just starting to surface and was far from running on Windows, CNTK didn't run in Python, and Theano was the current king of the heap. Seems like a lifetime ago in the Deep Learning world, and the whole universe of DL has changed since then. For one, it's dramatically easier to get up and running, and my example is woefully out of date. It's time for an update.

## A Quick Guide to Deep Learning

Deep Learning is a newly-popular set of techniques in the field of Machine Learning that have shown the power to generalize well over a whole host of problems, and even solve some problems that were considered unsolveable just a few years before. There are [many](http://deeplearning.net/tutorial/) [tutorials](http://deeplearning.stanford.edu/tutorial/) and [write-ups](https://www.quora.com/What-is-deep-learning) on these techniques [online](https://www.microsoft.com/en-us/research/publication/deep-learning-methods-and-applications/), so I won't go too deep, but I'll lay out the basics.

People have known for some time that a particular Machine Learning technique - Neural Networks - has the capability to learn complex mappings from inputs (e.g. images) to outputs (e.g. "which digit is this?") through the use of a "hidden layer" that mapped between the two.

![A Simple MLP]({filename}/images/Multilayer_Perceptron.png)

With the advent of _Big Data_, we suddenly have incredibly large sets of input data we could feed to these models, and with the increasing power of GPUs we have the compute capacity to do so. We had seen Neural Networks with multiple hidden layers in the past, but training them was so expensive and they didn't seem to outperform other techniques, so they'd been discarded. Someone realized that with the amount of data we now have and the compute resources available to us, these constraints no longer applied and these older networks were brought back.  

![Denser, Deeper Neural Network]({filename}/images/Dense_NN.png)

Since then, networks have only gotten deeper (more hidden layers) and their shapes have only gotten stranger (convolutional neurons, feedback loops, and layer skipping). At this point we know they are powerful, but we don't really know how powerful they can get and the field is wide open for advancement. For a more detailed and far more eloquent history of the field, see [NVidia's great post](https://devblogs.nvidia.com/parallelforall/deep-learning-nutshell-history-training/).

In this post I'll walk you through how to get one of the most popular toolkits up and running on Windows, and run through and explain some fun examples. Speaking of NVidia, this post assumes you have an NVidia GPU which will make your neural networks train _MUCH_ faster.

## Deep Learning Toolkits

Machine Learning has been around for a long time and there are dozens of frameworks out there written in everything from low-level C code to AzureML. In the Deep Learning space several frameworks have risen to prominence only to gradually lose ground to the "next big thing". It's hard to say who has the best framework, and a lot of it right now comes down to choices about whether it supports your current and expected needs, whether it runs on your platform and whether you can code to it in a language you enjoy. TensorFlow seems to be the current king of the heap and has a lot of mind-share behind it, but PyTorch is coming up as a strong contender and of course Microsoft's Cognitive Toolkit is now a player with v2's support for Python.

[Caffe](http://caffe.berkeleyvision.org/) is one of the elders of the field, and with their "Model Zoo" of pre-trained models makes a compelling case for continued usefulness. With plenty of tutorials, good documentation, and a binding for Python it's a solid choice. It was supplanted by [Torch](http://torch.ch/), Facebook's framework for Lua. This was popular for a while until it started being replaced by more modern Tensor-based variants. These Tensor-based networks allow for _networks of computations_ instead of _networks of layers_ and have proven to be more flexible for modern deep learning models. Since this is all just math, both of these have been revised to more gracefully support computation networks at this point, and with [PyTorch](http://pytorch.org/) and [Caffe2](https://caffe2.ai/) both of these frameworks have a new lease on life.

Microsoft's [Cognitive Toolkit](https://github.com/Microsoft/CNTK) and Google's [TensorFlow](https://github.com/tensorflow/tensorflow) are both Tensor-based systems - both run on Linux and Windows. [Keras](https://github.com/fchollet/keras) is a wrapper around existing Tensor toolkits that allows for easier model building, training, and evaluation - it easily runs atop TensorFlow and CNTK, as well as an older alternate I used in the previous version of this article ([Theano](https://github.com/Theano/Theano)).

## Keras, TensorFlow, and CNTK

### Installing on Windows

Keras, TensorFlow and CNTK all (can) run as Python libraries, so the first thing we'll need to do is get a Python installation on Windows. For this, there are a couple of great options out there, but I'll go with [Anaconda](https://www.continuum.io/downloads) - this differs from my previous post where I used [WinPython](https://winpython.github.io/). Why did I change? Primarily because I'm now on so many different projects that I need to maintain a large number of environments sometimes using different Python versions, and I find that Anaconda makes that easier. My point about WinPython having a side-effect-free installation, however, still holds true.

#### Installing Anaconda, Using Conda

Navigate to the Anaconda [download page](https://www.continuum.io/downloads) and download the latest 64-bit installer. Once you've installed it into your location of choice, start up a new command window and we'll be ready to install the rest of the tools. First, though, you should take a brief detour to learn about [`conda`](https://conda.io/docs/using/index.html) - we'll be using `conda` to manage our environment, consider it like a `virtualenv`++. If you already have Anaconda installed, consider trying `conda update conda` and potentially `conda update python` to make sure you're up to date.

You should create an environment to isolate your baseline Python installation from any packages you install - this is both good practice for maintaining your installation, and for allowing you to document it and replicate it elsewhere (e.g. Docker, other VMs). To do so, pick a name (e.g. "deep-windows") and create a new environment using `conda create -n deep-windows` (or whatever name you've chosen). You can then activate it using `activate deep-windows`.

#### Adding the Baseline

Within your new environment we need to install the modern Deep Learning toolkits we'll be using, but first let's install several packages that we'll commonly need. Anaconda's repos tend to be a bit out of date, but they contain [MKL-optimized](https://software.intel.com/en-us/mkl) versions of several packages that are useful. As such, I typically install those using `conda install` and then use `pip install` for all others. We'll be installing Numpy, Scipy, Pandas, Scikit-Learn, and Jupyter Notebooks. We'll need h5py because H5 is a common format for serialized models (including the Keras model we will be using below), and PIL (well, Pillow) for processing images. We should also consider installing Bokeh and/or Dash for better charting.

    > conda install numpy scipy
    > pip install pandas scikit-learn jupyter h5py Pillow
    > pip install bokeh dash

#### But First, a Word From Our GPU Overlords

We could install and run our Deep Learning tools right now, but as soon as you tried to train any model of complexity you'd grow old before it completed. For any reasonable training time, you'll need GPU support. I mentioned in the beginning that you should have an NVidia GPU for training, so let's set it up for Deep Learning Toolkit support. Head to the [NVidia CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit) home and download and install it. Then hit up the [NVidia Deep Learning](https://developer.nvidia.com/deep-learning) center and sign up for a developer account. Download the [CUDnn library](https://developer.nvidia.com/cudnn) and install it - currently [TensorFlow wants](https://www.tensorflow.org/install/install_windows) CUDnn v5.1 with CUDA Toolkit v8.0, but that changes fast so click through and choose appropritely.

#### Adding the Latest Versions of CNTK, TensorFlow, and Keras

Now that your environment has a solid baseline to build upon, we'll install the latest releases of some of the modern Deep Learning toolkits I mentioned above. CNTK installs via Wheel files which you can find on their [installation page](https://docs.microsoft.com/en-us/cognitive-toolkit/Setup-Windows-Python) (Note that if you want to use CNTK with BrainScript and/or the command line, you'll want [the full install](https://docs.microsoft.com/en-us/cognitive-toolkit/Setup-Windows-Binary-Script) instead). TensorFlow installs via Pip and we'll be using the GPU version. Keras installs via Pip as well - it used to depend on Theano (see my previous post) and as of this writing it still winds up installing it, so expect some compilation here. If anything fails, this is likely where it'll go wrong. 

    > # Choose the install wheel from https://docs.microsoft.com/en-us/cognitive-toolkit/Setup-Windows-Python 
    > pip install https://cntk.ai/PythonWheel/GPU/cntk-2.0-cp36-cp36m-win_amd64.whl
    > pip install tensorflow-gpu
    > pip install keras

#### Testing Your Installation

With the latest CNTK, TensorFlow and Keras installed, ensure you can import the libraries:

    > python
    >>> import cntk
    >>> import tensorflow
    >>> import keras

## Deep Dreaming

[Deep Dream](https://research.googleblog.com/2015/06/inceptionism-going-deeper-into-neural.html) has evolved some since my previous version of this post, so let's go straight to the (Keras) source, grab their example, and use that as our baseline. The Keras version now uses Inception V3 as opposed to the previous version using VGG16 - let's grab it and run it on our example image:

[![Ninjacat]({filename}/images/ninjacat_small.png)]({filename}/images/ninjacat_large.png)

Download the [`deep_dream.py`](https://raw.githubusercontent.com/fchollet/keras/master/examples/deep_dream.py) example from the Keras GitHub repo and run it on our example image. Assume you've downloaded the image above (the large version), you should be able to run the below and take a look at the result.

    > wget https://raw.githubusercontent.com/fchollet/keras/master/examples/deep_dream.py
    > python deep_dream.py ninjacat_large.png ninjadream
    > explorer ninjadream.png

And this would turn

[![Ninjacat]({filename}/images/ninjacat_small.png)]({filename}/images/ninjacat_large.png)

into

[![Ninjacat, dreamy edition]({filename}/images/ninjadream_small_redux.png)]({filename}/images/ninjadream_large_redux.png)


## Neural Artistry

Neural Artistry first surfaced with a [paper from Germany](https://arxiv.org/pdf/1508.06576v2.pdf) and has since become another big showcase example for the power of Deep Learning. Essentially, the way it works is to take an existing trained Convolutional Neural Network and use it to convolve two images together, by joining the outputs of different convolutional layers from each image. The Keras example (as of now) still uses VGG16 for its network, so download the script and we'll use it to merge our favorite NinjaCat with a [lesser known Norwegian work](https://en.wikipedia.org/wiki/The_Scream#/media/File:The_Scream.jpg).

    > wget https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/The_Scream.jpg/1280px-The_Scream.jpg -O the_scream.jpg
    > wget https://raw.githubusercontent.com/fchollet/keras/master/examples/neural_style_transfer.py
    > python neural_style_transfer.py ninjacat_large.png the_scream.jpg ninjascream

And that'd turn

[![Ninjacat]({filename}/images/ninjacat_small.png)]({filename}/images/ninjacat_large.png)

into

[![Ninjacat, screamy edition]({filename}/images/ninjascream_small_redux.png)]({filename}/images/ninjascream_large_redux.png)

## Conclusion and Future Work

Setting up deep learning toolkits on Windows has become substantially easier in just the short time since I wrote my initial version of this article. TensorFlow now runs on Windows (finally), CNTK v2 works with Python and installs much more easily, and Keras runs against both TensorFlow (its new default) and CNTK. I'll write a follow-up to this with information on using Keras to switch between CNTK and TensorFlow, and how to use Docker containers to manage your Deep Learning training.