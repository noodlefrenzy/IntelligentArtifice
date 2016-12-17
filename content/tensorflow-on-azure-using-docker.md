Title: TensorFlow on Azure Using Docker
Date: 2015-12-08 14:33
Author: noodlefrenzy
Category: Machine Learning
Tags: Azure, Containerization, Docker, Machine Learning, ML, Neural Networks, TensorFlow
Slug: tensorflow-on-azure-using-docker
Status: published

We live in a time of proliferating machine learning toolkits. From the
not-so-humble start of [OpenCV](http://opencv.org/) (for computer
vision), [Weka](http://www.cs.waikato.ac.nz/ml/weka/), and
[Caffe](http://caffe.berkeleyvision.org/), in just a short period of
time we've added [Torch](http://torch.ch/),
[Theano](http://www.deeplearning.net/software/theano/),
[CNTK](http://research.microsoft.com/apps/pubs/?id=226641)and now
[TensorFlow](https://googleblog.blogspot.com/2015/11/tensorflow-smarter-machine-learning-for.html)and
[SystemML](http://siliconangle.com/blog/2015/11/24/ibm-open-sources-its-systemml-machine-learning-tech/)
(and I'm not even mentioning things like
[SparkML](http://spark.apache.org/docs/latest/mllib-guide.html)and
[AzureML](https://azure.microsoft.com/en-us/services/machine-learning/)).
As a non-researcher who actually needs to make use of these things,
honestly, it's kind of freaking me out - way too much to learn in way
too short a time.

[TensorFlow](https://www.tensorflow.org/)is a shiny new tensor-based
neural network toolkit (so computational flow graphs instead of the more
traditional layer-based neural networks) which currently runs on Linux
and MacOS (but not Windows, due primarily to their dependence on Bazel
for building, see [issue
17](https://github.com/tensorflow/tensorflow/issues/17) on their GitHub
repo). However, in the new Microsoft we don't let things like that stop
us! In this guide I'll show you how to deploy a TensorFlow-enabled
Python (Jupyter, really) Notebook onto a Linux VM in Azure using Docker.

Docker On Azure
---------------

If you're unfamiliar with Docker, it's a containerization service -
meaning that you build out a machine once, and let Docker take care of
stamping that image on as many "machines" (really, containers) as you
want. Container definitions can inherit, meaning if someone has built
almost exactly what you need, you're free to inherit from that and
add/remove as you see fit. The good news for me is that I can "stand on
the shoulders of giants" and use the hard work of others for my own
purposes.

Docker came to Azure last year in a big way, and now it's easier than
ever to fire up a new VM running a Docker engine. Using the now-GA "new"
portal, just search for "Docker on Ubuntu":

![Search for docker on ubuntu
server]({filename}/images/New_Docker.png)

Once you select "Docker on Ubuntu Server" you'll be guided through the
creation process:

![Docker VM Creation
Process]({filename}/images/Docker_VM_Create.png)

Upon completion, your VM will start up, and you can then SSH into it and
execute whatever Docker commands you wish.

Installing TensorFlow
---------------------

Once you have Docker installed on a VM, it's simple to install
TensorFlow into a container on that VM. You could use the image that
[Google has
provided](https://www.tensorflow.org/versions/master/get_started/os_setup.html#docker_install)
with their release, but I prefer to have it running inside of a[Jupyter
notebook](http://jupyter.org/) to allow me to play around with it.

Fortunately, I'm not alone, and someone has already created a Docker
image on DockerHub containing a [Jupyter installation with
TensorFlow](https://hub.docker.com/r/xblaster/tensorflow-jupyter/) -
thanks xblaster! Since Jupyter notebooks run a local server, we need to
allow port-forwarding for the port we intend to run on. Let's assume we
use the default that xblaster mentions in his readme - 8888. We need to
not only port-forward from the container to the Docker-engine-running
VM, but we need to port-forward from the VM externally. To do so, we
simple expose that port via the Azure portal by adding a new endpoint
mapping 8888 to whichever external port you choose:

![Exposing the Jupyter notebook
endpoint]({filename}/images/Expose_VM_Endpoint.png)

Now that you've exposed the endpoint from Azure, you can fire up the
Docker container by using the command:

```bash
docker run -d -p 8888:8888 -v /notebook:/notebook xblaster/tensorflow-jupyter
```

This will take some time, but once it's complete you should have a fully
functional Docker container running TensorFlow inside a Jupyter
notebook, which will persist the notebook for you.

Testing the Installation
------------------------

Now that you have a running Jupyter notebook instance, you can hit your
endpoint from your own home machine at
http://\<your-vm\>.cloudapp.net:8888/ and see it in action. Create a new
Python2 notebook, and then paste the code below and run it to verify
that TensorFlow is installed and working (from [their
documentation](https://www.tensorflow.org/versions/master/get_started/index.html)):

```python
import tensorflow as tf
import numpy as np

# Create 100 phony x, y data points in NumPy, y = x * 0.1 + 0.3
x_data = np.random.rand(100).astype("float32")
y_data = x_data * 0.1 + 0.3

# Try to find values for W and b that compute y_data = W * x_data + b
# (We know that W should be 0.1 and b 0.3, but Tensorflow will
# figure that out for us.)
W = tf.Variable(tf.random_uniform([1], -1.0, 1.0))
b = tf.Variable(tf.zeros([1]))
y = W * x_data + b

# Minimize the mean squared errors.
loss = tf.reduce_mean(tf.square(y - y_data))
optimizer = tf.train.GradientDescentOptimizer(0.5)
train = optimizer.minimize(loss)

# Before starting, initialize the variables.  We will 'run' this first.
init = tf.initialize_all_variables()

# Launch the graph.
sess = tf.Session()
sess.run(init)

# Fit the line.
for step in xrange(201):
    sess.run(train)
    if step % 20 == 0:
        print step, sess.run(W), sess.run(b)

# Learns best fit is W: [0.1], b: [0.3]
```

Now you know it works, but notice that you didn't need to hit an https
endpoint or type in any credentials - this is "security through
obscurity", otherwise known as *not secure at all!* Do me a favor and
don't use this for anything you don't mind losing, and shut it down when
you're done. If you want to secure your notebook, that's beyond the
scope of this post, but the [documentation is easy to
follow](http://jupyter-notebook.readthedocs.org/en/latest/public_server.html).

Happy coding!

