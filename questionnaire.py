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
		self.questions.setColumnStretch( 1, 1 )
		self.questions.setHorizontalSpacing(15)

		self.description = None
		self.title = None

		self.buttonGroups = []

		cols = 2
		for v in self.data:
			if len(v) > cols:
				cols = len(v)

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
			elif v[0] == 'G':
				l = QLabel( v[1] )
				l.setFrameStyle( QFrame.Panel | QFrame.HLine )
				l.setStyleSheet( "font-weight: bold;" )
				self.questions.addWidget( l, row, 0, 1, cols+1 )
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
				question.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Preferred )
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

		self.setWindowTitle( self.title )

		self.showFullScreen()
		self.activateWindow()
		self.raise_()

		self.questionsW.setMinimumWidth( self.scrollArea.geometry().width() - self.scrollArea.geometry().x() )
		self.questionsW.updateGeometry()

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
	parser.add_argument( '-s', '--subdir', action = "store_true", dest = "subdir", help = 'Place each subjects data in their own sub-directory.' )

	group = parser.add_mutually_exclusive_group( required = True )
	group.add_argument( '--cfq', action = "store_true", dest = "cfq", help = 'Cognitive Failures' )
	group.add_argument( '--vg', action = "store_true", dest = "vg", help = 'Video Games' )

	args = parser.parse_args()

	d = datetime.datetime.now().timetuple()
	subjectInfo = getSubjectInfo( minimal = True )

	if not subjectInfo:
		sys.exit( 1 )

	results = None
	title = None

	if args.cfq:
		file = "files/cognitive_failures.txt"
	if args.vg:
		file = "files/video_games.txt"

	results, title = doQuestionnaire( file )

	if title and results:
		eid = rin2id( subjectInfo['rin'] )
		logdir = args.logdir
		if args.subdir:
			logdir = os.path.join( args.logdir, eid[:8] )
		if not os.path.exists( logdir ):
			os.makedirs(logdir)
		log_basename = os.path.join( logdir, "%s_%s_%d-%d-%d_%d-%d-%d" % ( "_".join( title.split() ), eid[:8], d[0], d[1], d[2], d[3], d[4], d[5] ) )
		subjectInfo['encrypted_rin'] = eid
		subjectInfo['cipher'] = 'AES/CBC (RIJNDAEL) - 16Byte Key'
		writeHistoryFile( log_basename, subjectInfo )
		log = open( log_basename + ".txt", "w" )
		log.write( "\t".join( map( str, results ) ) + "\n" )
		log.close()
		sys.exit( 0 )

	sys.exit( 1 )
