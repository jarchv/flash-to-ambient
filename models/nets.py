import torch
import torch.nn as nn

from .vgg import vgg16_encoder, vgg16_decoder

class vgg16_generator_unpool(nn.Module):
    def __init__(self, levels, opts):
        super(vgg16_generator_unpool, self).__init__()
        assert (levels > 0)

        self.enc5   = vgg16_encoder(levels=levels)
        self.dec5   = vgg16_decoder(levels=levels, mode=opts.upsample, out_act=opts.out_act)
        self.levels = levels

    def forward(self, input_imgs):  
        
        layers  = self.enc5.unpool_forward(input_imgs)
        att_map = input_imgs.mean(dim=1, keepdim=True)
        out_img = self.dec5.unpool_forward(layers, att_map = att_map)
            
        return layers['z'], out_img

    def set_vgg_as_encoder(self):
        from torchvision import models
        
        vgg16 = models.vgg16(pretrained=True, progress=True)
        features_list = list(vgg16.features)

        # [224x224]
        if self.levels > 1:
            self.enc5.conv1_1.weight.copy_(features_list[0].weight)
            self.enc5.conv1_1.bias.copy_(features_list[0].bias)
            self.enc5.conv1_2.weight.copy_(features_list[2].weight)
            self.enc5.conv1_2.bias.copy_(features_list[2].bias)
            
        # [112x112]
        if self.levels > 2:
            self.enc5.conv2_1.weight.copy_(features_list[5].weight)
            self.enc5.conv2_1.bias.copy_(features_list[5].bias)
            self.enc5.conv2_2.weight.copy_(features_list[7].weight)
            self.enc5.conv2_2.bias.copy_(features_list[7].bias)

        # [56x56]
        if self.levels > 3:
            self.enc5.conv3_1.weight.copy_(features_list[10].weight)
            self.enc5.conv3_1.bias.copy_(features_list[10].bias)
            self.enc5.conv3_2.weight.copy_(features_list[12].weight)
            self.enc5.conv3_2.bias.copy_(features_list[12].bias)
            self.enc5.conv3_3.weight.copy_(features_list[14].weight)
            self.enc5.conv3_3.bias.copy_(features_list[14].bias)

        # [28x28]
        if self.levels > 4:
            self.enc5.conv4_1.weight.copy_(features_list[17].weight)
            self.enc5.conv4_1.bias.copy_(features_list[17].bias)
            self.enc5.conv4_2.weight.copy_(features_list[19].weight)
            self.enc5.conv4_2.bias.copy_(features_list[19].bias)
            self.enc5.conv4_3.weight.copy_(features_list[21].weight)
            self.enc5.conv4_3.bias.copy_(features_list[21].bias)

        # [14x14]
        if self.levels > 5:
            self.enc5.conv5_1.weight.copy_(features_list[24].weight)
            self.enc5.conv5_1.bias.copy_(features_list[24].bias)
            self.enc5.conv5_2.weight.copy_(features_list[26].weight)
            self.enc5.conv5_2.bias.copy_(features_list[26].bias)
            self.enc5.conv5_3.weight.copy_(features_list[28].weight)
            self.enc5.conv5_3.bias.copy_(features_list[28].bias)

