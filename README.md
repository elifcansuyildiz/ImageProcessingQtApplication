# Image Processing Tool (PySide6)

## Introduction

This project provides a user interface for image processing so that the user can make fun images by applying effects one after the other as they wish.

[Youtube video link](xx) for the demo of this project

![image_processing_tool](imgs/image_processing_tool.png)

## Features

- Model-view-controller 
- Implemented with PySide6 which is the newest version of Qt library for Python
- Threads used in order to increase the performance and prevent lags on the interface.
- Various image warping and image filtering methods implemented
- Undo applied effects on the images
- Saving the effects and undoing them

## Dependencies

- Ubuntu 20.04

```bash
$ sudo apt install python3-pip 
$ python -m pip install --upgrade pip
$ pip install -r requirements.txt
```



## Image Processing Methods

### Fish Eye Effect

![fisheye_effect](imgs/gifs/fisheye_effect.gif)

### Swirl  Effect

![swirl_effect](imgs/gifs/swirl_effect.gif)

### Waves Effect

![waves_effect](imgs/gifs/waves_effect.gif)

### Cylinder Anamorphosis Effect

![cylinder_effect](imgs/gifs/cylinder_effect.gif)

### Radial Blur Effect

![radial_blur_effect](imgs/gifs/radial_blur_effect.gif)

### Perspective Mapping

![perspective_mapping](imgs/perspective_mapping.png)

![perspective_mapping2](imgs/perspective_mapping2.png)

### Square Eye Effect

![squareeye_effect](imgs/gifs/squareeye_effect.gif)

### Median Blurring

![median_filter](imgs/gifs/median_filter.gif)

### Gaussian Filtering

![gaussian_filter](imgs/gifs/gaussian_filter.gif)

### Mean Filter



![mean_filter](imgs/gifs/mean_filter.gif)
