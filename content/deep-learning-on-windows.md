Title: Deep Learning on Windows: A Getting Started Guide
Date: 2016-08-4 12:34
Author: noodlefrenzy
Category: Machine Learning
Tags: Windows, Deep Learning, Machine Learning, Theano, Keras, Lasagne
Slug: deep-learning-on-windows
Status: published
Summary: A primer on how to get deep learning frameworks up and running on Windows, with examples.

## UPDATE

Please see [my new post](./deep-learning-on-windows-redux.html) on this - everything has changed in less than a year so fairly massive revisions were necessary.

## A Quick Guide to Deep Learning

Deep Learning is a relatively new set of techniques in the field of Machine Learning that have shown the power to generalize well over a whole host of problems, and even solve some problems that were considered unsolveable just a few years before. There are [many](http://deeplearning.net/tutorial/) [tutorials](http://deeplearning.stanford.edu/tutorial/) and [write-ups](https://www.quora.com/What-is-deep-learning) on these techniques [online](https://www.microsoft.com/en-us/research/publication/deep-learning-methods-and-applications/), so I won't go too deep, but I'll lay out the basics.

People have known for some time that a particular Machine Learning technique - Neural Networks - has the capability to learn complex mappings from inputs (e.g. images) to outputs (e.g. "which digit is this?") through the use of a "hidden layer" that mapped between the two.

![A Simple MLP]({filename}/images/Multilayer_Perceptron.png)

With the advent of _Big Data_, we suddenly have incredibly large sets of input data we could feed to these models, and with the increasing power of GPUs we have the compute capacity to do so. We had seen Neural Networks with multiple hidden layers in the past, but training them was so expensive and they didn't seem to outperform other techniques that they'd been discarded. Someone realized that with the amount of data we now have and the compute resources available to us, these constraints no longer applied and these older networks were brought back.  

![Denser, Deeper Neural Network]({filename}/images/Dense_NN.png)

Since then, networks have only gotten deeper (more hidden layers) and their shapes have only gotten stranger (convolutional neurons, feedback loops, and layer skipping). At this point, we know they are powerful, but we don't really know how powerful they can get, and the field is wide open for advancement. For a more detailed and far more eloquent history of the field, see [NVidia's great post](https://devblogs.nvidia.com/parallelforall/deep-learning-nutshell-history-training/).

In this post, I'll walk you through how to get one of the most popular toolkits up and running on Windows, and run through and explain some fun examples.

## Deep Learning Toolkits

Machine Learning has been around for a long time and there are dozens of frameworks out there written in everything from low-level C code to AzureML. In the Deep Learning space, several frameworks have risen to prominence only to gradually lose ground to the "next big thing". It's hard to say who has the best framework, and a lot of it right now comes down to choices about whether it supports your current and expected needs, whether it runs on your platform, and whether you can code to it in a language you enjoy.

[Caffe](http://caffe.berkeleyvision.org/) is one of the elders of the field, and with their "Model Zoo" of pre-trained models makes a compelling case for continued usefulness. With plenty of tutorials, good documentation, and a binding for Python, it's a solid choice. It was supplanted by [Torch](http://torch.ch/), Facebook's framework for Lua. This was popular for a while, until it started being replaced by more modern Tensor-based variants. These Tensor-based networks allow for _networks of computations_ instead of _networks of layers_, and have proven to be more flexible for modern deep learning models.

Microsoft's [CNTK](https://github.com/Microsoft/CNTK) and Google's [TensorFlow](https://github.com/tensorflow/tensorflow) are both Tensor-based systems - both run on Linux, while CNTK runs on Windows and TensorFlow runs on Mac. Today I'll be focusing on one of TensorFlow's cheif competitors - [Theano](https://github.com/Theano/Theano). Theano is a Python-bound library that I find useful because it works in low-level Tensor space, but has libraries built on top of it like [Keras](https://github.com/fchollet/keras) and [Lasagne](https://github.com/Lasagne/Lasagne) that allow you to think at a higher level of abstraction, so e.g. defining a Convolutional Neural Network is trivial with Keras. This isn't meant to imply that Theano is the best - in fact if you want to see a more in-depth comparison of the frameworks, I'd recommend [this living article](https://github.com/zer0n/deepframeworks#ecosystem) by Kenneth Tran.

## Theano, Keras, and Lasagne

### Installing on Windows

Theano, Keras and Lasagne are all Python libraries, so the first thing we'll need to do is get a Python installation on Windows. For this, there are a couple of great options out there, but I'll go with [WinPython](https://winpython.github.io/) for two reasons - first, it installs with no side-effects, so can run side-by-side with any existing Anaconda or other installation you might have; second, it comes with a whole host of packages that you'll need already pre-installed (Numpy, Pandas, Sklearn).

#### Installing WinPython 3.x

As of the time of writing (2016-08-02) [WinPython 3.4.4.3](https://sourceforge.net/projects/winpython/files/WinPython_3.4/3.4.4.3/) is the latest branch of the 3.4 tree, and Theano did not yet support Python 3.5 on Windows (here's a [good description of why](http://stevedower.id.au/blog/building-for-python-3-5/)). If you're reading this far in the future, you should probably go to [the main WinPython page](https://winpython.github.io/) and [the Theano install docs](http://deeplearning.net/software/theano/install.html) to determine which version to use (or if you're _very_ far in the future, have your robot butler do it for you). Please use the 64-bit version (or if you're _insanely_ far in the future, the 512-bit version).

Once you've picked your version, installing is as trivial as downloading, double-clicking, and choosing where you want it. Since (as mentioned above) WinPython doesn't have any side-effects, I like to put it in a developer tools directory (c:\dev\tools\WinPython) so it's easy to find. WinPython comes with its own command window which instantiates with the correct path settings, allowing you to keep it off of your path and side-effect free.

#### Adding the Latest Theano, Keras and Lasagne

Now that you have WinPython installed, let's install the latest and greatest of the three toolkits we're using, via `pip`. Start up the `WinPython Command Prompt` and enter `pip --version` to ensure you're using the right version. It should mention the directory and version so you know exactly what you're dealing with, and you can then install the packages via:

    > pip install --upgrade --no-deps https://github.com/Theano/Theano/archive/master.zip
    > pip install --upgrade --no-deps https://github.com/fchollet/keras/archive/master.zip
    > pip install --upgrade --no-deps https://github.com/Lasagne/Lasagne/archive/master.zip

This installs the latest version of each directly from GitHub, without upgrading any of the dependencies (trust me, you don't want to accidentally upgrade Numpy unless you enjoy watching compiler errors).

#### Testing Your Installation

With the latest Theano installed, ensure you can import the library:

    > python
    >>> import theano

This should take some time, but complete successfully. Now you can clone the examples I've put together on [GitHub](https://github.com/noodlefrenzy/deep-learning-on-windows), and run the `mnist.py` example. This will test out both Lasagne and Theano by downloading the [MNIST data-set](http://yann.lecun.com/exdb/mnist/) and training a classifier to recognize images of digits.

    > git clone https://github.com/noodlefrenzy/deep-learning-on-windows.git
    > cd deep-learning-on-windows
    > python mnist.py

If this runs successfully, you know you have a working version of Theano and Lasagne. You might want to Ctrl+C before it finishes, since it'll be running pretty slow. Now to make it work at speeds where you can actually do something useful with it.

### GPU Support

If you have an NVidia GPU, you can make your deep learning frameworks **much** faster using [CUDA](https://www.nvidia.com/object/cuda_home_new.html) and [CUdnn](https://developer.nvidia.com/cudnn). First, you should download the [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit) and install it, then register for CUdnn, download that, and install it. I typically "install" CUdnn by just copying the contents of the `cuda` directory into the installed CUDA Toolkit (which for me on v7.5 is at `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v7.5`). At the time of this writing (2016-08-02), CUDA 8 isn't supported by Theano, so I've installed CUDA 7.5.

Once you have the libraries installed, you'll need to set the appropriate environment variable (`CUDA_PATH`) to your install (in my case `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v7.5`). I also add `%CUDA_PATH%\bin` to my `PATH` so I have access to the various CUDA tools.

#### Installing a Compiler

Using CUDA 7.5 requires an (old) Microsoft 64-bit C++ compiler be installed - specifically Visual Studio 2012 or 2013. For more details of CUDA on Windows, see [their intallation guide](http://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/#axzz4GDkECEZk). For those of you without VS2013 or an MSDN subscription, download the [community edition](https://www.visualstudio.com/en-us/news/vs2013-community-vs.aspx).

#### Configuring Theano To Use GPU

Theano has several configuration options that control how it builds and runs models, so to get it to run using your GPU, you'll need to reconfigure it. Since this is likely something you'll want for all of your Theano code, I create a `.theanorc` file for my entire WinPython install under the `settings` directory in WinPython (for me, that's `C:\dev\tools\WinPython\settings`). I've placed an example Theano configuration file in my GitHub repo, but the core settings are:

        [global]
        device=gpu

        [nvcc]
        compiler_bindir=C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC\bin\amd64
        flags=--cl-version=2013
 
#### (Re-)Testing Your Installation

Now that you've enabled GPU support, try running the MNIST example again (`python mnist.py`) and see what a difference having a GPU makes - the time for training a single epoch should be dramatically improved.  

## Deep Dreaming

I have to hand it to Google; their posts from the DeepMind team have been some of the most interesting in the field, not least [their post](https://research.googleblog.com/2015/06/inceptionism-going-deeper-into-neural.html) introducing "Deep Dream" and "Neural Artwork". We can replicate similar results using Keras, with the `deep_dream.py` example from my repo. This program uses the convolutional layers of the VGG16 network (from the [Visual Geometry Group](http://www.robots.ox.ac.uk/~vgg/research/very_deep/)) with pre-trained weights ([converted from Caffe](https://gist.github.com/baraldilorenzo/07d7802847aaad0a35d3)). VGG16 was a top model in the ImageNet competition (ILSVRC) of 2014, and is considered a great playground because it performs quite well and yet its structure is relatively easy to understand.

Assuming you've installed the pre-trained weights in `C:\dev\data` and are running against `C:\dev\images\ninjacat.png`, you could use the following command:

    > python deep_dream.py --weights_root c:\dev\data c:\dev\images\ninjacat.png ninjadream

And this would turn

[![Ninjacat]({filename}/images/ninjacat_small.png)]({filename}/images/ninjacat_large.png)

into

[![Ninjacat, dreamy edition]({filename}/images/ninjadream_small.png)]({filename}/images/ninjadream_large.png)

If you run into errors, it could be due to changes in the way Keras or Theano works or how they integrate with CUDA or CUdnn - they are all in _very_ active development. If so, please take a look at [the _official_ `deep_dream.py` example](https://github.com/fchollet/keras/blob/master/examples/deep_dream.py) from Keras - my copy just has enhanced argument handling and has factored a few things to make it easier to play around with.

## Neural Artistry

Neural Artistry first surfaced with a [paper from Germany](https://arxiv.org/pdf/1508.06576v2.pdf) and has since become another big showcase example for the power of Deep Learning. Essentially, the way it works is to take an existing trained Convolutional Neural Network and use it to convolve two images together, by joining the outputs of different convolutional layers from each image. Assuming (again) that you've installed the VGG16 pre-trained weights in `C:\dev\data` and are running against `C:\dev\images\ninjacat.png` in the style of, say, "The Scream" (which you have at `C:\dev\images\thescream.png`), your command would look like:

    > python neural_style_transfer.py --weights_root c:\dev\data c:\dev\images\ninjacat.png c:\dev\images\thescream.png ninjascream

And that'd turn

[![Ninjacat]({filename}/images/ninjacat_small.png)]({filename}/images/ninjacat_large.png)

into

[![Ninjacat, screamy edition]({filename}/images/ninjascream_small.png)]({filename}/images/ninjascream_large.png)

Once again, if you hit errors, please try [the _official_ `neural_style_transfer.py` example](https://github.com/fchollet/keras/blob/master/examples/neural_style_transfer.py) - my copy just factors out argument handling and lets you play around with which layers you use for transfer.

## Conclusion and Future Work

Setting up deep learning toolkits on Windows is fairly easy, and they've made it quite simple to experiment with them even if you have no background in the field. TensorFlow for Windows [is coming](https://github.com/tensorflow/tensorflow/issues/17) but is gated on Bazel support - once it happens, I'll create a follow-up post on [my blog](http://www.intelligent-artifice.net/) and go through a similar set of examples, but until then there is nothing stopping you from joining the Deep Learning revolution on your Windows machine.