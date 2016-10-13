import numpy as np

class Memory_game(object):
	def __init__(self, dims):
		self.dims = dims
		self.n_of_pairs = dims[0]*dims[1]/2		
		self.displayfield = (-1)*np.ones(dims)
		self.create_infofield()
		self.first_uncovered = False
		self.second_uncovered = False
			
	def create_infofield(self):
		info = np.arange(1,self.n_of_pairs + 1, 1)
		self.infofield = np.concatenate((info,info))
		np.random.shuffle(self.infofield)
		self.infofield = np.reshape(self.infofield, self.dims)			
				

	def check_field(self,y,x):
		if self.first_uncovered == False:
			self.displayfield[x,y] = self.infofield[x,y]
			self.first_uncovered = self.infofield[x,y]
			return 'first'


		else:
			if self.infofield[x,y] == self.first_uncovered:
				self.displayfield[x,y] = self.infofield[x,y]
				self.first_uncovered = False
				return 'second-hit'

								
			else:						
				self.displayfield[x,y] = self.infofield[x,y]
				self.second_uncovered = self.infofield[x,y]		
				return 'second-miss'
		
	def revert(self):
		self.displayfield -= (self.displayfield == self.first_uncovered)*(self.first_uncovered +1)
		self.displayfield -= (self.displayfield == self.second_uncovered)*(self.second_uncovered +1)
		self.first_uncovered = False
		self.second_uncovered = False

if __name__ == '__main__':
	game = Memory_game((3,4))
	
	print game.infofield

	game.check_field(0,0)
		
	print game.displayfield

	game.check_field(1,1)
	
	print game.displayfield

	game.revert()

	print game.displayfield
