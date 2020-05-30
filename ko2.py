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
		return Rating(mu=self.mu,sigma=self.sigma) 
		
	def db(self):
		return dict({'acbl':self.acbl,'name':self.name,
		'mu':self.mu,'sigma':self.sigma, 'initmu':self.initmu})
		
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
	  ('VAND','VNDY'), 
      ('SPIN',), 
	  ()        
    ]

codeToBW = { 'VAND':'-spring-nabc-vanderbilt-knockout-teams/bracket/',
             'VNDY':'-spring-nabc-vanderbilt-knockout-teams/bracket/',
			 'SPIN':'-summer-nabc-spingold-knockout-teams/bracket/'}

# inital session to scan

url1= 'http://live.acbl.org/event/NABC'
url2= '/2/recap'
BWurl= 'https://bridgewinners.com/tournament/ko/20'

mp = {}

ts.setup(tau=.1, draw_probability=.01) 

def getMPs():
	with open('D00MP') as f:
		for line in f:
			line = line.translate(str.maketrans('JKLMNOPQR','123456789'))
			if line[-2] not in '0123456789': line = line[:-2]+'\n'
			mp[str(line[:7])] = float(line[-9:]) # extra CR in string?
	
def verify(acbl):
	try:
		if len(acbl)!=7: return False
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
		s = 10 # Keeping all the initial sigmas the same
		return ts.Rating(mu=m,sigma=s)
    

def newPlayer(acbl, name):
	
	try:
		r = MPtoTS(acbl)
	except:
		r = ts.Rating(mu=25,sigma=10) 
		
	temp = Player(acbl, name, r.mu, r.sigma)
	if verify(acbl): 
		myhash = temp.db()
		table.insert(myhash)
		logger('create','%s %s %s %s %s' % (temp.name, temp.acbl, temp.mu, temp.sigma, temp.initmu))
		return temp
		
	#if (r.mu!=25.0): print("Adding %s..." % temp)

	return {}
	
def getRosters(allrows):
	teams = {}

	#scores = []
	for i in allrows.keys():
		#print('get rosters...',allrows[i][0][0],'\n\n')
		#print(i,type(i))
		p = []
		if allrows[i][0][0] == None: 
			print('oops')
			continue
		for j in range(6):
			x = table.find_one(acbl=allrows[i][j][0])
			if not x:
				 x = newPlayer(allrows[i][j][0],allrows[i][j][1])
				
			if x:
				if isinstance(x,Player):
					p.append(x.db())
				else:
					p.append(x)
		
		teams[int(i)] = p
		
	
	#print('rosters:',teams)
		
	return teams	

def rankEvent(roster, year, event):
	testurl = BWurl + str(year) + codeToBW[event]

	origSeed = {}
	
	for i in range(len(roster),64):
		print("only should hit this if below 64 teams")
		roster[i+1] = [Player(0,'Bye',0,0.001).db()]*4
	
	for i in range(1,len(roster)+1):
		origSeed[i]=i
		
	
	
	
	# add logic for >64 teams, day 1 stuff

	print('Eval...', testurl)
	r1 = requests.get(testurl)
	soup = BeautifulSoup(r1.content, 'html.parser')
	soup_rows = soup.find_all('div', class_='bw_ko_match')
	
	winnerList = []
	
	for div in soup_rows:
		winner = div.find_all('div', attrs={'class':'winner'})
		win = [i['seed'] for i in winner]	
		#print(win[0],div['low_seed'], div['high_seed'],'\n')
		#win[0] = input(div['low_seed'] + ' vs. ' + div['high_seed'])
		winnerList.append((win[0],div['low_seed'],div['high_seed']))
		
	for i in winnerList:  # tuple of winner, low seed, high seed
		#print('yes! ', i)
		upset = (i[0]!=i[1])
		winlose = [1,0] if upset else [0,1]
		
		# original seeds
		o1 = int(origSeed[int(i[1])])
		o2 = int(origSeed[int(i[2])])
		
		#print(roster[o1],roster[o2])
		
		# iterate over	 rosters, get player TS info
		list1 = [ts.Rating(x['mu'], x['sigma']) for x in roster[o1]] 
		list2 = [ts.Rating(x['mu'], x['sigma']) for x in roster[o2]]	
		try:	
			#print(i,list1,list2)
		
			newRanks = ts.rate((list1,list2),winlose)
			#print('----got here----', newRanks)
			addToDB(newRanks,roster[o1],roster[o2])
		except KeyError:
			print('keyerror',i,list1,list2)
			pass
		except ValueError:
			print('Team with no players due to bogus player numbers. Ignoring.')
			
		if upset:
			origSeed[int(i[1])]=int(i[0])
			
def addToDB(allrows,roster1,roster2):
	x,y = allrows
	
	#print(roster1)
	detectlist = ['6520898','4580699','8469873','7749511','8003602']
	
	for i,j in zip(x,roster1):
		temp = (i.mu*.1*(10-i.sigma))+(j['initmu']*.1*(i.sigma))
		if str(j['acbl']) in detectlist: 
			print('%s: %s/%s --> %s/%s' % (j['acbl'],j['mu'],j['sigma'],temp,i.sigma))
		
		logger('update','%s: %s/%s --> %s/%s' % (j['acbl'],j['mu'],j['sigma'],temp,i.sigma))
		
		j['mu'] = temp
		j['sigma'] = i.sigma		
		
		table.update(j,['acbl'])
	
	
	for i,j in zip(y,roster2):
		temp = (i.mu*.1*(10-i.sigma))+(j['initmu']*.1*(i.sigma))
		
		if str(j['acbl']) in detectlist: 
			print('%s: %s/%s --> %s/%s' % (j['acbl'],j['mu'],j['sigma'],temp,i.sigma))
		
		logger('update','%s: %s/%s --> %s/%s' % (j['acbl'],j['mu'],j['sigma'],temp,i.sigma))
		
		j['mu'] = temp
		j['sigma'] = i.sigma
		table.update(j,['acbl'])
	
def main():
	for year in range(14,20):
		for season in range(2):
			for event in eventCodes[season]:
			#if season==2: 
			#	years = range(13,19)
			#else: 
			#	years = range(14,19)
			
			#for year in years: 
				testurl = url1 + str(year)+ str(season+1) + '/' + str(event) + url2
				print("loading...", testurl)
				logger('Event',testurl)
				r1 = requests.get(testurl)
				soup = BeautifulSoup(r1.content, 'html.parser')

				soup_rows = soup.find_all('tr')

				rows = {}
				for tr in soup_rows:
					td = tr.find_all('td')
					if td:
						if (td[1].text=='1'): continue
							
						rows[td[0].text]=\
						    [(td[i].get('data-acbl'),td[i].text) for i in range(1,7)]						
				print('---------------------------')
				print(len(rows))
				print('---------------------------')


				if len(rows)>1: 
					rosters = getRosters(rows)
					#print(rosters)
				
				#if rosters:
					rankEvent(rosters, year, event)
					
				
			
getMPs()
main()
	
results = table.find()
test = []

for i in results:
	test.append((i['name'], i['mu'], i['sigma'], (i['mu']-3*i['sigma'])))

with open('output.txt','w') as f:
	for i in (sorted(test, key = lambda rank: rank[-1])):
		f.write(str(i)+'\n')
#		if (i[-1]<0): print(str(i)+'\n')
print(len(db['players']))

		
