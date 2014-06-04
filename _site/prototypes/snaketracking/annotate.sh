#!/bin/sh

IMAGE_DIR=/tmp/fig
j=0
for i in $(ls $IMAGE_DIR | grep -e ^snake_ )
	do
	f=$(echo $i | cut -f 2 -d _)
	it=$(echo $i | cut -f 3 -d _ | cut -f 1 -d .)
	img=$IMAGE_DIR/$i
	out=$IMAGE_DIR/annot_$(printf %04d ${j%}).png
	echo $img '->' $out
	convert $img -scale 300%  -gravity South   -background Plum -pointsize 32   -splice 0x70  -gravity SouthWest  -font Arial-Bold  -annotate +15+15 "Frame = $f; iter. =$it"  $out
	(( j++ ))
	done

ffmpeg -f image2 -i $IMAGE_DIR/annot_%04d.png -vcodec libx264 -vb 20M -r 25 $IMAGE_DIR/video.avi 
