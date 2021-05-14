import dataset as ds
import math
import trueskill as ts
from icecream import ic
import pickle

# trying to refactor this nonsense so I can actually grasp what I'm doing.

def logger(msg, data):
	logfile = 'tslog.txt'
	with open(logfile,'a') as f:
		f.write(msg+' '+str(data)+'\n')

class Player:

	def ts(self): # TrueSkill
		return ts.Rating(mu=self.mu,sigma=self.sigma) 
		
	def db(self):
		temp = dict({'acbl':self.acbl,'name':self.name,
		'mu':self.mu,'sigma':self.sigma, 'initmu':self.initmu})
		return temp
		
	def __init__(self, acbl=0, name='', mu=0, sigma=0):
		self.acbl = acbl
		self.name = name
		self.mu = mu
		self.sigma = sigma
		self.initmu = mu
		
	def addDict(self, dictionary={}):
		if dictionary:			
			self.acbl = dictionary['acbl']
			self.name = dictionary['name']
			self.mu = dictionary['mu']
			self.sigma = dictionary['sigma']
			self.initmu = dictionary['mu']
		else:
			print(dictionary, 'error')
		return self

# initial setup

db = ds.connect('sqlite:///NABCseed.db') # actual DB
#db = ds.connect('sqlite:///:memory:') # memory temporary
table = db.create_table('players', primary_id='acbl')
eventCodes = [
	  ('IMPS','MIXD','NAPA','PLAT','SILODOR','SLVR','SMITH','FAST'),
      ('LM','WERNHER','WAGR'),
	  ('BLUE','NAIL','SMIX','SS','WHITEHEAD')
    ]

# inital session to scan

mp = {}

ts.setup(tau=.1, beta=15, draw_probability=.5,backend='scipy') 

def getMPs():
	with open('D00MP') as f:
		for line in f:
			line = line.translate(str.maketrans('JKLMNOPQR','123456789'))
			if line[-2] not in '0123456789': line = line[:-2]+'\n' # wtf acbl?
			mp[str(line[:7])] = float(line[-9:]) # extra character in string?
	
def verify(acbl):
	if len(acbl)!=7: return False
	try:
		i = int(acbl)
		return True
	except:
		return False
	return True

def MPtoTS(acbl):
	
		a = str(acbl)
		
		if (mp[a]<=0):
			mp[a]=0.01 # no log errors
		# Working on pre-populating seeding based on masterpoints
		# More MP = higher mu, lower sigma
		# Higher mu = higher minimum for rating
		# Lower sigma = more confidence in mu
		# Formulae derived from Wolfram Alpha curve fitting, log or linear		
		#m = max(25,10.8574*math.log(.001*mp[a])) # reducing max for test 
		m = max(25,8.88601*math.log(.00277778*mp[a])) # 6k=25,100k=50

		#s = min(10,95/9.0 - (mp[a] / 18000.0))
		#s = min(6,2+(mp[a]-100000)**2/2025000000.0)
		s = min(6,2+(mp[a]-100000)**2/2209000000.0)
		#s = 10 # Keeping all the initial sigmas the same
		return ts.Rating(mu=m,sigma=s)
    


def newPlayer(acbl, name):
	
	try:
		r = MPtoTS(acbl)
	except:
		r = ts.Rating(sigma=10) 
		
	temp = Player(acbl, name, r.mu, r.sigma)
	if not temp.initmu:
		print('why?')
	if verify(acbl): 
		myhash = temp.db()
		table.insert(myhash)
		logger('create','%s %s %s %s %s' % (temp.name, temp.acbl, temp.mu, temp.sigma, temp.initmu))
		return temp
	else:
		print("ACBL Fail", acbl, name, len(acbl))
	
	return temp
	
def addToDB(allrows):
	players = []
	scores = []
	
	for row in allrows:
		p1 = table.find_one(acbl=row[0])
		p2 = table.find_one(acbl=row[2])
		
		if not p1:
			p1 = newPlayer(row[0],row[1])
		else:
			temp = Player()
			p1 = temp.addDict(dictionary=p1)
		if not p2:
			p2 = newPlayer(row[2],row[3])
		else:
			temp = Player()
			p2 = temp.addDict(dictionary=p2)
		
		players.append( (p1.ts(), p2.ts()))
		scores.append(-1*row[4])
		
	if len(players):
		newRanks = ts.rate(players, ranks=scores)
			
	# zip allows us to traverse both lists in sync
	detectlist = ['6520898','4580699','8469873','7749511','8003602','2879131']
	for (i,j) in zip(allrows, newRanks):
		x = table.find_one(acbl=str(i[0]))
		y = table.find_one(acbl=str(i[2]))
		if i[0] in detectlist:  # Meck = 4580699
			print('%s: %s/%s --> %s/%s' % (i[0],x['mu'],x['sigma'],j[0].mu,j[0].sigma))
		if i[2] in detectlist:
			print('%s: %s/%s --> %s/%s' % (i[2],y['mu'],y['sigma'],j[1].mu,j[1].sigma))

		try:
			temp1 = j[0].mu
			logger('update','%s: %s/%s --> %s/%s' % (i[0],x['mu'],x['sigma'],temp1,j[0].sigma))
			
			temp2 = j[1].mu
			logger('update','%s: %s/%s --> %s/%s' % (i[2],y['mu'],y['sigma'],temp2,j[1].sigma))
			table.update(dict(acbl=i[0], mu=temp1, sigma=j[0].sigma),['acbl'])
			table.update(dict(acbl=i[2], mu=temp2, sigma=j[1].sigma),['acbl'])

		except:
			print('No ACBL?',i[0],i[1],i[2],i[3])
			logger('No ACBL?',' '.join(i[0:4]))
			pass
		
		table.update(dict(acbl=i[0], mu=j[0].mu, sigma=j[0].sigma),['acbl'])
		table.update(dict(acbl=i[2], mu=j[1].mu, sigma=j[1].sigma),['acbl'])

def main():
	for year in range(14,20):
		ic(year)
		for season in range(3):
			for event in eventCodes[season]:
				for i in range(6):
					testurl = event+str(year)+str(season)+'-'+str(i)+'.pkl'
					
					
					logger('Event',testurl)
					
					try:
						rows = pickle.load(open('pkls/'+testurl,'rb'))
					except FileNotFoundError:
						ic('no file',testurl)
						rows = []
					

					if rows: addToDB(rows)
		ic(len(db['players']))
			
getMPs()
main()
	
results = table.find()
test = []
for i in results:
	test.append((i['acbl'], i['name'], i['mu'], i['sigma'], (2*i['mu']-6*i['sigma'])))
		
with open('output.txt','w') as f:
	for i in (sorted(test, key = lambda rank: rank[-1],reverse=True)):
		f.write(str(i)+'\n')
		#if (i[-1]<0): print(str(i)+'\n')

print(len(db['players']))

		
