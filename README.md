# live-tex

This is an explanation of how I recorded https://www.youtube.com/watch?v=1ADH3fP5fjs

This whole workflow could definitely be improved.

While I was using emacs, I captured the webcam and audio with

```shell
ffmpeg -f alsa -acodec pcm_s32le -ac 2 -ar 48000 -i hw:1,0 -f v4l2 -input_format mjpeg -s 1920x1080 -i /dev/video4 -c:v copy -map_channel 0.0.0 -acodec aac -ab 128k output.mkv
```

To capture my editing in emacs, I run the following in emacs:

```elisp
(start-process "live-emacs" "live-emacs" "python" "/home/jim/live-tex/server.py")

(defun post-command-hook-fn ()
  (process-send-string "live-emacs" "%%%point ")  
  (process-send-string "live-emacs" (number-to-string (point)))
  (process-send-string "live-emacs" " ")
  (process-send-string "live-emacs" "mark ")  
  (process-send-string "live-emacs" (number-to-string (mark)))
  (process-send-string "live-emacs" "\n")
  (process-send-string "live-emacs" "%%%buffer%%%\n")
  (process-send-region "live-emacs" (point-min) (point-max))
  (process-send-string "live-emacs" "%%%EOF%%%\n")
  )

(add-hook 'post-command-hook 'post-command-hook-fn nil :local)
```

This launches the `server.py` which receives the point and mark and
buffer contents after any editing command.

This produces a ton of files like `board1615404402309.tex` with the
buffer contents, and a corresponding `point1615404402309.txt` with the
point position.  Running `make` runs `latex` on all the `.tex` files,
producing `.pdf`s.

Those `.pdf`s are then loaded by `render.py` which opens `ffmpeg` in a
subprocess and uses cairo to rasterize the `.pdf`s and the buffer
contents.  The resulting `rendered.mp4` was composited with the webcam
and audio in `output.mkv` using `kdenlive`.  To synchronize the audio
with the emacs contents, I typed loudly at the beginning and aligned
`rendered.mp4` with `output.mkv` that way.
