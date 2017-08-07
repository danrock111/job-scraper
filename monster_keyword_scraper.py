# This is for the easy apply jobs on Monster.com
from bs4 import BeautifulSoup
from collections import Counter
from nltk.tokenize import word_tokenize, sent_tokenize
import nltk
import requests
import re

# Funtion used for gathering potential keywords
def gather_p_keywords(old_words_list, new_words_list):
    # To gather a single word
    for word in old_words_list:
        if word[1] == 'NN' or word[1] == 'VB' or word[1] == 'NNP':
            new_words_list.append(word[0].lower())
        if word[1] == 'JJ':
            new_words_list.append(word[0].lower())
    # To gather two words
    for i in range(0,len(old_words_list)):
        if old_words_list[i][1] == 'NNS' and old_words_list[i-1][1] =='NN':
            new_words_list.append("{} {}".format(old_words_list[i-1][0].lower(), old_words_list[i][0].lower()))

        if old_words_list[i][1] == 'NNP' and old_words_list[i-1][1] =='NNP':
            new_words_list.append("{} {}".format(old_words_list[i-1][0].lower(), old_words_list[i][0].lower()))

        if old_words_list[i][1] == 'NN' and old_words_list[i-1][1] =='JJ':
            new_words_list.append("{} {}".format(old_words_list[i-1][0].lower(), old_words_list[i][0].lower()))

        if old_words_list[i][1] == 'NNS' and old_words_list[i-1][1] =='JJ':
            new_words_list.append("{} {}".format(old_words_list[i-1][0].lower(), old_words_list[i][0].lower()))


def clean_data(word_list_to_clean):
	new_list = []

	# Seperate words with slashes i.e. (java/javascript/sql)
	for val in word_list_to_clean:
		if '/' in val:
			x = val.replace('/', ' ')
			y = x.split(' ')
			for i in y:
				new_list.append(i)
		else:
			new_list.append(val)

	# remove symbols before/after a word, or before/after a space ' '
	odd_symbols_to_remove = ['•', '·', '@', '-', '>', '<', '●', '|', '*', '%', '/']
	extra_new_list = []

	for word in new_list:
		check = 0
		for symbol in odd_symbols_to_remove:
			if word.startswith(symbol) or word.endswith(symbol):
				extra_new_list.append(word.replace(symbol, ''))
				check = 1
		if check == 0:
			extra_new_list.append(word)

	extra_new_list = [x.strip(' ') for x in extra_new_list]
	return extra_new_list


