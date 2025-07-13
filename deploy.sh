#! /bin/bash

set -eux

echo -e "\033[0;32mDeploying updates to GitHub...\033[0m"

msg="rebuilding site `date`"
if [ $# -eq 1  ]
    then msg="$1"
fi

# Build the project.
hugo --buildDrafts=false -t blist

# Go To Public folder
cd public

# 确保public目录指向正确的仓库
git remote set-url origin git@github.com:HuizhiXu/huizhixu.github.io.git

# Add changes to git.
git add . -f

# Commit changes.
git commit -m "$msg"

# Push source and build repos.
git push origin master

# Come Back
cd ..

# 更新源代码仓库
git add .
git commit -m "$msg"
git push origin master