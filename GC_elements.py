#!/usr/local/bin/python3
from html.parser import HTMLParser
import requests, json
from bs4 import BeautifulSoup, UnicodeDammit

def process_urls(capability_name, capability_elements):
  print('Connecting to AC website...')
  baseurl = f'https://www.australiancurriculum.edu.au/f-10-curriculum/general-capabilities/{capability_name}/learning-continuum/?'
  params = {'level': [
              'Level+1',
              'Level+1a',
              'Level+1b',
              'Level+2',
              'Level+3',
              'Level+4',
              'Level+5',
              'Level+6',
              ],
            }
  url = baseurl + 'element=' + '&element='.join(capability_elements) + '&level=' + '&level='.join(params['level'])
  print('Getting', url)
  r = requests.get(url, headers=headers)
  soup = BeautifulSoup(r.text, 'html.parser')
  parse_html(soup, capability_name, capability_elements)

def parse_html(html, capability_name, capability_elements):
  global results

  # prepare relevant page sections
  # clear these, just in case of empty results carrying over
  elements = None
  elements = html.find_all('div',attrs={'class': 'accordion'})

  # deal with multiple pages
  next_page = None
  pagination = html.find('div',attrs={'class': 'pager'})
  if pagination:
    link_element = pagination.find('a',attrs={'rel':'next'})
    if link_element:
      next_page = link_element['href']

  # content descriptions
  for element in elements:
    # extract element name
    element_name = element.find('h3').get_text().strip()
    
    # get levels
    levels = element.contents[3].find_all('h2')
    for level in levels:
      level_name = level.get_text().strip()
      sub_elements = level.parent.find_all('h3')
      for sub_element in sub_elements:
        sub_element_name = sub_element.get_text().strip()
        sub_element_id = sub_element.next_sibling.next_sibling['id']
        sub_element_text = sub_element.next_sibling.next_sibling.get_text().strip()
        if capability_name not in results:
          results[capability_name] = {}
        if element_name not in results[capability_name]:
          results[capability_name][element_name] = {}
        if sub_element_name not in results[capability_name][element_name]:
          results[capability_name][element_name][sub_element_name] = {}
        if level_name not in results[capability_name][element_name][sub_element_name]:
          results[capability_name][element_name][sub_element_name][level_name] = {}
        results[capability_name][element_name][sub_element_name][level_name][sub_element_id] = {
          'text': sub_element_text,
        }

  # check if another page exists
  if next_page:
    # to fix the % encoding in the CCT capablity when using
    # the requests module
    next_page = next_page.replace('%u2013','–')
    print('Getting', next_page)
    r = requests.get(next_page, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    parse_html(soup, capability_name, capability_elements)

headers = {
  'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15',
  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

capability_elements = {
  #'literacy': ['Comprehending+texts+through+listening%2C+reading+and+viewing','Composing+texts+through+speaking%2C+writing+and+creating','Text+knowledge','Grammar+knowledge','Word+Knowledge','Visual+Knowledge'],
  #'numeracy': ['Estimating+and+calculating+with+whole+numbers','Recognising+and+using+patterns+and+relationships','Using+fractions%2C+decimals%2C+percentages%2C+ratios+and+rates','Using+spatial+reasoning','Interpreting+statistical+information','Using+measurement'],
  #'information-and-communication-technology-ict-capability': ['Applying+social+and+ethical+protocols+and+practices+when+using+ICT','Investigating+with+ICT','Creating+with+ICT','Communicating+with+ICT','Managing+and+operating+ICT'],
  'critical-and-creative-thinking': ['Inquiring+–+identifying%2C+exploring+and+organising+information+and+ideas','Generating+ideas%2C+possibilities+and+actions','Reflecting+on+thinking+and+processes','Analysing%2C+synthesising+and+evaluating+reasoning+and+procedures'],
  #'personal-and-social-capability': ['Self-awareness','Self-management','Social+awareness','Social+management'],
  #'ethical-understanding': ['Understanding+ethical+concepts+and+issues','Reasoning+in+decision+making+and+actions','Exploring+values%2C+rights+and+responsibilities'],
  #'intercultural-understanding': ['Recognising+culture+and+developing+respect','Interacting+and+empathising+with+others','Reflecting+on+intercultural+experiences+and+taking+responsibility'],
}

# process data
for capability_name in capability_elements:
  results = {}
  process_urls(capability_name, capability_elements[capability_name])

  with open(capability_name+'_GC_elements.json', 'w') as f:
    f.write(json.dumps(results,indent=2))