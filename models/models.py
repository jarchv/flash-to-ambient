import torch

if torch.cuda.is_available():
	torch.cuda.manual_seed_all(20)

import torch.nn as nn
import os
import numpy as np

from torchvision import transforms

from .nets import vgg16_generator_unpool
from .nets import vgg16_generator_deconv
from .nets import discriminator
from .nets import GANLoss

class VGG_ED:
	def __init__(self, opts, isTrain=True):
		self.opts    = opts
		self.isTrain =  isTrain
		self.device  = torch.device('cuda:{}'.format(self.opts.gpu_ids[0])) if self.opts.gpu_ids else torch.device('cpu') 
		self.attention = opts.attention
		if isTrain:
			print('Training mode [{}]'.format(self.device))
			if opts.upsample == 'deconv':
				self.Gen = vgg16_generator_deconv(levels=5, opts=opts).cuda()
			elif opts.upsample == 'unpool':
				self.Gen = vgg16_generator_unpool(levels=5, opts=opts).cuda()

			self.Gen.set_vgg_as_encoder()	
			
			if   opts.R_loss == 'Cauchy': self.criterion = self.CauchyLoss
			elif opts.R_loss == 'L1'    : self.criterion = torch.nn.L1Loss()

			print('Training with:\n')
			print('\tmodel      \t{}'.format(opts.model))
			print('\tloss 	  \t{}'.format(opts.R_loss))
			print('\tupsample \t{}'.format(opts.upsample))
			print('\tAttention\t{}'.format(opts.attention))
			print('\tvgg_freezed\t{}'.format(opts.vgg_freezed))
			print('\tout_act  \t{}\n'.format(opts.out_act))
			self.optimizer_gen = torch.optim.Adam(self.Gen.parameters(), lr=opts.lr1, betas=(opts.beta1, 0.999))
		else:
			print('Testing mode![on {}]\n'.format(self.device))
			if opts.upsample == 'deconv':
				self.Gen = vgg16_generator_deconv(levels=5, opts=opts).cuda()
			elif opts.upsample == 'unpool':
				self.Gen = vgg16_generator_unpool(levels=5, opts=opts).cuda()
			self.Gen.set_vgg_as_encoder()

	def CauchyLoss(self, inputs, targets, C=0.1): # C=0.1 -> 0.1*255/2=12.75[0-255]
		diff_err = inputs-targets
		loss_raw = C * torch.log(torch.mul(diff_err, diff_err)/(C*C)+1)
		return loss_raw.mean()

	def set_inputs(self, inputs, targets=None):
		self.real_X = torch.cuda.FloatTensor(inputs)
		if targets is not None: 
			self.real_Y = torch.cuda.FloatTensor(targets)
			if self.attention:
				self.att_map= 1.0 - torch.abs(self.real_X - self.real_Y).mean(dim=1, keepdim=True)

	def forward(self):
		self.Z, self.fake_Y = self.Gen(self.real_X)
		
	def backward_gen(self):
		if self.attention:
			self.loss_R = self.criterion(self.fake_Y * self.att_map, self.real_Y * self.att_map)
		else: 
			self.loss_R = self.criterion(self.fake_Y, self.real_Y)
		self.loss_R.backward()

	def optimize_parameters(self):
		self.optimizer_gen.zero_grad()
		self.forward()
		self.backward_gen()
		self.optimizer_gen.step()

	def set_requires_grad(self, nets, requires_grad=False):
		"""Set requies_grad=Fasle for all the networks to avoid unnecessary computations
		Parameters:
            nets (network list)   -- a list of networks
            requires_grad (bool)  -- whether the networks require gradients or not
		"""
		if not isinstance(nets, list):
			nets = [nets]
		for net in nets:
			if net is not None:
				for param in net.parameters():
					param.requires_grad = requires_grad

	def save_model(self, ep):
		file_model = 'model-{}.pth'.format(str(ep))
		save_path = os.path.join(self.opts.checkpoints_dir, file_model)

		if len(self.opts.gpu_ids) > 0 and torch.cuda.is_available():
			torch.save(self.Gen.cpu().state_dict(), save_path)
			self.Gen.cuda()

	def load_model(self, ep):
		file_model = 'model-{}.pth'.format(str(ep))
		load_path  = os.path.join(self.opts.checkpoints_dir, file_model)
		state_dict = torch.load(load_path, map_location=str(self.device))

		self.Gen.load_state_dict(state_dict)

