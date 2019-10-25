#Rough beta build. Sorrow446.

import os
import re
import sys
import time
import json
import platform
import traceback

import morapy
import requests
from tqdm import tqdm
from mutagen import File
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC, Picture

client = morapy.Client()

def get_os():
	if platform.system() == 'Windows':
		return True
	else:
		return False

def os_cmds(arg):
	if get_os():
		if arg == "c":
			os.system('cls')
		elif arg == "t":
			os.system('title MQ-DL R1 (by Sorrow446)')
	else:
		if arg == "c":
			os.system('clear')
		elif arg == "t":
			sys.stdout.write('\x1b]2;MQ-DL R1 (by Sorrow446)\x07')

def read_config():
	with open("config.json") as f:
		return json.load(f)

def exist_check(f):
	if os.path.isfile(f):
		os.remove(f)
			
def dir_setup(dir):
	if not os.path.isdir(dir):
		os.makedirs(dir)
		# try:
			# os.makedirs(dir)
		# except OSError:
			# pass

def sanitize(f):
	if get_os():
		return re.sub(r'[\\/:*?"><|]', '-', f)
	else:
		return re.sub('/', '-', f)
		
def write_tags(f, meta, cov, com, fmt):
	if fmt == "FLAC":
		audio = FLAC(f)
		for tag, value in meta.items():
			if value:
				audio[tag] = str(value)
		if com:
			audio['COMMENT'] = com
	else:
		audio = MP4(f)
		audio['\xa9nam'] = meta['TITLE']
		audio['\xa9alb'] = meta['ALBUM']
		audio['aART'] = meta['ALBUMARTIST']
		audio['\xa9ART'] = meta['ARTIST']
		audio['trkn'] = [(meta['TRACK'], meta['TRACKTOTAL'])]
		audio['\xa9day'] = meta['YEAR']
		if meta['COPYRIGHT']:
			audio['cprt'] = meta['COPYRIGHT']
		if com:
			audio['\xa9cmt'] = com			
	with open(cov, 'rb') as cov_obj:
		if fmt == "FLAC":
			image = Picture()
			image.type = 3
			image.mime = "image/jpeg"
			image.data = cov_obj.read()
			audio.add_picture(image)
		else:
			audio['covr'] = [MP4Cover(cov_obj.read(), imageformat = MP4Cover.FORMAT_JPEG)]
	audio.save()
	
def parse_meta(src, meta, num):
	if meta:
		meta['ARTIST'] = src['artistName']
		meta['ISRC'] = src['isrc']
		meta['TITLE'] = src['name']
		meta['TRACK'] = num
		return meta
	else:
		parsed_meta={
			'ALBUM':src['name'],
			'ALBUMARTIST':src['artistName'],
			'COPYRIGHT':src['copyright'],
			'LABEL':src['label'],
			'TRACKTOTAL':src['trackCount'],
			'YEAR':src['originallyReleased'].split('-')[0],
			'UPC':src['upc']}
		return parsed_meta

def query_qual(j, req_qual):
	best = "AAC PLUS"
	ext = ".m4a"
	if req_qual == "FLAC":
		if j['losslessFormats']:
			best = "FLAC"
			ext = ".flac"
		else:
			if len(j['formats']) == 1:
				best = "AAC PLUS"
			elif len(j['formats']) == 2:
				best = "AAC"
	elif req_qual == "AAC":
		if len(j['formats']) == 2:
			best = "AAC"
		else:
			best = "AAC PLUS"
	if best == "FLAC":
		fmt = j['losslessFormats'][0]['name']
		bd = j['losslessFormats'][0]['sampleBits']
		sr = j['losslessFormats'][0]['sampleRate']
		br = j['losslessFormats'][0]['bitrate']
	elif best == "AAC PLUS":
		fmt = j['formats'][0]['name']
		bd = j['formats'][0]['sampleBits']
		sr = j['formats'][0]['sampleRate']
		br = j['formats'][0]['bitrate']
	elif best == "AAC":
		fmt = j['formats'][1]['name']
		bd = j['formats'][1]['sampleBits']
		sr = j['formats'][1]['sampleRate']
		br = j['formats'][1]['bitrate']
	if req_qual != best:
		print("Requested quality " + req_qual + " unavailalable. Using " + best + " instead...")
	return fmt, bd, br, sr, ext

