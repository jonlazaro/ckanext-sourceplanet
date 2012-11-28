import csv
import os

here = os.path.dirname(__file__)
CSV_PATH = here + '/sourceplanet_data_model.csv'
#CSV_PATH = 'sourceplanet_data_model.csv'
'''
        #'name': [ignore_missing],
        #'uri': [ignore_missing],
        #'category': [ignore_missing],
        #'project_type': [ignore_missing],
        #'value': [ignore_missing],

'''


def load_data_model():
	with open(CSV_PATH, 'r') as stdoc:
		#Each line of CSV represents an station. Content of each line: OBJECTID, IDEST, NAME, DIR, POBL, URL, ZONE, URL_ZONE, PROV_COD,..., XUTM, YUTM
		reader = csv.reader(stdoc, delimiter='\t', quoting=csv.QUOTE_NONE)
		eval_list = []
		for details in reader:
			eval = {'name': unicode(details[4], 'utf-8'),
				#Spanish   ->   'name': unicode(details[2], 'utf-8'),
				'uri': 'http://dbpedia.org/resource/' + details[3].encode('utf-8'),
				'category': details[1].encode('utf-8'), 
				'dataset_type': details[0].encode('utf-8'), 
				'value': ''}
			eval_list.append(eval)

		#for a in eval_list:
		#	print a

	return eval_list
