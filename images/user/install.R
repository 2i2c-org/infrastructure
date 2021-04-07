#!/usr/bin/env r

# Install devtools, so we can install versioned packages
install.packages("devtools")

# Install a bunch of R packages
# This doesn't do any dependency resolution or anything,
# so refer to `installed.packages()` for authoritative list
cran_packages <- c(
  "tidyverse", "1.3.0",
  "learnr", "0.10.1",
  "knitr", "1.29",
  "rmarkdown", "2.3",
  "Rcpp", "1.0.5",
  "reticulate", "1.16",
  "openintro", "2.0.0",
  "gridExtra", "2.3",
  "BHH2", "2016.05.31",
  "nycflights13", "1.0.1",
  "tinytex", "0.25",
  "spdep", "1.1-5",
  "shiny", "1.5.0",
  "rstan", "2.21.2",
  # https://github.com/utoronto-2i2c/jupyterhub-deploy/issues/31
  "ggforce", "0.3.2",
  "ggthemes", "4.2.0",
  # https://github.com/2i2c-org/pilot/issues/66
  "rJava", "0.9-13",
  "igraph", "1.2.6",
  "devtools", "2.3.2",
  "Rcpp", "1.0.6",
  "roxygen2", "7.1.1"
)

github_packages <- c(
  # https://github.com/utoronto-2i2c/jupyterhub-deploy/issues/31
  "cutterkom/generativeart", "56ce6beed0433748b4372bfffba0e1c9f2740f9b",
  "djnavarro/flametree", "0999530f758d074c214c068726e68786bb4698f6",
  "davidsjoberg/ggsankey", "afe822bc92c3a34d834cd787d22c15e255b36cf3"
)

for (i in seq(1, length(cran_packages), 2)) {
  devtools::install_version(
    cran_packages[i],
    version = cran_packages[i + 1]
  )
}


for (i in seq(1, length(github_packages), 2)) {
  devtools::install_github(
    github_packages[i],
    ref = github_packages[i + 1]
  )
}