class MonsterScraper:
	def __init__(self):
		self.url = 'https://www.monster.com/jobs/search/'
		self.data_list = []


	def scrape(self, job_and_location_list):
		print('Starting...')
		if job_and_location_list[1] == '':
			payload = {'q':job_and_location_list[0]}
		else:
			payload = {'q':job_and_location_list[0], 'where':job_and_location_list[1]}

		page = 1
		next_url = ''
		job_found = 1
		while page < 5: # Change value for more pages!
			if page == 1:
				response = requests.get(self.url, params=payload)
				next_url = response.url
				print(next_url)
			else:
				next_page = next_url + '&page={}'.format(page)
				print(next_page)
				response = requests.get(next_page)
			data = response.text
			soup = BeautifulSoup(data, "html.parser")
			tags = soup.find_all(href=re.compile('job-openings.monster'))
			print('Finding Jobs...')
			for tag in tags:
				try:
					new_url = tag.get('href')
					new_response = requests.get(new_url, timeout=6)
					if 'job-openings.monster' in new_response.url:
						print('{} Job(s) Found'.format(job_found))
						raw_data = new_response.text
						new_soup = BeautifulSoup(raw_data, "html.parser")
						try:
							company_info = new_soup.find(class_='opening').extract()
						except AttributeError:
							print('Company Info - Invalid Data')
							company_info = ''
						try:
							job_description = new_soup.find(id='JobDescription').extract()
						except AttributeError:
							print('Company Info - Invalid Data')
							job_description = ''
						# Just getting job_description for finding keywords
						#temp_list = [new_response.url, company_info.get_text(), job_description.get_text()]
						try:
							self.data_list.append(job_description.get_text())
						except AttributeError:
							print("Can't gather job posting for job {}".format(job_found))
						job_found += 1
				except requests.exceptions.SSLError:
					continue
				except requests.exceptions.ConnectionError:
					continue
				except requests.exceptions.ReadTimeout:
					continue
			page += 1
		return self.data_list


	def get_keywords(self, list_of_jobs):
		print('Getting Keywords.....')
		jobs_string = ' '.join(list_of_jobs)
		
		token = word_tokenize(jobs_string)
		word_pos = nltk.pos_tag(token)
		# Load stopwords 
		with open('SmartStoplist.txt', 'r') as f:
			stopwords = [line.strip() for line in f]

		# Setting up lists to store words
		old_words_list = []
		new_words_list = []

		# All words in old_word_list
		for i in range(0, len(word_pos)):
			if word_pos[i][0].lower() not in stopwords:
				old_words_list.append(word_pos[i])

		# Gather all keywords
		gather_p_keywords(old_words_list, new_words_list)
		# Clean Keywords
		clean_keywords = clean_data(new_words_list)
		# Count Keywords
		word_count = Counter(clean_keywords)
		words_to_files = []
		for count in word_count.most_common():
			if count[1] == 1:
				break
			words_to_files.append(count[0])

		return words_to_files


	# Before creating a file, this function will remove action verbs, lemmatized action verbs,
	# soft skill words/phrases, and useless words/phrases 
	def create_file_of_keywords(self, keyword_list, job_title):
		print('Writing to file...')
		file_path = '/<path>/<to>/<store>/<file>/'+job_title+'_NEEDS_REVIEW.txt'

		# CLEANING DATA - VERBS
		# Removing redundant verbs in the text
		verbs_to_remove = []
		a_path = '/<path>/<to>/<verbs>/1_action_verbs.txt'
		a_lemma_path = '/<path>/<to>/<lemmatized>/<verbs>/1_action_verbs_lemmatized.txt'
		with open(a_path, 'r') as f:
			for line in f:
				verbs_to_remove.append(line.strip('\n'))
		with open(a_lemma_path, 'r') as f:
			for line in f:
				verbs_to_remove.append(line.strip('\n'))

		# Removing Unnecessary verbs
		for verb in verbs_to_remove:
			if verb in keyword_list:
				keyword_list.remove(verb)

		# CLEANING DATA - COMPUTER SKILLS / TECHINCAL SKILLS
		tech_comp_skills_to_remove = []
		technical_skills_path = '/<path>/<to>/<tech>/<skills>/1_technical_skills.txt'
		computer_skills_path = '/<path>/<to>/<computer>/<skills>/1_computer_skills.txt'
		with open(technical_skills_path, 'r') as f:
			for line in f:
				tech_comp_skills_to_remove.append(line.strip('\n'))
		with open(computer_skills_path, 'r') as f:
			for line in f:
				tech_comp_skills_to_remove.append(line.strip('\n'))

		# Removing computer skills and technical skills
		for word in tech_comp_skills_to_remove:
			if word in keyword_list:
				keyword_list.remove(word)


		# CLEANING DATA - SOFT SKILLS WORDS/PHRASES / USELESS WORDS/PHRASES
		soft_and_useless_words_to_remove = []
		soft_skills_path = "/<path>/<to>/<soft>/<skills>/1_soft_skills.txt"
		useless_words_path = "/<path>/<to>/<useless>/<words>/0_useless_words.txt"
		with open(soft_skills_path, 'r') as f:
			for line in f:
				soft_and_useless_words_to_remove.append(line.strip('\n'))
		with open(useless_words_path, 'r') as f:
			for line in f:
				soft_and_useless_words_to_remove.append(line.strip('\n'))

		# Removing soft skills and useless words/phrases
		for word in soft_and_useless_words_to_remove:
			if word in keyword_list:
				keyword_list.remove(word)

		#####################################################################################

		# Writing Data to File for Review
		with open(file_path, 'w') as f:
			for keyword in keyword_list:
				f.write(keyword+'\n')
		print('DONE.\n')



################ TEST ##################
x = MonsterScraper()
#x.scrape('electrical engineer', 'boston ma')
print('SEARCH FOR KEYWORDS')
user_job_input = input('Enter Job Title: ')
user_location_input = input('Enter Location: ')
job_t_l = [user_job_input, user_location_input]
jobs = x.scrape(job_t_l)
keywords = x.get_keywords(jobs)
x.create_file_of_keywords(keywords, job_t_l[0])


