
makeDf <-function(file_name, speed_up=60*5, fps=5, start_hour){
	start_hour = 18
	df <- read.table(file_name, h=T,sep=",")
	if(nrow(df) < 10)
		return(NULL)
		
	df$th <- start_hour + df$f * speed_up / fps /3600
	df$day_time <- (df$th) %% 24
	df$is_day <- ifelse(df$day_time > 9 & df$day_time < 21, T, F)
	#todo interpolate
	df$diff <- c(NA, abs(diff(complex(real=df$x, imag=df$y))))
	return(df)
	}

all_my_files <- list.files(".")


all_dfs <- lapply(all_my_files, makeDf)
df <- do.call("rbind",all_dfs)
df <- na.omit(df)

df$label <- NA

min_speed <- 10
max_speed <- 0.1

df[df$diff > min_speed, ]$label <- TRUE
df[df$diff < max_speed, ]$label <- FALSE

trainning_set <- na.omit(df)
test_set <- df[is.na(df$label),]

train_s <- trainning_set[,c("id","area", "perim", "h", "w")]

rf <- randomForest(train_s,as.factor(trainning_set$label), ntree=100)
df$preds  <- predict(rf, df[,c("id","area", "perim", "h", "w")])



pdf("/tmp/the_best.pdf",w=16,h=8)
for (d in sort(unique(df$id))){
	
	plot(runmed(diff, 5) ~ th, na.omit(subset(df,id==d)),main=d)
	for(i in 0:7){
		abline(v = 21+ 24*i,col="red",lwd=2)
		abline(v = 9+ 24*i,col="blue",lwd=2)
	}
}
dev.off()


#~ pdf("/tmp/the_best.pdf",w=16,h=8)
#~ for (i in all_my_files){
#~ 	df <- makeDf(i)
#~ 	print(nrow(df))
#~ 	if(!is.null(df))
#~ 		plot(runmed(diff, 5) ~ th, na.omit(df),main=i)
#~ 	}
#~ 
#~ dev.off()
