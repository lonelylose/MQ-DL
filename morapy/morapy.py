# Rough wrapper for mora-DL. Sorrow446.

import sys
import requests

from morapy.exceptions import AuthenticationError

class Client:
	def __init__(self):	
		self.session = requests.Session()
		self.session.headers.update({
			'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36',
			'Referer':'http://localhost:19330/'})
		self.base = 'https://api.napster.com/'
		self.key = 'NTEwNDI1OGUtY2IyMi00MGNmLWIxMjQtYzI2MjVkYWM0ODJh'

	def api_call(self, epoint, method, **kwargs):
		url = self.base + epoint
		if method == "auth":
			data={
				'username':kwargs['email'], 
				'password':kwargs['pwd'],
				'grant_type':'password'}
			headers={
				'Authorization': 'Basic TlRFd05ESTFPR1V0WTJJeU1pMDBNR05tTFdJeE1qUXRZekkyTWpWa1lXTTBPREpo=='}			
		elif method == "tr_url":
			params={
				'bitrate':kwargs['br'],
				'format':kwargs['fmt'],
				'protocol':'',
				'track':kwargs['id']}
			headers={
				'Authorization':'Bearer ' + self.token,
				'Referer':kwargs['ref']}
		elif method == "get_id":
			url = '' + epoint
			params={
				'albumShortcut':kwargs['al_scut'],
				'artistShortcut':kwargs['ar_scut'],
				'developerKey':'5C8F8G9G8B4D0E5J'}
			headers = ""	
		elif method in ['al_meta', 'tr_meta']:
			params={
				'catalog':'JP_MORAQUALITAS',
				'lang':kwargs['lang'],
				'rights':'2'}
			headers = {'apikey':self.key}		
		elif method == "cover":
			params = ""
			headers = {'apikey':self.key}
		if method == "auth":
			r = self.session.post(epoint, data=data, headers=headers)
			if r.status_code == 403:
				raise AuthenticationError('Invalid credentials.')
		else:
			r = self.session.get(epoint, params=params, headers=headers)
		return r.json()

	def auth(self, email, pwd):
		j = self.api_call(self.base + 'oauth/token', 'auth', email=email, pwd=pwd)
		self.token = j['access_token']
		self.ref_token = j['refresh_token']
		return j
		
	def get_id(self, ar_scut, al_scut):
		j = self.api_call('http://direct.rhapsody.com/metadata/data/methods/getIdByShortcut.js?', 
			'get_id', ar_scut=ar_scut, al_scut=al_scut)
		return j
		
	def get_album_meta(self, id, lang):
		j = self.api_call(self.base + "v2.2/albums/" + id + "?", 'al_meta', lang=lang)
		return j['albums'][0]
	
	def get_track_meta(self, id, lang):
		j = self.api_call(self.base + "v2.2/albums/" + id + "/tracks?", 'tr_meta', lang=lang)
		return j

	def get_track_url(self, id, br, fmt, ref):
		j = self.api_call(self.base + "v2.2/streams?", 'tr_url', id=id, br=br, fmt=fmt, ref=ref)
		if not j['streams']:
			print("The API didn't return a track URL. This is a temporary account issue that affects hi-res tracks. Skipped.")
			return
		return j['streams'][0]

	def get_cover(self, id, dim):
		j = self.api_call(self.base + "v2.2/albums/" + id + "/images", 'cover')
		dim = str(dim) + "x" + str(dim)
		# The API will sometimes won't return any covers. Secondary endpoint.
		if j['images']:	
			pre_cov = j['images'][0]['url'].split('_')[0]
			cov = 'http://static.rhap.com/img/' + dim + "/" + "/".join(pre_cov.split('/')[5:]) + "_" + dim + ".jpg"
		else:
			cov = 'https://api.napster.com/imageserver/v2/albums/' + id + '/images/' + dim + ".jpg"
		return cov
	
	# def refresh_token():
		# pass