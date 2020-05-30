from bs4 import BeautifulSoup
import requests 
import dataset as ds
import math
import trueskill as ts

# trying to refactor this nonsense so I can actually grasp what I'm doing.

def logger(msg, data):
	logfile = 'tslog.txt'
	with open(logfile,'a') as f:
		f.write(msg+' '+str(data)+'\n')

class Player:

	def ts(self): # TrueSkill
		return ts.Rating(mu=self.mu,sigma=self.sigma) 
		
	def db(self):
		return {'acbl':self.acbl,'name':self.name,
		'mu':self.mu,'sigma':self.sigma}
		
	def __init__(self, acbl=0, name='', mu=0, sigma=0):
		self.acbl = acbl
		self.name = name
		self.mu = mu
		self.sigma = sigma
		
	def addDict(self, dictionary={}):
		if dictionary:			
			self.acbl = dictionary['acbl']
			self.name = dictionary['name']
			self.mu = dictionary['mu']
			self.sigma = dictionary['sigma']
		else:
			print(dictionary, 'error')
		return self

# initial setup

db = ds.connect('sqlite:///NABCseed.db') # actual DB
#db = ds.connect('sqlite:///:memory:') # memory temporary
table = db.create_table('players', primary_id='acbl')
eventCodes = [
	  ('NAPA','PLAT','IMP','IMPS','MIXD','OPPR','OPEN','FAST','WMPR','WMEN','WMLM','SILV','SLVR'),
      ('LMPR','LM','LMO','OPEN','FAST','WAGR'),
	  ('LMPR','OPEN','NAIL','BLUE','WMLM','WMPR','PINK','WMEN','SRMX','SMIX',
	   'SMXD','SRMX','SRPR','SSP','SSRP','SSR')
    ]

# inital session to scan

url1= 'http://live.acbl.org/event/NABC'
#url2= '3/SSR/'

mp = {}

ts.setup(tau=.1, draw_probability=.01) 

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
		m = max(25,10.8574*math.log(.001*mp[a])) # reducing max for test 
		#s = min(25/3.0,247/27.0 - (11*mp[a] / 135000.0))
		s = 25/5.0 # Keeping all the initial sigmas the same
		return ts.Rating(mu=m,sigma=s)
    


def newPlayer(acbl, name):
	
	try:
		r = MPtoTS(acbl)
	except:
		r = ts.Rating() 
		
	temp = Player(acbl, name, r.mu, r.sigma)
	if verify(acbl): 
		table.insert(temp.db())
		logger('create',temp.db())
	
	#if (r.mu!=25.0): print("Adding %s..." % temp)

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
		print('Players detected: ',len(players))
		newRanks = ts.rate(players, ranks=scores)
	
	# zip allows us to traverse both lists in sync
	detectlist = ['6520898','4580699','8469873','7749511','8003602']
	for (i,j) in zip(allrows, newRanks):
		x = table.find_one(acbl=i[0])
		y = table.find_one(acbl=i[2])
		if i[0] in detectlist:  # Meck = 4580699
			print('%s: %s/%s --> %s/%s' % (i[0],x['mu'],x['sigma'],j[0].mu,j[0].sigma))
		if i[2] in detectlist:
			print('%s: %s/%s --> %s/%s' % (i[2],y['mu'],y['sigma'],j[1].mu,j[1].sigma))

		if x: logger('update','%s: %s/%s --> %s/%s' % (i[0],x['mu'],x['sigma'],j[0].mu,j[0].sigma))
		if y: logger('update','%s: %s/%s --> %s/%s' % (i[2],y['mu'],y['sigma'],j[1].mu,j[1].sigma))
		table.update(dict(acbl=i[0], mu=j[0].mu, sigma=j[0].sigma),['acbl'])
		table.update(dict(acbl=i[2], mu=j[1].mu, sigma=j[1].sigma),['acbl'])

def main():
	for year in range(14,20):
		for season in range(3):
			for event in eventCodes[season]:
                #if season==2: 
				#years = range(13,19)
                #else: 
				#years = range(14,20)
			
			#for year in years: 
				for i in range(6):
					testurl = url1 + str(year)+ str(season+1) + '/' + str(event) + '/' + str(i+1) + '/recap'
					print("loading...", testurl)
					logger('Event',testurl)
					r1 = requests.get(testurl)
					soup = BeautifulSoup(r1.content, 'html.parser')

					soup_rows = soup.find_all('tr')

					rows = []
					for tr in soup_rows:
						td = tr.find_all('td')
						if td:
							row = [td[1].get('data-acbl'), td[1].text,
							td[2].get('data-acbl'), td[2].text, (td[11].text if (td[11].text!='') else td[15].text)]
					# 11 or 15 works too, usable for imps
							if row[0]: 
								rows.append(row)
					print('---------------------------')
					print(len(rows))
					print('---------------------------')


					if rows: addToDB(rows)

			
getMPs()
main()
	
results = table.find()
test = []
for i in results:
	try:
		x = MPtoTS(i['acbl'])
		test.append((i['name'], i['mu'], i['sigma'], (i['mu']-3*i['sigma']+x.mu)))
	except KeyError:
		test.append(('No ACBL', i['acbl'], i['name'], i['mu'], i['sigma'], (i['mu']-3*i['sigma'])))
		
with open('output.txt','w') as f:
	for i in (sorted(test, key = lambda rank: rank[3])):
		f.write(str(i)+'\n')
		if (i[-1]<0): print(str(i)+'\n')

print(len(db['players']))

		
