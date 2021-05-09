from bs4 import BeautifulSoup
import requests 
import dataset as ds
import math
import pickle

# trying to refactor this nonsense so I can actually grasp what I'm doing.

def logger(msg, data):
	logfile = 'tslog.txt'
	with open(logfile,'a') as f:
		f.write(msg+' '+str(data)+'\n')


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

	
def verify(acbl):
	if len(acbl)!=7: return False
	try:
		i = int(acbl)
		return True
	except:
		return False
	return True


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


					if rows:
						tempname = './pkls/'+event+str(year)+str(season)+'-'+str(i)+'.pkl'
						openfile = open(tempname,'wb')
						pickle.dump(rows,openfile)
						openfile.close()
			
main()
	
		
