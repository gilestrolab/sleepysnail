rm(list=ls())



RAW_DIR <- "/data/sleepysnail/raw"
MAIN_TASK_DIR <- "/data/sleepysnail/task-output/MainTask"


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
getFeatureDf <- function(MAIN_TASK_DIR, list_of_targs){
	target_file <- list.files(MAIN_TASK_DIR, pattern=experiment, full.names=T)
	to_read <- scan(target_file,what="character")
	dfs <- lapply(to_read, read.csv)
	
	col_numbers <- sapply(dfs,ncol)
	features = dfs[[which(col_numbers != 1)]]
	features <- subset(features, select=-c(error))
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


addSecondaryFeatures <- function(df,max_frames,median_size=5, threshold=5){
	mat <- as.matrix(df)
	cplx <- complex(real=mat[,"x"], imag=mat[,"y"])
	dist <- abs(diff(cplx))
	out <- cbind(mat, dist=c(NA, dist))
	out <- na.omit(out)
	
	out[,"dist"] <- runmed(out[,"dist"],median_size)

	new_f <- 2:max_frames
	out <- apply(out, 2, function(y, f, new_f){
				approx(f, y, xout=new_f, method="linear")$y},
				 out[, "frame"], new_f)
	out[,"is_day"] <- ifelse(out[,"is_day"] <0.5, 0, 1)
	out <- cbind(out, is_active=ifelse(out[,"dist"] > threshold,1, 0))
	return(out)
	}

summarise_one_experiment <- function(experiment){



	is_day_mat <- getIsDayDf(experiment)
	feature_mat <- getFeatureDf(MAIN_TASK_DIR, list_of_targs)
	#experiment_df <- getRawDf(RAW_DIR, experiment)

	#checking number of rows
	expected <- nrow(is_day_mat)
	observed <- table(feature_mat[,"id"])
	if(any(expected != observed))
		stop("error with feature dataframe sizes")


	feature_mat <- merge(feature_mat, is_day_mat, by="frame")

	feature_mat <- na.omit(feature_mat)

	last_frame <- max(feature_mat[,"frame"])


	features_per_indiv <- split(feature_mat, feature_mat[,"id"])

	print(lapply(features_per_indiv, function(x)max(x[,"frame"])))

	features_per_indiv <- lapply(features_per_indiv, addSecondaryFeatures, max_frames=last_frame)
	features_per_indiv <- lapply(features_per_indiv, as.data.frame)

	feature_mat <- do.call("rbind", features_per_indiv)
			
	pdf(sprintf("/tmp/%s.pdf", experiment))
	print("Generating pdf")
	for (f in features_per_indiv){
		title <- paste(unique(f[, "id"]),
					#unique(f$Species), 
					sep=";")
		print(class(f))
		plot(dist ~ frame,f,pch=20,col=ifelse(is_day==0,"black","red"),main=title)
	 }

	dev.off()
}
experiment = "20140425-175349_0"
summarise_one_experiment(experiment)
experiment = "20140516-173616_0"
summarise_one_experiment(experiment)

experiment = "20140516-173617_2"
summarise_one_experiment(experiment)
