rm(list=ls())
graphics.off()
library(lme4)
library(parallel)

source("functions.R")
#~ 
getFeatures <- function(){

	experiments <- c("20140425-175349_0", "20140502-175216_0")
	feature_mat_list <- lapply(experiments, summarise_one_experiment, is_local=FALSE)
	feature_mat <- do.call("rbind", feature_mat_list)


	#remove first two hours
	feature_mat <- subset(feature_mat, hour>2)
	feature_mat$experiment <- as.factor(feature_mat$Date_exp_started)
	#make snail id unique
	feature_mat$id <- as.factor(paste(feature_mat$experiment,feature_mat$id, sep="_"))

	#we just keep what we need ;) 

	feature_mat <- subset(feature_mat, select= c(is_active, Age,
											id, minutes, Species,
											hour, hour_in_day,
											experiment,is_day))
	return(feature_mat)
}

feature_mat <- getFeatures()


predictFromOneModed <- function(mod, data_){
	print("stamp")
	return (predict(mod, feature_mat, type= "response"))
	}

predictFromBatch <- function(file_){
	
		print (file_)
		load(file_)
		print ("loaded")
		return(sapply(replics, predictFromOneModed))
	
	}
	


fixedFromOneModed <- function(mod, data_){
	print("stamp")
	print(summary(mod))
	return (fixef(mod))
	}

fixedFromBatch <- function(file_){
	
		print (file_)
		load(file_)
		print ("loaded")
		return(sapply(replics, fixedFromOneModed))
	
	}
fixed_list <- lapply(files, fixedFromBatch)
all_fixed <- do.call("cbind", fixed_list)
fixed_df<- data.frame(	q3=apply(all_fixed,1, function(v){quantile(v, 0.95)}),
						q1=apply(all_fixed,1, function(v){quantile(v, 0.05)}), 
						med=apply(all_fixed,1, median))


files <- list.files(pattern="*.Rda")
my_list <- lapply(files[1], predictFromBatch)

#~ my_list <- lapply(files, predictFromBatch)


all_preds <- do.call("cbind", my_list)


y_theo_replics_ch <- apply(all_preds,1, function(v){quantile(v, 0.95)})
y_theo_replics_cl <- apply(all_preds,1, function(v){quantile(v, 0.05)})
y_theo_replics_med <- apply(all_preds,1, median)
pred <- cbind(y_theo = y_theo_replics_med , y_theo_replics_ch, y_theo_replics_cl,feature_mat)
#~ 
#~ hour_df <- aggregate(is_active ~ hour *Age, feature_mat,  mean)


# day, night incidations
is_day_df <- aggregate(is_day ~ hour, feature_mat,  mean)
xy_dn <- approx(is_day_df$is_day, xout = seq(from = min(is_day_df$hour), to=max(is_day_df$hour), length.out=1000), rule=c(1,2) )
xy_dn$y <- ifelse(xy_dn$y >0.5, "grey","black")
y <- rep(-0.05, length(xy_dn$x))

###################################################
out <- aggregate(y_theo ~ hour * Species, pred,  mean)
out$ch <- aggregate(y_theo_replics_ch ~ hour * Species, pred,  mean)$y_theo_replics_ch
out$cl <- aggregate(y_theo_replics_cl ~ hour * Species, pred,  mean)$y_theo_replics_cl
hour_df <- aggregate(is_active ~ hour *Species, feature_mat,  mean)
pdf("/tmp/species_glmm.pdf",w=9, h=6)
	
plot(is_active ~ hour, hour_df,col=ifelse(Species=="H_a", "blue", "red"), pch=20, ylim=c(y[1], max(is_active)),
	ylab="Activity ratio (averag per hour)",
		xlab="t(h)")
points(y ~ xy_dn$x, col=xy_dn$y, pch="|", cex=1.1)
lines(y_theo ~ hour, subset(out, Species=="H_a"), col="blue", lwd=2)
lines(ch ~ hour, subset(out, Species=="H_a"), col="blue", lwd=1,lty=2)
lines(cl ~ hour, subset(out, Species=="H_a"), col="blue", lwd=1,lty=2)

lines(y_theo ~ hour, subset(out, Species=="C_n"), col="red", lwd=2)
lines(ch ~ hour, subset(out, Species=="C_n"), col="red", lwd=1,lty=2)
lines(cl ~ hour, subset(out, Species=="C_n"), col="red", lwd=1,lty=2)
dev.off()
#~ 


###################################################
pred_2 <- subset(pred, Age <4)
out <- aggregate(y_theo ~ hour * Age, pred_2,  mean)
out$ch <- aggregate(y_theo_replics_ch ~ hour * Age, pred_2,  mean)$y_theo_replics_ch
out$cl <- aggregate(y_theo_replics_cl ~ hour * Age, pred_2,  mean)$y_theo_replics_cl
hour_df <- aggregate(is_active ~ hour *Age, subset(feature_mat, Age <4),  mean)

pdf("/tmp/age_glmm.pdf",w=9, h=6)
	
plot(is_active ~ hour, hour_df,col=Age, pch=20, ylim=c(y[1], max(is_active),
		ylab="Activity ratio (averag per hour)",
		xlab="t(h)")
points(y ~ xy_dn$x, col=xy_dn$y, pch="|", cex=1.1)
age1 <- subset(out, Age==1)
lines(y_theo ~ hour, age1, col=Age, lwd=2)
lines(ch ~ hour, age1, col=Age, lwd=1,lty=2)
lines(cl ~ hour, age1, col=Age, lwd=1,lty=2)

age2 <- subset(out, Age==2)
lines(y_theo ~ hour, age2, col=Age, lwd=2)
lines(ch ~ hour, age2, col=Age, lwd=1,lty=2)
lines(cl ~ hour, age2, col=Age, lwd=1,lty=2)

age3 <- subset(out, Age==3)
lines(y_theo ~ hour, age3, col=Age, lwd=2)
lines(ch ~ hour, age3, col=Age, lwd=1,lty=2)
lines(cl ~ hour, age3, col=Age, lwd=1,lty=2)
dev.off()
