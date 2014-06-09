rm(list=ls())
graphics.off()
library(lme4)
library(parallel)

source("functions.R")

getFeatures <- function(){

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
	return(feature_mat)
}

feature_mat <- getFeatures()



all_formulas <- c(
			is_active ~  is_day * minutes + (1 | id),
			is_active ~  is_day * minutes *Age + (1 | id),		
			is_active ~  is_day * minutes * Species + (1 | id),
			is_active ~  is_day * minutes * Species * Age + (1 | id),
			is_active ~  is_day * minutes + Species * Age + (1 | id),
			is_active ~  is_day * minutes + Species + Age + (1 | id),
			is_active ~  is_day * minutes * Age + Species + (1 | id)
			
			)

fitOneGLMM <- function(form, data_){
	print(form)
	glmer(form,data_,family=binomial())
	}
all_models <- mclapply(all_formulas, fitOneGLMM , feature_mat, mc.cores=4)




aics <- sapply(all_models[c(-3, -7)], AIC)
forms <- sapply(all_models[c(-3, -7)], function(m)as.character(formula(m))[3])

write.csv(data.frame(forms, aics))
