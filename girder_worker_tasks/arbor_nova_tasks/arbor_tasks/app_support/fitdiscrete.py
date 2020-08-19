
from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

# implement fitDiscrete from geiger 

@girder_job(title='fitdiscrete')
@app.task(bind=True)
def fitdiscrete(
    self,
    tree_file,
    table_file,
    selectedColumn,
    model,
    selectedTransformation,
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
    env['selectedTransformation'] = selectedTransformation
    env['results_file'] = results_file
    r('''
  require(ape)
  require(treeplyr)
  require(geiger)

  tree <- read.tree(tree_file)
  table <- read.csv(table_file, row.names = 1, check.names = FALSE)

  td <- treedata(tree, table)
  df <- as.data.frame(td$data)
  dat <- df[,selectedColumn, drop = FALSE]
  phy <- td$phy

  result <- fitDiscrete(phy, dat, model, selectedTransformation)

  result <- t(as.data.frame(unlist(result$opt)))
  rownames(result) <- "Primary results"
  write.csv(result, results_file)
'''
    )

    return results_file 
