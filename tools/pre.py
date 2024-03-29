from __future__ import print_function

import glob
import numpy as np
import sys
import os
import random
import math

from PIL import Image
from PIL import ImageOps

def read_pair(a, f):
    img_a = Image.open(a)
    img_f = Image.open(f)
    return img_a, img_f

def dataset_list(path):
    source_path  = 'datasets/'
    dataset_path = os.path.join(source_path, path)
    train_ambnt_set = glob.glob(dataset_path + '/train/*ambient.png')
    train_flash_set = glob.glob(dataset_path + '/train/*flash.png')

    train_ambnt_set.sort()
    train_flash_set.sort()

    train_set = []

    for i,j in zip(train_ambnt_set,train_flash_set):
        assert (i[:-12] == j[:-10])
        train_set.append([i,j])

    test_ambnt_set = glob.glob(dataset_path+'/test/*ambient.png')
    test_flash_set = glob.glob(dataset_path+'/test/*flash.png')

    test_ambnt_set.sort()
    test_flash_set.sort()

    test_set = []
    for i,j in zip(test_ambnt_set,test_flash_set):
        assert (i[:-12] == j[:-10])
        test_set.append([i,j])

    return train_set, test_set


def random_crop(img, crop_size, wrand, hrand):
    img = img.crop((wrand, hrand, wrand+crop_size, hrand+crop_size))
    return img

def get_array_list_on_train(
    input_list    = None,
    filtered_list = None, 
    crop          = True, 
    load_min_size = None,
    out_size      = None,
    out_act       = 'tanh'):

    ambnt_list = []
    flash_list = []
    
    ambnt_bf_list = []
    flash_bf_list = []

    for iobj, (img_a, img_f) in enumerate(input_list):
        #img_a.show()
        #img_f.show()
        if filtered_list:
            img_a_bf, img_f_bf = filtered_list[iobj]

        if crop:
            flip_rand = random.random()
            if flip_rand < 0.5:
                img_a = img_a.transpose(Image.FLIP_LEFT_RIGHT)
                img_f = img_f.transpose(Image.FLIP_LEFT_RIGHT)

            M     = load_min_size * random.uniform(0.8, 1.0)
            wrand = random.randint(0, int(img_a.size[0]-M))
            hrand = random.randint(0, int(img_a.size[1]-M))
 
            img_a = random_crop(img_a, M, wrand, hrand)
            img_f = random_crop(img_f, M, wrand, hrand)
            
            img_a = img_a.resize([out_size, out_size], Image.ANTIALIAS)
            img_f = img_f.resize([out_size, out_size], Image.ANTIALIAS)

            if filtered_list:
                if flip_rand < 0.5:
                    img_a_bf = img_a_bf.transpose(Image.FLIP_LEFT_RIGHT)
                    img_f_bf = img_f_bf.transpose(Image.FLIP_LEFT_RIGHT)    

                img_a_bf = random_crop(img_a_bf, M, wrand, hrand)
                img_f_bf = random_crop(img_f_bf, M, wrand, hrand)
                img_a_bf = img_a_bf.resize([out_size, out_size], Image.ANTIALIAS)
                img_f_bf = img_f_bf.resize([out_size, out_size], Image.ANTIALIAS)


                #img_a_bf.show()
                #img_f_bf.show()

        #img_a.show()
        #img_f.show()

        if filtered_list:
            img_a_bf_out = get_array_to_net(img_a_bf, out_act)
            img_f_bf_out = get_array_to_net(img_f_bf, out_act)

            ambnt_bf_list.append(img_a_bf_out)
            flash_bf_list.append(img_f_bf_out)

            img_a_bf.close()
            img_f_bf.close()

        img_a_out = get_array_to_net(img_a, out_act)
        img_f_out = get_array_to_net(img_f, out_act)

        ambnt_list.append(img_a_out)
        flash_list.append(img_f_out)
        
        img_a.close()
        img_f.close()

    data_dict = {
            'ambnt_imgs'    : ambnt_list,
            'flash_imgs'    : flash_list,
            'ambnt_bf_imgs' : ambnt_bf_list,
            'flash_bf_imgs' : flash_bf_list
    }

    return data_dict

def get_array_list_on_test(
    input_list    = None,
    filtered_list = None,
    load_min_size = None,
    out_size      = None,
    out_act       = 'tanh'):

    ambnt_list = []
    flash_list = []
    
    ambnt_bf_list = []
    flash_bf_list = []

    for iobj, img_f in enumerate(input_list):
        if filtered_list:
            img_f_bf     = filtered_list[iobj]
            img_f_bf_out = get_array_to_net(img_f_bf)

            flash_bf_list.append(img_f_bf_out)
            img_f_bf.close()

        img_f_out = get_array_to_net(img_f, out_act)
        flash_list.append(img_f_out)

        img_f.close()

    data_dict = {
            'flash_imgs'    : flash_list,
            'flash_bf_imgs' : flash_bf_list
    }

    return data_dict

def get_array_to_net(im, out_act):
    img_arr = np.asarray(im, dtype=np.float32)/255.0
    if out_act == 'tanh': 
        img_arr = img_arr * 2.0 - 1.0
    img_arr = np.transpose(img_arr, (2, 0, 1))

    return img_arr


def read_train_data(path):
    data_list, _ = dataset_list(path)

    im_list = []
    n_pairs    = 0
    list_size  = len(data_list)

    for a, f in data_list:
        img_a_tmp, img_f_tmp = read_pair(a,f)
        img_a = img_a_tmp.copy()
        img_f = img_f_tmp.copy()

        im_list.append([img_a, img_f])
        img_a_tmp.close()
        img_f_tmp.close()
        n_pairs+=1
        print("\rreading data\t: [{:3}/{:3}] {:3.1f}%".format(n_pairs, list_size, 100.0*(n_pairs/list_size)), end='')
    print("\rreading data\t: [{:3}/{:3}] {:3.1f}%".format(n_pairs, list_size, 100.0*(n_pairs/list_size)))
    print("train size\t: {:d} pairs of images".format(len(im_list)), end='\n\n')

    return im_list

def read_test_data(path):
    _, data_list = dataset_list(path)

    im_list   = []
    file_list = []
    list_size = len(data_list)
    
    for n_imgs, (a, f) in enumerate(data_list):
        img_f_tmp = Image.open(f)
        #img_a_tmp, img_f_tmp = read_pair(a,f)
        #img_a = img_a_tmp.copy()
        img_f = img_f_tmp.copy()
        im_list.append(img_f)
        file_list.append(f)
        #im_list.append([img_a, img_f])
        #img_a_tmp.close()
        #img_f_tmp.close()
        #n_pairs+=1
        print("\rreading data\t: [{:3}/{:3}] {:3.1f}%".format((n_imgs+1), list_size, 100.0*((n_imgs+1)/list_size)), end='')
    print("\rreading data\t: [{:3}/{:3}] {:3.1f}%".format((n_imgs+1), list_size, 100.0*((n_imgs+1)/list_size)))
    print("test size\t: {:d} pairs of images".format(len(im_list)), end='\n\n')

    return file_list, im_list

def shuffle_data(imgs_sets):
    rng_state = np.random.get_state()
    out = []
    print(len(imgs_sets))
    for img_set in imgs_sets:
        np.random.set_state(rng_state)
        np.random.shuffle(img_set)
        out.append(img_set)

    return out

                

