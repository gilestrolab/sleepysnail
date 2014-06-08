


RAW_DIR <- "/data/sleepysnail/raw"
MAIN_TASK_DIR <- "/data/sleepysnail/task-output/MainTask"
FRAME_PER_HOUR <- 60
DAY_NIGHT_FILE_PATTERN <- "DayNight"
FEATURES_FILE_PATTERN <- "MergeCSVs"

getTimeCorrectionCoeff <- function(is_day_mat, experiment){
	day_to_night <- which(diff(is_day_mat[,"is_day"]) == -1)
	night_to_day <- which(diff(is_day_mat[,"is_day"]) == 1)
	ref <- min(day_to_night)
	
	day_to_night <- day_to_night - ref
	night_to_day <- night_to_day - ref
	
	
	exp_d2n <- 0:(length(day_to_night)-1) * (24 * 60)
	exp_n2d <- 0:(length(night_to_day)-1) * (24 * 60) + 12*60
	
	
	dn_cor_df <- data.frame(trans=c(day_to_night, night_to_day),
							d2n = c(rep(T,length(day_to_night)), c(rep(F,length(night_to_day)))),
							expected = c(exp_d2n, exp_n2d))
	dn_cor_df$observed_h <- dn_cor_df$trans/ 60
	
	mod <- lm(trans - expected ~ observed_h + d2n, dn_cor_df)
	
	print(summary(mod))
	
	
	
	pdf(sprintf("/tmp/time_correction_%s.pdf", experiment),w=7, h=7)
	
	plot(trans - expected ~ observed_h , 
								dn_cor_df, 
								pch=ifelse(d2n, 20, 3),
								col=ifelse(d2n, "red", "blue"),
								xlab=(expression(t[observed] (h))),
								ylab=(expression(t[observed] - t[expected] (min)))
								)
	mod <- lm(trans - expected ~ observed_h, subset(dn_cor_df, d2n==T))
	abline(mod, lwd=2, col="red")
	
	mod <- lm(trans - expected ~ observed_h, subset(dn_cor_df, d2n==F))
	abline(mod, lwd=2, col="blue")
	
	legend("topright", c(expression(day %->% night),expression(day %<-% night)), pch= c(20,4), lwd=2, col=c("red", "blue"),title="Transition" )

	dev.off()
	
	time_shift_coef <-  mod$coefficients["observed_h"]/60

	return (time_shift_coef)
}

getIsDayDf <- function(experiment, is_local=FALSE){
	if(! is_local){
		target_file <- list.files(MAIN_TASK_DIR, pattern=experiment, full.names=T)
		to_read <- scan(target_file,what="character")
		dfs <- lapply(to_read, read.csv)
		col_numbers <- sapply(dfs,ncol)
		day_night = dfs[[which(col_numbers == 1)]]
		
		}
	else{
		experiment_files <- (list.files("./", 
					pattern=experiment,
					full.names=F))
		good_file <- grep(DAY_NIGHT_FILE_PATTERN, experiment_files, value=T)
		day_night <- read.csv(good_file)
	}
	day_night$frame <- 1:nrow(day_night)
	is_day_mat <- as.matrix(day_night)
	return(is_day_mat)
	}
getFeatureDf <- function(experiment, is_local=FALSE){
	if(! is_local){
		target_file <- list.files(MAIN_TASK_DIR, pattern=experiment, full.names=T)
		to_read <- scan(target_file,what="character")
		dfs <- lapply(to_read, read.csv)
		col_numbers <- sapply(dfs,ncol)
		features = dfs[[which(col_numbers != 1)]]
	}
	else{
		
		experiment_files <- (list.files("./", 
					pattern=experiment,
					full.names=F))
		good_file <- grep(FEATURES_FILE_PATTERN, experiment_files, value=T)
		features <- read.csv(good_file)
	}
	print (colnames(features))
	features <- subset(features, select=c(frame,id,x,y,area,hull_area, hull_perim, w,h))
	#features <- subset(features, select=-c(error))
	features <- as.matrix(features)
	features[,"x"] <- round(features[,"x"])
	features[,"y"] <- round(features[,"y"])
	
	return(features)
	}

getRawDf <- function(experiment, is_local=FALSE ){
	
	if( ! is_local){
		my_dir <- grep(experiment, list.dirs(RAW_DIR), value=TRUE)
		if(length(my_dir) !=1)
			stop("different dirs have the same expereimental ID")
		my_file <- list.files(my_dir,pattern="*.csv",full.name=TRUE)
		if(length(my_file) !=1)
			stop(paste("there are several CSVs in",my_dir))
	}
	else{
		my_file <- paste(experiment, "csv",sep=".")
	}
	df <- read.csv(my_file, comment.char="#")
	id_col <- which(colnames(df) == "Index")
	names <- colnames(df) 
	names[id_col] <- "id"
	
	colnames(df) <- names
	
	return(df)
	}