def download(url, f, num, tot, title, bd, br, sr, fmt):
	if fmt == "FLAC":
		spec = bd + "-bit / " + sr[0:2] + "kHz FLAC"
	else:
		spec = br + "kbps AAC"
	print("Downloading track " + num + " of " + tot + ": " + title + " - " + spec)
	r = requests.get(url, stream=True, headers={
		"range":"bytes=0-",
		'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36',
		'Referer':'http://localhost:19330/'})
	r.raise_for_status()
	size = int(r.headers.get('content-length', 0))
	with open(f, 'wb') as f:
		with tqdm(total=size, unit='B',
			unit_scale=True, unit_divisor=1024,
			initial=0, miniters=1) as bar:		
				for chunk in r.iter_content(32*1024):
					if chunk:
						f.write(chunk)
						bar.update(len(chunk))

def download_cov(url, cov):
	r = requests.get(url)
	r.raise_for_status()
	with open (cov, 'wb') as f:
			f.write(r.content)

def main():
	cfg = read_config()	
	req_qual = cfg['quality']
	cov_size = cfg['cover_size']
	com = cfg['comment'].strip()
	if cfg['naming_scheme'] == "1":
		scheme = ". "
	else:
		scheme = " - "
	if req_qual == "1":
		req_qual = "AAC PLUS"
	elif req_qual == "2":
		req_qual = "AAC"
	elif req_qual == "3":
		req_qual = "FLAC"
	if cov_size == "1":
		cov_size = 70
	elif cov_size == "2":
		cov_size = 170
	elif cov_size == "3":
		cov_size = 300
	elif cov_size == "4":
		cov_size = 500
	elif cov_size == "5":	
		cov_size = 600
	client.auth(cfg['email'], cfg['password'])
	print("Signed in successfully.\n")
	while True:		
		url = input("Input URL:").strip()
		if not url:	
			os_cmds('c')
			continue		
		elif not url.startswith('https://content.mora-qualitas.com/artist/', 0):
			print("Invalid URL.")
			time.sleep(1)
			os_cmds('c')
			continue	
		if '/track/' in url:
			raise NotImplementedError('Support for downloading single tracks coming soon.')
		if '/playlist/' in url:
			raise NotImplementedError('Support for downloading playlists coming soon.')
		url = url.split('?')[0]
		ref = 'http://localhost:19330/' + "/".join(url.split('/')[3:7])
		os_cmds('c')
		id = url.split('/')[-1]
		if not id.lower().startswith("alb"):
			id = "alb." + url.split('-')[-1]
		al_src_meta = client.get_album_meta(id, cfg['language'])
		tr_src_meta = client.get_track_meta(id, cfg['language'])
		al_meta = parse_meta(al_src_meta, "", "")
		album_fol = al_meta['ALBUMARTIST'] + " - " + al_meta['ALBUM']
		album_fol_s = os.path.join("MQ-DL downloads", sanitize(album_fol))
		cov = os.path.join(album_fol_s, "cover.jpg")
		dir_setup(album_fol_s)
		exist_check(cov)
		download_cov(client.get_cover(id, cov_size), cov)
		num = 0
		tot = al_meta['TRACKTOTAL']	
		print(album_fol + "\n")
		for track in tr_src_meta['tracks']:
			if not track['isStreamable']:
				print("This track can't be downloaded as it's not allowed to be streamed. Skipped.")
				continue
			fmt, bd, br, sr, ext = query_qual(track, req_qual)
			num += 1
			final_meta = parse_meta(track, al_meta, num)
			title = final_meta['TITLE']
			pre = os.path.join(album_fol_s, str(num) + ".mq-dl_download")
			post = os.path.join(album_fol_s, str(num).zfill(2) + scheme + sanitize(title) + ext)	
			exist_check(pre)
			exist_check(post)
			url = client.get_track_url(track['id'], br, fmt, ref)
			if not url:
				continue
			download(url['url'], pre, str(num), str(tot), title, str(bd), str(br), str(sr), fmt)
			write_tags(pre, final_meta, cov, com, fmt)
			try:
				os.rename(pre, post)
			except OSError:
				print("Failed to rename track.")
		os_cmds('c')

if __name__ == '__main__':
	try:
		os_cmds('t')
		main()
	except (KeyboardInterrupt, SystemExit):
		sys.exit()
	except:
		traceback.print_exc()
		input("\nAn exception has occurred. Press enter to exit.")
		sys.exit()
