

experiment = "20140425-175349_0"
RAW_DIR <- "/data/sleepysnail/raw"
MAIN_TASK_DIR <- "/data/sleepysnail/task-output/MainTask"
list_of_targs <- "MainTask-data_sleepysnail_raw_20140425-175349_0.0b364d485ada1360a53af526fc62be6b.targets"

getIsDayDf <- function(MAIN_TASK_DIR, list_of_targs){
	path <- paste(MAIN_TASK_DIR,list_of_targs, sep="/")
	to_read <- scan(path,what="character")
	dfs <- lapply(to_read, read.csv)
	col_numbers <- sapply(dfs,ncol)
	day_night = dfs[[which(col_numbers == 1)]]
	day_night$frame <- 1:nrow(day_night)
	return(day_night)
	}
getFeatureDf <- function(MAIN_TASK_DIR, list_of_targs){
	path <- paste(MAIN_TASK_DIR,list_of_targs, sep="/")
	to_read <- scan(path,what="character")
	dfs <- lapply(to_read, read.csv)
	col_numbers <- sapply(dfs,ncol)
	features = dfs[[which(col_numbers != 1)]]
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
	print(names)
	colnames(df) <- names
	return(df)
	}


addSecondaryFeatures <- function(df){
	out <- df
	cplx <- complex(df$x, df$y)
	dist <- abs(diff(cplx))
	out$dist <- c(NA, dist)
	return(na.omit(out))
	}


is_day_df <- getIsDayDf(MAIN_TASK_DIR, list_of_targs)
feature_df <- getFeatureDf(MAIN_TASK_DIR, list_of_targs)
experiment_df <- getRawDf(RAW_DIR, experiment)

#checking number of rows
expected <- nrow(is_day_df)
observed <- table(feature_df$id)
if(any(expected != observed))
	stop("error with feature dataframe sizes")
	
feature_df <- merge(feature_df, is_day_df, by="frame")
feature_df <- na.omit(feature_df)
features_per_indiv <- split(feature_df, feature_df$id)
features_per_indiv <- lapply(features_per_indiv, addSecondaryFeatures)


pdf("/tmp/R.pdf")

for (f in features_per_indiv){
	title <- paste(unique(f$id),
				unique(f$Species), 
				sep=";")
				
	 plot(runmed(dist,11) ~ frame,f,pch=20,col=ifelse(is_day==0,"blue","red"),main=title)
 }

dev.off()
