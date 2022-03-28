#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p "python3.withPackages(ps:[ps.pycairo ps.tqdm])"

import os
import re
import math
import sys
import subprocess
import cairo
import tqdm

# should render a single long page
# and then move to ensure the current line is visible
################################################################
print('Reading timestamps...')
stamps = []
for file in os.listdir("."):
    if file.endswith('.pdf'):
        t = re.sub("[^0-9]", "", file)
        if len(t) > 0:
            stamps.append(int(t))

################################################################            
print('Computing cursor position...')
rows = {}
columns = {}
for s in tqdm.tqdm(sorted(stamps)):
    infile = "board{:d}.tex".format(s)
    f = open(infile, "r")
    lines = f.readlines()
    f.close()

    g = open("point{:d}.txt".format(s), "r")
    point = int(g.readlines()[0])
    g.close()
    count = 0
    row = 1
    for line in lines:
        if count + len(line) >= point:
            rows[s] = row
            columns[s] = point - count
            break
        row = row + 1
        count = count + len(line)

################################################################
print('Computing synctex...')
synctex = {}
for s in tqdm.tqdm(sorted(stamps)):
    infile = "board{:d}.tex".format(s)    
    row = rows[s]
    column = columns[s]
    
    p = subprocess.run(['synctex','view',"-i","{:d}:{:d}:{}".format(row,column,infile),"-o",infile],capture_output=True)
    x,y,width,height = [0,0,0,0]
    synctex[s] = {}
    for line in p.stdout.split(b'\n'):
        line = line.split(b':')
        if len(line) == 2:
            if line[0] == b'h':
                synctex[s]['x'] = float(line[1])
            if line[0] == b'v':
                synctex[s]['y'] = float(line[1])                
            if line[0] == b'W':
                synctex[s]['width'] = float(line[1])                                
            if line[0] == b'H':
                synctex[s]['height'] = float(line[1])                                                
            if line[0] == b'after':
                break

imagesize = (1920,1080)
paperheight = 6400

cursor_x = math.nan
cursor_y = math.nan
current_row = math.nan
current_synctex = math.nan

