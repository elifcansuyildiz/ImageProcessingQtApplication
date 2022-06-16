# Image Processing Tool (PySide6)

![image_processing_tool](imgs/gifs/image_processing_tool.gif)

## Introduction

This project provides a Qt user interface for some image processing methods so that the user can play with these methods interactively. Also, I hope this project to be a reference for developers since there are not many PySide6 examples on the Internet right now. 

[Youtube video link](https://youtu.be/8llrNf-44yw) for the demo of this project: 

[![](https://img.youtube.com/vi/8llrNf-44yw/0.jpg)](https://www.youtube.com/watch?v=8llrNf-44yw)



## Features

- Model-view-controller based design: `model.py`, `mainwindow.ui`, `controller.py` respectively.
- Used PySide6 which is the newest version of Qt library for Python.
- Multi-thread approach is used in order to increase the performance and prevent shuttering on the interface.
- Various image warping and image filtering methods are implemented.
- Applying multiple effects progressively and undo feature.

## Dependencies

- Tested on Ubuntu 20.04

```bash
$ sudo apt install python3.8 python3-pip python-is-python3
$ python -m pip install --upgrade pip
$ pip install -r requirements.txt
```

## Running

```bash
$ python controller.py
```



## Implemented Image Processing Methods

### Fish Eye Effect

Parameters: `x`, `y`, `sigma`

![fisheye_effect](imgs/gifs/fisheye_effect.gif)

### Swirl  Effect

Parameters: `x`, `y`, `sigma`, `magnitute`

![swirl_effect](imgs/gifs/swirl_effect.gif)

### Waves Effect

Parameters: `amplitute`, `frequency`, `phase`

![waves_effect](imgs/gifs/waves_effect.gif)

### Cylinder Anamorphosis Effect

Parameters: `angle`

![cylinder_effect](imgs/gifs/cylinder_effect.gif)

### Radial Blur Effect

Parameters: `sigma`

![radial_blur_effect](imgs/gifs/radial_blur_effect.gif)

### Perspective Mapping

Parameters: `A second image for warping`, `x1`, `y1`, `x2`, `y2`, `x3`, `y3`, `x4`, `y4`

![perspective_mapping](imgs/perspective_mapping.png)

![perspective_mapping2](imgs/perspective_mapping2.png)

### Square Eye Effect

Parameters: `center x`, `center y`, `sigma`, `p value`

![squareeye_effect](imgs/gifs/squareeye_effect.gif)

### Median Blurring

Parameters: `size`

![median_filter](imgs/gifs/median_filter.gif)

### Gaussian Filtering

Parameters: `radius`

![gaussian_filter](imgs/gifs/gaussian_filter.gif)

### Mean Filter

Parameters: `size`

![mean_filter](imgs/gifs/mean_filter.gif)
