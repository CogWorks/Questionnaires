#!/usr/bin/env python

from PySide.QtCore import *
from PySide.QtGui import *

import sys, os
import argparse

from pycogworks.cwsubject import *
from pycogworks.util import rin2id

class Questionnaire( QDialog ):

	def __init__( self, app, file ):
		super( Questionnaire, self ).__init__()

		self.app = app

		self.questionsPerPage = -1

		#self.setModal( True )

		self.data = None
		self.loadFile( file )

		self.main_layout = QVBoxLayout()
		self.questions = QGridLayout()
		#self.questions.setFixedSize(800,600)
		#self.questions.setSizePolicy( QSizePolicy.Maximum, QSizePolicy.Maximum )

		self.description = None
		self.title = None

		self.buttonGroups = []

		row = 0
		q = 1
		for v in self.data:
			if v[0] == 'T':
				self.title = v[1]
			elif v[0] == '~':
				self.description = v[1]
			elif v[0] == 'H':
				col = 2
				for l in v[1:]:
					self.questions.addWidget( QLabel( l ), row, col )
					col += 1
				row += 1
			elif v[0] == '1':
				bg = QButtonGroup()
				col = 0
				num = QLabel( "%d." % ( q ) )
				num.setSizePolicy( QSizePolicy.Maximum, QSizePolicy.Maximum )
				self.questions.addWidget( num , row, col )
				col += 1
				question = QLabel( v[1] )
				question.setWordWrap( True )
				question.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Preferred )
				self.questions.addWidget( question, row, col )
				col += 1
				for l in v[2:]:
					button = QRadioButton( l )
					bg.addButton( button )
					button.setSizePolicy( QSizePolicy.Maximum, QSizePolicy.Maximum )
					self.questions.addWidget( button, row, col )
					col += 1
				QObject.connect( bg, SIGNAL( 'buttonClicked(QAbstractButton *)' ), self.questionClick )
				self.buttonGroups.append( bg )
				row += 1
				q += 1


		self.scrollArea = QScrollArea()
		self.questionsW = QWidget()

		self.questionsW.setLayout( self.questions )
		self.scrollArea.setWidget( self.questionsW )
		if self.description:
			q = QLabel( self.description )
			q.setWordWrap( True )
			self.main_layout.addWidget( q )
		self.main_layout.addWidget( self.scrollArea )
		self.doneButton = QPushButton( "Submit" )
		self.doneButton.setDisabled( True )
		QObject.connect( self.doneButton, SIGNAL( 'clicked(bool)' ), self.submit )
		self.main_layout.addWidget( self.doneButton )
		self.setLayout( self.main_layout )

		self.setWindowTitle( 'Questionnaire' )

		self.show()
		self.activateWindow()
		self.raise_()

		self.setFixedSize( 900, 700 )

		screen = QDesktopWidget().screenGeometry()
		size = self.geometry()
		self.move( ( screen.width() - size.width() ) / 2, ( screen.height() - size.height() ) / 2 )

	def questionClick( self, button ):
		for b in self.buttonGroups:
			if b.checkedId() == -1:
				self.doneButton.setDisabled( True )
				return
		self.doneButton.setDisabled( False )

	def submit( self, checked ):
		print "Done"
		self.done( 1 )

	def getResults( self ):
		if self.result():
			return ( [ b.checkedButton().text() for b in self.buttonGroups ], self.title )
		else:
			return None, None


	def loadFile( self, file ):

		f = open( file, "rb" )
		self.data = []
		for line in f.readlines():
			self.data.append( line.strip().split( '\t' ) )


def doQuestionnaire( file ):
	app = QCoreApplication.instance()
	if not app:
		app = QApplication( sys.argv )
	q = Questionnaire( app, file )
	app.exec_()
	return q.getResults()

if __name__ == "__main__":

	parser = argparse.ArgumentParser( formatter_class = argparse.ArgumentDefaultsHelpFormatter )
	parser.add_argument( '-d', '--logdir', action = "store", dest = "logdir", default = 'data', help = 'Log dir' )

	group = parser.add_mutually_exclusive_group( required = True )
	group.add_argument( '--cfq', action = "store_true", dest = "cfq", help = 'Cognitive Failures Questionnaire' )

	args = parser.parse_args()

	d = datetime.datetime.now().timetuple()
	subjectInfo = getSubjectInfo( minimal = True )

	results = None
	title = None

	if args.cfq:
		results, title = doQuestionnaire( "files/cognitive_failures.txt" )

	if title and results:
		if not os.path.exists( args.logdir ):
			os.mkdir( args.logdir )
		log_basename = os.path.join( args.logdir, "%s-%d-%d-%d_%d-%d-%d" % ( "_".join( title.split() ), d[0], d[1], d[2], d[3], d[4], d[5] ) )
		eid = rin2id( subjectInfo['rin'] )
		subjectInfo['encrypted_rin'] = eid
		subjectInfo['cipher'] = 'AES/CBC (RIJNDAEL) - 16Byte Key'
		writeHistoryFile( log_basename, subjectInfo )
		log = open( log_basename + ".txt", "w" )
		log.write( "\t".join( map( str, results ) ) + "\n" )
		log.close()
