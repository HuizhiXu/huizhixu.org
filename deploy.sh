#! /bin/bash

set -eux

echo -e "\033[0;32mDeploying updates to GitHub...\033[0m"

msg="rebuilding site `date`"
if [ $# -eq 1  ]
    then msg="$1"
fi

# Build the project.
hugo --buildDrafts=false -t blist # if using a theme, replace by `hugo -t <yourtheme>`

# Go To Public folder
cd public

# Add changes to git.
git add -f

# Commit changes.
git commit -m "$msg"

# Push source and build repos.
git push origin master

# Come Back
cd ..

git add .
git commit -m "$msg"
git push origin master