def render(cr, frame, s, t, slide, text, df):
    dpi = 400 / 72
    x = synctex[s]['x']*dpi
    y = synctex[s]['y']*dpi
    width = synctex[s]['width']*dpi
    height = synctex[s]['height']*dpi
    #print(synctex[s])
    #print(x,y-height,width,height)
    
    global current_row
    global cursor_x
    global cursor_y
    global current_synctex

    scroll_goal = imagesize[1]*0.4
    
    if math.isnan(current_synctex):
        current_synctex = y-height/2.0 - scroll_goal
    else:
        new_goal = (y-height/2.0 - scroll_goal)
        if abs(current_synctex - new_goal) > 5:
            current_synctex = 0.9 * current_synctex + 0.1 * new_goal
    
    cr.set_source_surface(slide, 0, -current_synctex)
    cr.paint()
    
    # current synctex
    margin = height * 0.5
    #lg = cairo.LinearGradient(0, (y-height) - margin, 0, y + margin)
    lg = cairo.LinearGradient(0.0, -current_synctex, 0.0, paperheight-current_synctex)

    darkness = 0.27
    lg.add_color_stop_rgba(0.0, 0, 0, 0, darkness)
    lg.add_color_stop_rgba(0.9*(y-height-margin)/paperheight, 0, 0, 0, darkness)
    lg.add_color_stop_rgba((y+margin)/paperheight, 0, 0, 0, 0.0)            
    lg.add_color_stop_rgba(1.1*(y+margin)/paperheight, 0, 0, 0, darkness)
    lg.add_color_stop_rgba(1.0, 0, 0, 0, darkness)

    # lg.add_color_stop_rgba(0.0, 0, 0, 0, 0)
    # lg.add_color_stop_rgba(0.99*(y-height-margin)/paperheight, 1, 1, 0, 0.0)
    # print('offset',(y-height-margin)/paperheight)
    # lg.add_color_stop_rgba((y-height-margin)/paperheight, 1, 1, 0, 0.5)
    # lg.add_color_stop_rgba((y+margin)/paperheight, 1, 1, 0, 0.5)
    # print('end',(y+margin)/paperheight)    
    # lg.add_color_stop_rgba(1.01 * (y+margin)/paperheight, 1, 1, 0, 0.0)            
    # lg.add_color_stop_rgba(1.0, 0, 0, 0, 0)    

    #cr.rectangle(0, -10, imagesize[0], 2*imagesize[1])
    cr.rectangle(0, -current_synctex, imagesize[0], paperheight)
    cr.set_source(lg)
    cr.fill()

    # highlight current synctex?
    #cr.set_source_rgba(0.5, 0.0, 1.0, 1)
    #cr.set_operator(cairo.Operator.ADD)
    #cr.rectangle(0, (y-height-margin)-current_synctex, imagesize[0]/3, height+2*margin)

    if math.isnan(cursor_x):
        cursor_x = columns[s]
    else:
        cursor_x = (cursor_x + columns[s])/2.0
        
    if math.isnan(cursor_y):
        cursor_y = rows[s]
    else:
        cursor_y = (cursor_y + rows[s])/2.0        

    if math.isnan(current_row):
        current_row = rows[s]
    else:
        current_row = 0.9 * current_row + 0.1 * rows[s]
        
    margin = 7.086599 * 400 / 72
    bottom_margin = 2 * 7.70443 * 400 / 72

    # cursor
    cr.select_font_face("Cascadia Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

    fontscale = 50
    lineheight = fontscale
    cr.set_font_size(fontscale)

    extents = cr.text_extents("M")
    
    cr.set_source_rgba(0.5, 0.0, 0.0, 1)
    cr.set_operator(cairo.Operator.ADD)
    cr.rectangle(margin + (cursor_x - 1) * extents.x_advance,
                 imagesize[1] - bottom_margin - extents.height * 1.15 + (cursor_y - current_row) * lineheight,
                 extents.x_advance, extents.height * 1.30)
    cr.fill()    

    # text
    cr.set_source_rgba(1, 1, 1, 0.5) # gray
    lg1 = cairo.LinearGradient(0.0, 0.0, 0.0, imagesize[1])
       
    lg1.add_color_stop_rgba(0.0, 1, 1, 1, 0)
    lg1.add_color_stop_rgba(0.5, 1, 1, 1, 0)    
    lg1.add_color_stop_rgba(1.0, 1, 1, 1, 0.5)

    cr.set_source(lg1)
    cr.set_operator(cairo.Operator.OVER)
    
    #for r in range(-math.ceil(imagesize[1]/lineheight),2):
    #for r in range(-math.ceil(imagesize[1]/lineheight),2):
    #if row-1+r >= 0 and row-1+r < len(text):
    #cr.move_to(margin,imagesize[1] - bottom_margin + r * lineheight)
    #cr.show_text(text[row-1+r])

    #for r in range(-math.ceil(imagesize[1]/lineheight),2):
    #for r in range(-math.ceil(imagesize[1]/lineheight),2):
    for r in range(len(text)):
        words = text[r]
        if (text[r].lstrip().startswith('\\documentclass')):
            words = '\\documentclass{article}'
        cr.move_to(margin,imagesize[1] - bottom_margin + (r - current_row + 1) * lineheight)
        cr.show_text(words)
        if (text[r].lstrip().startswith('\\end{document}')):
            break

loaded_slide = 0
slide = cairo.ImageSurface(cairo.FORMAT_RGB24, *imagesize)

loaded_text = 0
text = []

start = min(stamps)
finish = max(stamps)
fps = 30
duration = int(fps * (finish - start) / 1000)

subset = 1000

FFMPEG_BIN = "/home/jim/.nix-profile/bin/ffmpeg"
# https://zulko.github.io/blog/2013/09/27/read-and-write-video-frames-in-python-using-ffmpeg/
command = [ FFMPEG_BIN,
        '-y', # (optional) overwrite output file if it exists
        '-f', 'rawvideo',
        '-vcodec','rawvideo',
        '-s', '1920x1080', # size of one frame
        '-pix_fmt', 'rgb32',
        '-r', str(fps), # frames per second
        '-i', '-', # The imput comes from a pipe
        '-an', # Tells FFMPEG not to expect any audio
        '-vcodec', 'h264',
        'rendered.mp4' ]

ffmpeg = subprocess.Popen( command, stdin=subprocess.PIPE)

print("Rendering frames...")
#for frame in tqdm.tqdm(range(subset,duration)):
#for frame in tqdm.tqdm(range(subset,subset+100)):
for frame in tqdm.tqdm(range(duration)):
    t = start + frame * 1000 / fps
    s = max([s for s in stamps if s <= t])

    if loaded_slide != s:
        #print('  loading slide',s)
        slide = cairo.ImageSurface.create_from_png("board{:d}.png".format(s))
        loaded_slide = s

    if loaded_text != s:
        #print('  loading text',s)        
        infile = "board{:d}.tex".format(s)
        f = open(infile, "r")
        text = [x.rstrip("\n") for x in f.readlines()]
        f.close()
        loaded_text = s        

    imagesize = (1920,1080)
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, *imagesize)
    cr = cairo.Context(surface)
    
    df = 1.0 / fps
    render(cr, frame, s, t, slide, text, df)
    
    #framename = "frame{:05d}.png".format(frame)
    #print(framename,s)    
    #os.link("board" + str(s) + ".png", framename)
    #surface.write_to_png(framename)

    ffmpeg.stdin.write( surface.get_data() )

# ffmpeg -r 60 -i frame%05d.png test.avi
    
ffmpeg.stdin.close()
ffmpeg.wait()
if ffmpeg.returncode !=0:
    print('ffmpeg failed')
