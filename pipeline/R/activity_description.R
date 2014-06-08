rm(list=ls())
graphics.off()
library(lme4)
library(parallel)
generateDNLabs <- function(feature_mat, y2){
	hour_df <- aggregate(is_active ~ hour * Species, feature_mat,  mean)
	is_day_df <- aggregate(is_day ~ hour, feature_mat,  mean)
	

	# day, night incidations
	xy_dn <- approx(is_day_df$is_day, xout = seq(from = min(is_day_df$hour), to=max(is_day_df$hour), length.out=1000), rule=c(1,2) )
	xy_dn$y <- ifelse(xy_dn$y >0.5, "grey","black")
#~ 	y1 <- rep(max(hour_df$is_active) +max(hour_df$is_active) * 0.1, length(xy_dn$x))
	y1 <- -0.05
	out <- data.frame(y1, y2, x=xy_dn$x)
	out$colour <- as.character(xy_dn$y)
	return(out)
}
source("functions.R")

experiments <- c("20140425-175349_0", "20140502-175216_0")
feature_mat_list <- lapply(experiments, summarise_one_experiment, is_local=FALSE)
feature_mat <- do.call("rbind", feature_mat_list)
col_dn  <-generateDNLabs(feature_mat, y2=-5)

#remove first two hours
feature_mat <- subset(feature_mat, hour>2)
feature_mat$experiment <- as.factor(feature_mat$Date_exp_started)
#make snail id unique
feature_mat$id <- as.factor(paste(feature_mat$experiment,feature_mat$id, sep="_"))

sub_df <- subset(feature_mat, id == "20140502_8")


pdf("/tmp/descriptions.pdf",w=7, h=5)
	
sub_df$float_h <- sub_df$minutes/60
plot(dist ~ float_h, xlab="t(h)", ylab="Speed (mm/min)",
				sub_df, pch=20, ylim=c(col_dn$y2[1], max(dist)))
				
points(y2 ~ x,col_dn, col=colour, pch="|", cex=1)
abline(h=1.5, col= "red")

hour_sub_df <- aggregate( is_active ~ hour , sub_df, mean)
plot(is_active ~ hour, hour_sub_df, pch=20, type="b",
			ylim=c(col_dn$y1[1],1),
			ylab="Activity ratio (average per hour)",
			xlab="t(h)" )
points(y1 ~ x,col_dn, col=colour, pch="|", cex=1)


hour_sub_df <- aggregate( is_active ~ hour , feature_mat, mean)
hour_sub_df$sd <- aggregate( is_active ~ hour , feature_mat, sd)$is_active

plot(is_active ~ hour, hour_sub_df, pch=20, type="b",
			ylim=c(col_dn$y1[1],0.5),
			ylab="Activity ratio (average per hour)",
			xlab="t(h)" )
points(y1 ~ x,col_dn, col=colour, pch="|", cex=1)


zeit_sub_df <- aggregate( is_active ~ hour_in_day , feature_mat, mean)

x_bar_plot <- zeit_sub_df$is_active
names(x_bar_plot) <- zeit_sub_df$hour_in_day
barplot(x_bar_plot, col=rep(c("black","grey"),each=12), width=1, space=0.1, 
					xlab= "Zeitgeber time(h)",
					ylab= "Average activity ratio")
dev.off()
