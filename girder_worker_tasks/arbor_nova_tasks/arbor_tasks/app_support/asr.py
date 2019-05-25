
from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

# implement the Ancestral State Resconstruction algorithm by
# calling it from aRbor

@girder_job(title='ancestralState')
@app.task(bind=True)
def asr(
    self,
    tree_file,
    table_file,
    selectedColumn,
    **kwargs
):
    from rpy2 import robjects
    r = robjects.r
    results_file = NamedTemporaryFile(delete=False).name
    plot_file = NamedTemporaryFile(delete=False).name
    env = robjects.globalenv
    env['tree_file'] = tree_file
    env['table_file'] = table_file
    env['selectedColumn'] = selectedColumn 
    env['results_file'] = results_file
    env['plot_file'] = plot_file
 #   r('''
 # require(ape)
 # require(aRbor)
#
#  plotsize = 1000
#
#  tree <- read.tree(tree_file)
#  table <- read.csv(table_file, check.names = FALSE)
#
#  method <- "marginal"
#  td <- make.treedata(tree, table)
#  td1 <- select_(td, as.name(selectedColumn))
#  dat <- td1$dat
#  type <- aRbor:::detectCharacterType(dat[[1]], cutoff = 0.2)
#
#  if (type == "continuous") td1 <- checkNumeric(td1)
#  if (type == "discrete") td1 <- checkFactor(td1)
#
#  output <- aceArbor(td1, charType = type, aceType = method)
#
#  TH <- max(branching.times(td$phy))
#
#  png(plot_file, width = plotsize, height = plotsize)
#  plot(output, label.offset = 0.05 * TH)
#  dev.off()
#
#  res <- output[[1]]
#  node_labels <- 1:td1$phy$Nnode + length(td1$phy$tip.label)
#  res <- cbind(node_labels, res)
#  write.csv(res, results_file)
#''')

# temporarily put the PGLS definition in here until the make.treedata() function is fixed
    r('''
require(ape)
require(nlme)

tree <- read.tree(tree_file)
table <- read.csv(table_file, check.names = TRUE)
ind_variable <- make.names("PCI_limbs")
dep_variable <- make.names("PCII_head")

correlation <- "BM"

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
write.csv(modelfit_summary, results_file)

png(plot_file, width = 1000, height = 1000)
plot(table[, ind_variable], table[, dep_variable],
    pch = 21, bg = "gray80", xlab = ind_variable, ylab = dep_variable)
abline(res, lty = 2, lwd = 2)
dev.off()
''')
    return results_file, plot_file
