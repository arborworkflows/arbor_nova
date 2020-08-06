
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
    env['results_file'] = results_file
    r('''
  require(ape)
  require(treeplyr)
  require(geiger)

  tree <- read.tree(tree_file)
  table <- read.csv(table_file, row.names = 1, check.names = FALSE)

  # Note: using treedata instead of make.treedata because the tibble
  # was leaving out the row names, which we need for this function
  td <- treedata(tree, table)
  df <- as.data.frame(td$data)
  dat <- df[,selectedColumn, drop = FALSE]
  phy <- td$phy

  result <- fitContinuous(phy, dat, SE = 0, model)
  
  result <- t(as.data.frame(unlist(result$opt)))
  rownames(result) <- "Primary results"
  write.csv(result, results_file)
'''
    )

    return results_file 
