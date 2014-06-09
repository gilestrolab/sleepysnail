rm(list=ls())
graphics.off()
library(lme4)
library(parallel)

source("functions.R")



experiments <- c("20140425-175349_0", "20140502-175216_0")
feature_mat_list <- lapply(experiments, summarise_one_experiment, is_local=FALSE)
feature_mat <- do.call("rbind", feature_mat_list)


#remove first two hours
feature_mat <- subset(feature_mat, hour>2)
feature_mat$experiment <- as.factor(feature_mat$Date_exp_started)
#make snail id unique
feature_mat$id <- as.factor(paste(feature_mat$experiment,feature_mat$id, sep="_"))

#~ we just keep what we need ;) 

feature_mat <- subset(feature_mat, select= c(is_active, Age,
										id, minutes, Species,
										hour, hour_in_day,
										experiment,is_day))



bootStrap <- function(dummy, form, data){
	df <- feature_mat[sample(1:nrow(data),size= nrow(data), replace=T),]
	mod <- glmer(form,df,family=binomial())
	return(mod)
}


all_formulas <- c(
#~ 			is_active ~  is_day * minutes + (1 | id),
#~ 			is_active ~  is_day * minutes + (1 | experiment/id),
#~ 			is_active ~  is_day * minutes *Age + (1 | id),
#~ 			is_active ~  is_day * minutes *Age + (1 | experiment/id),
			
#~ 			is_active ~  is_day * minutes *Species + (1 | experiment/id),
#~ 			is_active ~  is_day * minutes + Age + (1 | id),
#~ 			is_active ~  is_day * minutes + Age + (1 | experiment/id),
#~ 			is_active ~  is_day * minutes + Species + (1 | id),
#~ 			is_active ~  is_day * minutes + Species + (1 | experiment/id),
#~ 			is_active ~  is_day * minutes * Age * Species + (1 | experiment/id),
#~ 			is_active ~  is_day * minutes * Age * Species + (1 | id),
#~ 			is_active ~  is_day * minutes + Age + Species + (1 | id),
#~ 			is_active ~  is_day * minutes * Age + Species + (1 | id),
#~ 			is_active ~  is_day * minutes + Age * Species + (1 | id),
#~ 			is_active ~  is_day * minutes  * Species + Age + (1 | id)
			is_active ~  is_day * minutes *Species + (1 | id)
			)


# compare models:
#~ cl <- makeCluster(mc <- getOption("cl.cores", 8))
#~ clusterExport(cl=cl, varlist=c("feature_mat", "glmer"))
#~ all_models <- parLapply(cl, all_formulas, function(form, df){glmer(form,df,family=binomial())}, feature_mat)
#~ stopCluster(cl)
#~ 
#~ 
#~ write.csv(data.frame(as.character(all_formulas),sapply(all_models, AIC)))


all_models = list(glmer(all_formulas[[1]],feature_mat,family=binomial())) #fixme
aics <- sapply(all_models, AIC)

best <- all_models[[which(aics == min(aics))]]
form_best <- all_formulas[which(aics == min(aics))][[1]]

print (summary(best))

# bootstraping confidence interval
print("bootstrap MAN!")
response <- feature_mat$is_active
result_list <- as.list(letters[1:10])
names(result_list) <- letters[1:10]
for r in 1:length(result_list){
	cl <- makeCluster(mc <- getOption("cl.cores", 4))
	clusterExport(cl=cl, varlist=c("feature_mat", "form_best","glmer"))
	print(result_list[[r]])
	system.time(replics <- parLapply(cl, 32, bootStrap,form_best, feature_mat))
	result_list[[r]] <- replics
	save(,result_list)
	stopCluster(cl)
}


y_theo  <- predict(best, feature_mat, type= "response")

y_theo_replics  <- sapply(replics,predict, feature_mat, type= "response")
y_theo_replics_ch <- apply(y_theo_replics,1, function(v){quantile(v, 0.95)})
y_theo_replics_cl <- apply(y_theo_replics,1, function(v){quantile(v, 0.05)})
pred <- cbind(y_theo, y_theo_replics_ch, y_theo_replics_cl,feature_mat)

hour_df <- aggregate(is_active ~ hour * Species, feature_mat,  mean)


# day, night incidations
is_day_df <- aggregate(is_day ~ hour, feature_mat,  mean)
xy_dn <- approx(is_day_df$is_day, xout = seq(from = min(is_day_df$hour), to=max(is_day_df$hour), length.out=1000), rule=c(1,2) )
xy_dn$y <- ifelse(xy_dn$y >0.5, "grey","black")
y <- rep(-0.05, length(xy_dn$x))

#
out <- aggregate(y_theo ~ hour * Species, pred,  mean)
out$ch <- aggregate(y_theo_replics_ch ~ hour * Species, pred,  mean)$y_theo_replics_ch
out$cl <- aggregate(y_theo_replics_cl ~ hour * Species, pred,  mean)$y_theo_replics_cl

pdf("/tmp/species.glmm.pdf",w=9, h=6)
	
plot(is_active ~ hour, hour_df,col=ifelse(Species=="H_a", "blue", "red"), pch=20, ylim=c(y[1], max(is_active)))
points(y ~ xy_dn$x, col=xy_dn$y, pch="|", cex=1.1)
lines(y_theo ~ hour, subset(out, Species=="H_a"), col="blue", lwd=2)
lines(ch ~ hour, subset(out, Species=="H_a"), col="blue", lwd=1,lty=2)
lines(cl ~ hour, subset(out, Species=="H_a"), col="blue", lwd=1,lty=2)

lines(y_theo ~ hour, subset(out, Species=="C_n"), col="red", lwd=2)
lines(ch ~ hour, subset(out, Species=="C_n"), col="red", lwd=1,lty=2)
lines(cl ~ hour, subset(out, Species=="C_n"), col="red", lwd=1,lty=2)
dev.off()