class vgg16_generator_deconv(nn.Module):        
    def __init__(self, levels, opts):
        super(vgg16_generator_deconv, self).__init__()
        assert (levels > 0)

        self.enc5   = vgg16_encoder(levels=levels)
        self.dec5   = vgg16_decoder(levels=levels, mode=opts.upsample, out_act=opts.out_act)
        self.levels = levels

    def forward(self, input_imgs):  

        layers  = self.enc5.deconv_forward(input_imgs)
        att_map = input_imgs.mean(dim=1, keepdim=True)
        out_img = self.dec5.deconv_forward(layers, att_map = att_map)
            
        return layers['z'], out_img

    def set_vgg_as_encoder(self):
        from torchvision import models
        
        vgg16 = models.vgg16(pretrained=True, progress=True)
        features_list = list(vgg16.features)

        if True:
            if self.levels > 0:
                # [224x224]
                self.enc5.conv1_1.weight.copy_(features_list[0].weight)
                self.enc5.conv1_1.bias.copy_(features_list[0].bias)
                self.enc5.conv1_2.weight.copy_(features_list[2].weight)
                self.enc5.conv1_2.bias.copy_(features_list[2].bias)
            
            if self.levels > 1:
                # [112x112]
                self.enc5.conv2_1.weight.copy_(features_list[5].weight)
                self.enc5.conv2_1.bias.copy_(features_list[5].bias)
                self.enc5.conv2_2.weight.copy_(features_list[7].weight)
                self.enc5.conv2_2.bias.copy_(features_list[7].bias)

            if self.levels > 2:
                # [56x56]
                self.enc5.conv3_1.weight.copy_(features_list[10].weight)
                self.enc5.conv3_1.bias.copy_(features_list[10].bias)
                self.enc5.conv3_2.weight.copy_(features_list[12].weight)
                self.enc5.conv3_2.bias.copy_(features_list[12].bias)
                self.enc5.conv3_3.weight.copy_(features_list[14].weight)
                self.enc5.conv3_3.bias.copy_(features_list[14].bias)

            if self.levels > 3:
                # [28x28]
                self.enc5.conv4_1.weight.copy_(features_list[17].weight)
                self.enc5.conv4_1.bias.copy_(features_list[17].bias)
                self.enc5.conv4_2.weight.copy_(features_list[19].weight)
                self.enc5.conv4_2.bias.copy_(features_list[19].bias)
                self.enc5.conv4_3.weight.copy_(features_list[21].weight)
                self.enc5.conv4_3.bias.copy_(features_list[21].bias)

            if self.levels > 4:
                # [14x14]
                self.enc5.conv5_1.weight.copy_(features_list[24].weight)
                self.enc5.conv5_1.bias.copy_(features_list[24].bias)
                self.enc5.conv5_2.weight.copy_(features_list[26].weight)
                self.enc5.conv5_2.bias.copy_(features_list[26].bias)
                self.enc5.conv5_3.weight.copy_(features_list[28].weight)
                self.enc5.conv5_3.bias.copy_(features_list[28].bias)

class discriminator(nn.Module):
    def __init__(
        self, 
        init_ch    = 64, 
        ksize      = 3, 
        down_leves = 3, 
        deep       = 5,
        att        = False):
        
        """
            Discriminator:

            default layers: 224(in)-112(down)-56(down)-28(down)-28-28(out)
            levels = 5
            down_levels = 3 
        """
        super(discriminator, self).__init__()
        
        self.input_ch  = 3

        in_ch  = self.input_ch
        seq    = []
        out_ch = init_ch
        pad    = int((ksize/2 - 1) if ksize%2 == 0 else (ksize - 1)/2)

        self.att = att

        # input: [224x224], output: [28x28] (default)
        for _ in range(down_leves):
            seq += self.conv_block(in_ch, out_ch, ksize, 2, pad)
            in_ch  = out_ch
            out_ch = out_ch*2
        
        # convs with stride 1: deep-down_leves-1=5-3-1=1
        for _ in range(deep-down_leves-1):
            seq += self.conv_block(in_ch, out_ch, ksize, 1, pad)
            in_ch  = out_ch
            out_ch = out_ch*2

        seq.append(nn.Conv2d(in_channels = in_ch,
                             out_channels= 1,
                             kernel_size = ksize,
                             stride      = 1,
                             padding     = pad))

        self.dis_arch = nn.Sequential(*seq)
        

    def conv_block(self, in_ch, out_ch, ksize, stride, pad):
        subseq = [nn.Conv2d(in_channels  = in_ch,
                            out_channels = out_ch,
                            kernel_size  = ksize, 
                            stride       = stride, 
                            padding      = pad)]

        if in_ch != self.input_ch:
            subseq.append(nn.BatchNorm2d(out_ch))
        subseq.append(nn.LeakyReLU(inplace=True))

        return  subseq


    def forward(self, input_pair, att_map=None):
        if self.att:
            input_pair = torch.mul(input_pair, att_map)
        out = self.dis_arch(input_pair) #[28x28]
        return out

class GANLoss(nn.Module):
    def __init__(self):
        super(GANLoss, self).__init__()
        self.register_buffer('real_label', torch.tensor(1.0))
        self.register_buffer('fake_label', torch.tensor(0.0))
        
        self.loss = nn.BCEWithLogitsLoss()

    def __call__(self, pred, mode):
        if mode == 'real':
            target = self.real_label
        elif mode == 'fake':
            target = self.fake_label

        target = target.expand_as(pred)
        out    = self.loss(pred, target)
        
        return out