class advModel:
	def __init__(self, opts, isTrain=True):
		self.opts    = opts
		self.isTrain = isTrain
		self.device  = torch.device('cuda:{}'.format(self.opts.gpu_ids[0])) if self.opts.gpu_ids else torch.device('cpu') 
		self.attention_gen = opts.attention_gen
		self.attention_dis = opts.attention_dis

		if isTrain:
			print('Training mode [{}]'.format(self.device))
			if opts.upsample == 'deconv':
				self.Gen = vgg16_generator_deconv(levels=5, opts=opts).cuda()
			elif opts.upsample == 'unpool':
				self.Gen = vgg16_generator_unpool(levels=5, opts=opts).cuda()

			self.Gen.set_vgg_as_encoder()	
			
			if   opts.R_loss == 'Cauchy': self.criterion = self.CauchyLoss
			elif opts.R_loss == 'L1'    : self.criterion = torch.nn.L1Loss()

			print('Training with:\n')
			print('\tmodel      \t{}'.format(opts.model))
			print('\tloss 	  \t{}'.format(opts.R_loss))
			print('\tupsample \t{}'.format(opts.upsample))
			print('\tAttention gen\t{}'.format(opts.attention_gen))
			print('\tAttention dis\t{}'.format(opts.attention_dis))
			print('\tvgg_freezed\t{}'.format(opts.vgg_freezed))
			print('\tout_act  \t{}\n'.format(opts.out_act))

			self.Dis = discriminator(deep=6, down_leves=5, ksize=3, att=opts.attention_dis).cuda()
			self.criterionGAN  = GANLoss().cuda()
			self.optimizer_gen = torch.optim.Adam(self.Gen.parameters(), lr=opts.lr1, betas=(opts.beta1, 0.999))
			self.optimizer_dis = torch.optim.Adam(self.Dis.parameters(), lr=opts.lr2, betas=(opts.beta1, 0.999))

		else:
			print('Testing mode![on {}]\n'.format(self.device))
			if opts.upsample == 'deconv':
				self.Gen = vgg16_generator_deconv(levels=5, opts=opts).cuda()
			elif opts.upsample == 'unpool':
				self.Gen = vgg16_generator_unpool(levels=5, opts=opts).cuda()
			self.Gen.set_vgg_as_encoder()

	def CauchyLoss(self, inputs, targets, C=0.1):
		diff_err = inputs-targets
		loss_raw = C * torch.log(torch.mul(diff_err, diff_err)/(C*C)+1)
		return loss_raw.mean(0)

	def set_inputs(self, inputs, targets):
		self.real_X = torch.cuda.FloatTensor(inputs)
		if targets is not None: 
			self.real_Y = torch.cuda.FloatTensor(targets)
			if self.attention_gen or self.attention_dis:
				self.att_map= 1.0 - torch.abs(self.real_X - self.real_Y).mean(dim=1, keepdim=True)

	def forward(self):
		_, self.fake_Y = self.Gen(self.real_X)

	def backward_gen(self):
		#synthetic_pair = torch.cat((self.real_X, self.fake_Y), dim=1)
		# We set mode=real, because we will use the first term of the BCEWithLogitsLoss
		
		if self.attention_gen:
			self.loss_R  = self.criterion(self.fake_Y * self.att_map, self.real_Y * self.att_map)
		else: 
			self.loss_R  = self.criterion(self.fake_Y, self.real_Y)

		if self.attention_dis:
			dis_out_fake = self.Dis(self.fake_Y, self.att_map)
		else:
			dis_out_fake = self.Dis(self.fake_Y)
		
		self.loss_Gen  = self.criterionGAN(dis_out_fake, 'real')   # log(D(G(x)))
		self.loss_Gen_L1 = self.loss_R + self.loss_Gen * self.opts.lambda_GAN
		self.loss_Gen_L1.backward()	

	def backward_dis(self):
		#synthetic_pair = torch.cat((self.real_X, self.fake_Y), dim=1)
		#authentic_pair = torch.cat((self.real_X, self.real_Y), dim=1)

		# No backpropagation along the generator (detach)

		if self.attention_dis:
			dis_out_fake = self.Dis(self.fake_Y.detach(), self.att_map)
			dis_out_real = self.Dis(self.real_Y, self.att_map)
		else:
			dis_out_fake = self.Dis(self.fake_Y.detach())
			dis_out_real = self.Dis(self.real_Y)

		self.loss_dis_fake = self.criterionGAN(dis_out_fake, 'fake')  # log(1-D(x_hat)))
		self.loss_dis_real = self.criterionGAN(dis_out_real, 'real')  # log(D(x)))

		self.loss_Dis  = self.loss_dis_fake + self.loss_dis_real
		self.loss_Dis_ = self.loss_Dis * self.opts.lambda_GAN
		self.loss_Dis_.backward()

	def optimize_parameters(self):
		# Update Discriminator
		self.forward()
		self.set_requires_grad(self.Dis, True)
		self.optimizer_dis.zero_grad()
		self.backward_dis()
		self.optimizer_dis.step()

		# Update Generator
		self.set_requires_grad(self.Dis, False)
		self.optimizer_gen.zero_grad()
		self.backward_gen()
		self.optimizer_gen.step()

	def set_requires_grad(self, nets, requires_grad=False):
		"""Set requies_grad=Fasle for all the networks to avoid unnecessary computations
		Parameters:
            nets (network list)   -- a list of networks
            requires_grad (bool)  -- whether the networks require gradients or not
		"""
		if not isinstance(nets, list):
			nets = [nets]
		for net in nets:
			if net is not None:
				for param in net.parameters():
					param.requires_grad = requires_grad

	def save_model(self, ep):
		file_model = 'model-{}.pth'.format(str(ep))
		save_path = os.path.join(self.opts.checkpoints_dir, file_model)

		if len(self.opts.gpu_ids) > 0 and torch.cuda.is_available():
			torch.save(self.Gen.cpu().state_dict(), save_path)
			self.Gen.cuda()

	def load_model(self, ep):
		file_model = 'model-{}.pth'.format(str(ep))
		load_path  = os.path.join(self.opts.checkpoints_dir, file_model)
		state_dict = torch.load(load_path, map_location=str(self.device))

		self.Gen.load_state_dict(state_dict)

def setModel(opts, isTrain=True):
	if opts.model == 'advModel':
		return advModel(opts, isTrain), True
	elif opts.model == 'VGG_ED':
		return VGG_ED(opts, isTrain), False
	else:
		print('Non available model...')