#!/usr/bin/env python3

# Forked from:
# https://github.com/CuBiC3D/SeriesEverEx
# `wget` required

# if there's only 1080p version - it'll be skipped
# only mycdn.me/* links are downloaded automatically

# any url with indication to a series, w or w/o season or episode will do
show = 'http://seriesever.net/serien/die-sopranos.html'
show = 'http://seriesever.net/die-sopranos/staffel-1-episode-1.html'

# path to save
dl_path = '/med/German/TV/'
# 1 to create dir for the show dl_path/show_name/
# works only with seasons = range()
cdir = 1

# range(2, 5 + 1) for 2,3,4,5 seasons; works only with series
# 'all' to get all seasons and for movies
seasons = 'all'
seasons = range(1, 1 + 1)

# 1 to download subtitles if they're available 
subtitles = 1

####################################

import sys, os, time
import re
import json
import requests

def getHTMLContent(url):
	headers = {
		'User-Agent': useragent
	}
	r = requests.get(url, headers=headers)
	return r.text

def getVideoID(html):
	m = re.search(r'var video_id  = "(.*)";', html)
	return m.group(1)

def getVideoPart(videoID, part):
	headers = {
		'User-Agent': useragent,
		'X-Requested-With': 'XMLHttpRequest'
	}
	
	for res in ('720p', '480p', '360p'):
		payload = {
			'video_id': videoID,
			'part_name': res,
			'page': part
		}
		
		r = requests.post('http://seriesever.net/service/get_video_part', headers=headers, data=payload)
		
		if r.text != '{"test":1}':
			return json.loads(r.text)

def resolveParts(parts):
	links = []
	for part in parts:
		if part['source'] == 'url':
			links.append(resolveCDN(part['code']))
		elif part['source'] == 'other':
			links.append(resolveIFrame(part['code']))
	return links

def resolveCDN(code):
	headers = {
		'User-Agent': useragent,
	}
	payload = {'link': code}
	r = requests.post('http://play.seriesever.net/sevr/plugins/playerphp.php', headers=headers, data=payload)
	#print(r.text)
	links = json.loads(r.text)
	if 'error' in links:
		print("Error resolving CDN: {}".format(links['error']))
		return None
	elif 'link' in links and type(links['link']) is str:
		return links['link']
	else:
		# myCDN
		return links['link'][0]['link']

def resolveIFrame(code):
	m = re.search(r'<iframe.*src="(.*?)"', code)
	return m.group(1)

def dl(url):
	html = getHTMLContent(url)
	
	if '<title>404: Seite nicht gefunden</title>' in html:
		return 'stop', 0

	videoID = getVideoID(html)
	#print("Video ID is: {}".format(videoID))

	part = getVideoPart(videoID, 0)
	#print("{} stream(s) are available".format(part['part_count']))
	parts = [part['part']]
	if not part['one_part']:
		for i in range(1, part['part_count']):
			part = getVideoPart(videoID, i)
			parts.append(part['part'])

	links = resolveParts(parts)
	
	for link in links:
		print('Avail. link >>> ' + str(link))
		#pass
	print()
	
	for link in links:
		if type(link) is str and 'mycdn.me' in link:
			return link, videoID

useragent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 OPR/46.0.2597.57'

#print(title)
#print(dl('http://seriesever.net/x-men/x-men-3.html'))
#open('z2.htm', 'w').write(p)
#exit()


fail = 0

if seasons == 'all':
	p = getHTMLContent(show)
	links = re.findall('<li class="list-group-item".*?<a class="img" href="(.*?)" title=".*?>.*?</li>', p, re.DOTALL)
	
	for link in links:
		p = getHTMLContent(link)
		title = re.findall('<div class="panel-heading">.*?<h1>(.*?)</h1>', p, re.DOTALL)[0]
		
		print(title)
		
		fname = dl_path + '/' + title + '.mp4'
		
		if os.path.isfile(fname):
			continue
		
		while 1:
			try:
				link, videoID = dl(link)
				fail = 0
				break
			except:
				fail += 1
				time.sleep(2)
				if fail > 10:
					link = None
					fail = 0
					break
				print('Failed #' + str(fail))
			
		if link is None:
			continue
			
		if link == 'stop':
			break
		
		print(link)
		print()
		
		
		os.system('wget --user-agent="' + useragent + '" "' + link + '" -O "' + fname + '"')
		if subtitles == 1:
			subs = getHTMLContent('http://seriesever.net/cc/serien/id/' + videoID + '.srt')
			if len(subs) and not '<title>404: Seite nicht gefunden</title>' in subs and not '<title>Database Fehler</title>' in subs:
				print(subs, file=open(fname + '.srt', 'w'))
					
else:
	p = getHTMLContent(show)

	title = re.findall('<div class="panel-heading">.*?<h1>(.*?)</h1>', p, re.DOTALL)[0].strip().split(' Staffel ')[0]
	show = re.sub('staffel-\d+(-|)|episode-\d+', '', show.replace('/serien/', '/').replace('.html', '/'))
	
	for season in seasons:
		ep = 1
		
		while 1:
			season2 = '0' + str(season) if season < 10 else str(season)
			ep2 = '0' + str(ep) if ep < 10 else str(ep)
			
			if cdir:
				if not os.path.isdir(dl_path + '/' + title):
					os.mkdir(dl_path + '/' + title)
				fname = dl_path + '/' + title + '/' + title + '.S' + season2 + 'E' + ep2 + '.mp4'
			else:
				fname = dl_path + '/' + title + '.S' + season2 + 'E' + ep2 + '.mp4'
			
			print(title + ' S' + season2 + 'E' + ep2)
			
			if os.path.isfile(fname):
				ep += 1
				continue
			
			while 1:
				try:
					link, videoID = dl(show + 'staffel-' + str(season) + '-episode-' + str(ep) + '.html')
					fail = 0
					break
				except:
					fail += 1
					time.sleep(1)
					if fail > 10:
						link = None
						fail = 0
						break
					print('Failed #' + str(fail))
				
			if link is None:
				ep += 1
				continue
				
			if link == 'stop':
				break
			
			print(link)
			print()

			os.system('wget --user-agent="' + useragent + '" "' + link + '" -O "' + fname + '"')
			if subtitles == 1:
				subs = getHTMLContent('http://seriesever.net/cc/serien/id/' + videoID + '.srt')
				if len(subs) and not '<title>404: Seite nicht gefunden</title>' in subs and not '<title>Database Fehler</title>' in subs:
					print(subs, file=open(fname + '.srt', 'w'))
					
			ep += 1
			print('----------------------------------')
