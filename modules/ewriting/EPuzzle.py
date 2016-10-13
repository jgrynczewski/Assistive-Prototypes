#!/bin/env python2.7
# -*- coding: utf-8 -*-

# This file is part of EPlatform.
#
# EPlatform is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EPlatform is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EPlatform. If not, see <http://www.gnu.org/licenses/>.

import wxversion
wxversion.select('2.8')

import glob, os, time, sys
import time
from random import shuffle

import wx
import wx.lib.buttons as bt
from pymouse import PyMouse
import Tkinter
import numpy as np

import subprocess as sp
import shlex
import pygame
from pygame import mixer

import check, spellerPuzzle

#=============================================================================
class cwiczenia(wx.Frame):
	def __init__(self, parent, id):

		self.winWidth, self.winHeight = wx.DisplaySize( )
		
		wx.Frame.__init__( self , parent , id , 'EGaps' )
                style = self.GetWindowStyle( )
		self.SetWindowStyle( style | wx.STAY_ON_TOP ) 
		self.parent = parent

		self.Maximize( True )
		self.Centre( True )
		self.MakeModal( True )

		self.initializeParameters( )
		self.createGui( )
		self.createBindings( )
		self.initializeTimer( )

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

                # with open( self.pathToAP + 'ewritingParameters', 'r' ) as parametersFile:
		# 	for line in parametersFile:                                                                

                #                 if line[ :line.find('=')-1 ] == 'textSize':
		# 			self.textSize = int( line[ line.rfind('=')+2:-1 ])
		# 		elif line[ :line.find('=')-1 ] == 'maxPoints':
		# 			self.maxPoints = int(line[ line.rfind('=')+2:-1 ])
		# 		elif line[ :line.find('=')-1 ] == 'checkTime':
                #                         self.checkTime = int(line[ line.rfind('=')+2:-1 ])
		# 		elif line[ :line.find('=')-1 ] == 'colorGrat':
		# 			self.colorGrat = line[ line.rfind('=')+2:-1 ]
		# 		elif line[ :line.find('=')-1 ] == 'colorNiest':
                #                         self.colorNiest = line[ line.rfind('=')+2:-1 ]
		# 		elif line[ :line.find('=')-1 ] == 'ileLuk':
                #                         self.ileLuk = int(line[ line.rfind('=')+2:-1 ])
		# 		elif line[ :line.find('=')-1 ] == 'sex':
                #                         self.sex = line[ line.rfind('=')+2:-1 ]
		
		# 		elif not line.isspace( ):
		# 			print 'Niewłaściwie opisane parametry'
		# 			print 'Błąd w linii', line
		# 			print 'Wczytano parametry domyślne'
					
                self.textSize = 80
                self.checkTime = 8000
                self.colorGrat = 'lime green'
                self.colorNiest = 'indian red'
                self.ileLuk = 1
                self.maxPoints = 2
                self.sex = 'D'
		
		self.ownWord = ''
		self.flaga = 0
		self.PicNr = 0
		self.result = 0

		self.WordsList = os.listdir( self.pathToAP + 'multimedia/ewriting/pictures' )
		shuffle( self.WordsList )

                self.poczatek = True
		self.czyBack = False

		self.numberOfPresses = 1

		self.mouseCursor = PyMouse( )
		self.mousePosition = self.winWidth - 8, self.winHeight - 8
               	self.mouseCursor.move( *self.mousePosition )			

		mixer.init( )

	#-------------------------------------------------------------------------	
	def initializeTimer(self):

                id1 = wx.NewId( )
                wx.RegisterId( id1 )
		self.stoper = wx.Timer( self, id1 )
		self.Bind( wx.EVT_TIMER, self.timerUpdate, self.stoper, id1 )
		
		self.id2 = wx.NewId( )
                wx.RegisterId( self.id2 )
                self.stoper2 = wx.Timer( self, self.id2 )

                self.id3 = wx.NewId( )
                wx.RegisterId( self.id3 )
                self.stoper3 = wx.Timer( self, self.id3 )

                self.id4 = wx.NewId( )
                wx.RegisterId( self.id4 )
                self.stoper4 = wx.Timer( self, self.id4 )
                self.Bind( wx.EVT_TIMER, self.pomocniczyStoper, self.stoper4, self.id4 )
                
		self.stoper.Start( self.timeGap )

	#-------------------------------------------------------------------------	
	def createGui(self):

                if self.PicNr == len( self.WordsList ):
                        self.PicNr = 0

		self.picture = self.WordsList[ self.PicNr ]
                self.PicNr += 1
		self.path = self.pathToAP + 'multimedia/ewriting/pictures/'

                im = wx.ImageFromStream( open( self.path + self.picture, "rb" ) )
		x=im.GetWidth( )
		y=im.GetHeight( )

		if x > y:
			im = im.Scale( 500, 400 )
                elif x == y:
                        im = im.Scale( 500, 500 )
                else:
                        im = im.Scale( 400, 500 )

		picture = wx.BitmapFromImage( im )
		self.word = self.picture[ :self.picture.index( '.' ) ]
		self.WORD = self.word.upper( )

		b = bt.GenBitmapButton( self, -1, bitmap = picture, name = 'picture' )
		# b.SetBackgroundColour( self.backgroundColour )
		b.Bind( wx.EVT_LEFT_DOWN, self.onPress )

                be = bt.GenButton( self, -1, self.WORD )
		be.SetFont( wx.Font( self.textSize, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False ) )
		# be.SetBackgroundColour( self.backgroundColour )
		be.Bind( wx.EVT_LEFT_DOWN, self.onPress )

                res = bt.GenButton( self, -1, u'TWÓJ WYNIK:   ' + str(self.result) + ' / ' + str( self.maxPoints ) )
		res.SetFont( wx.Font( 27, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False ) )
		# res.SetBackgroundColour( self.backgroundColour )
		res.Bind( wx.EVT_LEFT_DOWN, self.onPress )
		
		try:
                        self.subSizerP.Hide( 0 )
                        self.subSizerP.Remove( 0 )
                        self.subSizerP.Add( res, 0, wx.EXPAND )
                        self.subSizer0.Hide( 0 )
                        self.subSizer0.Remove( 0 )
                        self.subSizer0.Hide( 0 )
                        self.subSizer0.Remove( 0 )
                        self.subSizer0.Add( b, 0, wx.EXPAND )
		        self.subSizer0.Add( be, 0, wx.EXPAND )

		        items = self.subSizer.GetChildren( )

                        for i in items:
                                b=i.GetWindow( )
                                b.SetBackgroundColour( self.backgroundColour )
                                b.Update
                                
                except AttributeError:

                        if self.czyBack:
                                self.czyBack = False

                        else:
                                self. mainSizer = wx.BoxSizer( wx.VERTICAL )

                        self.subSizerP = wx.GridSizer( 1, 1, 3, 3 )
                        self.subSizer0 = wx.GridSizer( 1, 2, 3, 3 )
                        self.subSizer = wx.GridSizer( 1, 5, 3, 3 )
                        self.subSizerP.Add( res, 0, wx.EXPAND )
                        self.subSizer0.Add( b, 0, wx.EXPAND )
		        self.subSizer0.Add( be, 0, wx.EXPAND )

                        self.icons = sorted( os.listdir( self.pathToAP + 'icons/ewriting' ) )
                        self.path = self.pathToAP + 'icons/ewriting/'

                        for idx, icon in enumerate( self.icons ):

                                if icon[ 0 ].isdigit( ):
                                        i = wx.BitmapFromImage( wx.ImageFromStream( open( self.path + icon, "rb" ) ) )
                                        b = bt.GenBitmapButton( self, -1, bitmap = i )
                                        b.SetBackgroundColour( self.backgroundColour )
                                        b.Bind( wx.EVT_LEFT_DOWN, self.onPress )
                                        self.subSizer.Add( b, 0, wx.EXPAND )

                        self. mainSizer.Add( self.subSizerP, proportion = 1, flag = wx.EXPAND | wx.BOTTOM, border = 2 )
                        self. mainSizer.Add( self.subSizer0, proportion = 7, flag = wx.EXPAND )
                        self. mainSizer.Add( self.subSizer, proportion = 2, flag = wx.EXPAND | wx.TOP, border = 2 )
                        self.SetSizer( self. mainSizer,deleteOld = True )

                self.SetBackgroundColour( 'black' )
		self.Layout( )
		self.Refresh( )
		self.Center( )
		self.MakeModal( True )
		self.flaga = 0
		self.poczatek = True

	#-------------------------------------------------------------------------
	def createBindings(self):
		self.Bind( wx.EVT_CLOSE , self.OnCloseWindow )

	#-------------------------------------------------------------------------	
	def OnCloseWindow(self, event):

		self.mousePosition = self.winWidth/1.85, self.winHeight/1.85	
		self.mouseCursor.move( *self.mousePosition )	

		dial = wx.MessageDialog(None, 'Czy napewno chcesz wyjść z programu?', 'Wyjście',
					wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION | wx.STAY_ON_TOP)
            
		ret = dial.ShowModal( )
		
		if ret == wx.ID_YES:
			try:
				self.parent.parent.parent.parent.Destroy()
				self.parent.parent.parent.Destroy()
				self.parent.parent.Destroy()
				self.parent.Destroy()
				self.Destroy()
				
			except AttributeError:
				try:
					self.parent.parent.parent.Destroy()
					self.parent.parent.Destroy()
					self.parent.Destroy()
					self.Destroy()

				except AttributeError:
					try:
						self.parent.parent.Destroy()
						self.parent.Destroy()
						self.Destroy()

					except AttributeError:
						try:		
							self.parent.Destroy()
							self.Destroy()

						except AttributeError:
							self.Destroy()

		else:
			event.Veto( )
			self.mousePosition = self.winWidth - 8, self.winHeight - 8
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

                self.numberOfPresses += 1
		
		if self.numberOfPresses == 1:
                
                        item = self.subSizer.GetItem( self.flaga - 1 )
                        b = item.GetWindow( )
                        b.SetBackgroundColour( self.selectionColour )
                        b.SetFocus( )
                        b.Update( )
                
                	if 'speller' in self.icons[ self.flaga - 1 ]:
                		self.stoper.Stop( )
                		self.mainSizer.Clear( deleteWindows = True )
                		self.spellerW = spellerPuzzle.speller( self )
                		self.Bind( wx.EVT_TIMER, self.spellerW.timerUpdate, self.stoper2, self.id2 )
                                self.stoper2.Start( self.spellerW.timeGap )
                                
                	if 'cancel' in self.icons[ self.flaga-1 ] or self.flaga == 0:
                		if __name__ == '__main__':
                                        self.stoper.Stop( )
                                        self.Destroy( )
                                else:
                                        self.stoper.Stop( )
                                        self.MakeModal( False )
                                        self.parent.Show( True )
                                        self.parent.stoper.Start( self.parent.timeGap )
                                        self.Destroy( )

                        if 'speak' in self.icons[ self.flaga - 1 ]:
                        	time.sleep( 1 )
                        	self.stoper.Stop( )
                        	mixer.music.load( self.pathToAP + 'multimedia/ewriting/voices/' + str(self.word) + '.ogg' )
                                mixer.music.play()
                                self.stoper4.Start(2000)

                        if 'literuj' in  self.icons[ self.flaga - 1 ]:
                                self.stoper.Stop( )
                                if str( self.word )+'.ogg' not in os.listdir( self.pathToAP + 'multimedia/ewriting/spelling/' ):        
                                        command = 'sox -m ' + self.pathToAP + 'sounds/phone/' + list( self.word )[ 0 ].swapcase( ) + '.ogg'
                                        ile = 0
                                        for l in list( self.word )[ 1: ]:
                                                ile += 2
                                                command += ' "|sox ' + self.pathToAP + 'sounds/phone/' + l.swapcase( ) + '.ogg' + ' -p pad ' + str( ile ) + '"'
                                        command += ' ' + self.pathToAP + 'multimedia/ewriting/spelling/' + self.word + '.ogg'
                                        wykonaj = sp.Popen( shlex.split( command ) )

                                time.sleep( 1.5 )
                                do_literowania = mixer.Sound( self.pathToAP + 'multimedia/ewriting/spelling/' + self.word + '.ogg' )
                                do_literowania.play( )
                                self.stoper4.Start( ( do_literowania.get_length( ) + 0.5 ) * 1000 )
                                		
                        if 'undo' in self.icons[ self.flaga - 1 ]:
			
                        	self.stoper.Stop( )
                        	self.createGui( )			
                        	self.stoper.Start( self.timeGap )

                else:
                        event.Skip( )

	#-------------------------------------------------------------------------	
        def pomocniczyStoper(self, event):

                self.stoper4.Stop( )

                if hasattr( self, 'spellerW' ):
                        self.stoper2.Start( self.spellerW.timeGap )

                else:
                        self.stoper.Start( self.timeGap )
        
	#-------------------------------------------------------------------------	
	def check(self):

                self.mainSizer.Clear( deleteWindows = True )
		self.checkW=check.check( self )

	#-------------------------------------------------------------------------	
	def back(self):

                self.czyBack = True

                try:
                        del self.spellerW
                except NameError:
                        del self.checkW

                self.mainSizer.Clear( deleteWindows = True )
		self.createGui( )
		self.stoper.Start( self.timeGap )

	#-------------------------------------------------------------------------	
	def timerUpdate(self, event):

                self.mouseCursor.move( *self.mousePosition )

                self.numberOfPresses = 0

                if self.poczatek:
                        time.sleep( 1 )
                        self.stoper.Stop( )
                        mixer.music.load( self.pathToAP + 'multimedia/ewriting/voices/' + str( self.word ) + '.ogg' )
                        mixer.music.play( )
                        time.sleep( 2 )
                        self.stoper.Start( self.timeGap )
                        self.poczatek = False
                		
		for i in range( 5 ):
			item = self.subSizer.GetItem( i )
                        b = item.GetWindow( )
                        b.SetBackgroundColour( self.backgroundColour )
                        b.SetFocus( )

                if self.flaga == 5:
                        item = self.subSizer.GetItem( 0 )
                        b = item.GetWindow( )
                        b.SetBackgroundColour( self.scanningColour )
                        b.SetFocus( )

                        self.flaga = 1
				
                else: 
                        item = self.subSizer.GetItem( self.flaga )
                        b = item.GetWindow( )
                        b.SetBackgroundColour( self.scanningColour )
                        b.SetFocus( )

                        self.flaga += 1
		
#=============================================================================
if __name__ == '__main__':

	app = wx.App(False)
	frame = cwiczenia( parent = None, id = -1 )
	frame.Show( )
	app.MainLoop( )
