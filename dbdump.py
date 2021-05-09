import dataset as ds
from trueskill import Rating, rate, setup

db = ds.connect('sqlite:///NABCseed.db') # actual DB
table = db.create_table('players', primary_id='acbl')
			
	
results = table.find()
test = []
for i in results:
	test.append((i['acbl'], i['name'], i['mu'], i['sigma'], 2*(i['mu']-4*i['sigma'])))
		
with open('output.txt','w') as f:
	for i in (sorted(test, key = lambda rank: rank[-1],reverse=True)):
		f.write(str(i)+'\n')

print(len(db['players']))

		
