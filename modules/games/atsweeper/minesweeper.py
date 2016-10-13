import numpy as np

#=============================================================================
class Minesweeper_game(object):
	def __init__(self, dims, n_mines):

		self.dims = ( dims[ 0 ] - 1, dims[ 1 ] - 1 )		

		self.minefield = np.zeros( dims )
		self.infofield = np.zeros( dims )
		self.checkedfield = np.zeros( dims )
		self.displayfield = ( -1 ) * np.ones( dims )

		self.numberOfMines = n_mines
		self.numberOfFlags = 0

		self.fill_minefield( )
		self.fill_infofield( )

	#-------------------------------------------------------------------------
	def neighbors( self, x, y ):

		if x == 0 and y == 0:
			neighbors = [ ( 0, 1 ), ( 1, 1 ), ( 1, 0 ) ]

		elif x == 0 and y == self.dims[ 1 ]: 	
			neighbors = [ ( 0, self.dims[ 1 ] - 1 ), ( 1, self.dims[ 1 ] - 1 ), ( 1, self.dims[ 1 ] ) ]

		elif x == self.dims[ 0 ] and y == 0:
			neighbors = [ ( self.dims[ 0 ] - 1, 0 ), ( self.dims[ 0 ] - 1, 1 ), ( self.dims[ 0 ], 1 ) ]

		elif x == self.dims[ 0 ] and y == self.dims[ 1 ]:
			neighbors = [ ( self.dims[ 0 ] - 1, self.dims[ 1 ] ), ( self.dims[ 0 ], self.dims[ 1 ] - 1 ), ( self.dims[ 0 ] - 1, self.dims[ 1 ] - 1) ]
	
		elif x == 0 and y != 0 and y != self.dims[ 1 ]:
			neighbors = [ ( 0, y + 1 ), ( 0, y - 1 ), ( 1, y ), ( 1, y + 1 ), ( 1, y - 1 ) ]

		elif y == self.dims[ 1 ] and x != 0 and x != self.dims[ 0 ]:
			neighbors = [ ( x, self.dims[ 1 ] - 1 ), ( x + 1, self.dims[ 1 ] - 1 ), ( x - 1, self.dims[ 1 ] - 1 ), ( x + 1, self.dims[ 1 ] ), ( x - 1, self.dims[ 1 ] ) ]

		elif x == self.dims[ 0 ] and y != 0 and y != self.dims[ 1 ]:	
			neighbors = [ ( self.dims[ 0 ] - 1, y ), ( self.dims[ 0 ] - 1, y + 1 ), ( self.dims[ 0 ] - 1, y - 1 ), ( self.dims[ 0 ], y + 1 ), ( self.dims[ 0 ], y - 1 ) ]

		elif y == 0 and x != 0 and x != self.dims[ 0 ]:
			neighbors = [ ( x + 1, 0 ), ( x - 1, 0 ), ( x, 1 ), ( x + 1, 1 ), ( x - 1, 1 ) ]

		else:
			neighbors = [ ( x - 1, y - 1 ), ( x, y - 1 ), ( x + 1, y - 1 ), ( x - 1, y ), ( x + 1, y ), ( x - 1, y + 1 ), ( x, y + 1 ), ( x + 1, y + 1 ) ]

		return neighbors
	
        #-------------------------------------------------------------------------
	def fill_minefield(self):

		for m in xrange( self.numberOfMines ):
			placed = False

			while not placed:
				mine_x = np.random.randint( self.dims[ 0 ] + 1 )	
				mine_y = np.random.randint( self.dims[ 1 ] + 1 )

				if self.minefield[ mine_x, mine_y ] == 0:				
					self.minefield[ mine_x, mine_y ] = 1 # 1 symbolizes an unflagged mine
					placed = True
					
	#-------------------------------------------------------------------------
	def fill_infofield(self):

		minefield_copy = np.zeros( ( self.dims[ 0 ] + 3, self.dims[ 1 ] + 3 ) )
		infofield_copy = np.zeros( ( self.dims[ 0 ] + 3, self.dims[ 1 ] + 3 ) )

		minefield_copy[ 1 : -1, 1 : -1 ] = self.minefield	

		infofield_copy += np.roll( minefield_copy, -1, axis = 0 )
		infofield_copy += np.roll( minefield_copy, 1, axis = 0 )
		infofield_copy += np.roll( minefield_copy, -1, axis = 1 )
		infofield_copy += np.roll( minefield_copy, 1, axis = 1 )
		infofield_copy += np.roll( np.roll( minefield_copy, 1, axis = 1 ), 1, axis = 0 )
		infofield_copy += np.roll( np.roll( minefield_copy, -1, axis = 1 ), 1,axis = 0 )
		infofield_copy += np.roll( np.roll( minefield_copy, -1, axis = 1 ), -1, axis = 0)
		infofield_copy += np.roll( np.roll( minefield_copy, 1, axis = 1 ), -1, axis = 0)

		self.infofield = infofield_copy[ 1 : -1, 1 : -1 ]

	#-------------------------------------------------------------------------
	def check_for_mines(self, y, x):

		if self.minefield[ x, y ] == 1:
			self.displayfield = self.displayfield - self.minefield
			return True

		else:
			if self.infofield[ x, y ] == 0 and self.displayfield[ x, y ] == -1:
				self.displayfield[ x, y ] = 0

				for coords in self.neighbors( x, y):
					if self.displayfield[ coords[ 0 ], coords[ 1 ] ] != -3:
	
						self.check_for_mines( coords[ 1 ], coords[ 0 ] )
								
			else:						
				self.displayfield[ x, y ] = self.infofield[ x, y ]		
		
	#-------------------------------------------------------------------------
	def flag_field(self, y, x):
		# print self.displayfield
		if self.displayfield[ x, y ] == -1:
			self.numberOfFlags += 1	
			self.displayfield[ x, y ] = -3
						
			if self.numberOfFlags == self.numberOfMines and ( self.displayfield[ np.where( self.minefield == 1 ) ] == - 3 ).all( ):
				# print 'win'
				return True

		elif self.displayfield[ x, y ] == -3:
			self.numberOfFlags -= 1
			self.displayfield[ x, y ] = -1
		
		return False		


#=============================================================================
if __name__ == '__main__':

	game = Minesweeper_game( ( 10, 10 ), 1 )	
	game.check_for_mines( 9, 9 )
	print game.displayfield
	print game.minefield
