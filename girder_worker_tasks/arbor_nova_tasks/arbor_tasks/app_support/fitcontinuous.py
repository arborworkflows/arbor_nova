
from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

# implement the Phylosignal Algorithm, calling it from aRbor 

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
  require(aRbor)
  require(treeplyr)

  # Function makeTreedata created to use
  #  tibble::as_tibble() instead of tbl_df()

  makeTreedata <- function (tree, data, name_column = "detect") 
  {
    if (class(tree) != "phylo") 
      stop("tree must be of class 'phylo'")
    if (is.vector(data)) {
      data <- as.matrix(data)
      colnames(data) <- "trait"
    }
    if (is.null(colnames(data))) {
      colnames(data) <- paste("trait", 1:ncol(data), 
                              sep = "")
    }
    coln <- colnames(data)
    if (name_column == "detect") {
      if (is.null(rownames(data))) {
        tmp.df <- data.frame(data)
        offset <- 0
      }
      else {
        tmp.df <- data.frame(rownames(data), data)
        offset <- 1
      }
      matches <- sapply(tmp.df, function(x) sum(x %in% tree$tip.label))
      if (all(matches == 0)) 
        stop("No matching names found between data and tree")
      name_column <- which(matches == max(matches)) - offset
    }
    else {
      if (is.character(name_column)) {
        name_column <- which(name_column == coln)[1]
      }
    }
    dat <- tibble::as_tibble(as.data.frame(lapply(1:ncol(data), function(x) type.convert(apply(data[, 
                                                                                         x, drop = FALSE], 1, as.character)))))
    colnames(dat) <- coln
    if (name_column == 0) {
      clnm <- colnames(dat)
      dat <- dat[, clnm, drop = FALSE]
      dat.label <- as.character(rownames(data))
    }
    else {
      if (is.numeric(name_column)) {
        clnm <- (1:ncol(data))[-name_column]
      }
      else {
        clnm <- colnames(dat)[-which(colnames(dat) == name_column)]
      }
      dat <- dat[, clnm, drop = FALSE]
      dat.label <- as.character(as.data.frame(data)[[name_column]])
    }
    data_not_tree <- setdiff(dat.label, tree$tip.label)
    tree_not_data <- setdiff(tree$tip.label, dat.label)
    phy <- drop.tip(tree, tree_not_data)
    dat <- filter(dat, dat.label %in% phy$tip.label)
    dat.label <- dat.label[dat.label %in% phy$tip.label]
    if (any(duplicated(dat.label))) {
      warning("Duplicated data in dataset, selecting first unique entry for each species")
      dat <- filter(dat, !duplicated(dat.label))
      dat.label <- dat.label[!duplicated(dat.label)]
    }
    o <- match(dat.label, phy$tip.label)
    dat <- arrange(dat, o)
    td <- list(phy = phy, dat = dat)
    class(td) <- c("treedata", "list")
    attributes(td)$tip.label <- phy$tip.label
    attributes(td)$dropped <- list(dropped_from_tree = data_not_tree, 
                                   dropped_from_data = tree_not_data)
    return(td)
  }

  tree <- read.tree(tree_file)
  table <- read.csv(table_file, check.names = FALSE)

  td <- makeTreedata(tree, table)
  td <- select(td, as.name(selectedColumn))
  phy <- td$phy
  dat <- td$dat
  #type <- aRbor:::detectCharacterType(dat[[1]], cutoff = 0.2)

  #if (type == "discrete") {
  #  result <- physigArbor(td,charType=type,signalTest="pagelLambda")
  #  analysisType <- "discrete lambda"
  #}
  #if (type == "continuous") {

    if(model == "lambda") {
      result <- physigArbor(td, charType="continuous", signalTest="pagelLambda")
      analysisType <- "continuous lambda"
    }

    if(model == "K") {
      result <- physigArbor(td, charType="continuous", signalTest="Blomberg")
      analysisType <- "continuous K"
    }

  #}

  result <- t(as.data.frame(unlist(result)))
  rownames(result) <- NULL
  write.csv(result, results_file)
'''
    )

    return results_file 
