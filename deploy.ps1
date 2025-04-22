Write-Host "Deploying updates to GitHub..." -ForegroundColor Green

# Get commit message
$msg = "rebuilding site $(Get-Date)"
if ($args.Count -eq 1) {
    $msg = $args[0]
}

# Build the project
hugo --buildDrafts=false -t blist

# Go To Public folder
Set-Location -Path public

# Add changes to git
git add .

# Commit changes
git commit -m "$msg"

# Push source and build repos
git push origin master

# Come Back
Set-Location -Path ..

# Update main repo
git add .
git commit -m "$msg"
git push origin master