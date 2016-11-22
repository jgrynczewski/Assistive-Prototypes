#!/bin/env python2.7
# -*- coding: utf-8 -*-

# This file is part of AP - Assistive Prototypes - Assistive Prototypes.
#
# Assistive Prototypes is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Assistive Prototypes is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Assistive Prototypes. If not, see <http://www.gnu.org/licenses/>.


import wxversion
# wxversion.select('2.8')

import os, sys

import wx
import wx.lib.buttons as bt

from pymouse import PyMouse
from pygame import mixer
import numpy as np

#=============================================================================
class check(wx.Frame):

	def __init__(self, parent):

		self.winWidth, self.winHeight = wx.DisplaySize( )
                
		self.parent = parent
		self.initializeParameters( )
		self.createGui( )
		self.parent.stoper.Start( self.timeGap )

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

		self.mouseCursor = PyMouse( )
		if self.control != 'tracker':
			self.mousePosition = self.winWidth - 8 - self.xBorder, self.winHeight - 48 - self.yBorder
			self.mouseCursor.move( *self.mousePosition )

		mixer.init( )
		if self.pressSound.lower( ) != 'off':
			self.pressingSound = mixer.Sound( self.pathToAP + '/sounds/pressSound.ogg' )

	#-------------------------------------------------------------------------
	def createGui(self):
	
                self.subSizer = wx.GridSizer( 1, 1, self.xBorder, self.yBorder )
                self.subSizer2 = wx.GridSizer( 1, 1, self.xBorder, self.yBorder )

		if self.control != 'tracker':
			self.event = eval('wx.EVT_LEFT_DOWN')
		else:
			self.event = eval('wx.EVT_BUTTON')

                if self.parent.ownWord == self.parent.WORD:
                        self.parent.result += 1

                        if self.parent.result == self.parent.maxPoints:

                                if self.sex == 'M':
                                        text = u'BRAWO! \n \nZDOBYŁEŚ WSZYSTKIE PUNKTY. \n \nPRZYCIŚNIJ ŻEBY ODEBRAĆ NAGRODĘ.'
                                else:
                                        text = u'BRAWO! \n \nZDOBYŁAŚ WSZYSTKIE PUNKTY. \n \nPRZYCIŚNIJ ŻEBY ODEBRAĆ NAGRODĘ.'

                                kolor = 'dark slate blue'
                                self.app = False
                                self.oklaski = True
                                i = wx.BitmapFromImage( wx.ImageFromStream( open( self.pathToAP+'/icons/ewriting/thumbup.png', "rb" ) ) )
                                be = bt.GenBitmapButton( self.parent, -1, bitmap = i )
                                be.SetBackgroundColour( 'white' )
                                be.Bind( self.event, self.reward )

                        else:
                                if self.sex =='M':
                                        text = u'GRATULACJE! \n \nWPISAŁEŚ POPRAWNE SŁOWO!'
                                else:
                                        text = u'GRATULACJE! \n \nWPISAŁAŚ POPRAWNE SŁOWO!'

                                kolor = self.colorGrat
                                self.app = True
                                self.oklaski = True
                                i=wx.BitmapFromImage( wx.ImageFromStream( open( self.pathToAP + '/icons/ewriting/thumbup.png', "rb" ) ) )
                                be = bt.GenBitmapButton( self.parent, -1, bitmap = i )
                                be.SetBackgroundColour( 'white' )
				be.Bind( self.event, self.zamknij )

                else:
                        text = u'NIESTETY. \n \nSPRÓBUJ JESZCZE RAZ!'
                        kolor = self.colorNiest
			self.parent.PicNr -= 1
			self.app = True
			self.oklaski = False

			i = wx.BitmapFromImage( wx.ImageFromStream( open( self.pathToAP + '/icons/ewriting/sad.png', "rb" ) ) )
                        be = bt.GenBitmapButton( self.parent, -1, bitmap = i )
                        be.SetBackgroundColour( 'white' )
			be.Bind( self.event, self.zamknij )
			
		b = bt.GenButton( self.parent, -1, text )
		b.SetFont( wx.Font(50, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False) )
		b.SetBezelWidth( 3 )
		
		if self.parent.result == self.parent.maxPoints:
			self.parent.result = 0
			b.Bind( self.event, self.reward )
		else:
			b.Bind( self.event, self.zamknij )

		b.SetBackgroundColour( 'white' )
		b.SetForegroundColour( kolor)
		b.SetFocus( )
		
		self.subSizer.Add( b, 0, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP | wx.BOTTOM, border = self.xBorder)
		self.subSizer2.Add( be, 0, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.BOTTOM, border = self.xBorder )
		self.parent.mainSizer.Add( self.subSizer, proportion = 7, flag = wx.EXPAND )
		self.parent.mainSizer.Add(self.subSizer2, proportion = 3, flag = wx.EXPAND )
		self.parent.SetSizer( self.parent.mainSizer )
		self.parent.Layout( )

		if self.oklaski:
			voice = open(self.pathToAP + 'multimedia/ewriting/oklaski.ogg', 'rb')
                        mixer.music.load( voice )
                        mixer.music.play( )

                self.ileklik = 0

	#------------------------------------------------------------------------
	def reward(self, event):

                self.parent.mainSizer.Clear( deleteWindows = True )
                self.subSizer = wx.GridSizer( 1, 1, self.xBorder, self.yBorder)

                b = bt.GenButton( self.parent, -1, u'CHCESZ WYŁĄCZYĆ?\n \nPRZYCIŚNIJ.' )
		b.SetFont( wx.Font(25, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False) )
		b.SetBezelWidth( 3 )
		b.SetBackgroundColour( 'white' )
		b.Bind( self.event, self.OnExit)

		self.subSizer.Add( b, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, border = self.xBorder)
                self.parent.mainSizer.Add( self.subSizer, proportion = 1, flag = wx.EXPAND )
                self.parent.SetSizer( self.parent.mainSizer )
                self.parent.Layout( )

                path = self.pathToAP+'multimedia/ewriting/rewards/'
                song = os.listdir( path )[ np.random.randint( 0, len( os.listdir( path ) ), 1 ) ]
                mixer.music.stop( )
                mixer.music.load( path + song )
                mixer.music.play( )
                
	#-------------------------------------------------------------------------
        def OnExit(self, event):

                self.ileklik += 1

                if self.ileklik == 1:
			self.parent.checkFlag = False
                        mixer.music.stop( )
                        self.parent.back( )
		else:
                        event.Skip( )

	#-------------------------------------------------------------------------
	def zamknij(self, event):

		if self.pressSound.lower( ) != 'off':
			self.pressingSound.play( )

		self.parent.checkFlag = False
		self.parent.back( )

                if self.oklaski:
                        mixer.music.stop( )
