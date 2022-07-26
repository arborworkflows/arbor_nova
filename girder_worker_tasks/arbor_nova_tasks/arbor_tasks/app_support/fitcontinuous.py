
from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

# implement fitContinuous from geiger 

@girder_job(title='fitcontinuous')
@app.task(bind=True)
def fitcontinuous(
    self,
    tree_file,
    table_file,
    selectedColumn,
    model,
    stdError,
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
    env['model'] = model
    env['stdError'] = stdError 
    env['results_file'] = results_file
    env['plot_file'] = plot_file
    r('''
  require(ape)
  require(treeplyr)
  require(geiger)
  require(phytools)

  plotsize = 1000

  tree <- read.tree(tree_file)
  table <- read.csv(table_file, row.names = 1, check.names = FALSE)

  # Note: using treedata instead of make.treedata because the tibble
  # was leaving out the row names, which we need for this function
  td <- treedata(tree, table)
  df <- as.data.frame(td$data)
  dat <- df[,selectedColumn, drop = FALSE]
  phy <- td$phy

  # stdError might come over as a character instead as a number
  stderror <- as.numeric(stdError)
  
  # If the user inputs a non-number, conv_stderror will be NA
  # In that case, just make SE = 0
  if(is.na(stderror)) {
	stderror <- 0
  }

  result <- fitContinuous(phy = phy, dat = dat, SE = stderror, model = model)
  result <- t(as.data.frame(unlist(result$opt)))
  rownames(result) <- "Primary results"
  result <- cbind(result, stderror) # Just to double-check the SE
  write.csv(result, results_file)

  # Before the plot is made, dat needs to be named numbers
  dat <- dat[,1]
  names(dat) <- rownames(df)
  png(plot_file, width = plotsize, height = plotsize)
  phenogram(phy, dat, fsize=0.8, color = "darkgreen")
  dev.off()
'''
    )

    return results_file, plot_file 
