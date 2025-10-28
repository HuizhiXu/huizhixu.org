#! /bin/bash

set -eux

echo -e "\033[0;32mDeploying updates to GitHub...\033[0m"

msg="rebuilding site `date`"
if [ $# -eq 1  ]
    then msg="$1"
fi

# Build the project.
hugo --buildDrafts=false -t blist --minify --baseURL="https://huizhixu.github.io"

# Go To Public folder
cd public

# 如果 public 不是 git 仓库则初始化
if [ ! -d .git ]; then
    git init
    git remote add origin git@github.com:HuizhiXu/huizhixu.github.io.git
fi

git checkout master || git checkout -b master

# Add changes to git.
git add . -f

# Commit changes.
git commit -m "$msg" || echo "Nothing to commit"

# Push source and build repos.
git push origin master --force

# Come Back
cd ..

# 更新源代码仓库到 huizhixu.org
if [ ! -d .git ]; then
    git init
    git remote add origin git@github.com:HuizhiXu/huizhixu.org.git
fi

git add .
git commit -m "$msg" || echo "Nothing to commit"
git push origin master