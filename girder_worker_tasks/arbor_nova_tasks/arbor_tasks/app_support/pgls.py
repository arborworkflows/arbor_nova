from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile


@girder_job(title='PGLS')
@app.task(bind=True)
def pgls(
    self,
    tree_file,
    table_file,
    correlation,
    independent_variable,
    dependent_variable,
    **kwargs
):
    from rpy2 import robjects
    r = robjects.r
    modelfit_summary_file = NamedTemporaryFile(delete=False).name
    plot_file = NamedTemporaryFile(delete=False).name
    env = robjects.globalenv
    env['tree_file'] = tree_file
    env['table_file'] = table_file
    env['correlation'] = correlation
    env['independent_variable'] = independent_variable
    env['dependent_variable'] = dependent_variable
    env['modelfit_summary_file'] = modelfit_summary_file
    env['plot_file'] = plot_file
    r('''
require(ape)
require(nlme)

tree <- read.tree(tree_file)
table <- read.csv(table_file, check.names = TRUE)
ind_variable <- make.names(independent_variable)
dep_variable <- make.names(dependent_variable)

if (correlation == "BM"){
    cor <- corBrownian(1, phy = tree)
}
if (correlation == "OU"){
    cor <- corMartins(1, phy = tree, fixed = FALSE)
}
if (correlation == "Pagel"){
    cor <- corPagel(1, phy = tree, fixed = FALSE)
    cor1 <- corPagel(1, phy = tree, fixed = TRUE)
    cor0 <- corPagel(0, phy = tree, fixed = TRUE)
}
if (correlation == "ACDC"){
    cor <- corBlomberg(1, phy = tree, fixed = FALSE)
}

fmla <- as.formula(paste(as.character(dep_variable), ' ~ ', as.character(ind_variable), sep = ""))
res <- gls(model = fmla, correlation = cor, data = table, control = glsControl(opt = "optim"))
sum_res <- summary(res)
sum_aov <- anova(res)

parameter <- coef(summary(res))
coefficients <- cbind(rownames(parameter), parameter)
colnames(coefficients)[1] <- "parameter"

if (correlation == "OU") {
    alpha <- res$modelStruct[[1]][[1]]
    coefficients <- rbind(coefficients, c("alpha", alpha, NA, NA, NA))
}

modelfit_summary <- data.frame(
    "AIC" = sum_res$AIC,
    loglik = sum_res$logLik,
    residual_SE = sum_res$sigma,
    df_total = sum_res$dims$N,
    df_residual = sum_res$dims$N - sum_res$dims$p)
write.csv(modelfit_summary, modelfit_summary_file)

png(plot_file, width = 1000, height = 1000)
plot(table[, ind_variable], table[, dep_variable],
    pch = 21, bg = "gray80", xlab = ind_variable, ylab = dep_variable)
abline(res, lty = 2, lwd = 2)
dev.off()
''')
    return modelfit_summary_file, plot_file
