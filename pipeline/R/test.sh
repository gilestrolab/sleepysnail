
for i in $(seq 20)
	do
		Rscript make_bootstraps.R 2
		killall R
	done
