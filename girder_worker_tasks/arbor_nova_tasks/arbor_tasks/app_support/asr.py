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
    r('''
  require(ape)
  require(aRbor)

  plotsize = 1000

  tree <- read.tree(tree_file)
  table <- read.csv(table_file, check.names = FALSE)

  method <- "marginal"
  td <- make.treedata(tree, table)
  td1 <- select(td, as.name(selectedColumn))
  dat <- td1$dat
  type <- detectCharacterType(dat[[1]], cutoff = 0.2)

  if (type == "continuous") td1 <- forceNumeric(td1)
  if (type == "discrete") td1 <- forceFactor(td1)

  output <- ace.treedata(td1, charType = type, aceType = method)

  TH <- max(branching.times(td$phy))

  png(plot_file, width = plotsize, height = plotsize)
  plot(output, label.offset = 0.05 * TH)
  dev.off()

  res <- output[[1]]
  node_labels <- 1:td1$phy$Nnode + length(td1$phy$tip.label)
  res <- cbind(node_labels, res)
  write.csv(res, results_file)
'''
    )

    return results_file, plot_file