# threshold = N px/min. x>N => active. otherwise, inactive
addSecondaryFeatures <- function(df,max_frames,median_size=3, threshold=1.5){
	mat <- as.matrix(na.omit(df))
	frame <- 1:max_frames
	if(nrow(mat) < 500)
		return(NULL)
	
	x  <- runmed( mat[,"x"], median_size)
	y  <- runmed( mat[,"y"], median_size)
	area  <- runmed( mat[,"area"], median_size)
	w  <- runmed( mat[,"w"], median_size)
	h  <- runmed( mat[,"h"], median_size)
	hull_area  <- runmed( mat[,"hull_area"], median_size)
	
	x <- approx(mat[,"frame"], x, xout=frame, method="linear", rule=c(2,1))$y
	y <- approx(mat[,"frame"], y, xout=frame, method="linear", rule=c(1,2))$y
	area <- approx(mat[,"frame"], area, xout=frame, method="linear", rule=c(1,2))$y
	h <- approx(mat[,"frame"], h, xout=frame, method="linear", rule=c(1,2))$y
	w <- approx(mat[,"frame"], w, xout=frame, method="linear", rule=c(1,2))$y
	hull_area <- approx(mat[,"frame"], hull_area, xout=frame, method="linear", rule=c(1,2))$y
	
	cplx <- complex(real=x, imag=y)
	
	dist <- c(0, abs(diff(cplx)))
	is_active <- ifelse(dist > threshold, 1, 0)
	
	id <- df$id
	
	out <- na.omit(cbind(id, frame, x, y, area, hull_area, w,h, dist,is_active))
	if(nrow(out) < 500)
		return(NULL)

	return(out)
	}

summarise_one_experiment <- function(experiment, is_local=FALSE){

	start_hh_mm <- substring(strsplit(experiment,"[-_]")[[1]][2], c(1,3),c(2,4))
	
	start_hour  <- strtoi(start_hh_mm[1]) + strtoi(start_hh_mm[2])/60
	day_to_night_time <- 21

	is_day_mat <- getIsDayDf(experiment, is_local)

	
	feature_mat <- getFeatureDf(experiment, is_local)
	
	feature_mat <- as.data.frame(feature_mat)

	experiment_df <- getRawDf(experiment, is_local)
	#checking number of rows
	
	expected <- nrow(is_day_mat)
	observed <- table(feature_mat[,"id"])
#~ 	if(any(expected != observed))
#~ 		stop("error with feature dataframe sizes")

	# workaround
	feature_mat <- feature_mat[feature_mat[,"frame"]  <= min(observed),]
	
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
	time_shift_coef <- getTimeCorrectionCoeff(is_day_mat, experiment)
	minutes <- feature_mat[, "frame"] - time_shift_coef * feature_mat[, "frame"]
	feature_mat <- cbind(feature_mat ,minutes)
	feature_mat[, "hour"] <- trunc(feature_mat[, "minutes"]/FRAME_PER_HOUR )
	feature_mat[, "hour_in_day"] <- trunc((-day_to_night_time + feature_mat[, "minutes"]/FRAME_PER_HOUR )) %% 24
	
	print (experiment_df)
	feature_mat <- merge(feature_mat, experiment_df, by="id")
	feature_mat <- feature_mat[which(!is.na(feature_mat$Species)),]
	
	features_per_indiv <- split(feature_mat, feature_mat[,"id"])
	
	pdf(sprintf("%s.pdf", experiment),w=17*0.7, h=11*0.7)
	layout(matrix(1:4, 2,2))
	print("Generating pdf")
	for (f in features_per_indiv){

		title <- sprintf("%s:\n ID: %i; sp: %s", 
							experiment,
							unique(f[, "id"]),
							unique(f[,"Species"]))

		
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
#~ experiment <- "20140425-175349_0"
#~ feature_mat <- summarise_one_experiment(experiment, is_local=TRUE)

bino <- function(k, x){
				a <- k[1];
				b <- k[2];
				out <- exp(a + b* x)/ (1 + exp(a + b* x)); 
				return(out)
				}


#~ 
#~ dist_m <- aggregate(dist ~ Species * Age * is_day * id * Date_exp_started, feature_mat, mean)
#~ boxplot(dist ~ as.numeric(Age) * is_day, dist_m)
#~ dist_m <- aggregate(dist ~ hour_in_day, feature_mat, mean)
#~ plot(dist ~ hour_in_day, dist_m, type = 'b')


#~ experiments = c("20140425-175349_0", "20140502-175216_0", "20140516-173616_0",  "20140516-173617_2")
#~ features_per_exper <- lapply(experiments, summarise_one_experiment)

#~ 
#~ experiment = 
#~ mat <-summarise_one_experiment(experiment)

#~ experiment = 
#~ mat <- summarise_one_experiment(experiment)
