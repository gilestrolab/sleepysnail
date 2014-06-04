rm(list=ls())



RAW_DIR <- "/data/sleepysnail/raw"
MAIN_TASK_DIR <- "/data/sleepysnail/task-output/MainTask"
FRAME_PER_HOUR = 60


getIsDayDf <- function(experiment){
	target_file <- list.files(MAIN_TASK_DIR, pattern=experiment, full.names=T)
	to_read <- scan(target_file,what="character")
	dfs <- lapply(to_read, read.csv)
	col_numbers <- sapply(dfs,ncol)
	day_night = dfs[[which(col_numbers == 1)]]
	day_night$frame <- 1:nrow(day_night)
	is_day_mat <- as.matrix(day_night)
	return(is_day_mat)
	}
getFeatureDf <- function(MAIN_TASK_DIR, experiment){
	target_file <- list.files(MAIN_TASK_DIR, pattern=experiment, full.names=T)
	to_read <- scan(target_file,what="character")
	dfs <- lapply(to_read, read.csv)
	col_numbers <- sapply(dfs,ncol)
	features = dfs[[which(col_numbers != 1)]]
	features <- subset(features, select=c(frame,id,x,y))
	#features <- subset(features, select=-c(error))
	features <- as.matrix(features)
	features[,"x"] <- round(features[,"x"])
	features[,"y"] <- round(features[,"y"])
	
	return(features)
	}

getRawDf <- function(RAW_DIR, experiment){
	
	my_dir <- grep(experiment, list.dirs(RAW_DIR), value=TRUE)
	if(length(my_dir) !=1)
		stop("different dirs have the same expereimental ID")
	my_file <- list.files(my_dir,pattern="*.csv",full.name=TRUE)
	if(length(my_file) !=1)
		stop(paste("there are several CSVs in",my_dir))
	df <- read.csv(my_file)
	id_col <- which(colnames(df) == "Index")
	names <- colnames(df) 
	names[id_col] <- "id"
	
	colnames(df) <- names
	
	return(df)
	}

addSecondaryFeatures <- function(df,max_frames,median_size=3, threshold=5){
	mat <- as.matrix(na.omit(df))
	frame <- 1:max_frames
	if(nrow(mat) < 10)
		return(NULL)
	

	x <- approx(mat[,"frame"], mat[,"x"], xout=frame, method="linear", rule=c(2,1))$y
	y <- approx(mat[,"frame"], mat[,"y"], xout=frame, method="linear", rule=c(1,2))$y
	
	cplx <- complex(real=x, imag=y)
	
	dist <- c(0, abs(diff(cplx)))
	dist <- ifelse(dist < threshold, 0, dist)
	is_active <- ifelse(dist > threshold, 1, 0)
	id <- df$id
	
	out <- cbind(id, frame, x, y, dist,is_active)
	#print(c(nrow(na.omit(out)),nrow(out) ))

	return(out)
	}

summarise_one_experiment <- function(experiment){

	start_hh_mm <- substring(strsplit(experiment,"[-_]")[[1]][2], c(1,3),c(2,4))
	
	start_hour  <- strtoi(start_hh_mm[1]) + strtoi(start_hh_mm[2])/60
	day_to_night_time <- 21

	is_day_mat <- getIsDayDf(experiment)
	feature_mat <- getFeatureDf(MAIN_TASK_DIR, experiment)
	feature_mat <- as.data.frame(feature_mat)
#~ 	experiment_df <- getRawDf(RAW_DIR, experiment)
	#checking number of rows
	
	expected <- nrow(is_day_mat)
	observed <- table(feature_mat[,"id"])
	if(any(expected != observed))
		stop("error with feature dataframe sizes")

	
	last_frame <- max(feature_mat[,"frame"])
	features_per_indiv <- split(feature_mat, feature_mat[,"id"])
	features_per_indiv <- lapply(features_per_indiv, addSecondaryFeatures, max_frames=last_frame)
	features_per_indiv <- lapply(features_per_indiv, as.data.frame)
	feature_mat <- do.call("rbind", features_per_indiv)
	feature_mat <- merge(feature_mat, is_day_mat, by="frame")
	
	
		
	day_night_trans <- which(diff(is_day_mat[, "is_day"]) == -1)
	night_day_trans <- which(diff(is_day_mat[, "is_day"]) == 1)
	
	a <- mean((day_night_trans / FRAME_PER_HOUR) %% 24)
	b <- mean((night_day_trans / FRAME_PER_HOUR) %% 24)
	
	day_to_night_time <- (a ) %% 24
	night_to_day_time <- (b ) %% 24
	
	
	night_length <- ((b %% 24) - (a %% 24)) %% 24
	
	print(night_length)
	
#~ 	print(c(start_hour, night_to_day_time, day_to_night_time, night_length))
	
	feature_mat[, "hour"] <- trunc(feature_mat[, "frame"]/FRAME_PER_HOUR )
	feature_mat[, "hour_in_day"] <- trunc((-day_to_night_time + feature_mat[, "frame"]/FRAME_PER_HOUR )) %% 24
	
	#feature_mat <- merge(feature_mat, experiment_df, by="id")
	
	features_per_indiv <- split(feature_mat, feature_mat[,"id"])
	
	pdf(sprintf("/tmp/%s.pdf", experiment),w=17*0.7, h=11*0.7)
	layout(matrix(1:4, 2,2))
	print("Generating pdf")
	for (f in features_per_indiv){

		

		title <- sprintf("%s:\n ID = %i; sp = %s", 
							experiment,
							unique(f[, "id"]),
							"TODO")
#~ 		
#~ 		title <- sprintf("%s:\n ID = %i; sp = %s", 
#~ 							experiment,
#~ 							unique(f[, "id"]),
#~ 							unique(f[,"Species"]))

		
		plot(dist ~ frame,f,pch=20,col=ifelse(is_day==0,"black","red"),main=title, ylim=c(0,150), xlim=c(0,last_frame),cex=0.5)
		mean_per_hour <- aggregate( is_active ~ hour , f, function(x) mean(x))
		d <- mean_per_hour$is_active
		names(d) <- mean_per_hour$hour
		barplot(d,ylim=c(0,1),ylab="Activity ratio",xlab ="time (h)")
	 }
	
	layout(matrix(1:1, 1,1))
	mean_per_hour <- aggregate( is_active ~ hour_in_day , feature_mat, function(x) mean(x))
	d <- mean_per_hour$is_active
	names(d) <- mean_per_hour$hour_in_day
	
	cols <- ifelse(0:23 < night_length , "black", "red")
	barplot(d,ylim=c(0,1), main="Activity average / hour for all indivs.",ylab="Activity ratio", width=1, space=0, col=cols)

	abline(v=night_length)
	
	dev.off()
	return(feature_mat)
}

experiments = c("20140425-175349_0", "20140502-175216_0", "20140516-173616_0",  "20140516-173617_2")
features_per_exper <- lapply(experiments, summarise_one_experiment)

#~ 
#~ experiment = 
#~ mat <-summarise_one_experiment(experiment)

#~ experiment = 
#~ mat <- summarise_one_experiment(experiment)
