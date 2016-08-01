# Deep Learning on Windows: A Getting Started Guide

## A Quick Guide to Deep Learning

Deep Learning is a relatively new set of techniques in the field of Machine Learning that have shown the power to generalize well over a whole host of problems, and even solve some problems that were considered unsolveable just a few years before. There are [many](http://deeplearning.net/tutorial/) [tutorials](http://deeplearning.stanford.edu/tutorial/) and [write-ups](https://www.quora.com/What-is-deep-learning) on these techniques [online](https://www.microsoft.com/en-us/research/publication/deep-learning-methods-and-applications/), so I won't go too deep, but I'll lay out the basics.

People had known for some time that a particular Machine Learning technique - Neural Networks - had the capability to learn complex mappings from inputs (e.g. images) to outputs (e.g. "which digit is this?") through the use of a "hidden layer" that mapped between the two.

![A Simple MLP](http://faculty.ksu.edu.sa/zitouni/Pictures%20Library/MultiLayer%20Perceptron.gif)

With the advent of _Big Data_, we suddenly had incredibly large sets of input data we could feed to these models, and with the increasing power of GPUs we had the compute capacity to do so. We had seen Neural Networks with multiple hidden layers before, but training them was so expensive and they didn't seem to outperform other techniques, so they'd been discarded. Someone realized that with the amount of data we now had and the compute resources available to us, these constraints no longer applied, and these older networks were brought back. Since then, networks have only gotten deeper (more hidden layers) and their shapes have only gotten stranger (convolutional neurons, feedback loops, and layer skipping). At this point, we know they are powerful, but we don't really know how powerful they can get, and the field is wide open for advancement. For a more detailed and far more eloquent history of the field, see [NVidia's great post](https://devblogs.nvidia.com/parallelforall/deep-learning-nutshell-history-training/).

## Deep Learning Toolkits

Mention Caffe, Torch, Theano, CNTK, and TensorFlow.

## Theano, Keras, and Lasagne

### Installing on Windows

### GPU Support

## Deep Dreaming

## Neural Artistry

## Conclusion