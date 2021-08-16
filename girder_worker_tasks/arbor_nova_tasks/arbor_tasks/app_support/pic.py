from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

# implement PIC using ape function

@girder_job(title='PIC')
@app.task(bind=True)
def pic(
    self,
    tree_file,
    table_file,
    independent_variable,
    dependent_variable,
    **kwargs
):
    from rpy2 import robjects
    r = robjects.r
    results_file = NamedTemporaryFile(delete=False).name
    plot_file = NamedTemporaryFile(delete=False).name
    env = robjects.globalenv
    env['tree_file'] = tree_file
    env['table_file'] = table_file
    env['independent_variable'] = independent_variable
    env['dependent_variable'] = dependent_variable 
    env['results_file'] = results_file
    env['plot_file'] = plot_file
    r('''
  require(geiger)

  plotsize = 1000

  tree <- read.tree(tree_file)
  table <- read.csv(table_file, row.names = 1, check.names = FALSE)

  td <- treedata(tree, table)
  phy <- td$phy
  df <- as.data.frame(td$data)

  # Get just variables we want and name based on tips
  ind_var <- df[,independent_variable]
  names(ind_var) <- rownames(df)

  dep_var <- df[,dependent_variable]
  names(dep_var) <- rownames(df)

  # Run PIC on each variable
  pic_ind <- pic(ind_var, phy)
  pic_dep <- pic(dep_var, phy)

  # Regression forced through the origin
  reg <- lm(pic_dep ~ pic_ind + 0)
  output <- anova(reg)

  # Create summary table
  an_out <- output[,1:5] # Good stuff from anova
  sum_reg <- summary(reg)
  coef_sum <- as.data.frame(sum_reg[["coefficients"]]) # Good stuff from summary
  coef_sum <- rbind(coef_sum, c(NA,NA,NA,NA)) # Make it match sum_reg
  rownames(coef_sum)[2] <- "Residuals"

  result <- cbind(an_out, coef_sum) 
  rownames(result)[1] <- independent_variable
  write.csv(result, results_file)

  # Plot PICs like in PCM class
  pic <- cbind(pic_ind, pic_dep)
  xlab = paste0("PICs for ", independent_variable)
  ylab = paste0("PICs for ", dependent_variable)

  png(plot_file, width = plotsize, height = plotsize)
  plot(pic_dep ~ pic_ind, data = pic,
	xlab = xlab,
	ylab = ylab,
	pch = 21, bg = "grey", cex = 2, las = 1,
	cex.axis = 1.3, cex.lab = 1.5, bty = "l")
  abline(h = 0, lty = "dotted", col = "grey")
  abline(v = 0, lty = "dotted", col = "grey")
  abline(reg, lwd = 2, col = "blue")
  dev.off()  


'''
    )

    return results_file, plot_file
