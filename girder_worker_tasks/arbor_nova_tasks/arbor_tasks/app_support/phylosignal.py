
from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

# implement the Phylosignal Algorithm, calling it from aRbor 

@girder_job(title='phylosignal')
@app.task(bind=True)
def phylosignal(
    self,
    tree_file,
    table_file,
    selectedColumn,
    method,
    selectedDiscrete,
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
    env['method'] = method 
    env['results_file'] = results_file
    env['selectedDiscrete'] = selectedDiscrete
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
  type <- treeplyr::detectCharacterType(dat[[1]], cutoff = 0.2)
 
  if (type == "discrete") {
    result <- physigArbor(td,charType=type,signalTest="pagelLambda", discreteModelType=selectedDiscrete)
    analysisType <- "discrete lambda"
  }
  if (type == "continuous") {
    if(method=="Lambda") {
      result <- physigArbor(td, charType=type, signalTest="pagelLambda")
      analysisType <- "continuous lambda"
    }

    if (method=="K") {
      result <- physigArbor(td, charType=type, signalTest="Blomberg")
      analysisType <- "continuous K"
    }

  }

  result <- t(as.data.frame(unlist(result)))
  rownames(result) <- analysisType
  if(method == "Lambda"){
    colnames(result) <- c("Log-Likelihood (Lambda fixed at 0)",
                        "Log-Likelihood (Lambda estimated)",
                        "Chi-Squared Test Statistic",
                        "Chi-Squared P Value",
                        "AICc Score (Lambda fixed at 0)",
                        "AICc Score (Lambda Estimated)",
                        "Lambda Value")
  }
  write.csv(result, results_file)
'''
    )

    return results_file 
