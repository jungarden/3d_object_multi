#!/usr/bin/python
# encoding: utf-8

import os
import random
import torch
import numpy as np
from PIL import Image
from torch.utils.data import Dataset

from utils_multi import read_truths_args, read_truths, get_all_files
from image_multi import *

class listDataset(Dataset):

    def __init__(self, root, shape=None, shuffle=True, transform=None, objclass=None, target_transform=None, train=False, seen=0, batch_size=64, num_workers=4, cell_size=32, num_keypoints=8, max_num_gt=50): 
       with open(root, 'r') as file:
           self.lines = file.readlines()
       if shuffle:
           random.shuffle(self.lines)
       self.nSamples         = len(self.lines)
       self.transform        = transform
       self.target_transform = target_transform
       self.train            = train
       self.shape            = shape
       self.seen             = seen
       self.batch_size       = batch_size
       self.num_workers      = num_workers
       self.objclass         = objclass
       self.cell_size        = cell_size
       self.nbatches         = self.nSamples // self.batch_size
       self.num_keypoints    = num_keypoints
       self.max_num_gt       = max_num_gt # maximum number of ground-truth labels an image can have

    def __len__(self):
        return self.nSamples

    def __getitem__(self, index):
        assert index <= len(self), 'index range error'
        imgpath = self.lines[index].rstrip()

        if self.train and index % self.batch_size == 0:
            if self.seen < 20*self.nbatches*self.batch_size:
               width = 13*self.cell_size
               self.shape = (width, width)
            elif self.seen < 40*self.nbatches*self.batch_size:
               width = (random.randint(0,3) + 13)*self.cell_size
               self.shape = (width, width)
            elif self.seen < 60*self.nbatches*self.batch_size:
               width = (random.randint(0,5) + 12)*self.cell_size
               self.shape = (width, width)
            elif self.seen < 80*self.nbatches*self.batch_size:
               width = (random.randint(0,7) + 11)*self.cell_size
               self.shape = (width, width)
            else: 
               width = (random.randint(0,9) + 10)*self.cell_size
               self.shape = (width, width)

        if self.train:
            # Decide on how much data augmentation you are going to apply
            jitter = 0.1
            hue = 0.05
            saturation = 1.5 
            exposure = 1.5

            img, label = load_data_detection(imgpath, self.shape, jitter, hue, saturation, exposure, self.num_keypoints, self.max_num_gt)
            label = torch.from_numpy(label)
        else:
            img = Image.open(imgpath).convert('RGB')
            if self.shape:
                img = img.resize(self.shape)

            filename = imgpath.split('/')[-1].replace('.png', '.txt').replace('.jpg', '.txt')
            
            # 경로에 맞게 labpath 변경
            labpath = os.path.join('data', imgpath.split('/')[-4], 'labels', filename)
                
            num_labels = 2*self.num_keypoints+1 # +2 for ground-truth of width/height , +1 for class label
            label = torch.zeros(self.max_num_gt*num_labels)
            if os.path.getsize(labpath):
                ow, oh = img.size
                tmp = torch.from_numpy(read_truths_args(labpath))
                tmp = tmp.view(-1)
                tsz = tmp.numel()
                if tsz > self.max_num_gt*num_labels:
                    label = tmp[0:self.max_num_gt*num_labels]
                elif tsz > 0:
                    label[0:tsz] = tmp

        if self.transform is not None:
            img = self.transform(img)

        if self.target_transform is not None:
            label = self.target_transform(label)

        self.seen = self.seen + self.num_workers
        return (img, label)
