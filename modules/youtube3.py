#!/bin/env python2.7
# -*- coding: utf-8 -*-

# This file is part of AP - Assistive Prototypes.
#
# AP is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# AP is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with AP. If not, see <http://www.gnu.org/licenses/>.

import wxversion
# wxversion.select( '2.8' )

import glob, os, time, sys

import wx
import wx.lib.buttons as bt
import subprocess

from pymouse import PyMouse
from pygame import mixer

from pilots import minitubePilot

#=============================================================================
class GenSymbolTextButton( bt.GenBitmapTextButton ): #Derive a class from GenBitmapTextButton and override _GetLabelSize and DrawLabel
    """Bitmapped button with text label displayed in accepted for AAC symbols position"""
    
    #-------------------------------------------------------------------------
    def _GetLabelSize(self):
        """ used internally """
        w, h = self.GetTextExtent( self.GetLabel( ) )
        if not self.bmpLabel:
            return w, h, True      # if there isn't a bitmap use the size of the text
        
        w_bmp = self.bmpLabel.GetWidth( ) + 2 
        h_bmp = self.bmpLabel.GetHeight( ) + 2

	height = h + h_bmp
	if w_bmp > w:
		width = w_bmp
	else:
		width = w

        return width, height, True

    #-------------------------------------------------------------------------
    def DrawLabel(self, dc, width, height, dx = 0, dy = 0):
        
        bmp = self.bmpLabel
        if bmp is not None:     # if the bitmap is used
            if self.bmpDisabled and not self.IsEnabled( ):
                bmp = self.bmpDisabled
            if self.bmpFocus and self.hasFocus:
                bmp = self.bmpFocus
            if self.bmpSelected and not self.up:
                bmp = self.bmpSelected
            bw,bh = bmp.GetWidth( ), bmp.GetHeight( ) ## size of the bitmap

            if not self.up:
                dx = dy = self.labelDelta

            hasMask = bmp.GetMask( ) is not None
        else:
            bw = bh = 0     # no bitmap -> size is zero

        if self.IsEnabled( ):
            dc.SetTextForeground( self.GetForegroundColour( ) )
        else:
            dc.SetTextForeground( wx.SystemSettings.GetColour( wx.SYS_COLOUR_GRAYTEXT ) )

        label = self.GetLabel( )
        tw, th = dc.GetTextExtent( label )     ## size of the text
        if not self.up:
            dx = dy = 4

        if bmp is not None:
            dc.DrawBitmap( bmp, ( width - bw ) / 2, ( height - 4*bh / 3 ) / 2, hasMask )      # draw bitmap if available (-bh)

        dc.DrawText( label, ( width - tw ) / 2, ( height + 2*bh / 3 ) / 2 )      # draw the text (+bh/2)


