
from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

# implement the Phylosignal Algorithm, calling it from aRbor 

@girder_job(title='fitdiscrete')
@app.task(bind=True)
def fitdiscrete(
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
  require(aRbor)
  require(treeplyr)

  tree <- read.tree(tree_file)
  table <- read.csv(table_file, check.names = FALSE)

  td <- make.treedata(tree, table)
  td <- select(td, as.name(selectedColumn))
  phy <- td$dat
  dat <- td$dat
  type <- aRbor:::detectCharacterType(dat[[1]], cutoff = 0.2)

  if (type == "discrete") {
    result <- physigArbor(td,charType=type,signalTest="pagelLambda")
    analysisType <- "discrete lambda"
  }
  if (type == "continuous") {
    if(method=="lambda") {
      result <- physigArbor(td, charType=charType, signalTest="pagelLambda")
      analysisType <- "continuous lambda"
    }
  
    if (method=="K") {
      result <- physigArbor(td, charType=charType, signalTest="Blomberg")
      analysisType <- "continuous K"
    }
  }

  result <- t(as.data.frame(unlist(result)))
  rownames(result) <- NULL
  write.csv(results, results_file)
'''
    )

    return results_file 