#=============================================================================
class youtube1( wx.Frame ):
	def __init__(self, parent, id):

	    self.winWidth, self.winHeight = wx.DisplaySize( )
            self.winHeight -= 20

            wx.Frame.__init__( self , parent , id, 'APYoutube1' )            
            style = self.GetWindowStyle( )
            self.SetWindowStyle( style | wx.STAY_ON_TOP )
            self.parent = parent

            self.Maximize( True )
            self.Centre( True )
            self.MakeModal( True )		
		
            self.initializeParameters( )				
            self.initializeBitmaps( )
            self.createGui( )								
            self.initializeTimer( )					
            self.createBindings( )						

	#-------------------------------------------------------------------------
	def initializeParameters(self):

            with open( './.pathToAP' ,'r' ) as textFile:
                self.pathToAP = textFile.readline( )
            
            sys.path.append( self.pathToAP )
            from reader import reader
            
            reader = reader()
            reader.readParameters()
            parameters = reader.getParameters()

            for item in parameters:
                try:
                    setattr(self, item[:item.find('=')], int(item[item.find('=')+1:]))
                except ValueError:
                    setattr(self, item[:item.find('=')], item[item.find('=')+1:])			
		
            self.panelIteration = 0
            self.rowIteration = 0						
            self.columnIteration = 0

            self.defaultNumberOfColumns = 6
            self.defaultNumberOfRows = 4
            
            self.countRows = 0
            self.countColumns = 0
            self.button = 1
            self.countMaxRows = 2									
            self.countMaxColumns = 2									
            self.numberOfPresses = 0

            self.numberOfSymbol = 0
            self.flag = 'panel'

            if self.control != 'tracker':
                self.mouseCursor = PyMouse( )
                self.mousePosition = self.winWidth - 8 - self.xBorder, self.winHeight - 8 - self.yBorder
                self.mouseCursor.move( *self.mousePosition )			

            if self.switchSound.lower( ) != 'off' or self.pressSound.lower( ) != 'off':
                mixer.init( )
                self.switchingSound = mixer.Sound( self.pathToAP + '/sounds/switchSound.ogg' )
                self.pressingSound = mixer.Sound( self.pathToAP + '/sounds/pressSound.ogg' )

                self.oneSound = mixer.Sound( self.pathToAP + '/sounds/rows/1.ogg' )
                self.twoSound = mixer.Sound( self.pathToAP + '/sounds/rows/2.ogg' )
                self.powrotSound = mixer.Sound( self.pathToAP + '/sounds/powrot.ogg' )
                self.pusteSound = mixer.Sound( self.pathToAP + '/sounds/puste.ogg' )

                self.pageFlipSounds = glob.glob( self.pathToAP + 'sounds/page_flip/*' )
            
                self.pageFlipSound = mixer.Sound( self.pageFlipSounds[ 1 ] )
                self.lastPageFlipSound = mixer.Sound( self.pathToAP + 'sounds/page-flip-13.ogg' )
                self.pageFlipSounds = [ mixer.Sound( self.pageFlipSound ) for self.pageFlipSound in self.pageFlipSounds ]

            self.SetBackgroundColour( 'black' )

	#-------------------------------------------------------------------------	
        def initializeBitmaps(self):

            dict = self.pathToAP + 'multimedia/youtube/*' 
            pages = sorted( [ item for item in glob.glob( dict ) if item[ item.rfind( '/' )+1: ].isdigit( ) ] )
            self.numberOfpages = len( pages )

            self.blissBook = {} #dictionary with keys as number of page and values as list of tuples (each tuple discribes one symbol) in form [bitmap, bitmap's position in sizer, bitmap's label] 
            self.numberOfRows, self.numberOfColumns, self.numberOfCells = [], [], [] 

            for page in pages:
                try:
                    pageNumber = int( page[ page.rfind( '/' )+1: ] )
                except ValueError:
                    print 'Folderowi %s nadano nieprawidłową nazwę. Dopuszczalna jest tylko nazwa numeryczna.' % page[ page.rfind( '/' )+1: ] 
                    pass

                sizerTopology = open( page + '/sizer' )
                
                for line in sizerTopology:

                    if line[ :12 ] == 'numberOfRows':
                        self.numberOfRows.append( int( line[ -2 ] ) )
                    elif line[ :15 ] == 'numberOfColumns':
                        self.numberOfColumns.append( int( line[ -2 ] ) )
                    else:
                        print 'Niewłaściwie opisana tablica na stronie %' % page
                        self.numberOfColumns.append( self.defaultNumberOfColumns )
                        self.numberOfRows.append( self.defaultNumberOfRows )     

                symbols = glob.glob( page + '/*.jpg' ) + glob.glob( page + '/*.png' ) + glob.glob( page + '/*.JPG' ) + glob.glob( page + '/*jpeg' )
                symbols = [item.decode('utf-8') for item in symbols]

                symbolInfo = []

                self.newHeight = 0.6*self.winHeight / self.numberOfRows[ -1 ]
                
                for symbol in symbols:
                    
                    image = wx.ImageFromStream( open( symbol, "rb" ) )

                    self.newWidth = image.GetSize( )[ 0 ] * ( self.newHeight / float( image.GetSize( )[ 1 ] ) )

                    image.Rescale( self.newWidth, self.newHeight, wx.IMAGE_QUALITY_HIGH )   
                    bitmapSymbol = wx.BitmapFromImage( image )

                    symbolName = symbol[ symbol.rfind( '/' )+1 : symbol.rfind( '.' ) ]

                    try:
                        symbolPosition = int( symbolName.split( '_' )[ 0 ] )
                        symbolTranslate = symbolName[ symbolName.find( '_' )+1: ].replace( '_', ' ' )
                        symbolInfo.append( [ bitmapSymbol, symbolPosition, symbolTranslate ] )
                    except ValueError:
                        print 'Symbol %s w folderze %s ma nieprawidłową nazwę.' % ( symbolName.split( '_' )[ 0 ], page[ page.rfind( '/' )+1: ] )
                        pass

                symbolInfo.sort( key = lambda symbolInfo: symbolInfo[ 1 ] )
                self.blissBook[ pageNumber ] = symbolInfo

	#-------------------------------------------------------------------------
	def createGui(self):

                self.mainSizer = wx.BoxSizer( wx.VERTICAL )

                self.panel = wx.Panel( self, 1,  style=wx.SUNKEN_BORDER )
                self.panel.SetSizeWH( self.winWidth, 0.22*self.winHeight )
                self.panelSize = self.panel.GetSize( )

                self.displaySizer = wx.BoxSizer ( wx.HORIZONTAL )
                self.displaySizer.SetMinSize( self.panelSize )
                self.displaySizer.Fit( self.panel )
                self.displaySizer.Add( self.panel, 1, wx.EXPAND )
                self.mainSizer.Add( self.displaySizer, 1, wx.EXPAND | wx.BOTTOM | wx.TOP, border = 1 )

                self.subSizers = []
               
                for item in range( len( self.numberOfRows ) ):
                    
                    subSizer = wx.GridSizer( self.numberOfRows[ item ], self.numberOfColumns[ item ], 1, 1 )
                    subSizer.SetMinSize( ( self.winWidth, 0.768*self.winHeight ) ) #this should not be done like this. Sizer should fit automatically.
                   
                    self.subSizers.append( subSizer )
                    
                    i, j = 0, 1

                    self.numberOfCells = self.numberOfRows[ item ] * self.numberOfColumns[ item ]
                    
                    while j <= self.numberOfCells:
                        try:
                            if i < len( self.blissBook[ item ] ):
                                while j != self.blissBook[ item ][ i ][ 1 ]:
                                    b = bt.GenButton( self, -1, name = 'puste' )
                                    b.Bind( wx.EVT_LEFT_DOWN, self.onPress )
                                    b.SetBackgroundColour( self.backgroundColour )
                                    self.subSizers[ item ].Add( b, 0, wx.EXPAND | wx.ALIGN_CENTER )
                                    j += 1

                                b = bt.GenBitmapButton( self , -1 , bitmap = self.blissBook[ item ][ i ][ 0 ], name = self.blissBook[item][i][2] )
                                b.Bind( wx.EVT_LEFT_DOWN, self.onPress )
                                b.SetBackgroundColour( self.backgroundColour )
                                self.subSizers[item].Add( b, 0, wx.EXPAND | wx.ALIGN_CENTER )
                                i += 1
                                j += 1

                            else:
                                b = bt.GenButton( self, -1, name = 'puste' )
                                b.Bind( wx.EVT_LEFT_DOWN, self.onPress )
                                b.SetBackgroundColour( self.backgroundColour )
                                self.subSizers[item].Add( b, 0, wx.EXPAND | wx.ALIGN_CENTER )
                                j += 1

                        except IndexError:
                            print 'IndexError'
                            print i, j
                        
                    self.Layout( )

                    self.mainSizer.Add( self.subSizers[ item ], proportion = 0, flag=wx.EXPAND | wx.LEFT, border = 3 )
                    
                    if item != 0:
                        self.mainSizer.Show( item = self.subSizers[ item ], show = False, recursive = True )
                    
                self.SetSizer( self.mainSizer )
                
	#-------------------------------------------------------------------------
	def initializeTimer(self):
		self.stoper = wx.Timer( self )
		self.Bind( wx.EVT_TIMER , self.timerUpdate , self.stoper )
		self.stoper.Start( self.timeGap )
	
	#-------------------------------------------------------------------------
	def createBindings(self):
		self.Bind( wx.EVT_CLOSE , self.OnCloseWindow )

	#-------------------------------------------------------------------------
	def OnCloseWindow(self, event):

		self.mousePosition = self.winWidth/1.85, (self.winHeight+20)/1.85 #+20 becouse of self.winHeight -= 20 in inicializator	
		self.mouseCursor.move( *self.mousePosition )	

		dial = wx.MessageDialog(None, 'Czy napewno chcesz wyjść z programu?', 'Wyjście',
					wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION | wx.STAY_ON_TOP)
            
		ret = dial.ShowModal()
		
		if ret == wx.ID_YES:
			if __name__ == '__main__':
				self.Destroy()
			else:
				self.parent.Destroy( )
				self.Destroy( )
		else:
			event.Veto()
			self.mousePosition = self.winWidth - 8, self.winHeight + 20 - 8 #+20 becouse of self.winHeight -= 20 in inicializator
			self.mouseCursor.move( *self.mousePosition )	

	#-------------------------------------------------------------------------
	def onExit(self):

		if __name__ == '__main__':
			self.stoper.Stop( )
			self.Destroy( )
		else:
			self.stoper.Stop( )
			self.MakeModal( False )
			self.parent.Show( True )
			self.parent.stoper.Start( self.parent.timeGap )
			self.Destroy( )
	
	#-------------------------------------------------------------------------
        def onPress(self, event):

                if self.pressSound.lower( ) != 'off':
                        self.pressingSound.play( )
            
                if self.numberOfPresses == 0:
 
			if self.flag == 'panel':
                            items = self.subSizers[ self.panelIteration ].GetChildren( )			

                            for item in items:
                                b = item.GetWindow( )
                                b.SetBackgroundColour( self.scanningColour )
                                b.SetFocus( )                            
                            if self.blissBook[ self.panelIteration ][ 0 ][ 2 ] == 'EXIT' and self.panelIteration == len( self.subSizers ) - 1:
                                if self.pressSound.lower( ) == "voice":
                                    self.stoper.Stop( )
                                    time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                    self.powrotSound.play()
                                    time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                    self.stoper.Start( self.timeGap )
                                self.onExit( )

                            else:

                                self.flag = 'row'
                                self.rowIteration = 0
			
			elif self.flag == 'row':

                                self.rowIteration -= 1

                                if self.pressSound == "voice":
                                    if (self.rowIteration == 0):
                                        self.oneSound.play()
                                    if (self.rowIteration == 1):
                                        self.twoSound.play()

                                buttonsToHighlight = range( ( self.rowIteration ) * self.numberOfColumns[ self.panelIteration ], ( self.rowIteration ) * self.numberOfColumns[ self.panelIteration ] + self.numberOfColumns[ self.panelIteration ] )
			
				for button in buttonsToHighlight:
					item = self.subSizers[ self.panelIteration ].GetItem( button )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.selectionColour )
					b.SetFocus( )

                                self.flag = 'columns'
                                self.columnIteration = 0                                
				
			elif self.flag == 'columns':
                            
                                self.columnIteration -= 1

                                item = self.subSizers[ self.panelIteration ].GetItem( ( self.rowIteration ) * self.numberOfColumns[ self.panelIteration ] + self.columnIteration )
				selectedButton = item.GetWindow( )
                                
                                self.Update( )

                                if self.pressSound == 'voice':
                                    if selectedButton.GetName() == 'puste':
                                        selectedButton.SetBackgroundColour( "red" )
                                        selectedButton.SetFocus( )
                                        self.Update( )
                                        self.pusteSound.play()
                                    else:
                                        selectedButton.SetBackgroundColour( self.selectionColour )
                                        selectedButton.SetFocus( )
                                        cmd = "milena_say %s" % selectedButton.GetName()
                                        subprocess.Popen(cmd , shell=True, stdin=subprocess.PIPE)
                                
                                        for item in self.blissBook[ self.panelIteration ]:
                                    
                                            if item[ 1 ] == self.rowIteration * self.numberOfColumns[ self.panelIteration ] + self.columnIteration + 1:

                                                self.bitmapSize = item[ 0 ].GetSize( )

                                                if self.bitmapSize[ 1 ] > 0.7 * self.panelSize[ 1 ]:
                                                    image = wx.ImageFromBitmap( item[ 0 ] )
                                                    rescaleImage = image.Rescale( ( 0.7 * self.panelSize[ 1 ] / self.bitmapSize[ 1 ] ) * self.bitmapSize[ 0 ], 0.7 * self.panelSize[ 1 ], wx.IMAGE_QUALITY_HIGH )
                                                    rescaleItem = wx.BitmapFromImage( image )

                                                    b = GenSymbolTextButton( self , -1 , bitmap = rescaleItem, label = item[ 2 ] )

                                                else:
                                                    b = GenSymbolTextButton( self , -1 , bitmap = item[ 0 ], label = item[ 2 ] )

                                                b.SetFont( wx.Font( 21, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False ) )
                                                b.SetBackgroundColour( self.backgroundColour )
                                                
                                                self.displaySizer.Add( b, 0, flag = wx.EXPAND | wx.BOTTOM | wx.TOP | wx.ALIGN_LEFT, border = 2 )
                                                self.displaySizer.Layout( )

                                                unicodeLabel = item[ 2 ].encode('utf-8')
                                                self.lastTextLenght = len( unicodeLabel ) + 1
                                                os.system('minitube "%s" &' %unicodeLabel)

                                                time.sleep( 0.5 )
                                                
                                                self.numberOfSymbol += 1
                                                os.system("sleep 1")
                                                
                                                self.stoper.Stop()
                                                self.Hide()
                                                self.menu = minitubePilot.pilot( self, id =1 )
                                                
                                                self.menu.Show()
                                                
                                                selectedButton.SetBackgroundColour( self.backgroundColour )
                                                # selectedButton.SetFocus( )
                                                # self.Update( )
                                                # selectedButto.nSetBackgroundColour( self.backgroundColour )

                                self.flag = 'panel'
                                self.panelIteration = 0
                                self.rowIteration = 0
                                self.columnIteration = 0
                                self.count = 0
                                self.countRows = 0
                        
                        self.numberOfPresses += 1

	#-------------------------------------------------------------------------
	def timerUpdate(self , event):

		self.mouseCursor.move( *self.mousePosition )	
                        
                self.numberOfPresses = 0

		if self.flag == 'panel': ## flag == panel ie. switching between panels
                        self.panelIteration += 1
                        
                        if self.panelIteration == len( self.blissBook ):
                            self.panelIteration = 0

                        if self.switchSound == "voice":
                            if self.panelIteration == len( self.blissBook ) - 1:
                                self.powrotSound.play( )

                            elif self.panelIteration == len( self.blissBook ) - 2:
                                self.lastPageFlipSound.play( )

                            else:
                                self.pageFlipSounds[ self.panelIteration % len( self.pageFlipSounds ) ].play( )

                        for item in range( len( self.blissBook ) ):
                            if item != self.panelIteration:
                                self.mainSizer.Show( item = self.subSizers[ item ], show = False, recursive = True )
                                
                        self.mainSizer.Show( item = self.subSizers[ self.panelIteration ], show = True, recursive = True )
                        
                        self.SetSizer( self.mainSizer )
                       
                        self.Layout( )

		if self.flag == 'row': #flag == row ie. switching between rows

			if self.countRows == self.countMaxRows:
				self.flag = 'panel'
				self.countRows = 0
                                
                                items = self.subSizers[ self.panelIteration ].GetChildren( )
				for item in items:
					b = item.GetWindow( )
					b.SetBackgroundColour( self.backgroundColour )
					b.SetFocus( )

			else:
				if self.rowIteration == self.numberOfRows[ self.panelIteration ]:
					self.rowIteration = 0
                                
                                if self.rowIteration == self.numberOfRows[ self.panelIteration ] - 1:
					self.countRows += 1

				items = self.subSizers[ self.panelIteration ].GetChildren( )
				for item in items:
					b = item.GetWindow( )
					b.SetBackgroundColour( self.backgroundColour )
					b.SetFocus( )

				zakres = range( self.rowIteration * self.numberOfColumns[ self.panelIteration ], self.rowIteration * self.numberOfColumns[ self.panelIteration ] + self.numberOfColumns[ self.panelIteration ] )

				for i in zakres:
					item = self.subSizers[ self.panelIteration ].GetItem( i )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.scanningColour )
					b.SetFocus( )
				self.rowIteration += 1

                                if self.switchSound == "voice":
                                    if (self.rowIteration == 1):
                                        self.oneSound.play()
                                    if (self.rowIteration == 2):
                                        self.twoSound.play()
                                    # if (self.rowIteration == 2):
                                    #     self.threeSound.play()
                                # os.system( 'milena_say %i' % ( self.rowIteration ) )
			
		elif self.flag == 'columns': #flag = columns ie. switching between cells in the particular row

			if self.countColumns == self.countMaxColumns:
				self.flag = 'row'
				self.rowIteration = 0
				self.columnIteration = 0
				self.countColumns = 0
                                self.countRows = 0
                                
                                items = self.subSizers[ self.panelIteration ].GetChildren( )
				for item in items:
					b = item.GetWindow( )
					b.SetBackgroundColour( self.backgroundColour )
                                        b.SetFocus( )

			else:
				if self.columnIteration == self.numberOfColumns[ self.panelIteration ]:
					self.columnIteration = 0
                                
                                if self.columnIteration == self.numberOfColumns[ self.panelIteration ] - 1:
					self.countColumns += 1

				items = self.subSizers[ self.panelIteration ].GetChildren( )
				for item in items:
					b = item.GetWindow( )
					b.SetBackgroundColour( self.backgroundColour )
                                        b.SetFocus( )

				item = self.subSizers[ self.panelIteration ].GetItem( self.rowIteration * self.numberOfColumns[ self.panelIteration ] + self.columnIteration )
				b = item.GetWindow( )
				b.SetBackgroundColour( self.scanningColour )
				b.SetFocus( )

				self.columnIteration += 1
                                
                                
                                if self.switchSound.lower() == 'voice':
                                    if b.Name == 'puste':
                                        self.pusteSound.play()
                                    else:
                                        cmd = "milena_say %s" % b.Name
                                        subprocess.Popen(cmd , shell=True, stdin=subprocess.PIPE)

                                elif self.switchSound.lower() != 'off':
                                    self.switchingSound.play()

#=============================================================================
if __name__ == '__main__':

	app = wx.App(False)
	frame = youtube1( parent = None, id = -1 )
        frame.Show( True )
	app.MainLoop( )
